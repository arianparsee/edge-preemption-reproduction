"""Stage-13D hand-sized four-policy temporal PIPE-NORMAL smoke scenario."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import numpy as np

from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import (
    KGPyeasygaConfig,
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack_greedy_preemption import (
    KnapsackGreedyPreemptionPolicy,
)
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    KnapsackGreedyRetentionPolicy,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.temporal_engine import (
    TemporalRun,
    TemporalRunConfig,
    run_temporal_policy,
    synthetic_normal_temporal_tasks,
)

POLICY_NAMES = (
    "knapsack_greedy_retention",
    "knapsack_greedy_preemption",
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a JSON object")
    return dict[str, object](value)


def _resource(raw: object) -> ResourceVector:
    values = _mapping(raw, name="resource vector")
    return ResourceVector(
        _number(values["storage"], name="storage"),
        _number(values["computation"], name="computation"),
        _number(values["upload"], name="upload"),
        _number(values["download"], name="download"),
    )


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    return float(value)


def _integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _load_config(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    config = _mapping(raw, name="temporal smoke config")
    if config.get("schema_version") != "stage13d-temporal-smoke-v1":
        raise ValueError("unexpected temporal smoke schema")
    if config.get("scientific_label") != "stage13d_smoke_not_full_paper_experiment":
        raise ValueError("missing Stage-13D smoke scientific label")
    if config.get("baseline") != "arXiv:2403.15665v2_2024":
        raise ValueError("unexpected reproduction baseline")
    return config


def _build_workload(config: Mapping[str, object]) -> tuple[tuple[Task, ...], tuple[Server, ...]]:
    raw_tasks = config["tasks"]
    raw_servers = config["servers"]
    if not isinstance(raw_tasks, list) or not isinstance(raw_servers, list):
        raise TypeError("tasks and servers must be JSON arrays")
    allocation_tasks = tuple(
        Task(
            str(item["task_id"]),
            _integer(item["arrival_slot"], name="arrival_slot"),
            _integer(item["deadline_slots"], name="deadline_slots"),
            _number(item["utility"], name="utility"),
            _resource(item["demand"]),
        )
        for raw_item in raw_tasks
        for item in (_mapping(raw_item, name="task"),)
    )
    tasks = synthetic_normal_temporal_tasks(allocation_tasks)
    servers = tuple(
        Server(str(item["server_id"]), _resource(item["capacity"]))
        for raw_item in raw_servers
        for item in (_mapping(raw_item, name="server"),)
    )
    return tasks, servers


def _method_seeds(config: Mapping[str, object]) -> dict[str, int]:
    raw = _mapping(config["policy_seeds"], name="policy_seeds")
    if set(raw) != set(POLICY_NAMES):
        raise ValueError("policy_seeds must name exactly the four paper policies")
    seeds = {name: _integer(raw[name], name=f"policy_seeds.{name}") for name in POLICY_NAMES}
    if len(set(seeds.values())) != len(seeds):
        raise ValueError("policy RNG streams must have distinct materialized seeds")
    return seeds


def run_temporal_smoke(config_path: Path) -> dict[str, object]:
    """Run the fixed hand scenario through all four persistent policy streams."""

    config = _load_config(config_path)
    tasks, servers = _build_workload(config)
    seeds = _method_seeds(config)
    root_seed = _integer(config["root_seed"], name="root_seed")
    generated = tuple(
        int(child.generate_state(1, dtype=np.uint64)[0])
        for child in np.random.SeedSequence(root_seed).spawn(len(POLICY_NAMES))
    )
    if tuple(seeds[name] for name in POLICY_NAMES) != generated:
        raise ValueError("materialized policy seeds do not match root SeedSequence")
    arrival_slots = _integer(config["arrival_slots"], name="arrival_slots")
    tolerance = _number(config["numerical_tolerance"], name="numerical_tolerance")

    kg_r_ga = KGPyeasygaConfig(seed=seeds[POLICY_NAMES[0]])
    kg_p_ga = KGPyeasygaConfig(seed=seeds[POLICY_NAMES[1]])
    dkr_ga = PyeasygaConfig(seed=seeds[POLICY_NAMES[2]])
    dkp_ga = PyeasygaConfig(seed=seeds[POLICY_NAMES[3]])
    dkr_config = PipelineDKRConfig.from_workload(ga=dkr_ga, workload_tasks=tasks)
    dkp_config = PipelineDKPConfig.from_workload(ga=dkp_ga, workload_tasks=tasks)
    kg_r_selector = PyeasygaUtilityKnapsackSelector(kg_r_ga)
    kg_p_selector = PyeasygaUtilityKnapsackSelector(kg_p_ga)
    dkr_selector = PyeasygaUtilityKnapsackSelector(dkr_ga)
    dkp_selector = PyeasygaUtilityKnapsackSelector(dkp_ga)
    specs = (
        (
            KnapsackGreedyRetentionPolicy(kg_r_selector),
            kg_r_ga.as_metadata(),
            kg_r_selector,
        ),
        (
            KnapsackGreedyPreemptionPolicy(kg_p_selector),
            kg_p_ga.as_metadata(),
            kg_p_selector,
        ),
        (
            PipelineDoubleKnapsackRetentionPolicy(
                dkr_config,
                dkr_selector,
            ),
            dkr_config.as_metadata(),
            dkr_selector,
        ),
        (
            PipelineDoubleKnapsackPreemptionPolicy(
                dkp_config,
                dkp_selector,
            ),
            dkp_config.as_metadata(),
            dkp_selector,
        ),
    )

    runs: list[TemporalRun] = []
    for policy, metadata, selector in specs:
        policy_metadata = dict(metadata)
        policy_metadata["rng.stream_name"] = f"policy.{policy.name}"
        policy_metadata["ga.single_candidate_compatibility"] = (
            "deterministic_exact_degenerate_objective_for_pyeasyga_0.3.1"
        )
        run = run_temporal_policy(
                original_tasks=tasks,
                servers=servers,
                policy=policy,
                config=TemporalRunConfig(
                    run_id=f"{config['run_id']}.{policy.name}",
                    policy_seed=seeds[policy.name],
                    arrival_slots=arrival_slots,
                    numerical_tolerance=tolerance,
                ),
                policy_metadata=policy_metadata,
            )
        run.metadata = MappingProxyType(
            dict(run.metadata) | selector.runtime_metadata()
        )
        runs.append(run)
    return {
        "schema_version": "stage13d-temporal-smoke-result-v1",
        "scientific_label": config["scientific_label"],
        "baseline": config["baseline"],
        "run_id": config["run_id"],
        "root_seed": root_seed,
        "seed_materialization": config["seed_materialization"],
        "workload_sharing": "same_immutable_original_workload_for_all_four_policies",
        "policy_seeds": seeds,
        "full_100_slot_30_repeat_run": False,
        "figure_6_reproduced": False,
        "runs": [run.as_dict() for run in runs],
    }
