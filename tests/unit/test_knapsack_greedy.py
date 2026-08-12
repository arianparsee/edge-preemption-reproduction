import pytest

from edge_reproduction.algorithms.knapsack_greedy import (
    preempt_first_eligible_and_admit,
    select_single_knapsack_greedy_victim,
)
from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import (
    allocate_now,
    preempt_and_allocate_now,
)
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


def task(task_id: str, demand: float, utility: float, deadline: int = 5) -> Task:
    return Task(
        task_id,
        arrival_slot=0,
        deadline_slots=deadline,
        utility=utility,
        demand=ResourceVector(demand, demand, demand, demand),
    )


def two_victim_state() -> tuple[SimulationState, Task, Task, Task]:
    low = task("low", 4.0, 5.0)
    high = task("high", 4.0, 20.0)
    incoming = task("incoming", 6.0, 12.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (low, high, incoming)},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=low.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=high.task_id, server_id=server.server_id)
    return state, low, high, incoming


def test_assump_005_selects_first_eligible_victim_in_ascending_ratio_order() -> None:
    state, low, _, incoming = two_victim_state()

    selected = select_single_knapsack_greedy_victim(
        state,
        incoming_task=incoming,
        server_id="server",
        victim_time_remaining={"low": 5.0, "high": 5.0},
    )

    assert selected == low.task_id


def test_assump_005_skips_low_ratio_victim_when_its_resources_are_insufficient() -> None:
    low = task("low", 1.0, 1.0)
    second = task("second", 4.0, 2.0)
    filler = task("filler", 3.0, 30.0)
    incoming = task("incoming", 6.0, 60.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (low, second, filler, incoming)},
        {server.server_id: server},
    )
    for running in (low, second, filler):
        state = allocate_now(state, task_id=running.task_id, server_id=server.server_id)

    selected = select_single_knapsack_greedy_victim(
        state,
        incoming_task=incoming,
        server_id="server",
        victim_time_remaining={"low": 10.0, "second": 10.0, "filler": 1.0},
    )

    assert selected == second.task_id


def test_assump_005_refuses_unreported_equal_ratio_tie_breaking() -> None:
    state, _, _, incoming = two_victim_state()

    with pytest.raises(UnresolvedDecisionError, match="tie-break"):
        select_single_knapsack_greedy_victim(
            state,
            incoming_task=incoming,
            server_id="server",
            victim_time_remaining={"low": 1.0, "high": 4.0},
        )


def test_assump_006_preempts_exactly_one_victim_and_stops() -> None:
    state, low, high, incoming = two_victim_state()

    updated, selected = preempt_first_eligible_and_admit(
        state,
        incoming_task=incoming,
        server_id="server",
        victim_time_remaining={"low": 5.0, "high": 5.0},
    )

    assert selected == low.task_id
    assert updated.task_states[low.task_id] is TaskState.PREEMPTED
    assert updated.task_states[high.task_id] is TaskState.ACCEPTED
    assert updated.task_states[incoming.task_id] is TaskState.ACCEPTED
    assert updated.allocations[high.task_id].is_active
    assert updated.allocations[incoming.task_id].is_active
    assert remaining_resources(updated, "server").is_zero()


def test_assump_006_failed_transaction_leaves_original_state_unchanged() -> None:
    victim = task("victim", 2.0, 1.0)
    incoming = task("incoming", 11.0, 100.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    original = SimulationState(
        0,
        {victim.task_id: victim, incoming.task_id: incoming},
        {server.server_id: server},
    )
    original = allocate_now(original, task_id=victim.task_id, server_id=server.server_id)
    original_state = original.snapshot()

    with pytest.raises(StateValidationError, match="insufficient residual resources"):
        preempt_and_allocate_now(
            original,
            incoming_task_id=incoming.task_id,
            server_id=server.server_id,
            victim_task_ids=(victim.task_id,),
        )

    assert original.task_states == original_state.task_states
    assert original.allocations == original_state.allocations
    assert remaining_resources(original, "server") == remaining_resources(original_state, "server")
