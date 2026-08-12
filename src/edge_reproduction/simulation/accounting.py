"""Transactional allocation, release and resource-safe preemption operations."""

from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.invariants import (
    has_sufficient_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState

RELEASE_STATES = frozenset({TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED})


def allocate_now(
    state: SimulationState,
    *,
    task_id: str,
    server_id: str,
    resources: ResourceVector | None = None,
) -> SimulationState:
    """Return a new state with a capacity-safe allocation at ``current_slot``."""

    if task_id not in state.tasks:
        raise KeyError(f"unknown task_id: {task_id}")
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    existing = state.allocations.get(task_id)
    if existing is not None:
        if existing.is_active:
            raise StateValidationError("task already has an active allocation")
        raise UnresolvedDecisionError(
            "re-allocation after a completed, expired or preempted allocation depends on "
            "the paper's unspecified retry semantics"
        )
    if state.task_states[task_id] in {
        TaskState.COMPLETED,
        TaskState.PREEMPTED,
        TaskState.EXPIRED,
    }:
        raise StateValidationError("terminal task cannot be allocated again")

    selected_resources = state.tasks[task_id].demand if resources is None else resources
    if not isinstance(selected_resources, ResourceVector):
        raise TypeError("resources must be a ResourceVector or None")
    if not has_sufficient_resources(state, server_id, selected_resources):
        raise StateValidationError("insufficient residual resources")

    updated = state.snapshot()
    updated.allocations[task_id] = Allocation(
        task_id=task_id,
        server_id=server_id,
        resources=selected_resources,
        start_slot=state.current_slot,
    )
    updated.task_states[task_id] = TaskState.ACCEPTED
    validate_state_invariants(updated)
    return updated


def release_now(
    state: SimulationState, *, task_id: str, terminal_state: TaskState
) -> SimulationState:
    """Return a new state after releasing one active allocation at the current slot."""

    if terminal_state not in RELEASE_STATES:
        raise ValueError("terminal_state must be COMPLETED, PREEMPTED or EXPIRED")
    try:
        allocation = state.allocations[task_id]
    except KeyError as error:
        raise StateValidationError("task has no allocation to release") from error
    if not allocation.is_active:
        raise StateValidationError("task allocation is already released")

    updated = state.snapshot()
    updated.allocations[task_id] = Allocation(
        task_id=allocation.task_id,
        server_id=allocation.server_id,
        resources=allocation.resources,
        start_slot=allocation.start_slot,
        end_slot=state.current_slot,
    )
    updated.task_states[task_id] = terminal_state
    validate_state_invariants(updated)
    return updated


def preempt_and_allocate_now(
    state: SimulationState,
    *,
    incoming_task_id: str,
    server_id: str,
    victim_task_ids: tuple[str, ...],
) -> SimulationState:
    """Atomically release victims and admit an incoming task.

    This function executes an already-made preemption decision. It does not
    select victims or choose between the conflicting 5% rules; those decisions
    belong to feasibility/policy code and must be explicit.
    """

    if not victim_task_ids:
        raise ValueError("at least one victim_task_id is required")
    if len(victim_task_ids) != len(set(victim_task_ids)):
        raise ValueError("victim_task_ids must not contain duplicates")
    candidate = state.snapshot()
    for victim_task_id in victim_task_ids:
        allocation = candidate.allocations.get(victim_task_id)
        if allocation is None or not allocation.is_active:
            raise StateValidationError("every victim must have an active allocation")
        if allocation.server_id != server_id:
            raise StateValidationError("every victim must be active on the selected server")
        candidate = release_now(
            candidate, task_id=victim_task_id, terminal_state=TaskState.PREEMPTED
        )
    candidate = allocate_now(
        candidate,
        task_id=incoming_task_id,
        server_id=server_id,
    )
    validate_state_invariants(candidate)
    return candidate
