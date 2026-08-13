"""Merge two sanitized DK diagnostic reports and report Round-1/Round-2 bottlenecks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

POLICIES = {
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
}


def merge(inputs: list[Path]) -> dict[str, Any]:
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in inputs]
    if {report["policy"] for report in reports} != POLICIES:
        raise ValueError("Stage 15-B requires exactly the two DK policy diagnostics")
    if any(not report["scientific_fingerprint_equal"] for report in reports):
        raise ValueError("a scientific equivalence check failed")
    policy_rows: dict[str, dict[str, Any]] = {}
    for report in reports:
        policy = report["policy"]
        rounds = report["instrumentation"]["by_round"]
        policy_rows[policy] = {
            "round_1": rounds["round_1"],
            "round_2": rounds["round_2"],
            "total_calls": report["instrumentation"]["total_calls"],
            "auction_count": report["instrumentation"]["auction_count"],
        }
    return {
        "schema_version": "stage15b-merged-ga-diagnostic-v1",
        "label": "[آزمون کمکی]",
        "workload_seed": 541501192080118187,
        "validated_baseline_equivalence": True,
        "baseline_recomputed": False,
        "raw_trace_in_artifact": False,
        "policies": policy_rows,
        "interpretation_boundary": (
            "diagnostic counts localize GA selection pressure and repairs; "
            "they do not change or replace the approved algorithm"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    report = merge(args.input)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "stage15b_merged", "policies": 2}))


if __name__ == "__main__":
    main()
