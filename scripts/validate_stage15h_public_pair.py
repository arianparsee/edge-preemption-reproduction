"""Fail closed on one sanitized Stage-15H pair artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

FORBIDDEN = (
    '"completed_task_ids": [',
    '"rejected_task_ids": [',
    '"ever_preempted_task_ids": [',
    '"chromosome_bits": [',
    '"raw_workload": {',
    '"task_trace": [',
    "workload.json",
    "result.json",
    "traceback",
)


def validate(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "stage15h-counterfactual-pair-v1":
        raise ValueError("invalid Stage 15-H pair schema")
    required_false = (
        "baseline_recomputed",
        "task_identifiers_in_artifact",
        "chromosome_bits_in_artifact",
        "raw_workload_in_artifact",
        "raw_trace_in_artifact",
        "official_algorithm_changed",
        "figure_6_overwritten",
        "scientific_failure_retry_allowed",
    )
    if any(data.get(key) is not False for key in required_false):
        raise ValueError("unsafe or scientifically invalid Stage 15-H flag")
    if data.get("replay_count") != 2 or data.get("replay_exact") is not True:
        raise ValueError("Stage 15-H replay gate failed")
    gate = data.get("rng_gate", {})
    if not all(
        gate.get(key) is True
        for key in (
            "passed_within_variant",
            "initial_rng_state_matches_policy_seed",
            "same_variant_final_rng_state_replay_exact",
            "same_variant_primitive_counts_replay_exact",
            "same_variant_call_shape_replay_exact",
        )
    ):
        raise ValueError("Stage 15-H RNG gate failed")
    lowered = path.read_text(encoding="utf-8").lower()
    if any(token in lowered for token in FORBIDDEN):
        raise ValueError("public Stage 15-H pair contains a forbidden detailed field")
    return cast(dict[str, Any], data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    data = validate(args.path)
    report = {
        "schema_version": "stage15h-pair-validation-v1",
        "status": "valid",
        "workload_seed": data["workload_seed"],
        "policy": data["policy"],
        "variant": data["variant"],
        "replay_exact": True,
        "rng_gate": "passed",
        "sensitive_detail_present": False,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
