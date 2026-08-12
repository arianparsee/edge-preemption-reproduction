import pytest

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_preemption import (
    KnapsackGreedyPreemptionPolicy,
    capture_victim_snapshot,
    run_kg_preemption_round_two_for_server,
)
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


def task(task_id: str, demand: float, utility: float, deadline: int = 5) -> Task:
    return Task(
        task_id,
        0,
        deadline,
        utility,
        ResourceVector(demand, demand, demand, demand),
    )


def state_with_two_victims() -> tuple[SimulationState, tuple[Task, ...]]:
    victim_low = task("victim-low", 4.0, 4.0)
    victim_high = task("victim-high", 4.0, 12.0)
    auto = task("auto", 2.0, 8.0)
    incoming_first = task("incoming-first", 4.0, 30.0)
    incoming_second = task("incoming-second", 4.0, 20.0)
    rejected = task("rejected", 4.0, 10.0)
    tasks = (
        victim_low,
        victim_high,
        auto,
        incoming_first,
        incoming_second,
        rejected,
    )
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim_low.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=victim_high.task_id, server_id=server.server_id)
    return state, tasks


def test_assump_010_snapshot_is_ascending_and_freezes_time_remaining() -> None:
    state, _ = state_with_two_victims()
    times = {"victim-low": 4.0, "victim-high": 4.0}

    snapshot = capture_victim_snapshot(state, server_id="server", time_remaining_by_task=times)
    times["victim-low"] = 1.0

    assert tuple(entry.task_id for entry in snapshot) == ("victim-low", "victim-high")
    assert tuple(entry.utility_time_ratio for entry in snapshot) == (1.0, 3.0)
    assert snapshot[0].time_remaining == 4.0


def test_assump_010_equal_snapshot_ratios_fail_fast() -> None:
    a = task("a", 2.0, 10.0)
    b = task("b", 2.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {a.task_id: a, b.task_id: b}, {server.server_id: server})
    state = allocate_now(state, task_id=a.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=b.task_id, server_id=server.server_id)

    with pytest.raises(UnresolvedDecisionError, match="victim snapshot"):
        capture_victim_snapshot(
            state,
            server_id=server.server_id,
            time_remaining_by_task={a.task_id: 1.0, b.task_id: 2.0},
        )


def test_assump_010_preempted_snapshot_members_are_removed_from_later_checks() -> None:
    state, tasks = state_with_two_victims()
    by_id = {item.task_id: item for item in tasks}

    result = run_kg_preemption_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(
            "auto",
            "incoming-first",
            "incoming-second",
            "rejected",
        ),
        auto_fit_task_ids=("auto",),
        time_remaining_by_task={task_id: 4.0 for task_id in by_id},
    )

    assert result.victim_snapshot_task_ids == ("victim-low", "victim-high")
    assert result.preempted_task_ids == ("victim-low", "victim-high")
    assert result.accepted_task_ids == ("auto", "incoming-first", "incoming-second")
    assert result.rejected_task_ids == ("rejected",)
    assert result.final_state.task_states["auto"] is TaskState.ACCEPTED
    assert remaining_resources(result.final_state, "server").is_zero()


def test_assump_010_current_round_auto_and_direct_admissions_are_protected() -> None:
    victim = task("victim", 6.0, 5.0)
    auto = task("auto", 2.0, 8.0)
    direct = task("direct", 2.0, 100.0, deadline=1)
    preemptor = task("preemptor", 6.0, 50.0)
    late = task("late", 2.0, 40.0)
    tasks = (victim, auto, direct, preemptor, late)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim.task_id, server_id=server.server_id)

    result = run_kg_preemption_round_two_for_server(
        state,
        server_id=server.server_id,
        returning_task_ids=(auto.task_id, direct.task_id, preemptor.task_id, late.task_id),
        auto_fit_task_ids=(auto.task_id,),
        time_remaining_by_task={task_item.task_id: 5.0 for task_item in tasks},
    )

    assert result.victim_snapshot_task_ids == (victim.task_id,)
    assert result.preempted_task_ids == (victim.task_id,)
    assert result.accepted_task_ids == (auto.task_id, direct.task_id, preemptor.task_id)
    assert result.rejected_task_ids == (late.task_id,)
    assert result.final_state.task_states[auto.task_id] is TaskState.ACCEPTED
    assert result.final_state.task_states[direct.task_id] is TaskState.ACCEPTED
    assert result.final_state.allocations[auto.task_id].is_active
    assert result.final_state.allocations[direct.task_id].is_active


def test_returning_ratio_tie_fails_before_autofit_admission() -> None:
    auto = task("auto", 1.0, 1.0)
    a = task("a", 1.0, 10.0)
    b = task("b", 1.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (auto, a, b)},
        {server.server_id: server},
    )

    with pytest.raises(UnresolvedDecisionError, match="returning"):
        run_kg_preemption_round_two_for_server(
            state,
            server_id=server.server_id,
            returning_task_ids=(auto.task_id, a.task_id, b.task_id),
            auto_fit_task_ids=(auto.task_id,),
            time_remaining_by_task={a.task_id: 1.0, b.task_id: 2.0},
        )

    assert state.task_states[auto.task_id] is TaskState.CREATED
    assert auto.task_id not in state.allocations


def test_each_incoming_task_preempts_at_most_the_first_eligible_victim() -> None:
    low = task("low", 4.0, 1.0)
    high = task("high", 4.0, 2.0)
    incoming = task("incoming", 4.0, 100.0)
    server = Server("server", ResourceVector(8.0, 8.0, 8.0, 8.0))
    state = SimulationState(
        0,
        {item.task_id: item for item in (low, high, incoming)},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=low.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=high.task_id, server_id=server.server_id)

    result = run_kg_preemption_round_two_for_server(
        state,
        server_id=server.server_id,
        returning_task_ids=(incoming.task_id,),
        auto_fit_task_ids=(),
        time_remaining_by_task={low.task_id: 1.0, high.task_id: 1.0, incoming.task_id: 1.0},
    )

    assert result.preempted_task_ids == (low.task_id,)
    assert result.final_state.task_states[high.task_id] is TaskState.ACCEPTED
    assert result.final_state.allocations[high.task_id].is_active


def test_preemption_policy_satisfies_common_runtime_contract() -> None:
    policy = KnapsackGreedyPreemptionPolicy(ExactUtilityKnapsackSelector())

    assert isinstance(policy, AllocationPolicy)
