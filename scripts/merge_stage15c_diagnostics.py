"""Merge two sanitized Stage 15-C policy diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast


def merge(paths: list[Path]) -> dict[str, object]:
    """Validate and merge exactly one DK-R and one DK-P diagnostic."""

    if len(paths) != 2:
        raise ValueError("Stage 15-C merge requires exactly two policy diagnostics")
    policies: dict[str, object] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["schema_version"] != "stage15c-dk-funnel-v1":
            raise ValueError("unexpected Stage 15-C schema")
        if not payload["scientific_fingerprint_equal"] or payload["baseline_recomputed"]:
            raise ValueError("Stage 15-C scientific equivalence invariant failed")
        if payload["workload_seed"] != 541501192080118187:
            raise ValueError("unexpected Stage 15-C workload seed")
        policy = str(payload["policy"])
        if policy in policies:
            raise ValueError("duplicate Stage 15-C policy")
        policies[policy] = {
            "selector_funnel": payload["selector_funnel"],
            "auction_funnel": payload["auction_funnel"],
            "lifecycle_funnel": payload["lifecycle_funnel"],
        }
    expected = {
        "pipeline_double_knapsack_retention",
        "pipeline_double_knapsack_preemption",
    }
    if set(policies) != expected:
        raise ValueError("Stage 15-C policy set is incomplete")
    return {
        "schema_version": "stage15c-merged-dk-funnel-v1",
        "label": "[آزمون کمکی] funnel غیرمداخله‌ای تصمیم DK",
        "workload_seed": 541501192080118187,
        "validated_baseline_equivalence": True,
        "baseline_recomputed": False,
        "raw_trace_in_artifact": False,
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "policies": policies,
        "interpretation_boundary": (
            "aggregate funnel counts localize losses but do not establish a causal "
            "counterfactual or modify the approved algorithm"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite merged diagnostic: {args.output}")
    report = merge(cast(list[Path], args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "merged", "policies": 2}))


if __name__ == "__main__":
    main()
