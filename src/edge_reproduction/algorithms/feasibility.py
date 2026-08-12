"""Retention and preemption feasibility without selecting an algorithm policy."""

from __future__ import annotations

from math import isfinite

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import PreemptionThresholdSemantics
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


def utility_time_ratio(utility: float, time_remaining: float) -> float:
    """Return the paper's ``utility/time_remaining`` ranking value."""

    for name, value in (("utility", utility), ("time_remaining", time_remaining)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a real number")
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if time_remaining <= 0:
        raise ValueError("time_remaining must be positive")
    return float(utility / time_remaining)


def meets_preemption_threshold(
    *,
    incoming_utility: float,
    incoming_time: float,
    current_utility: float,
    current_time_remaining: float,
    semantics: PreemptionThresholdSemantics = PreemptionThresholdSemantics.PROSE,
) -> bool:
    """Evaluate the 5% rule; ASSUMP-004 approves the prose interpretation."""

    incoming_ratio = utility_time_ratio(incoming_utility, incoming_time)
    current_ratio = utility_time_ratio(current_utility, current_time_remaining)
    if not isinstance(semantics, PreemptionThresholdSemantics):
        raise TypeError("semantics must be a PreemptionThresholdSemantics")
    if semantics is PreemptionThresholdSemantics.PROSE:
        return incoming_ratio >= 1.05 * current_ratio
    return 1.05 * incoming_ratio >= current_ratio


def can_retain_and_admit(state: SimulationState, task: Task, server_id: str) -> bool:
    """Check admission using only residual resources, with no victim removal."""

    if not isinstance(task, Task):
        raise TypeError("task must be a Task")
    return task.demand.fits_within(remaining_resources(state, server_id))


def resources_available_after_preemptions(
    state: SimulationState, server_id: str, victim_task_ids: tuple[str, ...]
) -> ResourceVector:
    """Return residual resources plus active reservations of explicit victims."""

    if len(victim_task_ids) != len(set(victim_task_ids)):
        raise ValueError("victim_task_ids must not contain duplicates")
    available = remaining_resources(state, server_id)
    for task_id in victim_task_ids:
        allocation = state.allocations.get(task_id)
        if allocation is None or not allocation.is_active:
            raise StateValidationError("each victim must have an active allocation")
        if allocation.server_id != server_id:
            raise StateValidationError("each victim must be allocated to the selected server")
        available = available + allocation.resources
    return available


def can_admit_after_preemptions(
    state: SimulationState,
    incoming_task: Task,
    server_id: str,
    victim_task_ids: tuple[str, ...],
) -> bool:
    """Check only the component-wise fit after releasing explicit victims."""

    if not isinstance(incoming_task, Task):
        raise TypeError("incoming_task must be a Task")
    return incoming_task.demand.fits_within(
        resources_available_after_preemptions(state, server_id, victim_task_ids)
    )


def can_preempt_single_victim(
    state: SimulationState,
    *,
    incoming_task: Task,
    victim_task: Task,
    server_id: str,
    incoming_time: float,
    victim_time_remaining: float,
    semantics: PreemptionThresholdSemantics = PreemptionThresholdSemantics.PROSE,
) -> bool:
    """Combine explicit threshold and fit checks for Algorithm 2's single victim."""

    return meets_preemption_threshold(
        incoming_utility=incoming_task.utility,
        incoming_time=incoming_time,
        current_utility=victim_task.utility,
        current_time_remaining=victim_time_remaining,
        semantics=semantics,
    ) and can_admit_after_preemptions(state, incoming_task, server_id, (victim_task.task_id,))
