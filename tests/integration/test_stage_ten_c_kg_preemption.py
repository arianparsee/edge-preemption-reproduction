"""End-to-end KnapsackGreedy Preemption integration test."""

import pytest

from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_preemption import (
    run_knapsack_greedy_preemption,
)
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


def test_complete_kg_preemption_two_round_flow() -> None:
    victim_low = make_task("victim-low", 4.0, 4.0)
    victim_high = make_task("victim-high", 4.0, 12.0)
    auto = make_task("auto", 2.0, 8.0)
    incoming_first = make_task("incoming-first", 4.0, 30.0)
    incoming_second = make_task("incoming-second", 4.0, 20.0)
    rejected = make_task("rejected", 4.0, 10.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    tasks = (
        victim_low,
        victim_high,
        auto,
        incoming_first,
        incoming_second,
        rejected,
    )
    state = SimulationState(
        0,
        {task.task_id: task for task in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim_low.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=victim_high.task_id, server_id=server.server_id)

    result = run_knapsack_greedy_preemption(
        state,
        requesting_task_ids=(
            auto.task_id,
            incoming_first.task_id,
            incoming_second.task_id,
            rejected.task_id,
        ),
        time_remaining_by_task={task.task_id: 4.0 for task in tasks},
        selector=ExactUtilityKnapsackSelector(),
    )

    validate_state_invariants(result.final_state)
    bids = {bid.task_id: bid for bid in result.round_one.bids}
    assert bids[auto.task_id].price == pytest.approx(7.2)
    assert bids[auto.task_id].auto_fit
    assert result.accepted_task_ids == (
        auto.task_id,
        incoming_first.task_id,
        incoming_second.task_id,
    )
    assert result.rejected_task_ids == (rejected.task_id,)
    assert result.preempted_task_ids == (victim_low.task_id, victim_high.task_id)
    assert result.final_state.task_states[victim_low.task_id] is TaskState.PREEMPTED
    assert result.final_state.task_states[victim_high.task_id] is TaskState.PREEMPTED
    assert result.final_state.task_states[auto.task_id] is TaskState.ACCEPTED
    assert remaining_resources(result.final_state, server.server_id).is_zero()
