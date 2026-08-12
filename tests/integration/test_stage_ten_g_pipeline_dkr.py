import pytest

from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
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


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def make_case() -> tuple[SimulationState, tuple[str, ...], PipelineDKRConfig]:
    current = task("current", 2.0, 4.0)
    a = task("a", 5.0, 20.0)
    b = task("b", 3.0, 12.0)
    c = task("c", 4.0, 11.0)
    impossible = task("impossible", 11.0, 30.0)
    tasks = (current, a, b, c, impossible)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {item.task_id: item for item in tasks}, {server.server_id: server})
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)
    requesting = (a.task_id, b.task_id, c.task_id, impossible.task_id)
    config = PipelineDKRConfig.from_workload(ga=PyeasygaConfig(seed=20240810), workload_tasks=tasks)
    return state, requesting, config


def test_official_pipeline_dkr_end_to_end_and_exact_auxiliary_comparison() -> None:
    state, requesting, config = make_case()
    policy = PipelineDoubleKnapsackRetentionPolicy(config)

    result = policy.run(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task={},
        epoch=3,
    )
    exact = ExactUtilityKnapsackSelector().select(
        capacity=ResourceVector(8.0, 8.0, 8.0, 8.0),
        tasks=tuple(state.tasks[task_id] for task_id in requesting),
    )

    validate_state_invariants(result.final_state)
    assert result.round_one_selected_by_server == {"server": exact}
    assert exact == ("a", "b")
    assert result.accepted_task_ids == ("a", "b")
    assert result.rejected_task_ids == ("impossible", "c")
    assert result.final_state.task_states["current"] is TaskState.ACCEPTED
    assert TaskState.PREEMPTED not in result.final_state.task_states.values()
    assert remaining_resources(result.final_state, "server").is_zero()
    assert result.metadata["ga.population_size"] == "200"
    assert result.metadata["ga.tournament_size"] == "20"
    assert result.metadata["ga.generations"] == "50"
    assert result.metadata["ga.seed"] == "20240810"
    assert result.metadata["exact_solver_role"] == "auxiliary_tests_only_not_official_path"
    assert state.task_states["a"] is TaskState.CREATED


def test_complete_pipeline_result_is_reproducible_with_fixed_seed() -> None:
    state, requesting, config = make_case()
    policy = PipelineDoubleKnapsackRetentionPolicy(config)

    first = policy.run(state, requesting_task_ids=requesting, time_remaining_by_task={})
    second = policy.run(state, requesting_task_ids=requesting, time_remaining_by_task={})

    assert first.accepted_task_ids == second.accepted_task_ids
    assert first.rejected_task_ids == second.rejected_task_ids
    assert first.selected_server_by_task == second.selected_server_by_task
    assert first.round_one_selected_by_server == second.round_one_selected_by_server
    assert first.final_price_by_task == pytest.approx(second.final_price_by_task)
    assert first.metadata == second.metadata
