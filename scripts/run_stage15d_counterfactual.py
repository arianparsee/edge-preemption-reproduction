"""Run one Stage-15D variant/policy pair twice and enforce the RNG gate."""

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
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy, lifecycle_funnel
from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import InstrumentedKnapsackSelector
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

STAGE15D_VARIANTS = (
    CounterfactualVariant.FIXED_PENALTY,
    CounterfactualVariant.INITIAL_POPULATION_REPAIR,
    CounterfactualVariant.OFFSPRING_REPAIR,
)
SHAPE_KEYS = (
    "selector_calls",
    "empty_calls",
    "single_candidate_calls",
    "ga_calls",
    "candidate_entries",
)


def _canonical_hash(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _policy(
    name: str,
    *,
    seed: int,
    tasks: tuple[Any, ...],
    server_count: int,
    variant: CounterfactualVariant,
    diagnostic_stage: str = "stage15d",
) -> tuple[
    InstrumentedDKPolicy,
    InstrumentedKnapsackSelector,
    CounterfactualKnapsackSelector,
    dict[str, str],
]:
    ga = PyeasygaConfig(seed=seed)
    counterfactual = CounterfactualKnapsackSelector(ga, variant)
    selector = InstrumentedKnapsackSelector(
        counterfactual,
        server_count=server_count,
        diagnostic_stage=diagnostic_stage,
    )
    if name == DK_POLICIES[0]:
        retention_config = PipelineDKRConfig.from_workload(ga=ga, workload_tasks=tasks)
        retention_policy = PipelineDoubleKnapsackRetentionPolicy(retention_config, selector)
        return (
            InstrumentedDKPolicy(retention_policy, selector),
            selector,
            counterfactual,
            retention_config.as_metadata(),
        )
    if name == DK_POLICIES[1]:
        preemption_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
        preemption_policy = PipelineDoubleKnapsackPreemptionPolicy(preemption_config, selector)
        return (
            InstrumentedDKPolicy(preemption_policy, selector),
            selector,
            counterfactual,
            preemption_config.as_metadata(),
        )
    raise ValueError(f"Stage 15-D supports only DK policies: {name}")


def _sanitized_selector_calls(
    selector: InstrumentedKnapsackSelector,
    counterfactual: CounterfactualKnapsackSelector,
) -> list[dict[str, object]]:
    funnel_rows = selector.observations_since(0)
    rng_rows = counterfactual.call_observations()
    if len(funnel_rows) != len(rng_rows):
        raise ValueError("selector funnel/RNG call count mismatch")
    rows: list[dict[str, object]] = []
    for funnel, rng in zip(funnel_rows, rng_rows, strict=True):
        if funnel.candidate_count != rng.candidate_count or funnel.call_kind != rng.call_kind:
            raise ValueError("selector funnel/RNG call shape mismatch")
        rows.append(
            {
                "auction_ordinal": funnel.auction_ordinal,
                "round_name": funnel.round_name,
                "server_ordinal": funnel.server_ordinal,
                "call_kind": rng.call_kind,
                "candidate_count": rng.candidate_count,
                "rng_primitive_calls": dict(rng.rng_counts),
                "rng_state_before_sha256": funnel.rng_state_before_sha256,
                "rng_state_after_sha256": funnel.rng_state_after_sha256,
                "initial_chromosomes_repaired": rng.initial_chromosomes_repaired,
                "initial_bits_removed": rng.initial_bits_removed,
                "offspring_repaired": rng.offspring_repaired,
                "offspring_bits_removed": rng.offspring_bits_removed,
            }
        )
    return rows


def _execute_once(
    *,
    config: dict[str, object],
    policy_name: str,
    variant: CounterfactualVariant,
    workload_seed: int = WORKLOAD_SEED,
    diagnostic_stage: str = "stage15d",
) -> dict[str, object]:
    descriptor = _descriptor(config, workload_seed)
    policy_seeds = _mapping(descriptor["policy_seeds"], "policy_seeds")
    policy_seed = int(cast(int, policy_seeds[policy_name]))
    workload, dataset = _workload_payload(workload_seed)
    workload_hash = sha256(
        (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    tasks = synthetic_normal_temporal_tasks(tuple(record.to_domain() for record in dataset.tasks))
    servers = tuple(record.to_domain() for record in dataset.servers)
    policy, selector, counterfactual, metadata = _policy(
        policy_name,
        seed=policy_seed,
        tasks=tasks,
        server_count=len(servers),
        variant=variant,
        diagnostic_stage=diagnostic_stage,
    )
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
        run_id=f"{diagnostic_stage.upper()}.{variant.value}.{workload_seed}.{policy_name}",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=metadata,
    )
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    payload: dict[str, object] = {
        "baseline": BASELINE,
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    selector_summary = selector.summary().as_dict()
    auction_summary = policy.summary()
    lifecycle = lifecycle_funnel(run.events)
    call_rows = _sanitized_selector_calls(selector, counterfactual)
    return {
        "scientific_fingerprint": scientific_fingerprint(payload),
        "selector_funnel": selector_summary,
        "auction_funnel": auction_summary,
        "lifecycle_funnel": lifecycle,
        "counterfactual": counterfactual.counterfactual_summary(),
        "selector_calls": call_rows,
        "selector_call_shape_sha256": _canonical_hash(
            [
                {
                    "auction_ordinal": row["auction_ordinal"],
                    "round_name": row["round_name"],
                    "server_ordinal": row["server_ordinal"],
                    "call_kind": row["call_kind"],
                    "candidate_count": row["candidate_count"],
                }
                for row in call_rows
            ]
        ),
        "selector_rng_trace_sha256": _canonical_hash(call_rows),
    }


def _baseline_shape_reasons(
    *, baseline: dict[str, object], replay: dict[str, object]
) -> list[str]:
    reasons: list[str] = []
    baseline_rounds = cast(dict[str, dict[str, int]], baseline["by_round"])
    selector = cast(dict[str, object], replay["selector_funnel"])
    replay_rounds = cast(dict[str, dict[str, int | float]], selector["by_round"])
    for round_name in ("round_1", "round_2"):
        for key in SHAPE_KEYS:
            old = int(baseline_rounds[round_name][key])
            new = int(replay_rounds[round_name][key])
            if old != new:
                reasons.append(f"{round_name}.{key}:{old}->{new}")
    counterfactual = cast(dict[str, object], replay["counterfactual"])
    old_choices = int(cast(int, baseline["uniform_choice_calls"]))
    new_choices = int(cast(int, counterfactual["uniform_choice_calls"]))
    if old_choices != new_choices:
        reasons.append(f"uniform_choice_calls:{old_choices}->{new_choices}")
    return reasons


def _enforce_baseline_rng_gate(
    *, baseline: dict[str, object], replay: dict[str, object]
) -> dict[str, object]:
    selector = cast(dict[str, object], replay["selector_funnel"])
    initial_rng = str(selector["initial_rng_state_sha256"])
    final_rng = str(selector["final_rng_state_sha256"])
    if initial_rng != baseline["initial_rng_state_sha256"]:
        raise ValueError("initial policy RNG state differs from Stage-15C baseline")
    reasons = _baseline_shape_reasons(baseline=baseline, replay=replay)
    final_equal = final_rng == baseline["final_rng_state_sha256"]
    if not final_equal and not reasons:
        raise ValueError("RNG state changed while the recorded call shape stayed equal")
    return {
        "passed": True,
        "initial_rng_state_equal": True,
        "final_rng_state_equal": final_equal,
        "recorded_call_shape_equal": not reasons,
        "allowed_difference_reasons": reasons,
        "baseline_primitive_counts_available": False,
        "baseline_primitive_count_note": (
            "Stage-15C stored final RNG hashes and aggregate call shape, not primitive counts; "
            "the baseline was not recomputed"
        ),
    }


def run_pair(
    *,
    config_path: Path,
    baseline_fingerprint_path: Path,
    baseline_rng_path: Path,
    policy_name: str,
    variant: CounterfactualVariant,
) -> dict[str, object]:
    """Execute two exact replays and return one sanitized pair artifact."""

    if variant not in STAGE15D_VARIANTS:
        raise ValueError("baseline control is forbidden for full Stage-15D execution")
    config = load_full_config(config_path)
    first_run = cast(list[dict[str, object]], config["runs"])[0]
    if first_run["workload_seed"] != WORKLOAD_SEED:
        raise ValueError("first materialized ASSUMP-033 seed changed")
    baseline_fingerprints = json.loads(baseline_fingerprint_path.read_text(encoding="utf-8"))
    baseline_rng = json.loads(baseline_rng_path.read_text(encoding="utf-8"))
    if baseline_rng["baseline_recomputed"]:
        raise ValueError("Stage-15C baseline guard must be reuse-only")
    baseline_scientific = baseline_fingerprints["policies"].get(policy_name)
    baseline_policy_rng = baseline_rng["policies"].get(policy_name)
    if baseline_scientific is None or baseline_policy_rng is None:
        raise ValueError("selected policy is missing from a baseline fixture")

    first = _execute_once(config=config, policy_name=policy_name, variant=variant)
    second = _execute_once(config=config, policy_name=policy_name, variant=variant)
    if first != second:
        raise ValueError("same-seed variant replay mismatch")
    rng_gate = _enforce_baseline_rng_gate(
        baseline=cast(dict[str, object], baseline_policy_rng), replay=first
    )
    fingerprint = cast(dict[str, object], first["scientific_fingerprint"])
    baseline_outcome = cast(dict[str, object], baseline_scientific["outcome"])
    variant_outcome = cast(dict[str, object], fingerprint["outcome"])
    numeric_delta = {
        key: float(cast(int | float, variant_outcome[key]))
        - float(cast(int | float, baseline_outcome[key]))
        for key in baseline_outcome
    }
    return {
        "schema_version": "stage15d-counterfactual-pair-v1",
        "label": "[آزمون کمکی] Stage 15-D single-factor counterfactual",
        "baseline": BASELINE,
        "baseline_source_stage": "Stage 15-C",
        "baseline_source_run": 31708325126,
        "baseline_recomputed": False,
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": fingerprint["policy_seed"],
        "policy": policy_name,
        "variant": variant.value,
        "replay_count": 2,
        "replay_exact": True,
        "rng_gate": rng_gate,
        "baseline_scientific_fingerprint": baseline_scientific,
        "variant_replay": first,
        "outcome_delta_from_baseline": numeric_delta,
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "official_algorithm_changed": False,
        "figure_6_overwritten": False,
        "thirty_workloads_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline-fingerprints", type=Path, required=True)
    parser.add_argument("--baseline-rng", type=Path, required=True)
    parser.add_argument("--policy", choices=DK_POLICIES, required=True)
    parser.add_argument(
        "--variant",
        choices=tuple(variant.value for variant in STAGE15D_VARIANTS),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite diagnostic: {args.output}")
    report = run_pair(
        config_path=args.config.resolve(),
        baseline_fingerprint_path=args.baseline_fingerprints.resolve(),
        baseline_rng_path=args.baseline_rng.resolve(),
        policy_name=args.policy,
        variant=CounterfactualVariant(args.variant),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "stage15d_pair_replay_exact_rng_gate_passed",
                "policy": args.policy,
                "variant": args.variant,
                "workload_seed": WORKLOAD_SEED,
                "output": args.output.name,
            }
        )
    )


if __name__ == "__main__":
    main()
