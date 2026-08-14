"""Validate and aggregate the complete auxiliary Stage-15H repair experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from validate_stage15h_public_pair import validate as validate_stage15h
from verify_stage15h_reuse import verify_repairs

POLICIES = ("pipeline_double_knapsack_retention", "pipeline_double_knapsack_preemption")
VARIANTS = ("initial_population_repair", "offspring_repair")
SHORT = {
    "knapsack_greedy_retention": "KG-R",
    "knapsack_greedy_preemption": "KG-P",
    "pipeline_double_knapsack_retention": "DK-R",
    "pipeline_double_knapsack_preemption": "DK-P",
}
OUTCOME_METRICS = (
    "completed_utility",
    "rejected_utility",
    "ever_preempted_utility",
    "completed_jobs",
    "rejected_jobs",
    "ever_preempted_jobs",
    "raw_auction_rejection_count",
)


def _number(value: object) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    raise TypeError(f"expected numeric value, got {type(value).__name__}")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(path)
    return value


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _normalize_pair(path: Path) -> dict[str, object]:
    data = _load(path)
    schema = data.get("schema_version")
    if schema == "stage15h-counterfactual-pair-v1":
        validate_stage15h(path)
        source = "Stage 15-H"
    elif schema == "stage15e-counterfactual-pair-v1":
        source = "Stage 15-E"
    elif schema == "stage15d-counterfactual-pair-v1":
        source = "Stage 15-D.1"
    else:
        raise ValueError(f"unexpected repair schema: {schema}")
    if data.get("baseline_recomputed") is not False or data.get("replay_exact") is not True:
        raise ValueError("repair pair failed reuse/replay gate")
    replay = data["variant_replay"]
    fingerprint = replay["scientific_fingerprint"]
    outcome = fingerprint["outcome"]
    lifecycle = replay["lifecycle_funnel"]
    auction = replay["auction_funnel"]["totals"]
    selector = replay["selector_funnel"]
    counter = replay["counterfactual"]
    ga_calls = sum(
        int(selector["by_round"][round_name]["ga_calls"]) for round_name in ("round_1", "round_2")
    )
    feasible = sum(
        int(selector["by_round"][round_name]["raw_best_feasible_ga_calls"])
        for round_name in ("round_1", "round_2")
    )
    repair_count = int(
        counter["initial_chromosomes_repaired"]
        if data["variant"] == VARIANTS[0]
        else counter["offspring_repaired"]
    )
    runtime = data.get("runtime_seconds", {})
    row: dict[str, object] = {
        "workload_seed": str(data["workload_seed"]),
        "policy_seed": str(data["policy_seed"]),
        "policy": data["policy"],
        "variant": data["variant"],
        "source_stage": source,
        "source_file_sha256": _hash(path),
        "workload_sha256": fingerprint["workload_sha256"],
        "replay_exact": True,
        "rng_gate_within_variant": True,
        "baseline_rng_comparison": "unknown_not_recorded_in_stage13_baseline",
        "round_1_admission": auction["round_1_tasks_selected_on_any_server"],
        "round_2_admission": auction["round_2_accepted"],
        "retry": lifecycle.get("retry_scheduled", 0),
        "expiration": lifecycle.get("expired", 0),
        "completion": lifecycle.get("completed", 0),
        "ga_call_count": ga_calls,
        "repair_count": repair_count,
        "repairs_per_ga_call": repair_count / ga_calls if ga_calls else 0.0,
        "feasibility_rate": feasible / ga_calls if ga_calls else 1.0,
        "zero_candidate_paths": sum(
            int(selector["by_round"][r]["empty_calls"]) for r in ("round_1", "round_2")
        ),
        "single_candidate_paths": sum(
            int(selector["by_round"][r]["single_candidate_calls"]) for r in ("round_1", "round_2")
        ),
        "multi_candidate_paths": ga_calls,
        "runtime_seconds": sum(float(v) for v in runtime.values())
        if isinstance(runtime, dict)
        else "",
    }
    row.update({key: outcome[key] for key in OUTCOME_METRICS})
    return row


def _mean_stats(values: list[float]) -> dict[str, float]:
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "mean": mean,
        "standard_deviation": sd,
        "ci95_low": mean - 1.96 * sd / math.sqrt(len(values)),
        "ci95_high": mean + 1.96 * sd / math.sqrt(len(values)),
    }


def _plot_bars(
    path_stem: Path, title: str, labels: list[str], completed: list[float], rejected: list[float]
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.4))
    x = list(range(len(labels)))
    width = 0.38
    ax.bar([i - width / 2 for i in x], completed, width, label="Completed utility")
    ax.bar([i + width / 2 for i in x], rejected, width, label="Rejected utility")
    ax.set_xticks(x, labels, rotation=18, ha="right")
    ax.set_ylabel("Mean utility across 30 paired workloads")
    ax.set_title(title + " — auxiliary test")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path_stem.with_suffix(".png"), dpi=180)
    fig.savefig(path_stem.with_suffix(".pdf"))
    plt.close(fig)


def finalize(
    *,
    new_root: Path,
    prior_root: Path,
    repair_manifest: Path,
    baseline_manifest: Path,
    baseline_metrics: Path,
    baseline_lifecycle: Path,
    output: Path,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    prior_rows = verify_repairs(repair_manifest, [prior_root])
    pinned_prior = {str(row["file_sha256"]) for row in prior_rows}
    prior_paths = [p for p in prior_root.rglob("*.json") if _hash(p) in pinned_prior]
    new_paths = [p for p in new_root.rglob("stage15h-*.json") if "validation" not in p.name]
    repairs = [_normalize_pair(path) for path in prior_paths + new_paths]
    keys = [(str(r["workload_seed"]), str(r["variant"]), str(r["policy"])) for r in repairs]
    if len(repairs) != 120 or len(set(keys)) != 120:
        incomplete = {
            "schema_version": "stage15h-completeness-v1",
            "status": "incomplete_not_aggregated",
            "repair_files_found": len(repairs),
            "unique_repair_pairs": len(set(keys)),
            "required_repair_pairs": 120,
            "partial_mean_reported": False,
        }
        (output / "completeness_report.json").write_text(
            json.dumps(incomplete, indent=2) + "\n", encoding="utf-8"
        )
        raise ValueError(f"repair completeness failed: {len(repairs)} rows/{len(set(keys))} unique")

    base_manifest = _load(baseline_manifest)
    base_entries = base_manifest["entries"]
    base_map = {(str(e["workload_seed"]), str(e["policy"])): e for e in base_entries}
    metrics = {(r["workload_seed"], r["policy"]): r for r in _csv(baseline_metrics)}
    lifecycle = {(r["workload_seed"], r["policy"]): r for r in _csv(baseline_lifecycle)}
    if len(base_map) != 120 or len(metrics) != 120 or len(lifecycle) != 120:
        raise ValueError("baseline reuse completeness is not 120/120")
    baseline_rows: list[dict[str, object]] = []
    for key, entry in sorted(base_map.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        raw, life = metrics[key], lifecycle[key]
        generated = int(life["generated_jobs"])
        completed = int(life["completed_jobs"])
        row: dict[str, object] = {
            "workload_seed": key[0],
            "policy": key[1],
            "policy_seed": entry["policy_seed"],
            "workload_sha256": entry["workload_sha256"],
            "source_result_sha256": entry["result_sha256"],
            "source_run_id": 31644121025,
            "validation": "pinned_after_120_pair_stage13k_audit",
            "completed_utility": float(raw["completed_utility"]),
            "rejected_utility": float(raw["rejected_utility"]),
            "ever_preempted_utility": float(raw["ever_preempted_utility"]),
            "completed_jobs": completed,
            "rejected_jobs": generated - completed,
            "ever_preempted_jobs": int(life["preempted_jobs"]),
            "raw_auction_rejection_count": int(life["round_two_rejections"]),
            "retry": int(life["retry_scheduled"]),
            "expiration": sum(
                int(life[k])
                for k in (
                    "canonical_expirations",
                    "post_rejection_expirations",
                    "waiting_deadline_expirations",
                    "active_deadline_expirations",
                )
            ),
            "completion": completed,
            "round_2_admission": int(life["accepted_jobs"]),
            "round_1_admission": "not_recorded_in_stage13_baseline",
            "ga_call_count": "not_recorded_in_stage13_baseline",
            "repair_count": int(life["ga_repairs"]),
            "feasibility_rate": "not_recorded_in_stage13_baseline",
        }
        baseline_rows.append(row)
    for repair in repairs:
        entry = base_map[(str(repair["workload_seed"]), str(repair["policy"]))]
        if (
            str(repair["policy_seed"]) != str(entry["policy_seed"])
            or repair["workload_sha256"] != entry["workload_sha256"]
        ):
            raise ValueError("repair/baseline seed or workload hash mismatch")

    _write_csv(output / "pair_inventory.csv", repairs)
    _write_csv(output / "baseline_reuse_inventory.csv", baseline_rows)
    _write_csv(output / "repair_results_30_workloads.csv", repairs)
    _write_csv(
        output / "rng_validation.csv",
        [
            {
                "workload_seed": r["workload_seed"],
                "policy": r["policy"],
                "variant": r["variant"],
                "within_variant_replay": "passed",
                "baseline_comparison": r["baseline_rng_comparison"],
            }
            for r in repairs
        ],
    )

    repair_map = {
        (str(r["workload_seed"]), str(r["variant"]), str(r["policy"])): r for r in repairs
    }
    baseline_map = {(str(r["workload_seed"]), str(r["policy"])): r for r in baseline_rows}
    effect_rows: list[dict[str, object]] = []
    comparisons = [(VARIANTS[0], "baseline"), (VARIANTS[1], "baseline"), (VARIANTS[0], VARIANTS[1])]
    effect_metrics = OUTCOME_METRICS + ("round_2_admission", "retry", "expiration", "completion")
    for seed in sorted({k[0] for k in repair_map}, key=int):
        for policy in POLICIES:
            for left, right in comparisons:
                lhs = repair_map[(seed, left, policy)]
                rhs = (
                    baseline_map[(seed, policy)]
                    if right == "baseline"
                    else repair_map[(seed, right, policy)]
                )
                for metric in effect_metrics:
                    a, b = _number(lhs[metric]), _number(rhs[metric])
                    effect_rows.append(
                        {
                            "workload_seed": seed,
                            "policy": policy,
                            "left": left,
                            "right": right,
                            "metric": metric,
                            "absolute_effect": a - b,
                            "relative_effect": "" if b == 0 else (a - b) / abs(b),
                        }
                    )
    _write_csv(output / "paired_effects_by_seed.csv", effect_rows)

    aggregate: list[dict[str, object]] = []
    series: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in baseline_rows:
        series[f"{SHORT[str(row['policy'])]} baseline"].append(row)
    for row in repairs:
        repair_label = (
            "initialization repair" if row["variant"] == VARIANTS[0] else "offspring repair"
        )
        series[f"{SHORT[str(row['policy'])]} {repair_label}"].append(row)
    aggregate_metrics = OUTCOME_METRICS + ("round_2_admission", "retry", "expiration", "completion")
    for label, rows in sorted(series.items()):
        for metric in aggregate_metrics:
            stats = _mean_stats([_number(row[metric]) for row in rows])
            aggregate.append(
                {
                    "series": label,
                    "metric": metric,
                    "n": len(rows),
                    **stats,
                    "classification": "[آزمون کمکی]",
                }
            )
    _write_csv(output / "aggregate_summary.csv", aggregate)

    means = {(r["series"], r["metric"]): _number(r["mean"]) for r in aggregate}
    combined_labels = [
        "KG-R baseline",
        "KG-P baseline",
        "DK-R baseline",
        "DK-P baseline",
        "DK-R initialization repair",
        "DK-P initialization repair",
        "DK-R offspring repair",
        "DK-P offspring repair",
    ]
    for name, labels in (
        ("combined_eight_series", combined_labels),
        (
            "initialization_panel",
            [
                "KG-R baseline",
                "KG-P baseline",
                "DK-R initialization repair",
                "DK-P initialization repair",
            ],
        ),
        (
            "offspring_panel",
            ["KG-R baseline", "KG-P baseline", "DK-R offspring repair", "DK-P offspring repair"],
        ),
    ):
        _plot_bars(
            output / name,
            name.replace("_", " ").title(),
            labels,
            [means[(label, "completed_utility")] for label in labels],
            [means[(label, "rejected_utility")] for label in labels],
        )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for ax, (policy, variant) in zip(
        axes.flat, [(p, v) for p in POLICIES for v in VARIANTS], strict=True
    ):
        vals = [
            _number(r["absolute_effect"])
            for r in effect_rows
            if r["policy"] == policy
            and r["left"] == variant
            and r["right"] == "baseline"
            and r["metric"] == "completed_utility"
        ]
        ax.axhline(0, color="black", linewidth=0.8)
        ax.plot(range(1, 31), vals, marker="o", markersize=3)
        ax.set_title(
            f"{SHORT[policy]} / {'initialization' if variant == VARIANTS[0] else 'offspring'}"
        )
        ax.set_ylabel("Paired completed-utility effect")
    fig.tight_layout()
    fig.savefig(output / "paired_effects.png", dpi=180)
    fig.savefig(output / "paired_effects.pdf")
    plt.close(fig)

    positive: dict[str, dict[str, int]] = {}
    for policy in POLICIES:
        for variant in VARIANTS:
            vals = [
                _number(r["absolute_effect"])
                for r in effect_rows
                if r["policy"] == policy
                and r["left"] == variant
                and r["right"] == "baseline"
                and r["metric"] == "completed_utility"
            ]
            positive[f"{SHORT[policy]}:{variant}"] = {
                "positive": sum(v > 0 for v in vals),
                "zero": sum(v == 0 for v in vals),
                "negative": sum(v < 0 for v in vals),
            }
    completeness = {
        "schema_version": "stage15h-completeness-v1",
        "status": "complete_and_valid",
        "baseline_pairs": 120,
        "repair_pairs": 120,
        "workloads": 30,
        "new_pairs": 100,
        "reused_pairs": 20,
        "all_replays_exact": True,
        "baseline_recomputed": False,
        "figure_6_status": "not_reproduced",
    }
    (output / "completeness_report.json").write_text(
        json.dumps(completeness, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# Stage 15-H — 30-workload DK repair validation",
        "",
        "- Classification: **[آزمون کمکی]**; neither repair is part of the paper method.",
        "- Official Figure 6 status remains **not reproduced**.",
        "- Baselines were reused; no baseline policy was recomputed.",
        "- Option-A baseline RNG comparison remains unavailable because Stage 13 "
        "did not record it.",
        "",
        "## Completed-utility direction by paired workload",
        "",
    ]
    report.extend(
        f"- {key}: {value['positive']} positive, {value['zero']} zero, "
        f"{value['negative']} negative."
        for key, value in positive.items()
    )
    (output / "stage15h_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    comparison_rows = [
        {
            "series": label,
            "completed_utility_mean": means[(label, "completed_utility")],
            "rejected_utility_mean": means[(label, "rejected_utility")],
        }
        for label in combined_labels
    ]
    _write_csv(output / "baseline_repair_comparison.csv", comparison_rows)
    manifest_files = sorted(
        path
        for path in output.iterdir()
        if path.is_file() and path.name != "checksum_manifest.json"
    )
    checksum = {
        "schema_version": "stage15h-checksum-manifest-v1",
        "files": [
            {"name": p.name, "bytes": p.stat().st_size, "sha256": _hash(p)} for p in manifest_files
        ],
    }
    (output / "checksum_manifest.json").write_text(
        json.dumps(checksum, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "complete_and_valid", "repair_pairs": 120, "baseline_pairs": 120}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--repair-manifest", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--baseline-metrics", type=Path, required=True)
    parser.add_argument("--baseline-lifecycle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            finalize(
                new_root=args.new_root,
                prior_root=args.prior_root,
                repair_manifest=args.repair_manifest,
                baseline_manifest=args.baseline_manifest,
                baseline_metrics=args.baseline_metrics,
                baseline_lifecycle=args.baseline_lifecycle,
                output=args.output,
            )
        )
    )


if __name__ == "__main__":
    main()
