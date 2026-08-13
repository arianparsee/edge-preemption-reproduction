"""Run one sanitized Stage 15-B instrumented DK diagnostic in memory."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    PipelineDoubleKnapsackRetentionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    InstrumentedKnapsackSelector,
)
from edge_reproduction.experiments.pipe_normal_full import (
    BASELINE,
    _descriptor,
    _mapping,
    _workload_payload,
    load_full_config,
)
from edge_reproduction.simulation.temporal_engine import (
    TemporalRunConfig,
    run_temporal_policy,
    synthetic_normal_temporal_tasks,
)

WORKLOAD_SEED = 541501192080118187
DK_POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def scientific_fingerprint(payload: dict[str, object]) -> dict[str, object]:
    """Create a sanitized exact fingerprint of scientific outcomes and state."""

    run = cast(dict[str, object], payload["run"])
    outcome = cast(dict[str, object], run["outcome"])
    scalar_outcome = {key: value for key, value in outcome.items() if not key.endswith("_task_ids")}
    id_hashes = {
        key: _canonical_hash(value) for key, value in outcome.items() if key.endswith("_task_ids")
    }
    scientific_state = {
        "events": run["events"],
        "final_task_states": run["final_task_states"],
        "progress_by_task": run["progress_by_task"],
        "rejection_reasons_by_task": run["rejection_reasons_by_task"],
        "retry_count_by_task": run["retry_count_by_task"],
    }
    return {
        "workload_seed": payload["workload_seed"],
        "policy_seed": payload["policy_seed"],
        "policy": payload["policy"],
        "workload_sha256": payload["workload_sha256"],
        "outcome": scalar_outcome,
        "outcome_task_id_sha256": id_hashes,
        "scientific_state_sha256": _canonical_hash(scientific_state),
    }


def _policy(
    name: str,
    *,
    seed: int,
    tasks: tuple[Any, ...],
    server_count: int,
) -> tuple[Any, InstrumentedKnapsackSelector, dict[str, str]]:
    ga = PyeasygaConfig(seed=seed)
    base_selector = PyeasygaUtilityKnapsackSelector(ga)
    selector = InstrumentedKnapsackSelector(base_selector, server_count=server_count)
    if name == DK_POLICIES[0]:
        retention_config = PipelineDKRConfig.from_workload(ga=ga, workload_tasks=tasks)
        return (
            PipelineDoubleKnapsackRetentionPolicy(retention_config, selector),
            selector,
            retention_config.as_metadata(),
        )
    if name == DK_POLICIES[1]:
        preemption_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
        return (
            PipelineDoubleKnapsackPreemptionPolicy(preemption_config, selector),
            selector,
            preemption_config.as_metadata(),
        )
    raise ValueError(f"Stage 15-B supports only DK policies: {name}")


def run_diagnostic(
    *, config_path: Path, baseline_path: Path, policy_name: str
) -> dict[str, object]:
    """Run the instrumented path and fail on any baseline scientific difference."""

    config = load_full_config(config_path)
    first_run = cast(list[dict[str, object]], config["runs"])[0]
    if first_run["workload_seed"] != WORKLOAD_SEED:
        raise ValueError("first materialized ASSUMP-033 seed changed")
    descriptor = _descriptor(config, WORKLOAD_SEED)
    policy_seeds = _mapping(descriptor["policy_seeds"], "policy_seeds")
    policy_seed = int(cast(int, policy_seeds[policy_name]))
    workload, dataset = _workload_payload(WORKLOAD_SEED)
    workload_hash = sha256(
        (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    tasks = synthetic_normal_temporal_tasks(tuple(record.to_domain() for record in dataset.tasks))
    servers = tuple(record.to_domain() for record in dataset.servers)
    policy, selector, policy_metadata = _policy(
        policy_name,
        seed=policy_seed,
        tasks=tasks,
        server_count=len(servers),
    )
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
            run_id=f"STAGE15B.{WORKLOAD_SEED}.{policy_name}",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=policy_metadata,
    )
    run.metadata = MappingProxyType(dict(run.metadata) | selector.runtime_metadata())
    payload: dict[str, object] = {
        "baseline": BASELINE,
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    fingerprint = scientific_fingerprint(payload)
    baselines = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = baselines["policies"].get(policy_name)
    if expected is None:
        raise ValueError("baseline fingerprint missing selected policy")
    if fingerprint != expected:
        raise ValueError("instrumented scientific fingerprint differs from validated baseline")
    summary = selector.summary().as_dict()
    return {
        "schema_version": "stage15b-ga-diagnostic-v1",
        "label": "[آزمون کمکی] instrumentation غیرمداخله‌ای GA",
        "baseline": BASELINE,
        "baseline_source_run": 31624982369,
        "baseline_recomputed": False,
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "scientific_fingerprint_equal": True,
        "rng_observation_only": True,
        "ga_configuration_changed": False,
        "task_identifiers_in_artifact": False,
        "raw_workload_in_artifact": False,
        "scientific_fingerprint": fingerprint,
        "instrumentation": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--policy", choices=DK_POLICIES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite diagnostic: {args.output}")
    report = run_diagnostic(
        config_path=args.config.resolve(),
        baseline_path=args.baseline.resolve(),
        policy_name=args.policy,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "scientific_fingerprint_equal",
                "policy": args.policy,
                "workload_seed": WORKLOAD_SEED,
                "diagnostic_output": args.output.name,
            }
        )
    )


if __name__ == "__main__":
    main()
