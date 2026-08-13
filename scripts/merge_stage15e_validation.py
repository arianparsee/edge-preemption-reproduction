"""Validate and aggregate the approved five-seed Stage-15E artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, cast

SEEDS = (
    541501192080118187,
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)
POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANTS = ("initial_population_repair", "offspring_repair")
T_CRITICAL_95_DF4 = 2.7764451051977987
METRICS = (
    "completed_jobs",
    "completed_utility",
    "rejected_jobs",
    "rejected_utility",
    "ever_preempted_jobs",
    "ever_preempted_utility",
    "raw_auction_rejection_count",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _normalize_seed_one(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        payload.get("schema_version") != "stage15e-seed-one-reuse-v1"
        or payload.get("baseline_recomputed") is not False
        or payload.get("variant_recomputed") is not False
        or payload.get("pair_count") != 4
    ):
        raise ValueError("invalid Stage 15-E seed-one reuse fixture")
    result: list[dict[str, Any]] = []
    for pair in payload["pairs"]:
        result.append(
            {
                "workload_seed": pair["workload_seed"],
                "policy_seed": pair["policy_seed"],
                "policy": pair["policy"],
                "variant": pair["variant"],
                "baseline_recomputed": False,
                "replay_exact": pair["replay_exact"],
                "rng_gate": pair["rng_gate"],
                "baseline_scientific_fingerprint": None,
                "baseline_lifecycle_funnel": None,
                "variant_replay": {
                    "scientific_fingerprint": pair["scientific_fingerprint"],
                    "selector_funnel": pair["selector_funnel"],
                    "auction_funnel": pair["auction_funnel"],
                    "lifecycle_funnel": pair["lifecycle_funnel"],
                    "counterfactual": pair["counterfactual"],
                },
                "outcome_delta_from_baseline": pair["outcome_delta_from_baseline"],
                "source": "reused_stage15d1",
            }
        )
    return result


def _summary_row(pair: dict[str, Any]) -> dict[str, object]:
    replay = cast(dict[str, Any], pair["variant_replay"])
    fingerprint = cast(dict[str, Any], replay["scientific_fingerprint"])
    outcome = cast(dict[str, int | float], fingerprint["outcome"])
    delta = cast(dict[str, int | float], pair["outcome_delta_from_baseline"])
    lifecycle = cast(dict[str, int], replay["lifecycle_funnel"])
    selector = cast(dict[str, Any], replay["selector_funnel"])
    counterfactual = cast(dict[str, Any], replay["counterfactual"])
    repair_count = int(counterfactual["initial_chromosomes_repaired"]) + int(
        counterfactual["offspring_repaired"]
    )
    round_data = cast(dict[str, dict[str, int | float]], selector["by_round"])
    ga_calls = int(round_data["round_1"]["ga_calls"]) + int(
        round_data["round_2"]["ga_calls"]
    )
    return {
        "workload_seed": pair["workload_seed"],
        "policy": pair["policy"],
        "variant": pair["variant"],
        "source": pair.get("source", "new_stage15e"),
        **{metric: outcome[metric] for metric in METRICS},
        **{f"delta_{metric}": delta[metric] for metric in METRICS},
        "repair_count": repair_count,
        "repair_per_ga_call": repair_count / ga_calls if ga_calls else 0.0,
        "accepted_events": lifecycle.get("accepted", 0),
        "retry_scheduled": lifecycle.get("retry_scheduled", 0),
        "expired_events": lifecycle.get("expired", 0),
        "canonical_expirations": lifecycle.get("expired_during_canonicalization", 0),
        "post_rejection_expirations": lifecycle.get(
            "expired_after_round_2_rejection", 0
        ),
        "completed_events": lifecycle.get("completed", 0),
        "rejected_events": lifecycle.get("rejected", 0),
        "replay_exact": pair["replay_exact"],
        "baseline_rng_comparison": (
            "available_seed_one"
            if int(pair["workload_seed"]) == SEEDS[0]
            else "unknown_not_recorded"
        ),
    }


def merge(new_paths: list[Path], seed_one_path: Path) -> dict[str, object]:
    if len(new_paths) != 16:
        raise ValueError("Stage 15-E requires exactly 16 new pair artifacts")
    pairs = _normalize_seed_one(_load(seed_one_path))
    for path in new_paths:
        pair = _load(path)
        gate = cast(dict[str, object], pair.get("rng_gate"))
        if (
            pair.get("schema_version") != "stage15e-counterfactual-pair-v1"
            or pair.get("baseline_recomputed") is not False
            or pair.get("replay_exact") is not True
            or gate.get("option") != "A"
            or gate.get("passed_within_variant") is not True
            or gate.get("baseline_rng_gate_claimed") is not False
            or gate.get("baseline_final_rng_comparison")
            != "unknown_not_recorded_in_stage13_baseline"
        ):
            raise ValueError("invalid Stage 15-E Option-A pair")
        for flag in (
            "task_identifiers_in_artifact",
            "chromosome_bits_in_artifact",
            "raw_workload_in_artifact",
            "raw_trace_in_artifact",
            "official_algorithm_changed",
            "figure_6_overwritten",
            "thirty_workloads_executed",
        ):
            if pair.get(flag) is not False:
                raise ValueError(f"Stage 15-E boundary failed: {flag}")
        pair["source"] = "new_stage15e"
        pairs.append(pair)
    keys = {
        (int(pair["workload_seed"]), str(pair["policy"]), str(pair["variant"]))
        for pair in pairs
    }
    expected = {
        (seed, policy, variant)
        for seed in SEEDS
        for policy in POLICIES
        for variant in VARIANTS
    }
    if keys != expected or len(pairs) != 20:
        raise ValueError("Stage 15-E five-seed matrix is incomplete or duplicated")
    rows = sorted(
        (_summary_row(pair) for pair in pairs),
        key=lambda row: (
            int(cast(int, row["workload_seed"])),
            str(row["policy"]),
            str(row["variant"]),
        ),
    )
    grouped: defaultdict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["policy"]), str(row["variant"]))].append(row)
    aggregate: list[dict[str, object]] = []
    for (policy, variant), items in sorted(grouped.items()):
        record: dict[str, object] = {"policy": policy, "variant": variant, "n": 5}
        for metric in (
            "delta_completed_jobs",
            "delta_completed_utility",
            "delta_raw_auction_rejection_count",
            "repair_per_ga_call",
            "accepted_events",
            "retry_scheduled",
            "expired_events",
            "canonical_expirations",
            "post_rejection_expirations",
            "completed_events",
        ):
            values = [float(cast(int | float, item[metric])) for item in items]
            mean = fmean(values)
            sd = stdev(values)
            margin = T_CRITICAL_95_DF4 * sd / math.sqrt(5)
            record[f"{metric}_mean"] = mean
            record[f"{metric}_sd"] = sd
            record[f"{metric}_ci95_low"] = mean - margin
            record[f"{metric}_ci95_high"] = mean + margin
        utility_deltas = [
            float(cast(int | float, item["delta_completed_utility"])) for item in items
        ]
        record["positive_utility_effect_seeds"] = sum(value > 0.0 for value in utility_deltas)
        record["nonnegative_utility_effect_seeds"] = sum(value >= 0.0 for value in utility_deltas)
        record["direction_stable_all_five"] = all(value > 0.0 for value in utility_deltas)
        aggregate.append(record)
    return {
        "schema_version": "stage15e-five-seed-summary-v1",
        "label": "[آزمون کمکی] limited five-seed paired counterfactual validation",
        "seed_count": 5,
        "new_pair_count": 16,
        "reused_pair_count": 4,
        "baseline_recomputed": False,
        "fixed_penalty_executed": False,
        "thirty_workloads_executed": False,
        "baseline_rng_option": "A_partial_observability",
        "all_replays_exact": True,
        "rows": rows,
        "aggregate": aggregate,
    }


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--seed-one", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-seed-csv", type=Path, required=True)
    parser.add_argument("--aggregate-csv", type=Path, required=True)
    args = parser.parse_args()
    report = merge(args.input, args.seed_one)
    for path in (args.output, args.per_seed_csv, args.aggregate_csv):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite: {path}")
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_csv(cast(list[dict[str, object]], report["rows"]), args.per_seed_csv)
    _write_csv(cast(list[dict[str, object]], report["aggregate"]), args.aggregate_csv)
    print(json.dumps({"status": "merged", "pairs": 20, "new_pairs": 16}))


if __name__ == "__main__":
    main()
