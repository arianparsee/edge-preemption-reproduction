import pytest

from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.pipeline import (
    PipelineProgress,
    advance_pipeline,
    canonicalize_admission,
    pipeline_complete,
)


def make_task(*, deadline: int = 4, upload: float = 2.0, download: float = 4.0) -> Task:
    return Task(
        "task",
        0,
        deadline,
        12.0,
        ResourceVector(4.0, 6.0, upload, download),
        output_size=4.0,
    )


def test_three_successive_active_slots_start_pipeline_stages() -> None:
    reservation = ResourceVector(4.0, 2.0, 2.0, 2.0)
    first = advance_pipeline(
        PipelineProgress(),
        input_size=4.0,
        total_computation=6.0,
        output_size=4.0,
        reservation=reservation,
        tolerance=1e-9,
    )
    second = advance_pipeline(
        first,
        input_size=4.0,
        total_computation=6.0,
        output_size=4.0,
        reservation=reservation,
        tolerance=1e-9,
    )
    third = advance_pipeline(
        second,
        input_size=4.0,
        total_computation=6.0,
        output_size=4.0,
        reservation=reservation,
        tolerance=1e-9,
    )

    assert first == PipelineProgress(2.0, 0.0, 0.0, 1)
    assert second == PipelineProgress(4.0, 2.0, 0.0, 2)
    assert third == PipelineProgress(4.0, 4.0, 2.0, 3)


def test_canonicalization_uses_only_computation_eligible_slots() -> None:
    admission = canonicalize_admission(
        make_task(deadline=4),
        auction_epoch=1,
        remaining_computation=6.0,
        tolerance=1e-9,
    )

    assert admission.service_slots == 3
    assert admission.compute_eligible_slots == 2
    assert admission.reservation.computation == 3.0
    assert admission.pipeline_feasible is True
    assert pipeline_complete(
        admission.isolated_final_progress,
        input_size=4.0,
        total_computation=6.0,
        output_size=4.0,
        tolerance=1e-9,
    )


def test_dry_run_rejects_insufficient_download_bandwidth() -> None:
    admission = canonicalize_admission(
        make_task(deadline=4, download=1.0),
        auction_epoch=1,
        remaining_computation=6.0,
        tolerance=1e-9,
    )
    assert admission.pipeline_feasible is False
    assert admission.reason == "isolated_pipeline_misses_deadline"


def test_too_late_admission_is_infeasible_without_division_by_zero() -> None:
    admission = canonicalize_admission(
        make_task(deadline=4),
        auction_epoch=3,
        remaining_computation=6.0,
        tolerance=1e-9,
    )
    assert admission.compute_eligible_slots == 0
    assert admission.pipeline_feasible is False
    assert admission.reason == "insufficient_computation_eligible_slots"


def test_pipeline_rejects_unapproved_tolerance() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        advance_pipeline(
            PipelineProgress(),
            input_size=1.0,
            total_computation=1.0,
            output_size=1.0,
            reservation=ResourceVector(1.0, 1.0, 1.0, 1.0),
            tolerance=-1.0,
        )
