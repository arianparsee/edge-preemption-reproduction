"""Fail-closed public-boundary validator for one Stage-15E pair artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = (
        "job-",
        "arrival_raw_draws",
        "workload.json",
        "result.json",
        "github_token",
        "github_pat_",
        ".env",
        "chromosome_bits\": true",
        "task_identifiers_in_artifact\": true",
        "raw_workload_in_artifact\": true",
        "raw_trace_in_artifact\": true",
    )
    if any(token in lowered for token in forbidden):
        raise ValueError("Stage 15-E pair contains a forbidden public field")
    payload = json.loads(text)
    gate = payload["rng_gate"]
    if (
        payload["schema_version"] != "stage15e-counterfactual-pair-v1"
        or payload["baseline_recomputed"]
        or not payload["replay_exact"]
        or gate["option"] != "A"
        or not gate["passed_within_variant"]
        or gate["baseline_rng_gate_claimed"]
        or payload["official_algorithm_changed"]
        or payload["figure_6_overwritten"]
        or payload["thirty_workloads_executed"]
    ):
        raise ValueError("Stage 15-E scientific boundary failed")
    if path.stat().st_size > 5_000_000:
        raise ValueError("Stage 15-E pair artifact unexpectedly large")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    validate(args.path)
    print(json.dumps({"status": "valid_public_stage15e_pair", "name": args.path.name}))


if __name__ == "__main__":
    main()
