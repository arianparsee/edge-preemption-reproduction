"""Validate and summarize the complete five-seed Stage-15K.2 pilot."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from hashlib import sha256
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
POLICIES = ("pipeline_double_knapsack_retention", "pipeline_double_knapsack_preemption")
METRICS = (
    "completed_jobs",
    "completed_utility",
    "rejected_jobs",
    "rejected_utility",
    "ever_preempted_jobs",
    "ever_preempted_utility",
    "raw_auction_rejection_count",
)
SEED_ONE_SOURCE_SHA256 = {
    "pipeline_double_knapsack_retention": (
        "61b28c8bf663f5cb212d814a42f2f200e2091a96ceca143d39da05414e4d3c4b"
    ),
    "pipeline_double_knapsack_preemption": (
        "7cca5a5decabfa9fcb03a3bab768ad6dcbe5fccc38404ad14714deb4e8512505"
    ),
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _num(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("expected a numeric result field")
    return float(value)


def _row(payload: dict[str, Any], *, source_sha256: str) -> dict[str, object]:
    schema = payload.get("schema_version")
    if schema not in {
        "stage15k1-r2-initialization-repair-pilot-v1",
        "stage15k2-r2-initialization-repair-pair-v1",
    }:
        raise ValueError("unexpected K.1/K.2 pair schema")
    if payload.get("replay_exact") is not True or payload.get("baseline_recomputed") is not False:
        raise ValueError("reuse/replay gate failed")
    seed = int(payload["workload_seed"])
    policy = str(payload["policy"])
    if schema.startswith("stage15k1") and source_sha256 != SEED_ONE_SOURCE_SHA256[policy]:
        raise ValueError("reused Stage 15-K.1 source checksum mismatch")
    repair = cast(dict[str, Any], payload["round_two_only_repair"])
    baseline = cast(dict[str, Any], payload["baseline"])
    repair_outcome = cast(dict[str, Any], repair["scientific_fingerprint"])["outcome"]
    baseline_outcome = cast(dict[str, Any], baseline["scientific_fingerprint"])["outcome"]
    lifecycle = cast(dict[str, Any], repair["lifecycle_funnel"])
    baseline_lifecycle = cast(dict[str, Any], baseline["lifecycle_funnel"])
    initialization = cast(dict[str, Any], repair["initialization_metrics"])
    prior = cast(dict[str, Any], payload["prior_all_round_initialization_repair"])
    prior_outcome = cast(dict[str, Any], prior["scientific_fingerprint"])["outcome"]
    row: dict[str, object] = {
        "workload_seed": seed,
        "policy": policy,
        "source": "reused_stage15k1" if schema.startswith("stage15k1") else "new_stage15k2",
        "replay_exact": True,
        "rng_gate_passed": True,
        "pre_admission_infeasible_unchanged": payload["invariant_gate"][
            "pre_admission_infeasible_unchanged"
        ],
        "round_1_unchanged": payload["invariant_gate"]["round_1_initial_repair_count_zero"],
        "round_2_admission": repair["round_2_admission"],
        "round_2_rejection": repair["round_2_rejection"],
        "baseline_round_2_admission": baseline_lifecycle.get("accepted", 0),
        "baseline_round_2_rejection": baseline_outcome["raw_auction_rejection_count"],
        "delta_round_2_admission": int(repair["round_2_admission"])
        - int(baseline_lifecycle.get("accepted", 0)),
        "delta_round_2_rejection": int(repair["round_2_rejection"])
        - int(baseline_outcome["raw_auction_rejection_count"]),
        "never_admitted_expired_proxy": repair["never_admitted_expired_proxy"],
        "baseline_never_admitted_expired_proxy": (
            int(baseline_lifecycle.get("expired_after_round_2_rejection", 0))
            + int(baseline_lifecycle.get("expired_waiting_at_deadline", 0))
        ),
        "accepted_events": lifecycle.get("accepted", 0),
        "completed_events": lifecycle.get("completed", 0),
        "preempted_events": lifecycle.get("preempted", 0),
        "completion_per_admission": lifecycle.get("completed", 0) / lifecycle.get("accepted", 1)
        if lifecycle.get("accepted", 0)
        else 0.0,
        "prior_completed_utility": prior_outcome["completed_utility"],
        "round_2_initial_infeasible_count": initialization["round_2_initial_infeasible_count"],
        "round_2_initial_feasibility_before": initialization[
            "round_2_initial_population_feasibility_rate_before_repair"
        ],
        "round_2_initial_feasibility_after": initialization[
            "round_2_initial_population_feasibility_rate_after_repair"
        ],
    }
    for metric in METRICS:
        row[f"baseline_{metric}"] = baseline_outcome[metric]
        row[f"repair_{metric}"] = repair_outcome[metric]
        row[f"delta_{metric}"] = float(repair_outcome[metric]) - float(baseline_outcome[metric])
        row[f"relative_delta_{metric}"] = (
            _num(row[f"delta_{metric}"]) / float(baseline_outcome[metric])
            if float(baseline_outcome[metric]) != 0.0
            else None
        )
    prior_delta = float(prior_outcome["completed_utility"]) - float(
        baseline_outcome["completed_utility"]
    )
    row["completed_utility_effect_share_of_prior"] = (
        _num(row["delta_completed_utility"]) / prior_delta if prior_delta else None
    )
    diag = repair.get("preemption_diagnostic")
    terminal = repair.get("terminal_preemption_outcome")
    row["preemption_diagnostic_available"] = isinstance(diag, dict) and schema.startswith(
        "stage15k2"
    )
    if row["preemption_diagnostic_available"]:
        diag_dict = cast(dict[str, Any], diag)
        terminal_dict = cast(dict[str, Any], terminal)
        counts = cast(dict[str, Any], diag_dict["counts"])
        row.update(
            {
                "preemption_batches": counts.get("preemption_batches", 0),
                "preemption_positive_net_batches": counts.get("positive_net_batches", 0),
                "preemption_zero_net_batches": counts.get("zero_net_batches", 0),
                "preemption_negative_net_batches": counts.get("negative_net_batches", 0),
                "accepted_new_utility": diag_dict["accepted_new_utility"],
                "victim_utility": diag_dict["victim_utility"],
                "preemption_net_utility": diag_dict["net_utility"],
                "five_percent_pair_count": counts.get("five_percent_pair_count", 0),
                "five_percent_pass": counts.get("five_percent_pass", 0),
                "five_percent_fail": counts.get("five_percent_fail", 0),
                "admissions_eventually_preempted": terminal_dict["admissions_eventually_preempted"],
            }
        )
    return row


def finalize(paths: list[Path]) -> dict[str, object]:
    rows = [
        _row(_load(path), source_sha256=sha256(path.read_bytes()).hexdigest()) for path in paths
    ]
    keys = {(int(_num(row["workload_seed"])), str(row["policy"])) for row in rows}
    expected = {(seed, policy) for seed in SEEDS for policy in POLICIES}
    if len(rows) != 10 or keys != expected:
        raise ValueError("Stage 15-K.2 completeness failed: expected 10 unique logical pairs")
    rows.sort(key=lambda row: (int(_num(row["workload_seed"])), str(row["policy"])))
    aggregate: list[dict[str, object]] = []
    for policy in POLICIES:
        subset = [row for row in rows if row["policy"] == policy]
        deltas = [_num(row["delta_completed_utility"]) for row in subset]
        shares = [
            _num(row["completed_utility_effect_share_of_prior"])
            for row in subset
            if row["completed_utility_effect_share_of_prior"] is not None
        ]
        aggregate.append(
            {
                "policy": policy,
                "n": 5,
                "delta_completed_utility_mean": fmean(deltas),
                "delta_completed_utility_std": stdev(deltas),
                "positive_effect_seeds": sum(value > 0 for value in deltas),
                "zero_effect_seeds": sum(value == 0 for value in deltas),
                "negative_effect_seeds": sum(value < 0 for value in deltas),
                "direction_stable_positive": all(value > 0 for value in deltas),
                "effect_share_of_prior_mean": fmean(shares),
            }
        )
    dkp_rows = [row for row in rows if row["policy"] == POLICIES[1]]
    diagnostic_rows = [row for row in dkp_rows if row["preemption_diagnostic_available"]]
    decision = {}
    for policy in POLICIES:
        values = [_num(row["delta_completed_utility"]) for row in rows if row["policy"] == policy]
        decision[policy] = Counter(
            "positive" if value > 0 else "negative" if value < 0 else "zero" for value in values
        )
    return {
        "schema_version": "stage15k2-five-seed-summary-v1",
        "label": "[آزمون کمکی] Stage 15-K.2 limited five-seed validation",
        "logical_pair_count": 10,
        "new_logical_pair_count": 8,
        "reused_seed_one_pair_count": 2,
        "new_physical_execution_count": 16,
        "baseline_recomputed": False,
        "thirty_workloads_executed": False,
        "preemption_diagnostic_seed_count": len(diagnostic_rows),
        "preemption_diagnostic_limitation": (
            "seed one reused Stage 15-K.1 artifact did not record the new aggregate fields"
        ),
        "rows": rows,
        "aggregate": aggregate,
        "decision_counts": {policy: dict(counts) for policy, counts in decision.items()},
        "figure_6_status": "بازتولید نشد",
    }


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-seed-csv", type=Path, required=True)
    parser.add_argument("--aggregate-csv", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    paths = list(args.input)
    if args.input_dir is not None:
        for path in args.input_dir.rglob("*.json"):
            try:
                schema = _load(path).get("schema_version")
            except (json.JSONDecodeError, TypeError):
                continue
            if schema in {
                "stage15k1-r2-initialization-repair-pilot-v1",
                "stage15k2-r2-initialization-repair-pair-v1",
            }:
                paths.append(path)
    report = finalize(paths)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_csv(cast(list[dict[str, object]], report["rows"]), args.per_seed_csv)
    _write_csv(cast(list[dict[str, object]], report["aggregate"]), args.aggregate_csv)
    lines = [
        "# Stage 15-K.2 — limited five-seed validation",
        "",
        "[آزمون کمکی]؛ Pipeline رسمی و Figure 6 تغییر نکرده‌اند.",
        "",
        f"Completeness: {report['logical_pair_count']}/10 logical pairs; 8 new and 2 reused.",
        f"New physical executions: {report['new_physical_execution_count']}.",
        (
            "DK-P preemption diagnostic coverage: "
            f"{report['preemption_diagnostic_seed_count']}/5 seeds; "
            "seed one was not rerun."
        ),
        "",
        "## Aggregate",
        "",
        "```json",
        json.dumps(report["aggregate"], indent=2),
        "```",
        "",
        "Official Figure 6 status: بازتولید نشد.",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
