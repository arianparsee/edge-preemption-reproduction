from __future__ import annotations

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy
from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import InstrumentedKnapsackSelector
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.state import SimulationState


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def _run(policy_name: str, variant: CounterfactualVariant) -> dict[str, object]:
    tasks = (
        _task("task-a", 2.0, 20.0),
        _task("task-b", 2.0, 12.0),
        _task("task-c", 3.0, 9.0),
    )
    servers = (
        Server("server-a", ResourceVector(4.0, 4.0, 4.0, 4.0)),
        Server("server-b", ResourceVector(4.0, 4.0, 4.0, 4.0)),
    )
    state = SimulationState(
        1,
        {task.task_id: task for task in tasks},
        {server.server_id: server for server in servers},
    )
    ga = PyeasygaConfig(seed=1901)
    base_selector = CounterfactualKnapsackSelector(ga, variant)
    selector = InstrumentedKnapsackSelector(
        base_selector, server_count=2, diagnostic_stage="stage15d"
    )
    if policy_name == "retention":
        retention_config = PipelineDKRConfig.from_workload(ga=ga, workload_tasks=tasks)
        policy = InstrumentedDKPolicy(
            PipelineDoubleKnapsackRetentionPolicy(retention_config, selector), selector
        )
    else:
        preemption_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
        policy = InstrumentedDKPolicy(
            PipelineDoubleKnapsackPreemptionPolicy(preemption_config, selector), selector
        )
    result = policy.run(
        state,
        requesting_task_ids=tuple(task.task_id for task in tasks),
        time_remaining_by_task={task.task_id: 7.0 for task in tasks},
        epoch=1,
    )
    return {
        "accepted": result.accepted_task_ids,
        "rejected": result.rejected_task_ids,
        "preempted": getattr(result, "preempted_task_ids", ()),
        "selector": selector.summary().as_dict(),
        "counterfactual": base_selector.counterfactual_summary(),
        "rng_state": base_selector._rng.getstate(),  # noqa: SLF001
        "funnel": policy.summary(),
    }


@pytest.mark.parametrize("policy_name", ["retention", "preemption"])
@pytest.mark.parametrize(
    "variant",
    [
        CounterfactualVariant.FIXED_PENALTY,
        CounterfactualVariant.INITIAL_POPULATION_REPAIR,
        CounterfactualVariant.OFFSPRING_REPAIR,
        CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR,
    ],
)
def test_small_policy_replay_is_exact(
    policy_name: str, variant: CounterfactualVariant
) -> None:
    first = _run(policy_name, variant)
    second = _run(policy_name, variant)

    assert first == second
    selector = first["selector"]
    assert isinstance(selector, dict)
    assert selector["total_calls"] == 4
