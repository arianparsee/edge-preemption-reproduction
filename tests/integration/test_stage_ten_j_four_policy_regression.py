from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_preemption import (
    KnapsackGreedyPreemptionPolicy,
)
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    KnapsackGreedyRetentionPolicy,
)
from edge_reproduction.evaluation.policy_comparison import (
    PolicyComparisonRecord,
    PolicyRunSpec,
    run_policy_comparison,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.state import SimulationState

SEED = 20240811


def task(task_id: str, demand: float, utility: float, deadline: int) -> Task:
    return Task(
        task_id,
        0,
        deadline,
        utility,
        ResourceVector(demand, demand, demand, demand),
    )


def make_case() -> tuple[
    SimulationState,
    tuple[str, ...],
    dict[str, float],
    tuple[PolicyRunSpec, ...],
]:
    tasks = (
        task("current-high", 4.0, 10.0, 8),
        task("current-low", 4.0, 9.0, 8),
        task("incoming", 4.0, 20.0, 5),
        task("extra", 2.0, 3.0, 5),
    )
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {item.task_id: item for item in tasks}, {server.server_id: server})
    state = allocate_now(state, task_id="current-high", server_id="server")
    state = allocate_now(state, task_id="current-low", server_id="server")
    dkr_config = PipelineDKRConfig.from_workload(ga=PyeasygaConfig(seed=SEED), workload_tasks=tasks)
    dkp_config = PipelineDKPConfig.from_workload(ga=PyeasygaConfig(seed=SEED), workload_tasks=tasks)
    provenance = {
        "comparison.role": "auxiliary_control_flow_regression",
    }
    specs = (
        PolicyRunSpec(KnapsackGreedyRetentionPolicy(ExactUtilityKnapsackSelector()), provenance),
        PolicyRunSpec(KnapsackGreedyPreemptionPolicy(ExactUtilityKnapsackSelector()), provenance),
        PolicyRunSpec(PipelineDoubleKnapsackRetentionPolicy(dkr_config), provenance),
        PolicyRunSpec(PipelineDoubleKnapsackPreemptionPolicy(dkp_config), provenance),
    )
    return (
        state,
        ("incoming", "extra"),
        {
            "current-high": 4.0,
            "current-low": 6.0,
            "incoming": 5.0,
            "extra": 3.0,
        },
        specs,
    )


def by_method(
    records: tuple[PolicyComparisonRecord, ...],
) -> dict[str, PolicyComparisonRecord]:
    return {record.method: record for record in records}


def test_four_policies_share_one_scenario_and_match_manual_outcomes() -> None:
    state, requesting, remaining, specs = make_case()
    original = state.snapshot()

    records = run_policy_comparison(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task=remaining,
        specs=specs,
    )
    outcomes = by_method(records)

    assert tuple(outcomes) == (
        "knapsack_greedy_retention",
        "knapsack_greedy_preemption",
        "pipeline_double_knapsack_retention",
        "pipeline_double_knapsack_preemption",
    )
    for method in (
        "knapsack_greedy_retention",
        "pipeline_double_knapsack_retention",
    ):
        assert outcomes[method].accepted_task_ids == ("extra",)
        assert outcomes[method].rejected_task_ids == ("incoming",)
        assert outcomes[method].retained_task_ids == (
            "current-high",
            "current-low",
        )
        assert outcomes[method].preempted_task_ids == ()
        assert outcomes[method].active_utility_after_auction == 22.0

    for method in (
        "knapsack_greedy_preemption",
        "pipeline_double_knapsack_preemption",
    ):
        assert set(outcomes[method].accepted_task_ids) == {"incoming", "extra"}
        assert outcomes[method].rejected_task_ids == ()
        assert outcomes[method].retained_task_ids == ("current-high",)
        assert outcomes[method].preempted_task_ids == ("current-low",)
        assert outcomes[method].active_utility_after_auction == 33.0

    assert all(record.residual_by_server["server"].is_zero() for record in records)
    assert state.current_slot == original.current_slot
    assert state.task_states == original.task_states
    assert state.allocations == original.allocations


def test_four_policy_regression_is_reproducible_with_fixed_seed() -> None:
    state, requesting, remaining, specs = make_case()

    first = run_policy_comparison(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task=remaining,
        specs=specs,
    )
    second = run_policy_comparison(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task=remaining,
        specs=specs,
    )

    assert tuple(record.as_dict() for record in first) == tuple(
        record.as_dict() for record in second
    )
