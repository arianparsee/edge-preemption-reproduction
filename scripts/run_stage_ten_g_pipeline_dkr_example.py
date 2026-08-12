"""Run the configured Stage-10G official Pipeline DK-R hand example."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState

CONFIG_PATH = Path("configs/stage10g_pipeline_dkr_example.json")
OUTPUT_PATH = Path("results/raw/stage10g/pipeline_dkr_example.json")


def _resource(value: float) -> ResourceVector:
    return ResourceVector(value, value, value, value)


def _load_config(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("example config must be a JSON object")
    return raw


def _build_ga_config(raw: dict[str, Any]) -> PyeasygaConfig:
    ga = raw["ga"]
    if not isinstance(ga, dict):
        raise TypeError("ga config must be a JSON object")
    return PyeasygaConfig(
        seed=int(raw["seed"]),
        population_size=int(ga["population_size"]),
        tournament_size=int(ga["tournament_size"]),
        generations=int(ga["generations"]),
        crossover_probability=float(ga["crossover_probability"]),
        mutation_probability=float(ga["mutation_probability"]),
        elitism=bool(ga["elitism"]),
        maximise_fitness=bool(ga["maximise_fitness"]),
        selection_operator=str(ga["selection_operator"]),
        crossover_operator=str(ga["crossover_operator"]),
        mutation_operator=str(ga["mutation_operator"]),
        chromosome_representation=str(ga["chromosome_representation"]),
        infeasible_fitness=float(ga["infeasible_fitness"]),
        library=str(ga["library"]),
        library_version=str(ga["library_version"]),
    )


def run_example(config_path: Path = CONFIG_PATH) -> dict[str, object]:
    """Execute twice and return the actual official-GA result plus checks."""

    raw = _load_config(config_path)
    raw_server = raw["server"]
    raw_tasks = raw["tasks"]
    if not isinstance(raw_server, dict) or not isinstance(raw_tasks, list):
        raise TypeError("server/tasks config has invalid structure")
    tasks = tuple(
        Task(
            str(item["task_id"]),
            0,
            5,
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
    for task_id in active_ids:
        state = allocate_now(state, task_id=task_id, server_id=server.server_id)
    requesting = tuple(task.task_id for task in tasks if task.task_id not in active_ids)
    config = PipelineDKRConfig.from_workload(ga=_build_ga_config(raw), workload_tasks=tasks)
    policy = PipelineDoubleKnapsackRetentionPolicy(config)
    first = policy.run(state, requesting_task_ids=requesting, time_remaining_by_task={})
    second = policy.run(state, requesting_task_ids=requesting, time_remaining_by_task={})

    residual_before = remaining_resources(state, server.server_id)
    exact_selected = ExactUtilityKnapsackSelector().select(
        capacity=residual_before,
        tasks=tuple(state.tasks[task_id] for task_id in requesting),
    )
    official_selected = first.round_one_selected_by_server[server.server_id]
    exact_objective = sum(state.tasks[task_id].utility for task_id in exact_selected)
    official_objective = sum(state.tasks[task_id].utility for task_id in official_selected)
    reproducible = (
        first.accepted_task_ids == second.accepted_task_ids
        and first.rejected_task_ids == second.rejected_task_ids
        and dict(first.selected_server_by_task) == dict(second.selected_server_by_task)
        and dict(first.round_one_selected_by_server) == dict(second.round_one_selected_by_server)
        and dict(first.final_price_by_task) == dict(second.final_price_by_task)
        and dict(first.metadata) == dict(second.metadata)
    )
    return {
        "label": raw["label"],
        "baseline": "arXiv:2403.15665v2_2024",
        "method": policy.name,
        "config_path": config_path.as_posix(),
        "metadata": dict(first.metadata),
        "round_one_selected_by_server": {
            key: list(value) for key, value in first.round_one_selected_by_server.items()
        },
        "round_one_bids": [
            {
                "task_id": bid.task_id,
                "server_id": bid.server_id,
                "price": bid.price,
                "feasible": bid.feasible,
            }
            for bid in first.round_one.bids
        ],
        "round_two_prices": dict(first.final_price_by_task),
        "accepted_task_ids": list(first.accepted_task_ids),
        "rejected_task_ids": list(first.rejected_task_ids),
        "final_task_states": {
            task_id: task_state.value
            for task_id, task_state in sorted(first.final_state.task_states.items())
        },
        "residual_before": residual_before.as_dict(),
        "residual_after": remaining_resources(first.final_state, server.server_id).as_dict(),
        "fixed_seed_repeat_equal": reproducible,
        "exact_solver_auxiliary": {
            "role": "auxiliary_not_official_pipeline",
            "selected_task_ids": list(exact_selected),
            "objective": exact_objective,
            "official_ga_objective": official_objective,
            "objective_gap": exact_objective - official_objective,
            "selected_subset_equal": exact_selected == official_selected,
        },
    }


def main() -> None:
    result = run_example()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"output_path={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
