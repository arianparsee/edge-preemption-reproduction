"""Validate one sanitized Stage-15K.2 pair artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate(payload: dict[str, Any]) -> dict[str, object]:
    if payload.get("schema_version") != "stage15k2-r2-initialization-repair-pair-v1":
        raise ValueError("unexpected Stage 15-K.2 schema")
    if payload.get("replay_exact") is not True or payload.get("replay_count") != 2:
        raise ValueError("two exact replays are required")
    if payload.get("baseline_recomputed") is not False:
        raise ValueError("baseline recomputation is forbidden")
    gate = payload["invariant_gate"]
    required = (
        "engine_capacity_and_state_invariants_passed",
        "task_partition_complete_and_disjoint",
        "utility_conservation_passed",
        "pre_admission_infeasible_unchanged",
        "round_1_initial_repair_count_zero",
    )
    if not all(gate.get(key) is True for key in required):
        raise ValueError("scientific invariant gate failed")
    rng = payload["rng_gate"]
    if not all(
        rng.get(key) is True
        for key in (
            "initial_rng_state_matches_policy_seed",
            "same_variant_final_rng_state_replay_exact",
            "same_variant_primitive_counts_replay_exact",
            "same_variant_call_shape_replay_exact",
        )
    ):
        raise ValueError("RNG Option-A replay gate failed")
    for key in (
        "task_identifiers_in_artifact",
        "chromosome_bits_in_artifact",
        "raw_workload_in_artifact",
        "raw_trace_in_artifact",
        "official_algorithm_changed",
        "figure_6_overwritten",
        "thirty_workloads_executed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"public artifact boundary failed: {key}")
    replay = payload["variant_replay"]
    if replay["preemption_diagnostic"].get("task_identifiers_recorded") is not False:
        raise ValueError("preemption diagnostic exposed task identifiers")
    return {
        "schema_version": "stage15k2-public-validation-v1",
        "status": "passed",
        "workload_seed": payload["workload_seed"],
        "policy": payload["policy"],
        "replay_exact": True,
        "rng_gate": "passed_option_A_partial_observability",
        "scientific_invariants": "passed",
        "public_data_boundary": "passed",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite: {args.report}")
    report = validate(json.loads(args.input.read_text(encoding="utf-8")))
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
