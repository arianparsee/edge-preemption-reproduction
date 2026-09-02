"""Run one approved Stage-15K.2 logical pair as two exact replays."""

from __future__ import annotations

import argparse
import errno
import json
import random
import time
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _policy, _sanitized_selector_calls
from run_stage15k1_pilot import (
    _never_admitted_expired,
    _outcome_delta,
    _prior_initialization_metrics,
    _relative_delta,
    _round_two_initialization_metrics,
    normalized_text_sha256,
)

from edge_reproduction.diagnostics.dk_funnel import lifecycle_funnel
from edge_reproduction.diagnostics.ga_counterfactual import CounterfactualVariant
from edge_reproduction.diagnostics.ga_instrumentation import _state_hash
from edge_reproduction.diagnostics.stage15k2_preemption import (
    Stage15K2PreemptionObserver,
    terminal_preemption_summary,
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

SEEDS = (
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)
POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANT = CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR
EXPECTED_CONFIG_SHA256 = "b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963"
EXPECTED_BASELINE_SHA256 = "5a76406da63fdcb853a5cb04d57e0a3e0bc41d6dac94b90b39e562ce686bc3ca"
EXPECTED_PRIOR_SHA256 = "2032a6ba51c2f4ae6f1d2543fd30ed84964f44e4674b94fe8e88d1bf1f723525"
TRANSIENT_ERRNOS = {
    errno.EAGAIN,
    errno.ECONNABORTED,
    errno.ECONNRESET,
    errno.ENETDOWN,
    errno.ENETRESET,
    errno.ENETUNREACH,
    errno.ETIMEDOUT,
}


def _load_pinned(path: Path, digest: str) -> dict[str, Any]:
    if normalized_text_sha256(path) != digest:
        raise ValueError(f"pinned input hash mismatch: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("pinned input must be a JSON object")
    return cast(dict[str, Any], value)


def _find_prior(payload: dict[str, Any], seed: int, policy: str) -> dict[str, Any]:
    rows = [
        cast(dict[str, Any], row)
        for row in cast(list[object], payload["pairs"])
        if int(cast(dict[str, Any], row)["workload_seed"]) == seed
        and cast(dict[str, Any], row)["policy"] == policy
    ]
    if len(rows) != 1:
        raise ValueError("expected one validated prior initialization-repair pair")
    return rows[0]


def _execute_once(
    *, config: dict[str, object], workload_seed: int, policy_name: str
) -> dict[str, object]:
    descriptor = _descriptor(config, workload_seed)
    policy_seed = int(cast(int, _mapping(descriptor["policy_seeds"], "policy_seeds")[policy_name]))
    workload, dataset = _workload_payload(workload_seed)
    workload_hash = sha256(
        (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    tasks = synthetic_normal_temporal_tasks(tuple(row.to_domain() for row in dataset.tasks))
    servers = tuple(row.to_domain() for row in dataset.servers)
    policy, selector, counterfactual, metadata = _policy(
        policy_name,
        seed=policy_seed,
        tasks=tasks,
        server_count=len(servers),
        variant=VARIANT,
        diagnostic_stage="stage15k2",
    )
    observer = Stage15K2PreemptionObserver(policy)
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=observer,
        config=TemporalRunConfig(
            run_id=f"STAGE15K2.{workload_seed}.{policy_name}",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=metadata,
    )
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    payload = {
        "baseline": BASELINE,
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    selector_summary = selector.summary().as_dict()
    calls = _sanitized_selector_calls(selector, counterfactual)
    return {
        "scientific_fingerprint": scientific_fingerprint(payload),
        "selector_funnel": selector_summary,
        "auction_funnel": policy.summary(),
        "lifecycle_funnel": lifecycle_funnel(run.events),
        "counterfactual": counterfactual.counterfactual_summary(),
        "selector_calls": calls,
        "selector_call_shape_sha256": _canonical_hash(
            [
                {
                    key: row[key]
                    for key in (
                        "auction_ordinal",
                        "round_name",
                        "server_ordinal",
                        "call_kind",
                        "candidate_count",
                    )
                }
                for row in calls
            ]
        ),
        "selector_rng_trace_sha256": _canonical_hash(calls),
        "preemption_diagnostic": observer.summary(),
        "terminal_preemption_outcome": terminal_preemption_summary(run.events),
    }


def _execute_with_retry(operation: Any) -> tuple[dict[str, object], float, int]:
    start = time.perf_counter()
    try:
        return cast(dict[str, object], operation()), time.perf_counter() - start, 0
    except OSError as error:
        if error.errno not in TRANSIENT_ERRNOS:
            raise
    start = time.perf_counter()
    return cast(dict[str, object], operation()), time.perf_counter() - start, 1


def run_pair(
    *,
    config_path: Path,
    baseline_path: Path,
    prior_path: Path,
    workload_seed: int,
    policy_name: str,
) -> dict[str, object]:
    if workload_seed not in SEEDS or policy_name not in POLICIES:
        raise ValueError("pair is outside the approved Stage 15-K.2 matrix")
    if normalized_text_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved config changed")
    config = load_full_config(config_path)
    descriptor = _descriptor(config, workload_seed)
    policy_seed = int(cast(dict[str, int], descriptor["policy_seeds"])[policy_name])
    baselines = _load_pinned(baseline_path, EXPECTED_BASELINE_SHA256)
    baseline = cast(dict[str, Any], baselines["records"][f"{workload_seed}:{policy_name}"])
    prior_fixture = _load_pinned(prior_path, EXPECTED_PRIOR_SHA256)
    prior = _find_prior(prior_fixture, workload_seed, policy_name)
    baseline_fp = cast(dict[str, Any], baseline["scientific_fingerprint"])
    prior_fp = cast(dict[str, Any], prior["scientific_fingerprint"])
    if baseline["baseline_rng_status"] != "unavailable_not_recorded":
        raise ValueError("unexpected baseline RNG observability")
    for field in ("workload_seed", "policy_seed", "policy", "workload_sha256"):
        if baseline_fp[field] != prior_fp[field]:
            raise ValueError(f"prior repair identity mismatch: {field}")
    if int(baseline["policy_seed"]) != policy_seed or prior["replay_exact"] is not True:
        raise ValueError("reuse evidence failed identity/replay validation")

    first, first_seconds, first_retry = _execute_with_retry(
        lambda: _execute_once(config=config, workload_seed=workload_seed, policy_name=policy_name)
    )
    second, second_seconds, second_retry = _execute_with_retry(
        lambda: _execute_once(config=config, workload_seed=workload_seed, policy_name=policy_name)
    )
    if first != second:
        raise ValueError("same-seed Stage 15-K.2 replay mismatch")
    selector = cast(dict[str, Any], first["selector_funnel"])
    if selector["initial_rng_state_sha256"] != _state_hash(random.Random(policy_seed).getstate()):
        raise ValueError("initial RNG state differs from policy seed")
    metrics = _round_two_initialization_metrics(first)
    fp = cast(dict[str, Any], first["scientific_fingerprint"])
    for field in ("workload_seed", "policy_seed", "policy", "workload_sha256"):
        if fp[field] != baseline_fp[field]:
            raise ValueError(f"variant identity mismatch: {field}")
    outcome = cast(dict[str, Any], fp["outcome"])
    baseline_outcome = cast(dict[str, Any], baseline_fp["outcome"])
    prior_outcome = cast(dict[str, Any], prior_fp["outcome"])
    residual = (
        float(outcome["completed_utility"])
        + float(outcome["rejected_utility"])
        - float(baseline_outcome["completed_utility"])
        - float(baseline_outcome["rejected_utility"])
    )
    if abs(residual) > 1e-9:
        raise ValueError("Utility conservation failed")
    lifecycle = cast(dict[str, Any], first["lifecycle_funnel"])
    baseline_lifecycle = cast(dict[str, Any], baseline["lifecycle_funnel"])
    if lifecycle.get("expired_during_canonicalization", 0) != baseline_lifecycle.get(
        "expired_during_canonicalization", 0
    ):
        raise ValueError("PRE_ADMISSION_INFEASIBLE changed")
    auction = cast(dict[str, Any], first["auction_funnel"])
    totals = cast(dict[str, Any], auction["totals"])
    if metrics["round_1_initial_chromosomes_repaired"] != 0:
        raise ValueError("Round 1 changed")
    delta = _outcome_delta(outcome, baseline_outcome)
    prior_delta = _outcome_delta(prior_outcome, baseline_outcome)
    share = (
        delta["completed_utility"] / prior_delta["completed_utility"]
        if prior_delta["completed_utility"] != 0
        else None
    )
    return {
        "schema_version": "stage15k2-r2-initialization-repair-pair-v1",
        "label": "[فرض آزمون کمکی] Stage 15-K.2 five-seed validation",
        "assumptions": ["ASSUMP-048", "ASSUMP-049"],
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "variant": VARIANT.value,
        "replay_count": 2,
        "replay_exact": True,
        "baseline_recomputed": False,
        "prior_repair_recomputed": False,
        "technical_retry_count": first_retry + second_retry,
        "runtime_seconds": {"replay_1": first_seconds, "replay_2": second_seconds},
        "rng_gate": {
            "option": "A_partial_observability",
            "initial_rng_state_matches_policy_seed": True,
            "same_variant_final_rng_state_replay_exact": True,
            "same_variant_primitive_counts_replay_exact": True,
            "same_variant_call_shape_replay_exact": True,
            "direct_random_draws_added_by_repair": 0,
            "baseline_comparison": "unknown_not_recorded_in_stage13_baseline",
            "baseline_rng_gate_claimed": False,
        },
        "invariant_gate": {
            "engine_capacity_and_state_invariants_passed": True,
            "task_partition_complete_and_disjoint": True,
            "utility_conservation_passed": True,
            "utility_conservation_residual": residual,
            "pre_admission_infeasible_unchanged": True,
            "round_1_initial_repair_count_zero": True,
            "round_1_algorithm_changed": False,
            "pricing_algorithm_changed": False,
            "server_selection_algorithm_changed": False,
            "lifecycle_changed": False,
            "preemption_rule_changed": False,
        },
        "baseline": {"scientific_fingerprint": baseline_fp, "lifecycle_funnel": baseline_lifecycle},
        "round_two_only_repair": {
            "scientific_fingerprint": fp,
            "lifecycle_funnel": lifecycle,
            "selector_funnel": selector,
            "auction_funnel": auction,
            "initialization_metrics": metrics,
            "round_1_admission": int(totals["round_1_server_assignments"]),
            "round_2_admission": int(totals["round_2_accepted"]),
            "round_2_rejection": int(totals["round_2_rejected"]),
            "never_admitted_expired_proxy": _never_admitted_expired(lifecycle),
            "delta_from_baseline": delta,
            "relative_delta_from_baseline": {
                key: _relative_delta(float(outcome[key]), float(baseline_outcome[key]))
                for key in baseline_outcome
            },
            "preemption_diagnostic": first["preemption_diagnostic"],
            "terminal_preemption_outcome": first["terminal_preemption_outcome"],
        },
        "prior_all_round_initialization_repair": {
            "scientific_fingerprint": prior_fp,
            "lifecycle_funnel": prior["lifecycle_funnel"],
            "initialization_metrics": _prior_initialization_metrics(prior),
            "delta_from_baseline": prior_delta,
            "source_artifact_sha256": prior["source_artifact_sha256"],
        },
        "effect_explained": {"completed_utility_effect_share_of_prior_repair": share},
        "variant_replay": first,
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
    parser.add_argument("--baselines", type=Path, required=True)
    parser.add_argument("--prior-repairs", type=Path, required=True)
    parser.add_argument("--workload-seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = run_pair(
        config_path=args.config,
        baseline_path=args.baselines,
        prior_path=args.prior_repairs,
        workload_seed=args.workload_seed,
        policy_name=args.policy,
    )
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": "stage15k2_pair_valid", "seed": args.workload_seed, "policy": args.policy}
        )
    )


if __name__ == "__main__":
    main()
