"""Multi-epoch PIPE-NORMAL engine under approved ASSUMP-033 through 041."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.evaluation.temporal_outcomes import (
    TemporalOutcome,
    aggregate_temporal_outcome,
)
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import EventType, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import release_now
from edge_reproduction.simulation.events import SimulationEvent
from edge_reproduction.simulation.invariants import remaining_resources, validate_state_invariants
from edge_reproduction.simulation.pipeline import (
    CanonicalAdmission,
    PipelineProgress,
    advance_pipeline,
    canonicalize_admission,
    pipeline_complete,
)
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class TemporalRunConfig:
    """One explicit temporal run; no seed or horizon default is hidden."""

    run_id: str
    policy_seed: int
    arrival_slots: int
    numerical_tolerance: float = 1e-9
    drain_policy: str = "through_maximum_inclusive_absolute_deadline"
    output_size_provenance: str = "reproduction_assumption_input_equals_output"
    capacity_slot_normalization: str = "table_I_rates_as_one_simulation_slot"

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if isinstance(self.policy_seed, bool) or not isinstance(self.policy_seed, int):
            raise TypeError("policy_seed must be an integer")
        if isinstance(self.arrival_slots, bool) or not isinstance(self.arrival_slots, int):
            raise TypeError("arrival_slots must be an integer")
        if self.arrival_slots <= 0:
            raise ValueError("arrival_slots must be positive")
        if self.numerical_tolerance != 1e-9:
            raise ValueError("numerical_tolerance must be 1e-9 under ASSUMP-038")
        if self.drain_policy != "through_maximum_inclusive_absolute_deadline":
            raise ValueError("unsupported drain_policy")
        if self.output_size_provenance != "reproduction_assumption_input_equals_output":
            raise ValueError("unsupported output-size provenance")
        if self.capacity_slot_normalization != "table_I_rates_as_one_simulation_slot":
            raise ValueError("unsupported capacity normalization")


@dataclass(slots=True)
class TemporalRun:
    """Final state, detailed log and ASSUMP-040 metrics for one policy/seed."""

    policy_name: str
    final_state: SimulationState
    outcome: TemporalOutcome
    events: tuple[SimulationEvent, ...]
    progress_by_task: Mapping[str, PipelineProgress]
    retry_count_by_task: Mapping[str, int]
    rejection_reasons_by_task: Mapping[str, tuple[str, ...]]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        self.progress_by_task = MappingProxyType(dict(self.progress_by_task))
        self.retry_count_by_task = MappingProxyType(dict(self.retry_count_by_task))
        self.rejection_reasons_by_task = MappingProxyType(dict(self.rejection_reasons_by_task))
        self.metadata = MappingProxyType(dict(self.metadata))

    def as_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy_name,
            "outcome": self.outcome.as_dict(),
            "final_task_states": {
                task_id: status.value
                for task_id, status in sorted(self.final_state.task_states.items())
            },
            "retry_count_by_task": dict(self.retry_count_by_task),
            "rejection_reasons_by_task": {
                key: list(value) for key, value in self.rejection_reasons_by_task.items()
            },
            "progress_by_task": {
                key: {
                    "uploaded": value.uploaded,
                    "computed": value.computed,
                    "downloaded": value.downloaded,
                    "active_slots": value.active_slots,
                }
                for key, value in self.progress_by_task.items()
            },
            "events": [event.as_dict() for event in self.events],
            "metadata": dict(self.metadata),
        }


def _event(
    events: list[SimulationEvent],
    *,
    epoch: int,
    event_type: EventType,
    task: Task,
    reason: str,
    server_id: str | None = None,
    resources_before: ResourceVector | None = None,
    resources_after: ResourceVector | None = None,
    earned_utility: float = 0.0,
    price: float | None = None,
) -> None:
    events.append(
        SimulationEvent(
            len(events),
            epoch,
            event_type,
            task.task_id,
            server_id,
            resources_before,
            resources_after,
            task.utility,
            earned_utility,
            price,
            reason,
        )
    )


def synthetic_normal_temporal_tasks(tasks: tuple[Task, ...]) -> tuple[Task, ...]:
    """Apply ASSUMP-037 without mutating Stage-11B task records."""

    return tuple(
        Task(
            task.task_id,
            task.arrival_slot,
            task.deadline_slots,
            task.utility,
            task.demand,
            output_size=task.demand.storage,
        )
        for task in tasks
    )


def _pipeline_feasible_on_any_server(
    admission: CanonicalAdmission, servers: Mapping[str, Server]
) -> bool:
    return admission.pipeline_feasible and any(
        admission.reservation.fits_within(server.capacity) for server in servers.values()
    )


def _accepted_price(result: object, task_id: str, server_id: str) -> float | None:
    final_prices = getattr(result, "final_price_by_task", None)
    if isinstance(final_prices, Mapping) and task_id in final_prices:
        value = float(final_prices[task_id])
        return value if isfinite(value) else None
    round_one = getattr(result, "round_one", None)
    bids = getattr(round_one, "bids", ())
    values = [bid.price for bid in bids if bid.task_id == task_id and bid.server_id == server_id]
    return float(values[0]) if len(values) == 1 and isfinite(values[0]) else None


def run_temporal_policy(
    *,
    original_tasks: tuple[Task, ...],
    servers: tuple[Server, ...],
    policy: AllocationPolicy,
    config: TemporalRunConfig,
    policy_metadata: Mapping[str, str] | None = None,
) -> TemporalRun:
    """Execute one policy over all epochs using the approved event order."""

    if not original_tasks or not servers:
        raise ValueError("temporal run requires nonempty tasks and servers")
    task_ids = tuple(task.task_id for task in original_tasks)
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("task identifiers must be unique")
    if any(task.output_size is None for task in original_tasks):
        raise ValueError("all temporal tasks require output_size")
    if any(task.arrival_slot >= config.arrival_slots for task in original_tasks):
        raise ValueError("task arrival lies outside configured arrival envelope")

    original = {task.task_id: task for task in original_tasks}
    state = SimulationState(0, original, {server.server_id: server for server in servers})
    configured_last_slot = max(task.absolute_deadline_slot for task in original_tasks)
    last_arrival_slot = config.arrival_slots - 1
    drain_slots = configured_last_slot - last_arrival_slot
    events: list[SimulationEvent] = []
    progress: dict[str, PipelineProgress] = {}
    retry_count = {task_id: 0 for task_id in task_ids}
    rejection_reasons: dict[str, list[str]] = {task_id: [] for task_id in task_ids}
    ever_preempted: set[str] = set()
    raw_rejections = 0

    for epoch in range(configured_last_slot + 1):
        state.current_slot = epoch

        # Steps 1-3: progress prior allocations, complete/release, then expire.
        active_at_start = tuple(
            task_id
            for task_id, allocation in state.allocations.items()
            if allocation.is_active and allocation.start_slot < epoch
        )
        for task_id in active_at_start:
            allocation = state.allocations[task_id]
            source = original[task_id]
            output_size = source.output_size
            if output_size is None:
                raise StateValidationError("active temporal task has no output_size")
            before = remaining_resources(state, allocation.server_id)
            current = progress.get(task_id, PipelineProgress())
            if current.active_slots == 0:
                state.task_states[task_id] = TaskState.PIPELINE_ACTIVE
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.ACTIVATED,
                    task=source,
                    server_id=allocation.server_id,
                    resources_before=before,
                    resources_after=before,
                    reason="accepted_previous_epoch_activation",
                )
            updated_progress = advance_pipeline(
                current,
                input_size=source.demand.storage,
                total_computation=source.demand.computation,
                output_size=output_size,
                reservation=allocation.resources,
                tolerance=config.numerical_tolerance,
            )
            progress[task_id] = updated_progress
            _event(
                events,
                epoch=epoch,
                event_type=EventType.PROGRESSED,
                task=source,
                server_id=allocation.server_id,
                resources_before=before,
                resources_after=before,
                reason=(
                    f"pipeline_slot={updated_progress.active_slots};"
                    f"uploaded={updated_progress.uploaded};"
                    f"computed={updated_progress.computed};"
                    f"downloaded={updated_progress.downloaded}"
                ),
            )
            if pipeline_complete(
                updated_progress,
                input_size=source.demand.storage,
                total_computation=source.demand.computation,
                output_size=output_size,
                tolerance=config.numerical_tolerance,
            ):
                state = release_now(state, task_id=task_id, terminal_state=TaskState.COMPLETED)
                after = remaining_resources(state, allocation.server_id)
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.COMPLETED,
                    task=source,
                    server_id=allocation.server_id,
                    resources_before=before,
                    resources_after=after,
                    earned_utility=source.utility,
                    reason="all_pipeline_activities_complete_by_inclusive_deadline",
                )

        for task_id in task_ids:
            if state.task_states[task_id] in {
                TaskState.COMPLETED,
                TaskState.PREEMPTED,
                TaskState.EXPIRED,
            }:
                continue
            source = original[task_id]
            if epoch < source.absolute_deadline_slot:
                continue
            expiring_allocation = state.allocations.get(task_id)
            if expiring_allocation is not None and expiring_allocation.is_active:
                before = remaining_resources(state, expiring_allocation.server_id)
                state = release_now(state, task_id=task_id, terminal_state=TaskState.EXPIRED)
                after = remaining_resources(state, expiring_allocation.server_id)
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.EXPIRED,
                    task=source,
                    server_id=expiring_allocation.server_id,
                    resources_before=before,
                    resources_after=after,
                    reason="active_pipeline_incomplete_after_inclusive_deadline_opportunity",
                )
            elif source.arrival_slot <= epoch:
                state.task_states[task_id] = TaskState.EXPIRED
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.EXPIRED,
                    task=source,
                    reason="waiting_task_no_remaining_completion_opportunity",
                )

        # Step 4: arrivals.
        for task_id in task_ids:
            source = original[task_id]
            if source.arrival_slot == epoch:
                state.task_states[task_id] = TaskState.WAITING_FOR_BID
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.ARRIVED,
                    task=source,
                    reason="workload_arrival_registered",
                )

        # Steps 5-7: canonicalize eligible jobs, auction once, atomically commit.
        eligible = tuple(
            task_id
            for task_id in task_ids
            if state.task_states[task_id] in {TaskState.WAITING_FOR_BID, TaskState.WAITING_RETRY}
            and original[task_id].arrival_slot < epoch
        )
        requesting: list[str] = []
        for task_id in eligible:
            if state.task_states[task_id] is TaskState.WAITING_RETRY:
                retry_count[task_id] += 1
            source = original[task_id]
            remaining_computation = source.demand.computation - progress.get(
                task_id, PipelineProgress()
            ).computed
            admission = canonicalize_admission(
                source,
                auction_epoch=epoch,
                remaining_computation=remaining_computation,
                tolerance=config.numerical_tolerance,
            )
            if not _pipeline_feasible_on_any_server(admission, state.servers):
                state.task_states[task_id] = TaskState.EXPIRED
                rejection_reasons[task_id].append(admission.reason)
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.EXPIRED,
                    task=source,
                    reason=f"canonical_admission_infeasible:{admission.reason}",
                )
                continue
            state.tasks[task_id] = admission.task
            requesting.append(task_id)

        if requesting:
            before_auction = state.snapshot()
            time_remaining = {
                task_id: float(original[task_id].absolute_deadline_slot - epoch)
                for task_id in task_ids
                if original[task_id].absolute_deadline_slot - epoch > 0
            }
            result = policy.run(
                state,
                requesting_task_ids=tuple(requesting),
                time_remaining_by_task=time_remaining,
                epoch=epoch,
            )
            state = result.final_state
            preempted_ids = tuple(getattr(result, "preempted_task_ids", ()))
            for task_id in preempted_ids:
                ever_preempted.add(task_id)
                allocation = state.allocations[task_id]
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.PREEMPTED,
                    task=original[task_id],
                    server_id=allocation.server_id,
                    resources_before=remaining_resources(before_auction, allocation.server_id),
                    resources_after=remaining_resources(state, allocation.server_id),
                    reason="policy_round_two_terminal_preemption",
                )
            selected_server_by_task = getattr(result, "selected_server_by_task", {})
            for task_id in result.accepted_task_ids:
                allocation = state.allocations[task_id]
                state.task_states[task_id] = TaskState.ACCEPTED
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.ACCEPTED,
                    task=original[task_id],
                    server_id=allocation.server_id,
                    resources_before=remaining_resources(before_auction, allocation.server_id),
                    resources_after=remaining_resources(state, allocation.server_id),
                    price=_accepted_price(result, task_id, allocation.server_id),
                    reason="atomic_round_two_admission_activation_next_epoch",
                )
            for task_id in result.rejected_task_ids:
                raw_rejections += 1
                rejection_reasons[task_id].append("policy_round_two_rejection")
                _event(
                    events,
                    epoch=epoch,
                    event_type=EventType.REJECTED,
                    task=original[task_id],
                    server_id=selected_server_by_task.get(task_id),
                    reason="policy_round_two_rejection_nonterminal",
                )
                source = original[task_id]
                next_epoch = epoch + 1
                next_admission = canonicalize_admission(
                    source,
                    auction_epoch=next_epoch,
                    remaining_computation=source.demand.computation,
                    tolerance=config.numerical_tolerance,
                )
                if _pipeline_feasible_on_any_server(next_admission, state.servers):
                    state.task_states[task_id] = TaskState.WAITING_RETRY
                    _event(
                        events,
                        epoch=epoch,
                        event_type=EventType.RETRY_SCHEDULED,
                        task=source,
                        reason=f"completed_retry_attempts={retry_count[task_id]};next_epoch={next_epoch}",
                    )
                else:
                    state.task_states[task_id] = TaskState.EXPIRED
                    rejection_reasons[task_id].append(next_admission.reason)
                    _event(
                        events,
                        epoch=epoch,
                        event_type=EventType.EXPIRED,
                        task=source,
                        reason=f"post_rejection_next_epoch_infeasible:{next_admission.reason}",
                    )

        validate_state_invariants(state)
        terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
        all_terminal = all(status in terminal for status in state.task_states.values())
        if epoch >= last_arrival_slot and all_terminal:
            break

    nonterminal = {
        task_id
        for task_id, status in state.task_states.items()
        if status not in {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
    }
    if nonterminal:
        raise StateValidationError(
            "nonterminal tasks after configured_last_slot="
            f"{configured_last_slot}: {sorted(nonterminal)}"
        )
    outcome = aggregate_temporal_outcome(
        state,
        ever_preempted_task_ids=ever_preempted,
        raw_auction_rejection_count=raw_rejections,
    )
    metadata = {
        "baseline": "arXiv:2403.15665v2_2024",
        "scientific_label": "reproduction_under_ASSUMP-033_through_ASSUMP-043",
        "run_id": config.run_id,
        "policy": policy.name,
        "policy_seed": str(config.policy_seed),
        "arrival_slots": str(config.arrival_slots),
        "last_arrival_slot": str(last_arrival_slot),
        "configured_last_slot": str(configured_last_slot),
        "drain_slots": str(drain_slots),
        "drain_policy": config.drain_policy,
        "numerical_tolerance": repr(config.numerical_tolerance),
        "output_size_provenance": config.output_size_provenance,
        "capacity_slot_normalization": config.capacity_slot_normalization,
        "auction_time_advances_simulation": "false",
        "full_100_slot_30_repeat_run": "false",
    }
    metadata.update(policy_metadata or {})
    return TemporalRun(
        policy.name,
        state,
        outcome,
        tuple(events),
        progress,
        retry_count,
        {key: tuple(value) for key, value in rejection_reasons.items()},
        metadata,
    )
