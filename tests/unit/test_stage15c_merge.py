from __future__ import annotations

import json
from pathlib import Path

from scripts.merge_stage15c_diagnostics import merge


def _payload(policy: str) -> dict[str, object]:
    return {
        "schema_version": "stage15c-dk-funnel-v1",
        "scientific_fingerprint_equal": True,
        "baseline_recomputed": False,
        "workload_seed": 541501192080118187,
        "policy": policy,
        "selector_funnel": {"by_round": {}},
        "auction_funnel": {"totals": {}},
        "lifecycle_funnel": {},
    }


def test_merge_requires_and_preserves_both_sanitized_policies(tmp_path: Path) -> None:
    paths: list[Path] = []
    for policy in (
        "pipeline_double_knapsack_retention",
        "pipeline_double_knapsack_preemption",
    ):
        path = tmp_path / f"{policy}.json"
        path.write_text(json.dumps(_payload(policy)), encoding="utf-8")
        paths.append(path)

    report = merge(paths)

    assert report["validated_baseline_equivalence"] is True
    assert report["baseline_recomputed"] is False
    assert report["task_identifiers_in_artifact"] is False
    assert set(report["policies"]) == {
        "pipeline_double_knapsack_retention",
        "pipeline_double_knapsack_preemption",
    }
