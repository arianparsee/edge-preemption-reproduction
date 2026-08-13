"""Validate and merge six sanitized Stage-15D counterfactual pair artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, cast

POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANTS = (
    "fixed_penalty",
    "initial_population_repair",
    "offspring_repair",
)


def _pair_summary(payload: dict[str, object]) -> dict[str, object]:
    replay = cast(dict[str, object], payload["variant_replay"])
    fingerprint = cast(dict[str, object], replay["scientific_fingerprint"])
    outcome = cast(dict[str, object], fingerprint["outcome"])
    selector = cast(dict[str, object], replay["selector_funnel"])
    rounds = cast(dict[str, dict[str, int | float]], selector["by_round"])
    counterfactual = cast(dict[str, object], replay["counterfactual"])
    primitive_calls = cast(dict[str, int], counterfactual["rng_primitive_calls"])
    delta = cast(dict[str, int | float], payload["outcome_delta_from_baseline"])
    gate = cast(dict[str, object], payload["rng_gate"])
    auction = cast(dict[str, object], replay["auction_funnel"])
    totals = cast(dict[str, int], auction["totals"])
    return {
        "policy": payload["policy"],
        "variant": payload["variant"],
        "completed_jobs": outcome["completed_jobs"],
        "completed_utility": outcome["completed_utility"],
        "rejected_jobs": outcome["rejected_jobs"],
        "rejected_utility": outcome["rejected_utility"],
        "ever_preempted_jobs": outcome["ever_preempted_jobs"],
        "ever_preempted_utility": outcome["ever_preempted_utility"],
        "raw_auction_rejection_count": outcome["raw_auction_rejection_count"],
        "delta_completed_jobs": delta["completed_jobs"],
        "delta_completed_utility": delta["completed_utility"],
        "delta_rejected_jobs": delta["rejected_jobs"],
        "delta_rejected_utility": delta["rejected_utility"],
        "delta_ever_preempted_jobs": delta["ever_preempted_jobs"],
        "delta_ever_preempted_utility": delta["ever_preempted_utility"],
        "delta_raw_auction_rejection_count": delta[
            "raw_auction_rejection_count"
        ],
        "round_1_ga_calls": rounds["round_1"]["ga_calls"],
        "round_2_ga_calls": rounds["round_2"]["ga_calls"],
        "round_1_candidate_entries": rounds["round_1"]["candidate_entries"],
        "round_2_candidate_entries": rounds["round_2"]["candidate_entries"],
        "round_1_final_guard_repairs": rounds["round_1"]["repair_count"],
        "round_2_final_guard_repairs": rounds["round_2"]["repair_count"],
        "round_2_accepted": totals["round_2_accepted"],
        "round_2_rejected": totals["round_2_rejected"],
        "initial_chromosomes_repaired": counterfactual["initial_chromosomes_repaired"],
        "initial_bits_removed": counterfactual["initial_bits_removed"],
        "offspring_repaired": counterfactual["offspring_repaired"],
        "offspring_bits_removed": counterfactual["offspring_bits_removed"],
        "rng_choice_calls": primitive_calls["choice"],
        "rng_getrandbits_calls": primitive_calls["getrandbits"],
        "rng_randint_calls": primitive_calls["randint"],
        "rng_random_calls": primitive_calls["random"],
        "rng_randrange_calls": primitive_calls["randrange"],
        "rng_sample_calls": primitive_calls["sample"],
        "final_rng_state_equal_to_baseline": gate["final_rng_state_equal"],
        "recorded_call_shape_equal_to_baseline": gate["recorded_call_shape_equal"],
        "allowed_rng_difference_reasons": ";".join(
            cast(list[str], gate["allowed_difference_reasons"])
        ),
        "selector_call_shape_sha256": replay["selector_call_shape_sha256"],
        "selector_rng_trace_sha256": replay["selector_rng_trace_sha256"],
        "replay_exact": payload["replay_exact"],
    }


def merge(paths: list[Path]) -> dict[str, object]:
    """Fail closed unless all six independent pair artifacts are valid."""

    if len(paths) != 6:
        raise ValueError("Stage 15-D merge requires exactly six pair artifacts")
    pairs: dict[tuple[str, str], dict[str, object]] = {}
    for path in paths:
        payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
        if payload.get("schema_version") != "stage15d-counterfactual-pair-v1":
            raise ValueError("unexpected Stage 15-D pair schema")
        gate = cast(dict[str, object], payload["rng_gate"])
        if (
            payload["baseline_recomputed"]
            or not payload["replay_exact"]
            or not gate["passed"]
            or payload["workload_seed"] != 541501192080118187
        ):
            raise ValueError("Stage 15-D replay/baseline/RNG invariant failed")
        if any(
            cast(bool, payload[field])
            for field in (
                "task_identifiers_in_artifact",
                "chromosome_bits_in_artifact",
                "raw_workload_in_artifact",
                "raw_trace_in_artifact",
                "figure_6_overwritten",
                "thirty_workloads_executed",
            )
        ):
            raise ValueError("Stage 15-D public-boundary invariant failed")
        key = (str(payload["policy"]), str(payload["variant"]))
        if key in pairs:
            raise ValueError("duplicate Stage 15-D pair")
        pairs[key] = _pair_summary(payload)
    expected = {(policy, variant) for policy in POLICIES for variant in VARIANTS}
    if set(pairs) != expected:
        raise ValueError("Stage 15-D policy/variant matrix is incomplete")
    return {
        "schema_version": "stage15d-counterfactual-summary-v1",
        "label": "[آزمون کمکی] Stage 15-D six single-factor pairs",
        "baseline_source_stage": "Stage 15-C",
        "baseline_source_run": 31708325126,
        "baseline_recomputed": False,
        "workload_seed": 541501192080118187,
        "pair_count": 6,
        "all_replays_exact": True,
        "all_rng_gates_passed": True,
        "raw_trace_in_artifact": False,
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "figure_6_overwritten": False,
        "thirty_workloads_executed": False,
        "pairs": [pairs[key] for key in sorted(pairs)],
    }


def write_csv(report: dict[str, object], path: Path) -> None:
    pairs = cast(list[dict[str, Any]], report["pairs"])
    if not pairs:
        raise ValueError("cannot write an empty Stage 15-D CSV")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.csv.exists():
        raise FileExistsError("refusing to overwrite Stage 15-D merged output")
    report = merge(cast(list[Path], args.input))
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_csv(report, args.csv)
    print(json.dumps({"status": "merged", "pairs": 6, "rng_gates": "passed"}))


if __name__ == "__main__":
    main()
