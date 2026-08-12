"""Approved single-victim primitives for KnapsackGreedy Preemption."""

from __future__ import annotations

from collections.abc import Mapping

from edge_reproduction.algorithms.feasibility import (
    can_preempt_single_victim,
    utility_time_ratio,
)
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import preempt_and_allocate_now
from edge_reproduction.simulation.state import SimulationState


def select_single_knapsack_greedy_victim(
    state: SimulationState,
    *,
    incoming_task: Task,
    server_id: str,
    victim_time_remaining: Mapping[str, float],
) -> str | None:
    """Return the first eligible victim under ASSUMP-004 and ASSUMP-005.

    Active jobs are ordered by ascending ``utility/time_remaining``. Equal ratios
    fail explicitly because neither arXiv v2 nor the approved assumptions define
    their tie-breaking rule. Returning from inside the loop encodes the approved
    one-victim limit and immediate ``break`` semantics.
    """

    if not isinstance(state, SimulationState):
        raise TypeError("state must be a SimulationState")
    if not isinstance(incoming_task, Task):
        raise TypeError("incoming_task must be a Task")
    if incoming_task.task_id not in state.tasks:
        raise KeyError("incoming_task must be registered in state.tasks")
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    if not isinstance(victim_time_remaining, Mapping):
        raise TypeError("victim_time_remaining must be a mapping")

    ranked: list[tuple[float, Task, float]] = []
    for allocation in state.active_allocations_for_server(server_id):
        victim = state.tasks[allocation.task_id]
        try:
            remaining = victim_time_remaining[victim.task_id]
        except KeyError as error:
            raise KeyError(f"missing time remaining for active task: {victim.task_id}") from error
        ratio = utility_time_ratio(victim.utility, remaining)
        ranked.append((ratio, victim, remaining))

    ratios = [ratio for ratio, _, _ in ranked]
    if len(ratios) != len(set(ratios)):
        raise UnresolvedDecisionError(
            "equal victim utility/time_remaining ratios require an unreported tie-break"
        )
    ranked.sort(key=lambda item: item[0])

    for _, victim, remaining in ranked:
        if can_preempt_single_victim(
            state,
            incoming_task=incoming_task,
            victim_task=victim,
            server_id=server_id,
            incoming_time=incoming_task.deadline_slots,
            victim_time_remaining=remaining,
        ):
            return victim.task_id
    return None


def preempt_first_eligible_and_admit(
    state: SimulationState,
    *,
    incoming_task: Task,
    server_id: str,
    victim_time_remaining: Mapping[str, float],
) -> tuple[SimulationState, str | None]:
    """Atomically replace the first eligible victim, or return the state unchanged."""

    victim_id = select_single_knapsack_greedy_victim(
        state,
        incoming_task=incoming_task,
        server_id=server_id,
        victim_time_remaining=victim_time_remaining,
    )
    if victim_id is None:
        return state, None
    updated = preempt_and_allocate_now(
        state,
        incoming_task_id=incoming_task.task_id,
        server_id=server_id,
        victim_task_ids=(victim_id,),
    )
    return updated, victim_id
