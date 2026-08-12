from collections.abc import Sequence

import pytest

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    KnapsackGreedyRetentionPolicy,
    run_kg_retention_round_one_for_server,
    run_kg_retention_round_two_for_server,
)
from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


class SelectOnly:
    def __init__(self, *task_ids: str) -> None:
        self.task_ids = task_ids

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        del capacity, tasks
        return self.task_ids


def task(task_id: str, demand: float, utility: float, deadline: int = 5) -> Task:
    return Task(
        task_id,
        0,
        deadline,
        utility,
        ResourceVector(demand, demand, demand, demand),
    )


def test_round_one_prices_autofit_preemption_and_impossible_branches() -> None:
    current = task("current", 6.0, 5.0)
    fit = task("fit", 4.0, 10.0)
    preemptive = task("preemptive", 5.0, 20.0)
    impossible = task("impossible", 11.0, 30.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (current, fit, preemptive, impossible)},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)

    bids = run_kg_retention_round_one_for_server(
        state,
        server_id=server.server_id,
        requesting_task_ids=(fit.task_id, preemptive.task_id, impossible.task_id),
        time_remaining_by_task={
            current.task_id: 5.0,
            fit.task_id: 5.0,
            preemptive.task_id: 5.0,
        },
        selector=ExactUtilityKnapsackSelector(),
    )
    by_task = {bid.task_id: bid for bid in bids}

    assert by_task[fit.task_id].price == pytest.approx(9.0)
    assert by_task[fit.task_id].auto_fit
    assert by_task[fit.task_id].marked_task_ids == (fit.task_id,)
    assert by_task[preemptive.task_id].price == pytest.approx(19.5)
    assert not by_task[preemptive.task_id].auto_fit
    assert by_task[impossible.task_id].price > impossible.utility
    assert not by_task[impossible.task_id].feasible


def test_assump_009_autofit_then_descending_fit_only_and_continue_after_reject() -> None:
    auto = task("auto", 4.0, 1.0)
    first = task("first", 4.0, 30.0, deadline=3)
    rejected = task("rejected", 5.0, 20.0, deadline=4)
    later = task("later", 2.0, 4.0, deadline=4)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (auto, first, rejected, later)},
        {server.server_id: server},
    )

    result = run_kg_retention_round_two_for_server(
        state,
        server_id=server.server_id,
        returning_task_ids=(auto.task_id, first.task_id, rejected.task_id, later.task_id),
        auto_fit_task_ids=(auto.task_id,),
        time_remaining_by_task={
            first.task_id: 3.0,
            rejected.task_id: 4.0,
            later.task_id: 4.0,
        },
    )

    assert result.accepted_task_ids == (auto.task_id, first.task_id, later.task_id)
    assert result.rejected_task_ids == (rejected.task_id,)
    assert result.final_state.task_states[rejected.task_id] is TaskState.REJECTED
    assert result.final_state.task_states[later.task_id] is TaskState.ACCEPTED
    assert remaining_resources(result.final_state, server.server_id).is_zero()
    assert all(
        state is not TaskState.PREEMPTED for state in result.final_state.task_states.values()
    )


def test_assump_009_equal_remaining_ratios_fail_before_hidden_tie_break() -> None:
    a = task("a", 1.0, 10.0)
    b = task("b", 1.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {a.task_id: a, b.task_id: b}, {server.server_id: server})

    with pytest.raises(UnresolvedDecisionError, match="tie-break"):
        run_kg_retention_round_two_for_server(
            state,
            server_id=server.server_id,
            returning_task_ids=(a.task_id, b.task_id),
            auto_fit_task_ids=(),
            time_remaining_by_task={a.task_id: 1.0, b.task_id: 2.0},
        )

    assert state.task_states == {a.task_id: TaskState.CREATED, b.task_id: TaskState.CREATED}


def test_round_two_never_calls_preemption_even_when_releasing_would_fit() -> None:
    current = task("current", 8.0, 1.0)
    incoming = task("incoming", 5.0, 100.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {current.task_id: current, incoming.task_id: incoming},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)

    result = run_kg_retention_round_two_for_server(
        state,
        server_id=server.server_id,
        returning_task_ids=(incoming.task_id,),
        auto_fit_task_ids=(),
        time_remaining_by_task={incoming.task_id: 1.0},
    )

    assert result.rejected_task_ids == (incoming.task_id,)
    assert result.final_state.task_states[current.task_id] is TaskState.ACCEPTED
    assert result.final_state.allocations[current.task_id].is_active


def test_kg_retention_policy_satisfies_common_runtime_contract() -> None:
    policy = KnapsackGreedyRetentionPolicy(ExactUtilityKnapsackSelector())

    assert isinstance(policy, AllocationPolicy)


def test_round_one_refuses_a_currently_active_requesting_task() -> None:
    active = task("active", 2.0, 10.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {active.task_id: active}, {server.server_id: server})
    state = allocate_now(state, task_id=active.task_id, server_id=server.server_id)

    with pytest.raises(StateValidationError, match="currently active"):
        run_kg_retention_round_one_for_server(
            state,
            server_id=server.server_id,
            requesting_task_ids=(active.task_id,),
            time_remaining_by_task={active.task_id: 5.0},
            selector=ExactUtilityKnapsackSelector(),
        )
