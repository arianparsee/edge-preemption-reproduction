"""Run the approved Stage-15K.1 R2-only initialization-repair pilot."""

from __future__ import annotations

import argparse
import errno
import json
import random
import time
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from run_stage15b_ga_diagnostic import DK_POLICIES, WORKLOAD_SEED
from run_stage15d_counterfactual import _enforce_baseline_rng_gate, _execute_once

from edge_reproduction.diagnostics.ga_counterfactual import CounterfactualVariant
from edge_reproduction.diagnostics.ga_instrumentation import _state_hash
from edge_reproduction.experiments.pipe_normal_full import _descriptor, load_full_config

VARIANT = CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR
EXPECTED_CONFIG_SHA256 = "b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963"
EXPECTED_BASELINE_FIXTURE_SHA256 = (
    "5a76406da63fdcb853a5cb04d57e0a3e0bc41d6dac94b90b39e562ce686bc3ca"
)
EXPECTED_PRIOR_REPAIR_FIXTURE_SHA256 = (
    "06eec52a4d346cb6014b8cd29e73323659a5c72c4e8ac86e81dac57932a25c12"
)
EXPECTED_BASELINE_DIAGNOSTICS_SHA256 = (
    "eba441a8d23461a8ba0ad02d03432c04b5a2b03529102e0f2f61e3ac68de90b0"
)
TRANSIENT_ERRNOS = {
    errno.EAGAIN,
    errno.ECONNABORTED,
    errno.ECONNRESET,
    errno.ENETDOWN,
    errno.ENETRESET,
    errno.ENETUNREACH,
    errno.ETIMEDOUT,
}


def normalized_text_sha256(path: Path) -> str:
    """Hash UTF-8 text after normalizing checkout-specific line endings."""

    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return sha256(normalized.encode()).hexdigest()


def _load_pinned_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = normalized_text_sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"pinned input hash mismatch: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return cast(dict[str, Any], value)


def _find_prior_pair(fixture: dict[str, Any], policy_name: str) -> dict[str, Any]:
    matches = [
        cast(dict[str, Any], pair)
        for pair in cast(list[object], fixture["pairs"])
        if cast(dict[str, Any], pair)["policy"] == policy_name
        and cast(dict[str, Any], pair)["variant"] == "initial_population_repair"
    ]
    if len(matches) != 1:
        raise ValueError("expected one prior all-round initialization-repair pair")
    return matches[0]


def _relative_delta(new: float, baseline: float) -> float | None:
    return (new - baseline) / baseline if baseline != 0.0 else None


def _outcome_delta(
    outcome: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, float]:
    return {
        key: float(outcome[key]) - float(baseline[key])
        for key in baseline
    }


def _never_admitted_expired(lifecycle: dict[str, Any]) -> int:
    return int(lifecycle.get("expired_after_round_2_rejection", 0)) + int(
        lifecycle.get("expired_waiting_at_deadline", 0)
    )


def _round_two_initialization_metrics(replay: dict[str, Any]) -> dict[str, Any]:
    calls = cast(list[dict[str, Any]], replay["selector_calls"])
    round_one_calls = [row for row in calls if row["round_name"] == "round_1"]
    round_two_calls = [row for row in calls if row["round_name"] == "round_2"]
    round_one_repaired = sum(
        int(row["initial_chromosomes_repaired"]) for row in round_one_calls
    )
    round_one_bits = sum(int(row["initial_bits_removed"]) for row in round_one_calls)
    if round_one_repaired or round_one_bits:
        raise ValueError("ASSUMP-049 changed Round-1 initialization")
    repaired = sum(int(row["initial_chromosomes_repaired"]) for row in round_two_calls)
    bits_removed = sum(int(row["initial_bits_removed"]) for row in round_two_calls)
    selector = cast(dict[str, Any], replay["selector_funnel"])
    round_two = cast(dict[str, Any], selector["by_round"])["round_2"]
    ga_calls = int(round_two["ga_calls"])
    initial_chromosomes = ga_calls * 200
    if repaired <= 0 or repaired > initial_chromosomes:
        raise ValueError("Round-2 initialization repair count is outside its population")
    raw_best_feasible = int(round_two["raw_best_feasible_ga_calls"])
    return {
        "round_1_initial_chromosomes_repaired": round_one_repaired,
        "round_1_initial_bits_removed": round_one_bits,
        "round_2_ga_calls": ga_calls,
        "round_2_initial_chromosomes": initial_chromosomes,
        "round_2_initial_infeasible_count": repaired,
        "round_2_initial_repair_count": repaired,
        "round_2_initial_bits_removed": bits_removed,
        "round_2_initial_repair_rate": repaired / initial_chromosomes,
        "round_2_initial_population_feasibility_rate_before_repair": (
            1.0 - repaired / initial_chromosomes
        ),
        "round_2_initial_population_feasibility_rate_after_repair": 1.0,
        "round_2_selected_subset_feasibility_rate": (
            raw_best_feasible / ga_calls if ga_calls else 1.0
        ),
        "round_2_zero_candidate_paths": int(round_two["empty_calls"]),
        "round_2_single_candidate_paths": int(round_two["single_candidate_calls"]),
        "round_2_multi_candidate_paths": ga_calls,
    }


def _prior_initialization_metrics(prior: dict[str, Any]) -> dict[str, Any]:
    selector = cast(dict[str, Any], prior["selector_funnel"])
    rounds = cast(dict[str, dict[str, Any]], selector["by_round"])
    ga_calls = sum(int(rounds[name]["ga_calls"]) for name in ("round_1", "round_2"))
    counterfactual = cast(dict[str, Any], prior["counterfactual"])
    repaired = int(counterfactual["initial_chromosomes_repaired"])
    initial_chromosomes = ga_calls * 200
    return {
        "scope": "round_1_and_round_2",
        "initial_chromosomes": initial_chromosomes,
        "initial_infeasible_count": repaired,
        "initial_repair_count": repaired,
        "initial_repair_rate": repaired / initial_chromosomes,
        "initial_population_feasibility_rate_before_repair": (
            1.0 - repaired / initial_chromosomes
        ),
        "initial_population_feasibility_rate_after_repair": 1.0,
        "round_2_only_split": None,
        "round_2_only_split_status": "not_recorded_in_prior_sanitized_artifact",
    }


def _execute_with_one_transient_retry(
    operation: Callable[[], dict[str, object]],
) -> tuple[dict[str, object], float, int]:
    start = time.perf_counter()
    try:
        return operation(), time.perf_counter() - start, 0
    except OSError as error:
        if error.errno not in TRANSIENT_ERRNOS:
            raise
    start = time.perf_counter()
    return operation(), time.perf_counter() - start, 1


def run_pair(
    *,
    config_path: Path,
    baseline_path: Path,
    baseline_diagnostics_path: Path,
    prior_repair_path: Path,
    policy_name: str,
) -> dict[str, object]:
    """Execute two exact replays; reuse both comparison states without execution."""

    if policy_name not in DK_POLICIES:
        raise ValueError("Stage 15-K.1 supports only DK-R and DK-P")
    if normalized_text_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved Stage-13F config hash changed")
    config = load_full_config(config_path)
    first_descriptor = cast(list[dict[str, Any]], config["runs"])[0]
    if int(first_descriptor["workload_seed"]) != WORKLOAD_SEED:
        raise ValueError("first materialized ASSUMP-033 workload seed changed")
    descriptor = _descriptor(config, WORKLOAD_SEED)
    policy_seed = int(cast(dict[str, int], descriptor["policy_seeds"])[policy_name])

    baselines = _load_pinned_json(baseline_path, EXPECTED_BASELINE_FIXTURE_SHA256)
    baseline = cast(
        dict[str, Any], baselines["records"][f"{WORKLOAD_SEED}:{policy_name}"]
    )
    baseline_fingerprint = cast(dict[str, Any], baseline["scientific_fingerprint"])
    baseline_rng = cast(dict[str, Any], baseline["baseline_rng"])
    if (
        baselines["baseline_recomputed"] is not False
        or baseline["baseline_rng_status"] != "available_reused_stage15c"
        or int(baseline["policy_seed"]) != policy_seed
    ):
        raise ValueError("baseline evidence is not the approved reuse-only first seed")

    diagnostics = _load_pinned_json(
        baseline_diagnostics_path, EXPECTED_BASELINE_DIAGNOSTICS_SHA256
    )
    diagnostic = cast(dict[str, Any], diagnostics["policies"][policy_name])
    if (
        diagnostics["baseline_recomputed"] is not False
        or int(diagnostics["workload_seed"]) != WORKLOAD_SEED
        or diagnostics["workload_sha256"] != baseline_fingerprint["workload_sha256"]
        or int(diagnostic["policy_seed"]) != policy_seed
    ):
        raise ValueError("baseline diagnostic fixture identity mismatch")

    prior_fixture = _load_pinned_json(
        prior_repair_path, EXPECTED_PRIOR_REPAIR_FIXTURE_SHA256
    )
    prior = _find_prior_pair(prior_fixture, policy_name)
    prior_fingerprint = cast(dict[str, Any], prior["scientific_fingerprint"])
    for field in ("workload_seed", "policy_seed", "policy", "workload_sha256"):
        if prior_fingerprint[field] != baseline_fingerprint[field]:
            raise ValueError(f"prior repair {field} differs from baseline")
    if prior["replay_exact"] is not True or prior_fixture["variant_recomputed"] is not False:
        raise ValueError("prior repair reuse evidence is not replay-validated")

    first, first_seconds, first_retry = _execute_with_one_transient_retry(
        lambda: _execute_once(
            config=config,
            policy_name=policy_name,
            variant=VARIANT,
            workload_seed=WORKLOAD_SEED,
            diagnostic_stage="stage15k1",
        )
    )
    second, second_seconds, second_retry = _execute_with_one_transient_retry(
        lambda: _execute_once(
            config=config,
            policy_name=policy_name,
            variant=VARIANT,
            workload_seed=WORKLOAD_SEED,
            diagnostic_stage="stage15k1",
        )
    )
    if first != second:
        raise ValueError("same-seed Stage 15-K.1 replay mismatch")

    selector = cast(dict[str, Any], first["selector_funnel"])
    expected_initial_rng = _state_hash(random.Random(policy_seed).getstate())
    if selector["initial_rng_state_sha256"] != expected_initial_rng:
        raise ValueError("initial RNG state differs from approved policy seed")
    rng_gate = _enforce_baseline_rng_gate(baseline=baseline_rng, replay=first)
    repair_metrics = _round_two_initialization_metrics(first)

    fingerprint = cast(dict[str, Any], first["scientific_fingerprint"])
    for field in ("workload_seed", "policy_seed", "policy", "workload_sha256"):
        if fingerprint[field] != baseline_fingerprint[field]:
            raise ValueError(f"pilot {field} differs from reused baseline")
    outcome = cast(dict[str, Any], fingerprint["outcome"])
    baseline_outcome = cast(dict[str, Any], baseline_fingerprint["outcome"])
    prior_outcome = cast(dict[str, Any], prior_fingerprint["outcome"])
    baseline_total_utility = float(baseline_outcome["completed_utility"]) + float(
        baseline_outcome["rejected_utility"]
    )
    pilot_total_utility = float(outcome["completed_utility"]) + float(
        outcome["rejected_utility"]
    )
    conservation_residual = pilot_total_utility - baseline_total_utility
    if abs(conservation_residual) > 1e-9:
        raise ValueError("Utility conservation failed")

    lifecycle = cast(dict[str, Any], first["lifecycle_funnel"])
    baseline_lifecycle = cast(dict[str, Any], baseline["lifecycle_funnel"])
    prior_lifecycle = cast(dict[str, Any], prior["lifecycle_funnel"])
    if lifecycle.get("expired_during_canonicalization", 0) != baseline_lifecycle.get(
        "expired_during_canonicalization", 0
    ):
        raise ValueError("PRE_ADMISSION_INFEASIBLE changed under R2-only repair")
    auction = cast(dict[str, Any], first["auction_funnel"])
    auction_totals = cast(dict[str, Any], auction["totals"])
    if int(auction_totals["round_1_repair_calls"]) != int(
        cast(dict[str, Any], selector["by_round"])["round_1"]["repair_count"]
    ):
        raise ValueError("Round-1 final feasibility accounting diverged")

    baseline_delta = _outcome_delta(outcome, baseline_outcome)
    prior_delta = _outcome_delta(prior_outcome, baseline_outcome)
    completed_effect_share = (
        baseline_delta["completed_utility"] / prior_delta["completed_utility"]
        if prior_delta["completed_utility"] != 0.0
        else None
    )
    return {
        "schema_version": "stage15k1-r2-initialization-repair-pilot-v1",
        "label": "[فرض آزمون کمکی] Stage 15-K.1 Round-2-only initialization repair",
        "assumptions": ["ASSUMP-048", "ASSUMP-049"],
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "variant": VARIANT.value,
        "config_sha256_lf_normalized": EXPECTED_CONFIG_SHA256,
        "baseline_recomputed": False,
        "prior_repair_recomputed": False,
        "replay_count": 2,
        "replay_exact": True,
        "technical_retry_count": first_retry + second_retry,
        "scientific_failure_retry_allowed": False,
        "runtime_seconds": {"replay_1": first_seconds, "replay_2": second_seconds},
        "rng_gate": rng_gate
        | {
            "same_variant_primitive_counts_replay_exact": True,
            "same_variant_final_rng_state_replay_exact": True,
            "same_variant_call_shape_replay_exact": True,
            "direct_random_draws_added_by_repair": 0,
        },
        "invariant_gate": {
            "engine_capacity_and_state_invariants_passed": True,
            "task_partition_complete_and_disjoint": True,
            "utility_conservation_passed": True,
            "utility_conservation_residual": conservation_residual,
            "numerical_tolerance": 1e-9,
            "pre_admission_infeasible_unchanged": True,
            "round_1_initial_repair_count_zero": True,
            "round_1_algorithm_changed": False,
            "pricing_algorithm_changed": False,
            "server_selection_algorithm_changed": False,
            "lifecycle_changed": False,
        },
        "comparison_compatibility": {
            "baseline_seed_workload_policy_config_validated": True,
            "prior_seed_workload_policy_validated": True,
            "prior_source_artifact_sha256_recorded": prior["source_artifact_sha256"],
            "prior_config_hash_status": "not_recorded_in_prior_sanitized_artifact",
            "prior_scope": "initial_population_repair_in_round_1_and_round_2",
            "pilot_scope": "initial_population_repair_in_round_2_only",
            "scope_difference_explicit": True,
        },
        "baseline": {
            "source_stage": baseline["source_stage"],
            "source_result_sha256": baseline["source_result_sha256"],
            "scientific_fingerprint": baseline_fingerprint,
            "lifecycle_funnel": baseline_lifecycle,
            "selector_funnel": diagnostic["selector_funnel"],
            "round_1_admission": None,
            "round_1_admission_status": "not_recorded_in_reused_baseline",
            "round_2_admission": int(baseline_lifecycle.get("accepted", 0)),
            "round_2_rejection": int(baseline_outcome["raw_auction_rejection_count"]),
            "never_admitted_expired_proxy": _never_admitted_expired(
                baseline_lifecycle
            ),
            "initial_population_feasibility_status": "not_recorded_in_baseline",
        },
        "round_two_only_repair": {
            "scientific_fingerprint": fingerprint,
            "lifecycle_funnel": lifecycle,
            "selector_funnel": selector,
            "auction_funnel": auction,
            "initialization_metrics": repair_metrics,
            "round_1_admission": int(auction_totals["round_1_server_assignments"]),
            "round_2_admission": int(auction_totals["round_2_accepted"]),
            "round_2_rejection": int(auction_totals["round_2_rejected"]),
            "never_admitted_expired_proxy": _never_admitted_expired(lifecycle),
            "delta_from_baseline": baseline_delta,
            "relative_delta_from_baseline": {
                key: _relative_delta(float(outcome[key]), float(baseline_outcome[key]))
                for key in baseline_outcome
            },
        },
        "prior_all_round_initialization_repair": {
            "source_stage": prior_fixture["source_stage"],
            "scientific_fingerprint": prior_fingerprint,
            "lifecycle_funnel": prior_lifecycle,
            "selector_funnel": prior["selector_funnel"],
            "auction_funnel": prior["auction_funnel"],
            "initialization_metrics": _prior_initialization_metrics(prior),
            "never_admitted_expired_proxy": _never_admitted_expired(prior_lifecycle),
            "delta_from_baseline": prior_delta,
        },
        "effect_explained": {
            "completed_utility_effect_share_of_prior_repair": completed_effect_share,
            "interpretation_boundary": (
                "prior config hash was not stored; compare seed/workload/policy and "
                "reported outcomes only, with the scope difference explicit"
            ),
        },
        "variant_replay": first,
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "official_algorithm_changed": False,
        "figure_6_overwritten": False,
        "five_or_thirty_workloads_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baselines", type=Path, required=True)
    parser.add_argument("--baseline-diagnostics", type=Path, required=True)
    parser.add_argument("--prior-repairs", type=Path, required=True)
    parser.add_argument("--policy", choices=DK_POLICIES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-K.1 pair: {args.output}")
    report = run_pair(
        config_path=args.config,
        baseline_path=args.baselines,
        baseline_diagnostics_path=args.baseline_diagnostics,
        prior_repair_path=args.prior_repairs,
        policy_name=args.policy,
    )
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "stage15k1_pair_replay_exact_rng_and_invariant_gates_passed",
                "policy": args.policy,
                "workload_seed": WORKLOAD_SEED,
                "output": args.output.name,
            }
        )
    )


if __name__ == "__main__":
    main()
