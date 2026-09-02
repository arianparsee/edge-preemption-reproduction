"""Validate one sanitized Stage-15K.1 pair without rerunning it."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, cast

BANNED_KEYS = {
    "chromosome",
    "chromosomes",
    "genes",
    "raw_tasks",
    "task_ids",
    "workload_records",
}
BANNED_TEXT = re.compile(
    r"(?:C:\\Users\\|/home/|github_pat_|ghp_|BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY|Bearer\s+\S+)",
    re.IGNORECASE,
)


def _walk(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in BANNED_KEYS:
                raise ValueError(f"public pair contains banned key: {key}")
            _walk(child)
    elif isinstance(value, list):
        for child in value:
            _walk(child)
    elif isinstance(value, str) and BANNED_TEXT.search(value):
        raise ValueError("public pair contains sensitive or local-path text")


def validate_pair(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "stage15k1-r2-initialization-repair-pilot-v1":
        raise ValueError("unexpected Stage 15-K.1 schema")
    if payload.get("variant") != "round_two_initial_population_repair":
        raise ValueError("unexpected Stage 15-K.1 variant")
    if payload.get("assumptions") != ["ASSUMP-048", "ASSUMP-049"]:
        raise ValueError("only ASSUMP-048 and ASSUMP-049 may be active")
    for key in (
        "task_identifiers_in_artifact",
        "chromosome_bits_in_artifact",
        "raw_workload_in_artifact",
        "raw_trace_in_artifact",
        "official_algorithm_changed",
        "figure_6_overwritten",
        "five_or_thirty_workloads_executed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"unsafe public artifact flag: {key}")
    if payload.get("replay_exact") is not True:
        raise ValueError("replay gate did not pass")
    rng = cast(dict[str, Any], payload["rng_gate"])
    invariants = cast(dict[str, Any], payload["invariant_gate"])
    if rng.get("passed") is not True or any(
        rng.get(key) is not True
        for key in (
            "same_variant_primitive_counts_replay_exact",
            "same_variant_final_rng_state_replay_exact",
            "same_variant_call_shape_replay_exact",
        )
    ):
        raise ValueError("RNG gate did not pass")
    if int(rng.get("direct_random_draws_added_by_repair", -1)) != 0:
        raise ValueError("repair added a direct random draw")
    required_invariants = (
        "engine_capacity_and_state_invariants_passed",
        "task_partition_complete_and_disjoint",
        "utility_conservation_passed",
        "pre_admission_infeasible_unchanged",
        "round_1_initial_repair_count_zero",
    )
    if any(invariants.get(key) is not True for key in required_invariants):
        raise ValueError("scientific invariant gate did not pass")
    metrics = cast(
        dict[str, Any],
        cast(dict[str, Any], payload["round_two_only_repair"])[
            "initialization_metrics"
        ],
    )
    if int(metrics["round_1_initial_chromosomes_repaired"]) != 0:
        raise ValueError("Round 1 received initialization repair")
    if int(metrics["round_2_initial_repair_count"]) <= 0:
        raise ValueError("Round 2 repair was not exercised")
    _walk(payload)
    return {
        "schema_version": "stage15k1-public-validation-v1",
        "status": "valid",
        "policy": payload["policy"],
        "workload_seed": payload["workload_seed"],
        "replay_exact": True,
        "rng_gate_passed": True,
        "invariant_gate_passed": True,
        "sanitization_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pair", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    report = validate_pair(args.pair)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "stage15k1_public_pair_valid", **report}))


if __name__ == "__main__":
    main()
