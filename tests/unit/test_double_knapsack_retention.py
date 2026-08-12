from collections.abc import Sequence
from statistics import fmean, pstdev

import pytest

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
    run_dkr_round_one_for_server,
    run_dkr_round_two_for_server,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.algorithms.pricing import (
    double_knapsack_round_one_price,
    double_knapsack_round_two_price,
    double_knapsack_violation,
)
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
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def make_state_and_config() -> tuple[SimulationState, PipelineDKRConfig]:
    current = task("current", 2.0, 8.0)
    a = task("a", 5.0, 12.0)
    b = task("b", 3.0, 10.0)
    c = task("c", 4.0, 11.0)
    impossible = task("impossible", 11.0, 13.0)
    tasks = (current, a, b, c, impossible)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {item.task_id: item for item in tasks}, {server.server_id: server})
    state = allocate_now(state, task_id="current", server_id="server")
    config = PipelineDKRConfig.from_workload(ga=PyeasygaConfig(seed=17), workload_tasks=tasks)
    return state, config


def test_assump_012_computes_f_once_with_population_standard_deviation() -> None:
    state, config = make_state_and_config()
    utilities = tuple(item.utility for item in state.tasks.values())

    assert config.workload_utility_mean == pytest.approx(fmean(utilities))
    assert config.workload_utility_std == pytest.approx(pstdev(utilities))
    assert config.scaling_factor_f == pytest.approx(fmean(utilities) - 1.1 * pstdev(utilities))
    assert config.as_metadata()["pricing.scaling_scope"] == "complete_workload_before_auction"


def test_assump_012_violation_uses_all_four_resource_dimensions() -> None:
    violation = double_knapsack_violation(
        ResourceVector(2.0, 2.0, 2.0, 2.0),
        ResourceVector(3.0, 3.0, 3.0, 3.0),
        ResourceVector(10.0, 10.0, 10.0, 10.0),
        scaling_factor=2.0,
    )

    assert violation == pytest.approx(5.0)


def test_round_one_covers_selected_feasible_nonselected_and_impossible_prices() -> None:
    state, config = make_state_and_config()

    result = run_dkr_round_one_for_server(
        state,
        server_id="server",
        requesting_task_ids=("a", "b", "c", "impossible"),
        selector=SelectOnly("a", "b"),
        config=config,
    )

    bids = {bid.task_id: bid for bid in result.bids}
    selected_demand = ResourceVector(8.0, 8.0, 8.0, 8.0)
    c_violation = double_knapsack_violation(
        state.tasks["c"].demand,
        selected_demand,
        state.servers["server"].capacity,
        scaling_factor=config.scaling_factor_f,
    )
    assert result.selected_task_ids == ("a", "b")
    assert result.selected_subset_demand == selected_demand
    assert bids["a"].price == pytest.approx(10.8)
    assert bids["b"].price == pytest.approx(9.0)
    assert bids["c"].price == pytest.approx(
        double_knapsack_round_one_price(
            11.0, selected=False, individually_feasible=True, violation=c_violation
        )
    )
    assert bids["impossible"].price > state.tasks["impossible"].utility
    assert not bids["impossible"].feasible


def test_round_two_retains_current_jobs_and_never_preempts() -> None:
    state, config = make_state_and_config()

    result = run_dkr_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=("a", "b", "c"),
        selector=SelectOnly("a", "b"),
        config=config,
    )

    assert result.accepted_task_ids == ("a", "b")
    assert result.rejected_task_ids == ("c",)
    assert result.final_state.task_states["current"] is TaskState.ACCEPTED
    assert result.final_state.task_states["c"] is TaskState.REJECTED
    assert TaskState.PREEMPTED not in result.final_state.task_states.values()
    assert remaining_resources(result.final_state, "server").is_zero()
    selected_demand = ResourceVector(8.0, 8.0, 8.0, 8.0)
    prices = {bid.task_id: bid.price for bid in result.bids}
    for task_id in ("a", "b"):
        item = state.tasks[task_id]
        violation = double_knapsack_violation(
            item.demand,
            selected_demand,
            state.servers["server"].capacity,
            scaling_factor=config.scaling_factor_f,
        )
        assert prices[task_id] == pytest.approx(
            double_knapsack_round_two_price(item.utility, violation=violation)
        )


def test_pipeline_policy_satisfies_common_runtime_contract() -> None:
    _, config = make_state_and_config()
    policy = PipelineDoubleKnapsackRetentionPolicy(config)

    assert isinstance(policy, AllocationPolicy)
