"""Run one approved Stage-15H DK repair pair twice without a baseline replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any, cast

from materialize_stage15e_reuse_fixtures import _lifecycle
from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _execute_once
from run_stage15e_counterfactual import _execute_with_one_transient_retry

from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    _state_hash,
)
from edge_reproduction.experiments.pipe_normal_full import (
    _descriptor,
    load_full_config,
)

POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANTS = (
    CounterfactualVariant.INITIAL_POPULATION_REPAIR,
    CounterfactualVariant.OFFSPRING_REPAIR,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path.name}")
    return value


def _baseline_record(
    *, config: dict[str, object], result_path: Path, workload_seed: int, policy: str
) -> dict[str, object]:
    """Validate one reused Stage-13 result and expose only sanitized evidence."""

    pair_dir = result_path.parent
    manifest_path = pair_dir / "manifest.json"
    workload_path = pair_dir / "workload.json"
    if not manifest_path.is_file() or not workload_path.is_file():
        raise ValueError("reused baseline checkpoint is incomplete")
    manifest = _object(manifest_path)
    if manifest.get("result_sha256") != _sha256(result_path) or manifest.get(
        "workload_sha256"
    ) != _sha256(workload_path):
        raise ValueError("reused baseline checkpoint checksum mismatch")
    payload = _object(result_path)
    descriptor = _descriptor(config, workload_seed)
    expected_policy_seed = int(cast(dict[str, int], descriptor["policy_seeds"])[policy])
    if (
        int(payload.get("workload_seed", -1)) != workload_seed
        or payload.get("policy") != policy
        or int(payload.get("policy_seed", -1)) != expected_policy_seed
    ):
        raise ValueError("reused baseline seed/policy identity mismatch")
    fingerprint = scientific_fingerprint(cast(dict[str, object], payload))
    run = cast(dict[str, object], payload["run"])
    events = cast(list[dict[str, object]], run["events"])
    return {
        "workload_seed": workload_seed,
        "policy_seed": expected_policy_seed,
        "policy": policy,
        "source_stage": "Stage 13-J/13-K",
        "source_run_id": 31644121025,
        "source_result_sha256": _sha256(result_path),
        "source_workload_sha256": _sha256(workload_path),
        "scientific_fingerprint": fingerprint,
        "lifecycle_funnel": _lifecycle(events),
        "baseline_rng_status": "unavailable_not_recorded",
    }


def run_pair(
    *,
    config_path: Path,
    baseline_result: Path,
    workload_seed: int,
    policy_name: str,
    variant: CounterfactualVariant,
) -> dict[str, object]:
    """Execute two exact repair replays for one of the remaining 25 workloads."""

    config = load_full_config(config_path)
    runs = cast(list[dict[str, object]], config["runs"])
    all_seeds = tuple(int(str(run["workload_seed"])) for run in runs)
    if len(all_seeds) != 30 or workload_seed not in all_seeds[5:]:
        raise ValueError("Stage 15-H permits only materialized workloads 6 through 30")
    if policy_name not in POLICIES or variant not in VARIANTS:
        raise ValueError("Stage 15-H pair is outside the approved matrix")
    baseline = _baseline_record(
        config=config,
        result_path=baseline_result,
        workload_seed=workload_seed,
        policy=policy_name,
    )
    policy_seed = int(str(baseline["policy_seed"]))

    started = time.perf_counter()
    first = _execute_once(
        config=config,
        policy_name=policy_name,
        variant=variant,
        workload_seed=workload_seed,
        diagnostic_stage="stage15h",
    )
    first_seconds = time.perf_counter() - started
    started = time.perf_counter()
    second = _execute_once(
        config=config,
        policy_name=policy_name,
        variant=variant,
        workload_seed=workload_seed,
        diagnostic_stage="stage15h",
    )
    second_seconds = time.perf_counter() - started
    if first != second:
        raise ValueError("scientific failure: same-seed Stage 15-H replay mismatch")
    selector = cast(dict[str, object], first["selector_funnel"])
    if selector["initial_rng_state_sha256"] != _state_hash(random.Random(policy_seed).getstate()):
        raise ValueError("scientific failure: initial RNG state differs from policy seed")
    fingerprint = cast(dict[str, object], first["scientific_fingerprint"])
    baseline_fingerprint = cast(dict[str, object], baseline["scientific_fingerprint"])
    for field in ("workload_seed", "policy_seed", "policy", "workload_sha256"):
        if fingerprint[field] != baseline_fingerprint[field]:
            raise ValueError(f"scientific failure: variant/baseline {field} mismatch")
    outcome = cast(dict[str, int | float], fingerprint["outcome"])
    baseline_outcome = cast(dict[str, int | float], baseline_fingerprint["outcome"])
    delta = {key: float(outcome[key]) - float(baseline_outcome[key]) for key in baseline_outcome}
    return {
        "schema_version": "stage15h-counterfactual-pair-v1",
        "label": "[آزمون کمکی] Stage 15-H thirty-workload DK repair validation",
        "workload_seed": workload_seed,
        "policy_seed": policy_seed,
        "policy": policy_name,
        "variant": variant.value,
        "baseline_source": baseline["source_stage"],
        "baseline_source_run_id": baseline["source_run_id"],
        "baseline_source_result_sha256": baseline["source_result_sha256"],
        "baseline_source_workload_sha256": baseline["source_workload_sha256"],
        "baseline_recomputed": False,
        "replay_count": 2,
        "replay_exact": True,
        "rng_gate": {
            "option": "A_partial_observability",
            "passed_within_variant": True,
            "initial_rng_state_matches_policy_seed": True,
            "same_variant_final_rng_state_replay_exact": True,
            "same_variant_primitive_counts_replay_exact": True,
            "same_variant_call_shape_replay_exact": True,
            "baseline_rng_comparison": "unknown_not_recorded_in_stage13_baseline",
            "baseline_rng_gate_claimed": False,
        },
        "baseline_scientific_fingerprint": baseline_fingerprint,
        "baseline_lifecycle_funnel": baseline["lifecycle_funnel"],
        "variant_replay": first,
        "outcome_delta_from_baseline": delta,
        "runtime_seconds": {"replay_1": first_seconds, "replay_2": second_seconds},
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "official_algorithm_changed": False,
        "figure_6_overwritten": False,
        "thirty_workload_repair_scope": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline-result", type=Path, required=True)
    parser.add_argument("--workload-seed", type=int, required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument("--variant", choices=tuple(item.value for item in VARIANTS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-H pair: {args.output}")
    report, technical_retry_count = _execute_with_one_transient_retry(
        lambda: run_pair(
            config_path=args.config,
            baseline_result=args.baseline_result,
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
                "status": "stage15h_pair_exact_option_a",
                "seed": args.workload_seed,
                "policy": args.policy,
                "variant": args.variant,
            }
        )
    )


if __name__ == "__main__":
    main()
