"""ASSUMP-036-A/037/038 deterministic pipeline admission and progress."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite

from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


@dataclass(frozen=True, slots=True)
class PipelineProgress:
    """Cumulative pipeline work for one task allocation."""

    uploaded: float = 0.0
    computed: float = 0.0
    downloaded: float = 0.0
    active_slots: int = 0

    def __post_init__(self) -> None:
        values = (self.uploaded, self.computed, self.downloaded)
        if any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError("pipeline cumulative progress must be finite and non-negative")
        if isinstance(self.active_slots, bool) or not isinstance(self.active_slots, int):
            raise TypeError("active_slots must be an integer")
        if self.active_slots < 0:
            raise ValueError("active_slots must be non-negative")


@dataclass(frozen=True, slots=True)
class CanonicalAdmission:
    """One retry-specific fixed reservation and its feasibility evidence."""

    task: Task
    auction_epoch: int
    service_slots: int
    compute_eligible_slots: int
    reservation: ResourceVector
    isolated_final_progress: PipelineProgress
    pipeline_feasible: bool
    reason: str


def _require_tolerance(tolerance: float) -> float:
    if not isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("tolerance must be finite and non-negative")
    return float(tolerance)


def advance_pipeline(
    progress: PipelineProgress,
    *,
    input_size: float,
    total_computation: float,
    output_size: float,
    reservation: ResourceVector,
    tolerance: float,
) -> PipelineProgress:
    """Advance one active slot in upload → computation → download order."""

    tolerance = _require_tolerance(tolerance)
    totals = (input_size, total_computation, output_size)
    if any(not isfinite(value) or value <= 0.0 for value in totals):
        raise ValueError("pipeline totals must be finite and positive")

    next_active_slot = progress.active_slots + 1
    uploaded = min(input_size, progress.uploaded + reservation.upload)

    computed = progress.computed
    if next_active_slot >= 2:
        predecessor_limit = total_computation * min(uploaded / input_size, 1.0)
        computed = min(
            total_computation,
            progress.computed + reservation.computation,
            predecessor_limit,
        )

    downloaded = progress.downloaded
    if next_active_slot >= 3:
        predecessor_limit = output_size * min(computed / total_computation, 1.0)
        downloaded = min(
            output_size,
            progress.downloaded + reservation.download,
            predecessor_limit,
        )

    def normalize(value: float, total: float) -> float:
        return total if isclose(value, total, rel_tol=0.0, abs_tol=tolerance) else value

    updated = PipelineProgress(
        normalize(uploaded, input_size),
        normalize(computed, total_computation),
        normalize(downloaded, output_size),
        next_active_slot,
    )
    if updated.computed / total_computation > updated.uploaded / input_size + tolerance:
        raise AssertionError("computation advanced beyond proportional uploaded input")
    if updated.downloaded / output_size > updated.computed / total_computation + tolerance:
        raise AssertionError("download advanced beyond proportional computation")
    return updated


def pipeline_complete(
    progress: PipelineProgress,
    *,
    input_size: float,
    total_computation: float,
    output_size: float,
    tolerance: float,
) -> bool:
    """Return whether all three cumulative activities reached their totals."""

    tolerance = _require_tolerance(tolerance)
    return (
        progress.uploaded >= input_size - tolerance
        and progress.computed >= total_computation - tolerance
        and progress.downloaded >= output_size - tolerance
    )


def canonicalize_admission(
    task: Task,
    *,
    auction_epoch: int,
    remaining_computation: float,
    tolerance: float,
) -> CanonicalAdmission:
    """Apply ASSUMP-036-A and dry-run ASSUMP-038 through the inclusive deadline."""

    if isinstance(auction_epoch, bool) or not isinstance(auction_epoch, int):
        raise TypeError("auction_epoch must be an integer")
    if auction_epoch < 0:
        raise ValueError("auction_epoch must be non-negative")
    if not isfinite(remaining_computation) or remaining_computation <= 0.0:
        raise ValueError("remaining_computation must be finite and positive")
    tolerance = _require_tolerance(tolerance)
    if task.output_size is None:
        raise ValueError("temporal pipeline admission requires output_size")

    service_slots = task.absolute_deadline_slot - auction_epoch
    compute_eligible_slots = service_slots - 1
    if service_slots <= 0 or compute_eligible_slots <= 0:
        return CanonicalAdmission(
            task,
            auction_epoch,
            service_slots,
            compute_eligible_slots,
            task.demand,
            PipelineProgress(),
            False,
            "insufficient_computation_eligible_slots",
        )

    reservation = ResourceVector(
        storage=task.demand.storage,
        computation=remaining_computation / compute_eligible_slots,
        upload=task.demand.upload,
        download=task.demand.download,
    )
    canonical = Task(
        task.task_id,
        task.arrival_slot,
        task.deadline_slots,
        task.utility,
        reservation,
        task.output_size,
    )
    progress = PipelineProgress()
    for _ in range(service_slots):
        progress = advance_pipeline(
            progress,
            input_size=task.demand.storage,
            total_computation=remaining_computation,
            output_size=task.output_size,
            reservation=reservation,
            tolerance=tolerance,
        )
    feasible = pipeline_complete(
        progress,
        input_size=task.demand.storage,
        total_computation=remaining_computation,
        output_size=task.output_size,
        tolerance=tolerance,
    )
    return CanonicalAdmission(
        canonical,
        auction_epoch,
        service_slots,
        compute_eligible_slots,
        reservation,
        progress,
        feasible,
        "isolated_pipeline_completes" if feasible else "isolated_pipeline_misses_deadline",
    )
