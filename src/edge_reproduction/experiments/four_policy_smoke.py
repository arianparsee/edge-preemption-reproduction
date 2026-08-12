"""Reusable Stage-10J single-auction four-policy auxiliary regression."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    PolicyRunSpec,
    run_policy_comparison,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.state import SimulationState


def _resource(value: float) -> ResourceVector:
    return ResourceVector(value, value, value, value)


def _load_mapping(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("regression config must be a JSON object")
    return dict[str, Any](raw)


def _official_ga_config(raw_method: object, *, seed: int) -> PyeasygaConfig:
    if not isinstance(raw_method, dict):
        raise TypeError("each DK method config must be a JSON object")
    return PyeasygaConfig(
        seed=seed,
        population_size=int(raw_method["population_size"]),
        tournament_size=int(raw_method["tournament_size"]),
        generations=int(raw_method["generations"]),
    )


def run_four_policy_smoke(config_path: Path, *, expected_seed: int) -> dict[str, object]:
    """Run four policies independently on one technical single-auction scenario."""

    raw = _load_mapping(config_path)
    if raw.get("label") != "auxiliary_control_flow_regression_not_paper_result":
        raise ValueError("scenario config lacks the required auxiliary scientific label")
    seed = int(raw["seed"])
    if seed != expected_seed:
        raise ValueError(f"execution seed {expected_seed} does not match scenario seed {seed}")
    raw_server = raw["server"]
    raw_tasks = raw["tasks"]
    raw_methods = raw["methods"]
    if (
        not isinstance(raw_server, dict)
        or not isinstance(raw_tasks, list)
        or not isinstance(raw_methods, dict)
    ):
        raise TypeError("server/tasks/methods config has invalid structure")
    tasks = tuple(
        Task(
            str(item["task_id"]),
            0,
            int(item["deadline_slots"]),
            float(item["utility"]),
            _resource(float(item["demand_per_dimension"])),
        )
        for item in raw_tasks
        if isinstance(item, dict)
    )
    if len(tasks) != len(raw_tasks):
        raise TypeError("every task config entry must be a JSON object")
    server = Server(
        str(raw_server["server_id"]),
        _resource(float(raw_server["capacity_per_dimension"])),
    )
    state = SimulationState(
        0,
        {task.task_id: task for task in tasks},
        {server.server_id: server},
    )
    active_ids = tuple(
        str(item["task_id"])
        for item in raw_tasks
        if isinstance(item, dict) and item["active"] is True
    )
    time_remaining = {
        str(item["task_id"]): float(item["time_remaining"])
        for item in raw_tasks
        if isinstance(item, dict)
    }
    for task_id in active_ids:
        state = allocate_now(state, task_id=task_id, server_id=server.server_id)
    requesting = tuple(task.task_id for task in tasks if task.task_id not in active_ids)

    dkr_config = PipelineDKRConfig.from_workload(
        ga=_official_ga_config(raw_methods["pipeline_double_knapsack_retention"], seed=seed),
        workload_tasks=tasks,
    )
    dkp_config = PipelineDKPConfig.from_workload(
        ga=_official_ga_config(raw_methods["pipeline_double_knapsack_preemption"], seed=seed),
        workload_tasks=tasks,
    )
    specs = (
        PolicyRunSpec(
            KnapsackGreedyRetentionPolicy(ExactUtilityKnapsackSelector()),
            {
                "comparison.selector": str(raw_methods["knapsack_greedy_retention"]["selector"]),
                "comparison.role": "auxiliary_control_flow_regression",
            },
        ),
        PolicyRunSpec(
            KnapsackGreedyPreemptionPolicy(ExactUtilityKnapsackSelector()),
            {
                "comparison.selector": str(raw_methods["knapsack_greedy_preemption"]["selector"]),
                "comparison.role": "auxiliary_control_flow_regression",
            },
        ),
        PolicyRunSpec(
            PipelineDoubleKnapsackRetentionPolicy(dkr_config),
            {
                "comparison.selector": str(
                    raw_methods["pipeline_double_knapsack_retention"]["selector"]
                ),
                "comparison.role": "auxiliary_control_flow_regression",
            },
        ),
        PolicyRunSpec(
            PipelineDoubleKnapsackPreemptionPolicy(dkp_config),
            {
                "comparison.selector": str(
                    raw_methods["pipeline_double_knapsack_preemption"]["selector"]
                ),
                "comparison.role": "auxiliary_control_flow_regression",
            },
        ),
    )
    records = run_policy_comparison(
        state,
        requesting_task_ids=requesting,
        time_remaining_by_task=time_remaining,
        specs=specs,
    )
    return {
        "scientific_label": "auxiliary_single_auction_smoke_not_paper_experiment",
        "scenario_label": raw["label"],
        "baseline": raw["baseline"],
        "scenario_config_path": config_path.as_posix(),
        "seed": seed,
        "requesting_task_ids": list(requesting),
        "initial_active_task_ids": list(active_ids),
        "metric_warning": "active_utility_after_auction_is_not_completed_paper_utility",
        "records": [record.as_dict() for record in records],
    }
