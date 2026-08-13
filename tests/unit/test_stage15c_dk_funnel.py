from __future__ import annotations

import random
from types import SimpleNamespace

from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import (
    GASelectionObservation,
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.diagnostics.dk_funnel import (
    InstrumentedDKPolicy,
    lifecycle_funnel,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    InstrumentedKnapsackSelector,
)
from edge_reproduction.models.enums import EventType
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.state import SimulationState


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def test_selector_observation_does_not_change_output_or_rng_stream() -> None:
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)
    tasks = (_task("a", 3.0, 12.0), _task("b", 2.0, 9.0), _task("c", 4.0, 7.0))
    direct = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=101))
    observations: list[GASelectionObservation] = []
    observed = PyeasygaUtilityKnapsackSelector(
        PyeasygaConfig(seed=101), observation_sink=observations.append
    )
    random.seed(811)
    caller_state = random.getstate()

    direct_result = direct.select(capacity=capacity, tasks=tasks)
    observed_result = observed.select(capacity=capacity, tasks=tasks)

    assert observed_result == direct_result
    assert observed._rng.getstate() == direct._rng.getstate()  # noqa: SLF001
    assert random.getstate() == caller_state
    assert len(observations) == 1
    observation = observations[0]
    assert observation.call_kind == "ga"
    assert observation.candidate_count == 3
    assert observation.final_selected_count == len(observed_result)
    assert observation.raw_selected_count >= observation.final_selected_count


def test_dkr_funnel_wrapper_preserves_auction_and_counts_each_stage() -> None:
    tasks = (_task("a", 1.0, 20.0), _task("b", 1.0, 10.0))
    server = Server("server", ResourceVector(2.0, 2.0, 2.0, 2.0))
    state = SimulationState(1, {task.task_id: task for task in tasks}, {server.server_id: server})
    direct_ga = PyeasygaConfig(seed=17)
    observed_ga = PyeasygaConfig(seed=17)
    direct_selector = PyeasygaUtilityKnapsackSelector(direct_ga)
    base_selector = PyeasygaUtilityKnapsackSelector(observed_ga)
    selector = InstrumentedKnapsackSelector(
        base_selector, server_count=1, diagnostic_stage="stage15c"
    )
    direct_config = PipelineDKRConfig.from_workload(ga=direct_ga, workload_tasks=tasks)
    observed_config = PipelineDKRConfig.from_workload(ga=observed_ga, workload_tasks=tasks)
    direct_policy = PipelineDoubleKnapsackRetentionPolicy(direct_config, direct_selector)
    policy = InstrumentedDKPolicy(
        PipelineDoubleKnapsackRetentionPolicy(observed_config, selector), selector
    )

    direct_result = direct_policy.run(
        state,
        requesting_task_ids=("a", "b"),
        time_remaining_by_task={"a": 7.0, "b": 7.0},
        epoch=1,
    )
    observed_result = policy.run(
        state,
        requesting_task_ids=("a", "b"),
        time_remaining_by_task={"a": 7.0, "b": 7.0},
        epoch=1,
    )

    assert observed_result.accepted_task_ids == direct_result.accepted_task_ids
    assert observed_result.rejected_task_ids == direct_result.rejected_task_ids
    assert observed_result.selected_server_by_task == direct_result.selected_server_by_task
    assert base_selector._rng.getstate() == direct_selector._rng.getstate()  # noqa: SLF001
    totals = policy.summary()["totals"]
    assert totals["requesting_task_attempts"] == 2
    assert totals["round_1_selector_calls"] == 1
    assert totals["round_1_server_assignments"] == 2
    assert totals["round_2_selector_calls"] == 1
    assert totals["round_2_accepted"] == 2
    assert totals["round_2_rejected"] == 0


def test_lifecycle_funnel_classifies_expiration_without_retaining_task_ids() -> None:
    events = (
        SimpleNamespace(event_type=EventType.RETRY_SCHEDULED, reason="retry"),
        SimpleNamespace(
            event_type=EventType.EXPIRED,
            reason="post_rejection_next_epoch_infeasible:no_service_slots",
        ),
        SimpleNamespace(event_type=EventType.COMPLETED, reason="complete"),
    )

    summary = lifecycle_funnel(events)

    assert summary == {
        "completed": 1,
        "expired": 1,
        "expired_after_round_2_rejection": 1,
        "retry_scheduled": 1,
    }
