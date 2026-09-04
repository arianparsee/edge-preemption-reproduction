"""Validate the sanitized public Stage 15-M.1 pair artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast


def validate(path: Path) -> dict[str, object]:
    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    if payload.get("schema_version") != "stage15m1-no-cascading-pilot-v1":
        raise ValueError("unexpected Stage 15-M.1 schema")
    if (
        int(payload.get("workload_seed", -1)) != 541501192080118187
        or int(payload.get("policy_seed", -1)) != 18158600156516774620
        or payload.get("logical_pairs") != 1
        or payload.get("replay_count") != 2
        or payload.get("replay_exact") is not True
    ):
        raise ValueError("Stage 15-M.1 scope or replay contract mismatch")
    if (
        payload.get("baseline_recomputed") is not False
        or payload.get("repair_only_recomputed") is not False
    ):
        raise ValueError("a comparator was recomputed")
    publication = cast(dict[str, object], payload["publication"])
    forbidden_flags = ("task_identifiers", "raw_edges", "chromosomes", "raw_workload")
    if any(publication.get(key) is not False for key in forbidden_flags):
        raise ValueError("public Stage 15-M.1 artifact exposes forbidden detail")
    if publication.get("official_pipeline_changed") is not False:
        raise ValueError("official pipeline change was incorrectly claimed")
    if publication.get("figure_6_status") != "بازتولید نشد":
        raise ValueError("Figure 6 status changed")
    modified = cast(dict[str, Any], payload["modified"])
    guard = cast(dict[str, Any], modified["no_cascading"])
    if (
        guard.get("task_identifiers_recorded") is not False
        or guard.get("raw_edges_recorded") is not False
    ):
        raise ValueError("No-Cascading summary was not sanitized")
    protection = cast(dict[str, int], guard["protection"])
    preemption = cast(dict[str, int], guard["preemption"])
    if protection["preempted"] != 0 or preemption["direct_chain_maximum_depth"] > 1:
        raise ValueError("No-Cascading invariant failed")
    return {
        "schema_version": "stage15m1-public-validation-v1",
        "valid": True,
        "pilot_success": bool(payload["pilot_success"]),
        "logical_pairs": 1,
        "replay_count": 2,
        "sanitized": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.input)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
