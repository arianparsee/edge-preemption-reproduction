"""Run one sanitized Stage 15-C DK decision-funnel diagnostic in memory."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import DK_POLICIES, WORKLOAD_SEED, scientific_fingerprint

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
from edge_reproduction.diagnostics.dk_funnel import (
    InstrumentedDKPolicy,
    lifecycle_funnel,
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


def _policy(
    name: str,
    *,
    seed: int,
    tasks: tuple[Any, ...],
    server_count: int,
) -> tuple[InstrumentedDKPolicy, InstrumentedKnapsackSelector, dict[str, str]]:
    ga = PyeasygaConfig(seed=seed)
    base_selector = PyeasygaUtilityKnapsackSelector(ga)
    selector = InstrumentedKnapsackSelector(
        base_selector,
        server_count=server_count,
        diagnostic_stage="stage15c",
    )
    if name == DK_POLICIES[0]:
        retention_config = PipelineDKRConfig.from_workload(ga=ga, workload_tasks=tasks)
        retention_policy = PipelineDoubleKnapsackRetentionPolicy(retention_config, selector)
        return (
            InstrumentedDKPolicy(retention_policy, selector),
            selector,
            retention_config.as_metadata(),
        )
    if name == DK_POLICIES[1]:
        preemption_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
        preemption_policy = PipelineDoubleKnapsackPreemptionPolicy(preemption_config, selector)
        return (
            InstrumentedDKPolicy(preemption_policy, selector),
            selector,
            preemption_config.as_metadata(),
        )
    raise ValueError(f"Stage 15-C supports only DK policies: {name}")


def run_diagnostic(
    *, config_path: Path, baseline_path: Path, policy_name: str
) -> dict[str, object]:
    """Execute one instrumented funnel and fail on any scientific difference."""

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
            run_id=f"STAGE15C.{WORKLOAD_SEED}.{policy_name}",
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
    if fingerprint != expected:
        raise ValueError("Stage 15-C scientific fingerprint differs from validated baseline")

    selector_summary = selector.summary().as_dict()
    auction_summary = policy.summary()
    lifecycle = lifecycle_funnel(run.events)
    totals = cast(dict[str, int], auction_summary["totals"])
    if totals["round_2_accepted"] != lifecycle.get("accepted", 0):
        raise ValueError("accepted funnel/event invariant failed")
    if totals["round_2_rejected"] != run.outcome.raw_auction_rejection_count:
        raise ValueError("rejected funnel/outcome invariant failed")
    if totals["round_2_preempted"] != lifecycle.get("preempted", 0):
        raise ValueError("preempted funnel/event invariant failed")
    for round_name in ("round_1", "round_2"):
        selector_round = cast(
            dict[str, dict[str, int | float]], selector_summary["by_round"]
        )[round_name]
        prefix = round_name
        if selector_round["candidate_entries"] != totals[f"{prefix}_candidate_entries"]:
            raise ValueError(f"{round_name} candidate funnel invariant failed")
        if (
            selector_round["raw_best_selected_entries"]
            != totals[f"{prefix}_raw_best_selected_entries"]
        ):
            raise ValueError(f"{round_name} raw chromosome funnel invariant failed")

    return {
        "schema_version": "stage15c-dk-funnel-v1",
        "label": "[آزمون کمکی] instrumentation غیرمداخله‌ای funnel تصمیم DK",
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
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "scientific_fingerprint": fingerprint,
        "selector_funnel": selector_summary,
        "auction_funnel": auction_summary,
        "lifecycle_funnel": lifecycle,
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
