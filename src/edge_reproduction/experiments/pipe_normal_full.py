"""Materialized, resumable Stage-13F harness for the future PIPE-NORMAL run."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from statistics import fmean
from types import MappingProxyType

import numpy as np

from edge_reproduction.algorithms.base import AllocationPolicy
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
from edge_reproduction.datasets.synthetic import (
    SyntheticDataset,
    SyntheticGenerationConfig,
    generate_synthetic,
)
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.temporal_engine import (
    TemporalRunConfig,
    run_temporal_policy,
    synthetic_normal_temporal_tasks,
)

SCHEMA = "stage13f-pipe-normal-full-v1"
BASELINE = "arXiv:2403.15665v2_2024"
POLICY_NAMES = (
    "knapsack_greedy_retention",
    "knapsack_greedy_preemption",
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
METRICS = (
    "completed_utility",
    "rejected_utility",
    "ever_preempted_utility",
    "completed_jobs",
    "rejected_jobs",
    "ever_preempted_jobs",
    "raw_auction_rejection_count",
)


def _seed_children(seed: int, count: int) -> tuple[int, ...]:
    return tuple(
        int(child.generate_state(1, dtype=np.uint64)[0])
        for child in np.random.SeedSequence(seed).spawn(count)
    )


def materialized_config(*, root_seed: int = 20240812) -> dict[str, object]:
    """Return the complete ASSUMP-033 run matrix before any full execution."""

    workload_seeds = tuple(sorted(_seed_children(root_seed, 30)))
    runs = [
        {
            "repeat_index": index,
            "workload_seed": workload_seed,
            "policy_seeds": dict(
                zip(POLICY_NAMES, _seed_children(workload_seed, len(POLICY_NAMES)), strict=True)
            ),
        }
        for index, workload_seed in enumerate(workload_seeds)
    ]
    return {
        "schema_version": SCHEMA,
        "experiment_id": "PIPE-NORMAL",
        "baseline": BASELINE,
        "scientific_label": "reproduction_under_explicit_ASSUMP-033_through_ASSUMP-043",
        "execution_status": "ready_not_started_stage13f",
        "paper_claims": {"figure_6_reproduced": False, "full_run_completed": False},
        "root_seed": root_seed,
        "repeat_count": 30,
        "arrival_slots": 100,
        "server_count": 8,
        "drain_policy": "through_maximum_inclusive_absolute_deadline",
        "numerical_tolerance": 1e-9,
        "aggregation": "arithmetic_mean_across_30_paired_workloads",
        "workload_sharing": "one_identical_workload_per_repeat_shared_by_four_policies",
        "policy_rng": "independent_named_stream_per_policy",
        "policies": list(POLICY_NAMES),
        "policy_ga_settings": {
            "knapsack_greedy_retention": {
                "library": "pyeasyga==0.3.1",
                "population_size": 200,
                "tournament_size": 20,
                "generations": 30,
                "crossover_probability": 0.8,
                "mutation_probability": 0.2,
                "elitism": True,
                "maximisation": True,
                "provenance": "ASSUMP-041",
            },
            "knapsack_greedy_preemption": {
                "library": "pyeasyga==0.3.1",
                "population_size": 200,
                "tournament_size": 20,
                "generations": 30,
                "crossover_probability": 0.8,
                "mutation_probability": 0.2,
                "elitism": True,
                "maximisation": True,
                "provenance": "ASSUMP-041",
            },
            "pipeline_double_knapsack_retention": {
                "library": "pyeasyga==0.3.1",
                "population_size": 200,
                "tournament_size": 20,
                "generations": 50,
                "crossover_probability": 0.8,
                "mutation_probability": 0.2,
                "elitism": True,
                "maximisation": True,
                "provenance": "ASSUMP-015",
            },
            "pipeline_double_knapsack_preemption": {
                "library": "pyeasyga==0.3.1",
                "population_size": 200,
                "tournament_size": 20,
                "generations": 50,
                "crossover_probability": 0.8,
                "mutation_probability": 0.2,
                "elitism": True,
                "maximisation": True,
                "provenance": "ASSUMP-018",
            },
        },
        "assumptions": [f"ASSUMP-{number:03d}" for number in range(33, 44)],
        "runs": runs,
    }


def write_materialized_config(path: Path) -> None:
    """Create, but never overwrite, the full pre-execution configuration."""

    if path.exists():
        raise FileExistsError(f"refusing to overwrite materialized config: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(materialized_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a JSON object")
    return dict[str, object](value)


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def load_full_config(path: Path) -> dict[str, object]:
    """Load and cryptographically-independent validate the full seed matrix."""

    raw: object = json.loads(path.read_text(encoding="utf-8"))
    config = _mapping(raw, "full config")
    expected = materialized_config(root_seed=_integer(config.get("root_seed"), "root_seed"))
    if config != expected:
        raise ValueError("materialized PIPE-NORMAL config differs from deterministic specification")
    return config


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _descriptor(config: Mapping[str, object], workload_seed: int) -> dict[str, object]:
    raw_runs = config["runs"]
    if not isinstance(raw_runs, list):
        raise TypeError("runs must be a list")
    matches = [
        _mapping(item, "run descriptor")
        for item in raw_runs
        if isinstance(item, dict) and item.get("workload_seed") == workload_seed
    ]
    if len(matches) != 1:
        raise ValueError("workload_seed must identify exactly one materialized repeat")
    return matches[0]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _workload_payload(workload_seed: int) -> tuple[dict[str, object], SyntheticDataset]:
    generation = SyntheticGenerationConfig(
        dataset_id=f"pipe-normal-{workload_seed}",
        label="PIPE_NORMAL_FULL_REPRODUCTION_ASSUMP_033_043",
        workload_kind="normal",
        seed=workload_seed,
        arrival_slots=100,
        drain_slots=0,
        server_count=8,
    )
    dataset = generate_synthetic(generation)
    payload: dict[str, object] = {
        "schema_version": "stage13f-pipe-normal-workload-v1",
        "temporal_conversion": "ASSUMP-036_and_ASSUMP-037",
        "metadata": dataset.metadata(),
        "arrival_raw_draws": list(dataset.arrival_raw_draws),
        "arrival_counts": list(dataset.arrival_counts),
        "servers": [server.as_dict() for server in dataset.servers],
        "tasks": [task.as_dict() for task in dataset.tasks],
    }
    return payload, dataset


def _policy(
    name: str, seed: int, tasks: tuple[Task, ...]
) -> tuple[AllocationPolicy, PyeasygaUtilityKnapsackSelector, Mapping[str, str]]:
    if name == POLICY_NAMES[0]:
        kg_ga = KGPyeasygaConfig(seed=seed)
        selector = PyeasygaUtilityKnapsackSelector(kg_ga)
        return KnapsackGreedyRetentionPolicy(selector), selector, kg_ga.as_metadata()
    if name == POLICY_NAMES[1]:
        kg_ga = KGPyeasygaConfig(seed=seed)
        selector = PyeasygaUtilityKnapsackSelector(kg_ga)
        return KnapsackGreedyPreemptionPolicy(selector), selector, kg_ga.as_metadata()
    dk_ga = PyeasygaConfig(seed=seed)
    selector = PyeasygaUtilityKnapsackSelector(dk_ga)
    if name == POLICY_NAMES[2]:
        dkr_config = PipelineDKRConfig.from_workload(ga=dk_ga, workload_tasks=tasks)
        return (
            PipelineDoubleKnapsackRetentionPolicy(dkr_config, selector),
            selector,
            dkr_config.as_metadata(),
        )
    if name == POLICY_NAMES[3]:
        dkp_config = PipelineDKPConfig.from_workload(ga=dk_ga, workload_tasks=tasks)
        return (
            PipelineDoubleKnapsackPreemptionPolicy(dkp_config, selector),
            selector,
            dkp_config.as_metadata(),
        )
    raise ValueError(f"unknown policy: {name}")


@dataclass(frozen=True, slots=True)
class FullRunOutcome:
    status: str
    result_path: Path
    manifest_path: Path


def run_full_pair(
    config_path: Path,
    *,
    workload_seed: int,
    policy_name: str,
    project_root: Path = Path("."),
    resume: bool = False,
) -> FullRunOutcome:
    """Execute one of 120 isolated pairs; existing artifacts are verified only."""

    resolved_config = project_root / config_path
    config = load_full_config(resolved_config)
    descriptor = _descriptor(config, workload_seed)
    raw_policy_seeds = _mapping(descriptor["policy_seeds"], "policy_seeds")
    if policy_name not in POLICY_NAMES:
        raise ValueError(f"unknown policy: {policy_name}")
    policy_seed = _integer(raw_policy_seeds[policy_name], "policy_seed")
    run_directory = (
        project_root / "results" / "raw" / "stage13f" / "PIPE-NORMAL"
        / f"seed-{workload_seed}" / policy_name
    )
    result_path = run_directory / "result.json"
    manifest_path = run_directory / "manifest.json"
    if run_directory.exists():
        if not resume:
            raise FileExistsError(f"run output exists: {run_directory}; use --resume")
        if not result_path.is_file() or not manifest_path.is_file():
            raise FileExistsError("incomplete run directory; refusing to overwrite")
        manifest = _mapping(json.loads(manifest_path.read_text(encoding="utf-8")), "manifest")
        if manifest.get("result_sha256") != file_sha256(result_path):
            raise ValueError("existing result hash mismatch")
        if manifest.get("config_sha256") != file_sha256(resolved_config):
            raise ValueError("existing config hash mismatch")
        return FullRunOutcome("skipped_existing_verified", result_path, manifest_path)

    workload, dataset = _workload_payload(workload_seed)
    workload_bytes = (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    workload_hash = sha256(workload_bytes).hexdigest()
    allocation_tasks = tuple(record.to_domain() for record in dataset.tasks)
    tasks = synthetic_normal_temporal_tasks(allocation_tasks)
    servers = tuple(record.to_domain() for record in dataset.servers)
    policy, selector, policy_metadata = _policy(policy_name, policy_seed, tasks)
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
            run_id=f"PIPE-NORMAL.{workload_seed}.{policy_name}",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=policy_metadata,
    )
    run.metadata = MappingProxyType(
        dict(run.metadata)
        | selector.runtime_metadata()
        | {
            "full_100_slot_30_repeat_run": "true",
            "workload_seed": str(workload_seed),
            "workload_sha256": workload_hash,
            "assumptions": "ASSUMP-033_through_ASSUMP-043",
        }
    )
    result = {
        "schema_version": "stage13f-pipe-normal-raw-result-v1",
        "baseline": BASELINE,
        "scientific_label": config["scientific_label"],
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    run_directory.mkdir(parents=True, exist_ok=False)
    workload_path = run_directory / "workload.json"
    workload_path.write_bytes(workload_bytes)
    _write_json(result_path, result)
    _write_json(
        manifest_path,
        {
            "schema_version": "stage13f-pipe-normal-manifest-v1",
            "config_sha256": file_sha256(resolved_config),
            "workload_sha256": file_sha256(workload_path),
            "result_sha256": file_sha256(result_path),
            "workload_seed": workload_seed,
            "policy_seed": policy_seed,
            "policy": policy_name,
        },
    )
    return FullRunOutcome("succeeded", result_path, manifest_path)


def aggregate_complete_full_run(
    config_path: Path, *, project_root: Path = Path(".")
) -> dict[str, object]:
    """Compute only arithmetic means, and only after all 120 raw runs exist."""

    config = load_full_config(project_root / config_path)
    raw_runs = config["runs"]
    if not isinstance(raw_runs, list):
        raise TypeError("runs must be a list")
    values: dict[str, dict[str, list[float]]] = {
        policy: {metric: [] for metric in METRICS} for policy in POLICY_NAMES
    }
    missing: list[str] = []
    for raw_descriptor in raw_runs:
        descriptor = _mapping(raw_descriptor, "run descriptor")
        seed = _integer(descriptor["workload_seed"], "workload_seed")
        for policy in POLICY_NAMES:
            path = (
                project_root / "results" / "raw" / "stage13f" / "PIPE-NORMAL"
                / f"seed-{seed}" / policy / "result.json"
            )
            if not path.is_file():
                missing.append(path.as_posix())
                continue
            result = _mapping(json.loads(path.read_text(encoding="utf-8")), "result")
            run = _mapping(result["run"], "run")
            outcome = _mapping(run["outcome"], "outcome")
            for metric in METRICS:
                value = outcome[metric]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"outcome.{metric} must be numeric")
                values[policy][metric].append(float(value))
    if missing:
        raise FileNotFoundError(
            f"full aggregation requires all 120 raw runs; missing {len(missing)}"
        )
    return {
        "schema_version": "stage13f-pipe-normal-aggregate-v1",
        "aggregation": "arithmetic_mean",
        "repeat_count": 30,
        "policies": {
            policy: {metric: fmean(items) for metric, items in metrics.items()}
            for policy, metrics in values.items()
        },
    }
