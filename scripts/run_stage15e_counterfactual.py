"""Run one new Stage-15E pair twice under the approved Option-A RNG boundary."""

from __future__ import annotations

import argparse
import errno
import json
import random
from pathlib import Path
from typing import cast

from run_stage15d_counterfactual import _execute_once

from edge_reproduction.diagnostics.ga_counterfactual import CounterfactualVariant
from edge_reproduction.diagnostics.ga_instrumentation import _state_hash
from edge_reproduction.experiments.pipe_normal_full import _descriptor, load_full_config

NEW_SEEDS = (
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)
POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANTS = (
    CounterfactualVariant.INITIAL_POPULATION_REPAIR,
    CounterfactualVariant.OFFSPRING_REPAIR,
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


def _execute_with_one_transient_retry(operation: object) -> tuple[dict[str, object], int]:
    """Retry only a narrowly classified transient OS failure, at most once."""

    if not callable(operation):
        raise TypeError("operation must be callable")
    try:
        return cast(dict[str, object], operation()), 0
    except OSError as error:
        if error.errno not in TRANSIENT_ERRNOS:
            raise
    return cast(dict[str, object], operation()), 1


def run_pair(
    *,
    config_path: Path,
    baseline_path: Path,
    workload_seed: int,
    policy_name: str,
    variant: CounterfactualVariant,
) -> dict[str, object]:
    """Execute two exact variant replays; never execute a baseline."""

    if workload_seed not in NEW_SEEDS or policy_name not in POLICIES or variant not in VARIANTS:
        raise ValueError("Stage 15-E pair is outside the approved 16-pair matrix")
    config = load_full_config(config_path)
    descriptor = _descriptor(config, workload_seed)
    policy_seeds = cast(dict[str, int], descriptor["policy_seeds"])
    policy_seed = int(policy_seeds[policy_name])
    baselines = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baselines.get("baseline_recomputed") is not False:
        raise ValueError("Stage 15-E baseline fixture must be reuse-only")
    baseline = baselines["records"].get(f"{workload_seed}:{policy_name}")
    if baseline is None:
        raise ValueError("selected baseline evidence is missing")
    if (
        baseline["policy_seed"] != policy_seed
        or baseline["baseline_rng_status"] != "unavailable_not_recorded"
        or baseline["baseline_rng"] is not None
    ):
        raise ValueError("Option-A baseline evidence boundary changed")

    first = _execute_once(
        config=config,
        policy_name=policy_name,
        variant=variant,
        workload_seed=workload_seed,
        diagnostic_stage="stage15e",
    )
    second = _execute_once(
        config=config,
        policy_name=policy_name,
        variant=variant,
        workload_seed=workload_seed,
        diagnostic_stage="stage15e",
    )
    if first != second:
        raise ValueError("same-seed Stage 15-E variant replay mismatch")
    selector = cast(dict[str, object], first["selector_funnel"])
    expected_initial = _state_hash(random.Random(policy_seed).getstate())
    if selector["initial_rng_state_sha256"] != expected_initial:
        raise ValueError("variant initial RNG state differs from materialized policy seed")
    fingerprint = cast(dict[str, object], first["scientific_fingerprint"])
    baseline_fingerprint = cast(dict[str, object], baseline["scientific_fingerprint"])
    if (
        fingerprint["workload_seed"] != baseline_fingerprint["workload_seed"]
        or fingerprint["policy_seed"] != baseline_fingerprint["policy_seed"]
        or fingerprint["policy"] != baseline_fingerprint["policy"]
        or fingerprint["workload_sha256"] != baseline_fingerprint["workload_sha256"]
    ):
        raise ValueError("variant workload/policy identity differs from reused baseline")
    outcome = cast(dict[str, int | float], fingerprint["outcome"])
    baseline_outcome = cast(dict[str, int | float], baseline_fingerprint["outcome"])
    delta = {key: float(outcome[key]) - float(baseline_outcome[key]) for key in baseline_outcome}
    return {
        "schema_version": "stage15e-counterfactual-pair-v1",
        "label": "[آزمون کمکی] Stage 15-E limited five-seed validation",
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "variant": variant.value,
        "baseline_source": baseline["source_stage"],
        "baseline_source_result_sha256": baseline["source_result_sha256"],
        "baseline_recomputed": False,
        "replay_count": 2,
        "replay_exact": True,
        "rng_gate": {
            "option": "A",
            "passed_within_variant": True,
            "initial_rng_state_matches_policy_seed": True,
            "same_variant_final_rng_state_replay_exact": True,
            "same_variant_primitive_counts_replay_exact": True,
            "same_variant_call_shape_replay_exact": True,
            "baseline_final_rng_comparison": "unknown_not_recorded_in_stage13_baseline",
            "baseline_call_shape_comparison": "unknown_not_recorded_in_stage13_baseline",
            "baseline_rng_gate_claimed": False,
        },
        "baseline_scientific_fingerprint": baseline_fingerprint,
        "baseline_lifecycle_funnel": baseline["lifecycle_funnel"],
        "variant_replay": first,
        "outcome_delta_from_baseline": delta,
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
    parser.add_argument("--workload-seed", type=int, choices=NEW_SEEDS, required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument(
        "--variant", choices=tuple(item.value for item in VARIANTS), required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-E pair: {args.output}")
    report, technical_retry_count = _execute_with_one_transient_retry(
        lambda: run_pair(
            config_path=args.config,
            baseline_path=args.baselines,
            workload_seed=args.workload_seed,
            policy_name=args.policy,
            variant=CounterfactualVariant(args.variant),
        )
    )
    report["technical_retry_count"] = technical_retry_count
    report["scientific_failure_retry_allowed"] = False
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "stage15e_pair_exact_option_a",
                "workload_seed": args.workload_seed,
                "policy": args.policy,
                "variant": args.variant,
            }
        )
    )


if __name__ == "__main__":
    main()
