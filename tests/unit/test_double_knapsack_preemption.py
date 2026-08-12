from collections.abc import Sequence

import pytest

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
    run_dkp_round_two_for_server,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
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


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def state_with_active(*, current: tuple[Task, ...], returning: tuple[Task, ...]) -> SimulationState:
    tasks = current + returning
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(3, {item.task_id: item for item in tasks}, {server.server_id: server})
    for item in current:
        state = allocate_now(state, task_id=item.task_id, server_id=server.server_id)
    return state


def test_assump_016_atomic_repack_can_preempt_multiple_current_jobs() -> None:
    current_high = task("current-high", 4.0, 10.0)
    current_low = task("current-low", 4.0, 9.0)
    incoming = task("incoming", 8.0, 20.0)
    extra = task("extra", 2.0, 3.0)
    state = state_with_active(current=(current_high, current_low), returning=(incoming, extra))

    result = run_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id, extra.task_id),
        time_remaining_by_task={
            current_high.task_id: 4.0,
            current_low.task_id: 6.0,
            incoming.task_id: 5.0,
            extra.task_id: 3.0,
        },
        selector=SelectOnly(incoming.task_id, extra.task_id),
    )

    assert result.knapsack_selected_task_ids == (incoming.task_id, extra.task_id)
    assert result.accepted_task_ids == (incoming.task_id, extra.task_id)
    assert result.preempted_task_ids == (current_high.task_id, current_low.task_id)
    assert result.retained_task_ids == ()
    assert result.rejected_task_ids == ()
    assert result.final_residual.is_zero()
    assert state.task_states[current_high.task_id] is TaskState.ACCEPTED
    assert result.final_state.task_states[current_high.task_id] is TaskState.PREEMPTED
    assert result.final_state.task_states[current_low.task_id] is TaskState.PREEMPTED
    assert remaining_resources(result.final_state, "server").is_zero()


def test_assump_016_retained_current_keeps_original_start_and_nonmember_can_fill_gap() -> None:
    retained = task("retained", 2.0, 12.0)
    preempted = task("preempted", 6.0, 5.0)
    incoming = task("incoming", 6.0, 20.0)
    gap = task("gap", 2.0, 2.0)
    state = state_with_active(current=(retained, preempted), returning=(incoming, gap))
    original_start = state.allocations[retained.task_id].start_slot

    result = run_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id, gap.task_id),
        time_remaining_by_task={
            retained.task_id: 2.0,
            preempted.task_id: 5.0,
            incoming.task_id: 4.0,
            gap.task_id: 4.0,
        },
        selector=SelectOnly(retained.task_id, incoming.task_id),
    )

    assert result.retained_task_ids == (retained.task_id,)
    assert result.accepted_task_ids == (incoming.task_id, gap.task_id)
    assert result.preempted_task_ids == (preempted.task_id,)
    assert result.final_state.allocations[retained.task_id].start_slot == original_start
    assert result.score_entries[-1].task_id == gap.task_id
    assert not result.score_entries[-1].in_knapsack
    assert remaining_resources(result.final_state, "server").is_zero()


def test_assump_017_uses_literal_scores_and_frozen_times() -> None:
    current = task("current", 2.0, 12.0)
    returning = task("returning", 2.0, 10.0)
    state = state_with_active(current=(current,), returning=(returning,))

    result = run_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(returning.task_id,),
        time_remaining_by_task={current.task_id: 2.0, returning.task_id: 4.0},
        selector=SelectOnly(returning.task_id),
    )
    by_task = {entry.task_id: entry for entry in result.score_entries}

    assert by_task[returning.task_id].utility_time_ratio == pytest.approx(2.5)
    assert by_task[returning.task_id].score == pytest.approx(1002.5)
    assert by_task[current.task_id].utility_time_ratio == pytest.approx(6.0)
    assert by_task[current.task_id].score == pytest.approx(7.0)
    assert by_task[current.task_id].time_remaining == pytest.approx(2.0)


def test_nonfitting_returning_job_is_rejected_while_current_job_is_retained() -> None:
    current = task("current", 8.0, 20.0)
    incoming = task("incoming", 4.0, 3.0)
    state = state_with_active(current=(current,), returning=(incoming,))

    result = run_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 2.0, incoming.task_id: 3.0},
        selector=SelectOnly(current.task_id),
    )

    assert result.retained_task_ids == (current.task_id,)
    assert result.rejected_task_ids == (incoming.task_id,)
    assert result.final_state.task_states[current.task_id] is TaskState.ACCEPTED
    assert result.final_state.task_states[incoming.task_id] is TaskState.REJECTED
    assert remaining_resources(result.final_state, "server") == ResourceVector(2.0, 2.0, 2.0, 2.0)


def test_assump_017_equal_scores_fail_before_any_state_change() -> None:
    first = task("first", 2.0, 10.0)
    second = task("second", 2.0, 20.0)
    state = state_with_active(current=(first,), returning=(second,))

    with pytest.raises(UnresolvedDecisionError, match="equal DK-P"):
        run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(second.task_id,),
            time_remaining_by_task={first.task_id: 1.0, second.task_id: 2.0},
            selector=SelectOnly(first.task_id, second.task_id),
        )

    assert state.task_states[first.task_id] is TaskState.ACCEPTED
    assert state.task_states[second.task_id] is TaskState.CREATED


def test_assump_017_cross_tier_priority_conflict_fails_fast() -> None:
    selected = task("selected", 2.0, 1.0)
    nonmember = task("nonmember", 2.0, 2000.0)
    state = state_with_active(current=(selected,), returning=(nonmember,))

    with pytest.raises(UnresolvedDecisionError, match="knapsack-first priority"):
        run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(nonmember.task_id,),
            time_remaining_by_task={selected.task_id: 1.0, nonmember.task_id: 1.0},
            selector=SelectOnly(selected.task_id),
        )


def test_round_two_refuses_active_allocations_that_differ_from_task_demand() -> None:
    current = task("current", 2.0, 10.0)
    incoming = task("incoming", 2.0, 11.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {current.task_id: current, incoming.task_id: incoming},
        {server.server_id: server},
    )
    state = allocate_now(
        state,
        task_id=current.task_id,
        server_id=server.server_id,
        resources=ResourceVector(1.0, 1.0, 1.0, 1.0),
    )

    with pytest.raises(StateValidationError, match="equal task demand"):
        run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(incoming.task_id,),
            time_remaining_by_task={current.task_id: 2.0, incoming.task_id: 2.0},
            selector=SelectOnly(current.task_id, incoming.task_id),
        )


def test_assump_018_and_019_metadata_and_policy_contract() -> None:
    current = task("current", 2.0, 10.0)
    incoming = task("incoming", 2.0, 11.0)
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=101), workload_tasks=(current, incoming)
    )
    metadata = config.as_metadata()
    policy = PipelineDoubleKnapsackPreemptionPolicy(config)

    assert metadata["ga.population_size"] == "200"
    assert metadata["ga.tournament_size"] == "20"
    assert metadata["ga.generations"] == "50"
    assert metadata["ga.seed"] == "101"
    assert metadata["round_two.price_status"] == "absent_no_source_formula_ASSUMP-019"
    assert "ASSUMP-019" in metadata["assumptions"]
    assert isinstance(policy, AllocationPolicy)
