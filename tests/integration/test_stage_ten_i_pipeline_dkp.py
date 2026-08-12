from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
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
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def make_case() -> tuple[SimulationState, tuple[str, ...], PipelineDKPConfig]:
    current_high = task("current-high", 4.0, 10.0)
    current_low = task("current-low", 4.0, 9.0)
    incoming = task("incoming", 8.0, 20.0)
    extra = task("extra", 2.0, 3.0)
    tasks = (current_high, current_low, incoming, extra)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(0, {item.task_id: item for item in tasks}, {server.server_id: server})
    state = allocate_now(state, task_id=current_high.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=current_low.task_id, server_id=server.server_id)
    config = PipelineDKPConfig.from_workload(ga=PyeasygaConfig(seed=20240810), workload_tasks=tasks)
    return state, (incoming.task_id, extra.task_id), config


def time_remaining() -> dict[str, float]:
    return {
        "current-high": 4.0,
        "current-low": 6.0,
        "incoming": 5.0,
        "extra": 3.0,
    }


def test_official_pipeline_dkp_end_to_end_and_exact_auxiliary_comparison() -> None:
    state, requesting, config = make_case()
    policy = PipelineDoubleKnapsackPreemptionPolicy(config)

    result = policy.run(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task=time_remaining(),
        epoch=4,
    )
    combined = tuple(state.tasks[task_id] for task_id in state.tasks)
    exact = ExactUtilityKnapsackSelector().select(
        capacity=state.servers["server"].capacity,
        tasks=combined,
    )

    validate_state_invariants(result.final_state)
    assert result.round_one_selected_by_server == {"server": ("extra",)}
    round_one_prices = {bid.task_id: bid.price for bid in result.round_one.bids}
    assert round_one_prices == {"incoming": 19.0, "extra": 2.7}
    official_selected = result.round_two_knapsack_by_server["server"]
    assert set(official_selected) == set(exact) == {"incoming", "extra"}
    assert sum(state.tasks[task_id].utility for task_id in official_selected) == sum(
        state.tasks[task_id].utility for task_id in exact
    )
    assert result.accepted_task_ids == ("incoming", "extra")
    assert result.rejected_task_ids == ()
    assert result.retained_task_ids == ()
    assert result.preempted_task_ids == ("current-high", "current-low")
    assert result.final_state.task_states["current-high"] is TaskState.PREEMPTED
    assert result.final_state.task_states["current-low"] is TaskState.PREEMPTED
    assert remaining_resources(result.final_state, "server").is_zero()
    assert result.round_two.bids == ()
    assert not hasattr(result, "final_price_by_task")
    assert result.metadata["round_two.price_status"].startswith("absent")
    assert state.task_states["current-high"] is TaskState.ACCEPTED


def test_complete_pipeline_dkp_is_reproducible_with_fixed_seed() -> None:
    state, requesting, config = make_case()
    policy = PipelineDoubleKnapsackPreemptionPolicy(config)

    first = policy.run(
        state, requesting_task_ids=requesting, time_remaining_by_task=time_remaining()
    )
    second = policy.run(
        state, requesting_task_ids=requesting, time_remaining_by_task=time_remaining()
    )

    assert first.accepted_task_ids == second.accepted_task_ids
    assert first.rejected_task_ids == second.rejected_task_ids
    assert first.retained_task_ids == second.retained_task_ids
    assert first.preempted_task_ids == second.preempted_task_ids
    assert first.selected_server_by_task == second.selected_server_by_task
    assert first.round_one_selected_by_server == second.round_one_selected_by_server
    assert first.round_two_knapsack_by_server == second.round_two_knapsack_by_server
    assert first.round_two_scores_by_server == second.round_two_scores_by_server
    assert first.metadata == second.metadata
