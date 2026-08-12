"""A deterministic scripted event engine used before Stage-10 policies exist."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from edge_reproduction.algorithms.feasibility import resources_available_after_preemptions
from edge_reproduction.evaluation.utility import all_or_nothing_utility
from edge_reproduction.models._validation import (
    ensure_identifier,
    ensure_nonnegative_integer,
    ensure_unique,
)
from edge_reproduction.models.config import ExperimentConfig
from edge_reproduction.models.enums import (
    AssignmentFlowSemantics,
    DeadlineBoundary,
    EventType,
    ResultStatus,
    ScriptedAction,
    TaskState,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.result import ExperimentResult
from edge_reproduction.simulation.accounting import (
    allocate_now,
    preempt_and_allocate_now,
    release_now,
)
from edge_reproduction.simulation.events import SimulationEvent
from edge_reproduction.simulation.invariants import (
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState
from edge_reproduction.simulation.time import meets_deadline


@dataclass(frozen=True, slots=True)
class SimulationCommand:
    """An explicit decision command for the policy-free Stage-9 simulator."""

    time: int
    order: int
    action: ScriptedAction
    task_id: str
    reason: str
    server_id: str | None = None
    victim_task_ids: tuple[str, ...] = field(default_factory=tuple)
    resources: ResourceVector | None = None
    price: float | None = None

    def __post_init__(self) -> None:
        ensure_nonnegative_integer("time", self.time)
        ensure_nonnegative_integer("order", self.order)
        if not isinstance(self.action, ScriptedAction):
            raise TypeError("action must be a ScriptedAction")
        ensure_identifier("task_id", self.task_id)
        ensure_identifier("reason", self.reason)
        if self.server_id is not None:
            ensure_identifier("server_id", self.server_id)
        victims = tuple(self.victim_task_ids)
        for victim_id in victims:
            ensure_identifier("victim_task_id", victim_id)
        ensure_unique("victim_task_ids", victims)
        object.__setattr__(self, "victim_task_ids", victims)
        if self.resources is not None and not isinstance(self.resources, ResourceVector):
            raise TypeError("resources must be a ResourceVector or None")
        if self.price is not None:
            if isinstance(self.price, bool) or not isinstance(self.price, (int, float)):
                raise TypeError("price must be a real number or None")
            if not isfinite(self.price):
                raise ValueError("price must be finite")
        if (
            self.action
            in {
                ScriptedAction.ACCEPT,
                ScriptedAction.PREEMPT_AND_ACCEPT,
            }
            and self.server_id is None
        ):
            raise ValueError("admission commands require server_id")
        if self.action is ScriptedAction.PREEMPT_AND_ACCEPT and not victims:
            raise ValueError("preemption command requires at least one victim")


@dataclass(frozen=True, slots=True)
class SimulationRun:
    """Final state, event log and paper-aligned summary for one scripted run."""

    final_state: SimulationState
    events: tuple[SimulationEvent, ...]
    experiment_result: ExperimentResult
    expired_task_ids: tuple[str, ...]


def _event(
    events: list[SimulationEvent],
    *,
    time: int,
    event_type: EventType,
    task_id: str,
    server_id: str | None,
    resources_before: ResourceVector | None,
    resources_after: ResourceVector | None,
    utility: float,
    earned_utility: float = 0.0,
    price: float | None = None,
    reason: str,
) -> None:
    events.append(
        SimulationEvent(
            sequence=len(events),
            time=time,
            event_type=event_type,
            task_id=task_id,
            server_id=server_id,
            resources_before=resources_before,
            resources_after=resources_after,
            utility=utility,
            earned_utility=earned_utility,
            price=price,
            reason=reason,
        )
    )


def _expire_overdue_active_tasks(
    state: SimulationState,
    events: list[SimulationEvent],
    *,
    boundary: DeadlineBoundary,
) -> SimulationState:
    updated = state
    active_task_ids = tuple(
        task_id for task_id, allocation in updated.allocations.items() if allocation.is_active
    )
    for task_id in active_task_ids:
        task = updated.tasks[task_id]
        if meets_deadline(task, updated.current_slot, boundary=boundary):
            continue
        allocation = updated.allocations[task_id]
        before = remaining_resources(updated, allocation.server_id)
        updated = release_now(updated, task_id=task_id, terminal_state=TaskState.EXPIRED)
        after = remaining_resources(updated, allocation.server_id)
        _event(
            events,
            time=updated.current_slot,
            event_type=EventType.EXPIRED,
            task_id=task_id,
            server_id=allocation.server_id,
            resources_before=before,
            resources_after=after,
            utility=task.utility,
            reason="inclusive_deadline_missed",
        )
    return updated


def run_scripted_simulation(
    initial_state: SimulationState,
    commands: tuple[SimulationCommand, ...],
    config: ExperimentConfig,
    *,
    deadline_boundary: DeadlineBoundary,
    assignment_semantics: AssignmentFlowSemantics,
) -> SimulationRun:
    """Execute explicit commands while enforcing resources and approved semantics."""

    config.ensure_resolved()
    if not isinstance(deadline_boundary, DeadlineBoundary):
        raise TypeError("deadline_boundary must be a DeadlineBoundary")
    if not isinstance(assignment_semantics, AssignmentFlowSemantics):
        raise TypeError("assignment_semantics must be an AssignmentFlowSemantics")
    if deadline_boundary is not DeadlineBoundary.INCLUSIVE:
        raise ValueError("this run does not match approved assumption ASSUMP-001")
    if assignment_semantics is not AssignmentFlowSemantics.SELECTED_SERVER_ONLY:
        raise ValueError("this run does not match approved assumption ASSUMP-002")

    ordered = tuple(sorted(commands, key=lambda item: (item.time, item.order)))
    keys = tuple((item.time, item.order) for item in ordered)
    if len(keys) != len(set(keys)):
        raise ValueError("command (time, order) pairs must be unique")
    if any(command.time >= config.horizon_slots for command in ordered):
        raise ValueError("command time must be inside the configured horizon")

    commands_by_time: dict[int, list[SimulationCommand]] = {}
    for command in ordered:
        commands_by_time.setdefault(command.time, []).append(command)

    state = initial_state.snapshot()
    events: list[SimulationEvent] = []
    arrived: set[str] = set()

    for time in range(config.horizon_slots):
        state.current_slot = time
        state = _expire_overdue_active_tasks(state, events, boundary=deadline_boundary)
        for command in commands_by_time.get(time, []):
            task = state.tasks[command.task_id]

            if command.action is ScriptedAction.ARRIVE:
                if command.task_id in arrived:
                    raise ValueError("task cannot arrive twice")
                if task.arrival_slot != time:
                    raise ValueError("arrival command must match Task.arrival_slot")
                arrived.add(command.task_id)
                state.task_states[command.task_id] = TaskState.WAITING_FOR_BID
                _event(
                    events,
                    time=time,
                    event_type=EventType.ARRIVED,
                    task_id=command.task_id,
                    server_id=None,
                    resources_before=None,
                    resources_after=None,
                    utility=task.utility,
                    reason=command.reason,
                )
                continue

            if command.task_id not in arrived:
                raise ValueError("task must arrive before another command")

            if command.action is ScriptedAction.ACCEPT:
                assert command.server_id is not None
                before = remaining_resources(state, command.server_id)
                state = allocate_now(
                    state,
                    task_id=command.task_id,
                    server_id=command.server_id,
                    resources=command.resources,
                )
                after = remaining_resources(state, command.server_id)
                _event(
                    events,
                    time=time,
                    event_type=EventType.ACCEPTED,
                    task_id=command.task_id,
                    server_id=command.server_id,
                    resources_before=before,
                    resources_after=after,
                    utility=task.utility,
                    price=command.price,
                    reason=command.reason,
                )
            elif command.action is ScriptedAction.REJECT:
                state.task_states[command.task_id] = TaskState.REJECTED
                _event(
                    events,
                    time=time,
                    event_type=EventType.REJECTED,
                    task_id=command.task_id,
                    server_id=None,
                    resources_before=None,
                    resources_after=None,
                    utility=task.utility,
                    price=command.price,
                    reason=command.reason,
                )
            elif command.action is ScriptedAction.PREEMPT_AND_ACCEPT:
                assert command.server_id is not None
                before = remaining_resources(state, command.server_id)
                after_release = resources_available_after_preemptions(
                    state, command.server_id, command.victim_task_ids
                )
                state = preempt_and_allocate_now(
                    state,
                    incoming_task_id=command.task_id,
                    server_id=command.server_id,
                    victim_task_ids=command.victim_task_ids,
                )
                after_admission = remaining_resources(state, command.server_id)
                for victim_id in command.victim_task_ids:
                    _event(
                        events,
                        time=time,
                        event_type=EventType.PREEMPTED,
                        task_id=victim_id,
                        server_id=command.server_id,
                        resources_before=before,
                        resources_after=after_release,
                        utility=state.tasks[victim_id].utility,
                        reason=command.reason,
                    )
                _event(
                    events,
                    time=time,
                    event_type=EventType.ACCEPTED,
                    task_id=command.task_id,
                    server_id=command.server_id,
                    resources_before=after_release,
                    resources_after=after_admission,
                    utility=task.utility,
                    price=command.price,
                    reason=command.reason,
                )
            elif command.action is ScriptedAction.COMPLETE:
                allocation = state.allocations[command.task_id]
                if not meets_deadline(task, time, boundary=deadline_boundary):
                    raise ValueError("completion command misses the approved inclusive deadline")
                before = remaining_resources(state, allocation.server_id)
                state = release_now(
                    state, task_id=command.task_id, terminal_state=TaskState.COMPLETED
                )
                after = remaining_resources(state, allocation.server_id)
                earned = all_or_nothing_utility(
                    task, assignment=1, completion_indicator=1, deadline_met=True
                )
                _event(
                    events,
                    time=time,
                    event_type=EventType.COMPLETED,
                    task_id=command.task_id,
                    server_id=allocation.server_id,
                    resources_before=before,
                    resources_after=after,
                    utility=task.utility,
                    earned_utility=earned,
                    reason=command.reason,
                )
        validate_state_invariants(state)

    completed = tuple(
        task_id
        for task_id, task_state in state.task_states.items()
        if task_state is TaskState.COMPLETED
    )
    rejected = tuple(
        task_id
        for task_id, task_state in state.task_states.items()
        if task_state is TaskState.REJECTED
    )
    preempted = tuple(
        dict.fromkeys(event.task_id for event in events if event.event_type is EventType.PREEMPTED)
    )
    expired = tuple(
        task_id
        for task_id, task_state in state.task_states.items()
        if task_state is TaskState.EXPIRED
    )
    result = ExperimentResult(
        run_id="stage9-smoke-seed-20240809",
        experiment_id=config.experiment_id,
        method=config.method,
        random_seed=config.random_seed,
        completed_task_ids=completed,
        rejected_task_ids=rejected,
        ever_preempted_task_ids=preempted,
        completed_utility=sum(state.tasks[item].utility for item in completed),
        rejected_utility=sum(state.tasks[item].utility for item in rejected),
        preempted_utility=sum(state.tasks[item].utility for item in preempted),
        event_count=len(events),
        status=ResultStatus.SUCCEEDED,
        metadata={
            "deadline_boundary": deadline_boundary.value,
            "assignment_flow_semantics": assignment_semantics.value,
            "scenario": "stage9_scripted_smoke",
        },
    )
    return SimulationRun(state, tuple(events), result, expired)
