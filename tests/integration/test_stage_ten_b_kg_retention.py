"""End-to-end two-round KnapsackGreedy Retention integration test."""

import pytest

from edge_reproduction.algorithms.genetic_knapsack import (
    KGPyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    run_knapsack_greedy_retention,
)
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import (
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


def make_task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def test_complete_kg_retention_two_round_flow() -> None:
    current = make_task("current", 4.0, 5.0)
    auto = make_task("auto", 6.0, 15.0)
    rejected_high = make_task("rejected-high", 4.0, 10.0)
    rejected_low = make_task("rejected-low", 2.0, 4.0)
    impossible = make_task("impossible", 11.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    tasks = (current, auto, rejected_high, rejected_low, impossible)
    state = SimulationState(
        0,
        {task.task_id: task for task in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)

    result = run_knapsack_greedy_retention(
        state,
        requesting_task_ids=(
            auto.task_id,
            rejected_high.task_id,
            rejected_low.task_id,
            impossible.task_id,
        ),
        time_remaining_by_task={
            current.task_id: 4.0,
            auto.task_id: 5.0,
            rejected_high.task_id: 4.0,
            rejected_low.task_id: 4.0,
        },
        selector=ExactUtilityKnapsackSelector(),
        epoch=0,
    )

    validate_state_invariants(result.final_state)
    bids = {bid.task_id: bid for bid in result.round_one.bids}
    assert bids[auto.task_id].auto_fit
    assert bids[auto.task_id].price == pytest.approx(13.5)
    assert bids[rejected_high.task_id].price == pytest.approx(9.666666666666666)
    assert bids[impossible.task_id].price > impossible.utility
    assert result.accepted_task_ids == (auto.task_id,)
    assert result.rejected_task_ids == (
        impossible.task_id,
        rejected_high.task_id,
        rejected_low.task_id,
    )
    assert result.selected_server_by_task == {
        auto.task_id: server.server_id,
        rejected_high.task_id: server.server_id,
        rejected_low.task_id: server.server_id,
    }
    assert result.final_state.task_states[current.task_id] is TaskState.ACCEPTED
    assert result.final_state.task_states[auto.task_id] is TaskState.ACCEPTED
    assert all(
        result.final_state.task_states[task_id] is TaskState.REJECTED
        for task_id in (rejected_high.task_id, rejected_low.task_id, impossible.task_id)
    )
    assert remaining_resources(result.final_state, server.server_id).is_zero()
    assert TaskState.PREEMPTED not in result.final_state.task_states.values()


def test_multi_server_round_one_selects_unique_lowest_offer() -> None:
    incoming = make_task("incoming", 6.0, 10.0)
    large = Server("large", ResourceVector(10.0, 10.0, 10.0, 10.0))
    small = Server("small", ResourceVector(5.0, 5.0, 5.0, 5.0))
    state = SimulationState(
        0,
        {incoming.task_id: incoming},
        {large.server_id: large, small.server_id: small},
    )

    result = run_knapsack_greedy_retention(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={incoming.task_id: 5.0},
        selector=ExactUtilityKnapsackSelector(),
    )

    assert result.selected_server_by_task == {incoming.task_id: large.server_id}
    assert result.accepted_task_ids == (incoming.task_id,)
    assert result.final_state.allocations[incoming.task_id].server_id == large.server_id


def test_impossible_on_all_servers_is_rejected_without_irrelevant_price_tie() -> None:
    incoming = make_task("incoming", 11.0, 10.0)
    servers = {
        server_id: Server(server_id, ResourceVector(10.0, 10.0, 10.0, 10.0))
        for server_id in ("server-a", "server-b")
    }
    state = SimulationState(0, {incoming.task_id: incoming}, servers)

    result = run_knapsack_greedy_retention(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={},
        selector=ExactUtilityKnapsackSelector(),
    )

    assert result.rejected_task_ids == (incoming.task_id,)
    assert result.selected_server_by_task == {}


def test_equal_acceptable_server_prices_fail_fast() -> None:
    incoming = make_task("incoming", 1.0, 10.0)
    servers = {
        server_id: Server(server_id, ResourceVector(10.0, 10.0, 10.0, 10.0))
        for server_id in ("server-a", "server-b")
    }
    state = SimulationState(0, {incoming.task_id: incoming}, servers)

    with pytest.raises(UnresolvedDecisionError, match="client tie-break"):
        run_knapsack_greedy_retention(
            state,
            requesting_task_ids=(incoming.task_id,),
            time_remaining_by_task={incoming.task_id: 5.0},
            selector=ExactUtilityKnapsackSelector(),
        )

    assert state.task_states[incoming.task_id] is TaskState.CREATED


def test_assump_043_official_kg_selector_resolves_equal_prices_reproducibly() -> None:
    incoming = make_task("incoming", 1.0, 10.0)
    servers = {
        server_id: Server(server_id, ResourceVector(10.0, 10.0, 10.0, 10.0))
        for server_id in ("server-a", "server-b")
    }
    state = SimulationState(0, {incoming.task_id: incoming}, servers)

    def execute() -> tuple[dict[str, str], dict[str, str]]:
        selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=314))
        result = run_knapsack_greedy_retention(
            state,
            requesting_task_ids=(incoming.task_id,),
            time_remaining_by_task={incoming.task_id: 5.0},
            selector=selector,
            choose_equal_server=selector.choose_kg_equal_minimum_server,
        )
        return dict(result.selected_server_by_task), selector.runtime_metadata()

    first_choice, first_metadata = execute()
    second_choice, second_metadata = execute()

    assert first_choice == second_choice
    assert set(first_choice.values()) <= {"server-a", "server-b"}
    assert first_metadata == second_metadata
    assert first_metadata["client.equal_minimum_price_ties"] == "1"
