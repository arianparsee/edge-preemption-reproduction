"""Verify and record externally measured Stage-13G wall-clock durations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.orchestration import file_sha256
from edge_reproduction.experiments.pipe_normal_full import (
    POLICY_NAMES,
)


def _row_integer(row: dict[str, object], key: str) -> int:
    value = row[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--workload-seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timing", action="append", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite timing artifact: {args.output}")
    timings: dict[str, float] = {}
    for item in args.timing:
        policy, separator, raw_seconds = item.partition("=")
        if not separator or policy not in POLICY_NAMES or policy in timings:
            raise ValueError(f"invalid or duplicate timing: {item}")
        seconds = float(raw_seconds)
        if seconds <= 0.0:
            raise ValueError("timing seconds must be positive")
        timings[policy] = seconds
    if tuple(timings) != POLICY_NAMES:
        raise ValueError("timings must be supplied once in canonical policy order")

    base = (
        args.root
        / "results"
        / "raw"
        / "stage13f"
        / "PIPE-NORMAL"
        / f"seed-{args.workload_seed}"
    )
    rows: list[dict[str, object]] = []
    workload_hashes: set[str] = set()
    total_bytes = 0
    for policy in POLICY_NAMES:
        directory = base / policy
        result_path = directory / "result.json"
        workload_path = directory / "workload.json"
        manifest_path = directory / "manifest.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["result_sha256"] != file_sha256(result_path):
            raise ValueError(f"result hash mismatch: {policy}")
        if manifest["workload_sha256"] != file_sha256(workload_path):
            raise ValueError(f"workload hash mismatch: {policy}")
        workload_hashes.add(manifest["workload_sha256"])
        result_bytes = result_path.stat().st_size
        workload_bytes = workload_path.stat().st_size
        total_bytes += result_bytes + workload_bytes + manifest_path.stat().st_size
        outcome = result["run"]["outcome"]
        metadata = result["run"]["metadata"]
        rows.append(
            {
                "policy": policy,
                "wall_seconds": timings[policy],
                "policy_seed": result["policy_seed"],
                "completed_jobs": outcome["completed_jobs"],
                "rejected_jobs": outcome["rejected_jobs"],
                "ever_preempted_jobs": outcome["ever_preempted_jobs"],
                "completed_utility": outcome["completed_utility"],
                "rejected_utility": outcome["rejected_utility"],
                "ever_preempted_utility": outcome["ever_preempted_utility"],
                "raw_auction_rejection_count": outcome["raw_auction_rejection_count"],
                "zero_fitness_repairs": int(
                    metadata["ga.zero_fitness_feasibility_repairs"]
                ),
                "equal_minimum_price_ties": int(
                    metadata["client.equal_minimum_price_ties"]
                ),
                "result_bytes": result_bytes,
                "workload_bytes": workload_bytes,
                "result_sha256": manifest["result_sha256"],
            }
        )
    if len(workload_hashes) != 1:
        raise ValueError("policies did not use one byte-identical workload")
    serial_seconds = sum(timings.values())
    task_counts = {
        _row_integer(row, "completed_jobs") + _row_integer(row, "rejected_jobs")
        for row in rows
    }
    if len(task_counts) != 1:
        raise ValueError("policy outcomes do not share one generated task count")
    artifact = {
        "schema_version": "stage13g-timing-gate-v1",
        "scientific_label": "auxiliary_timing_gate_not_paper_runtime",
        "baseline": "arXiv:2403.15665v2_2024",
        "workload_seed": args.workload_seed,
        "arrival_slots": 100,
        "task_count": next(iter(task_counts)),
        "shared_workload_sha256": next(iter(workload_hashes)),
        "measured_serial_seconds_one_workload": serial_seconds,
        "measured_serial_minutes_one_workload": serial_seconds / 60.0,
        "extrapolated_serial_seconds_30_workloads": serial_seconds * 30,
        "extrapolated_serial_hours_30_workloads": serial_seconds * 30 / 3600.0,
        "extrapolated_remaining_serial_hours_29_workloads": serial_seconds * 29 / 3600.0,
        "extrapolation_status": "auxiliary_linear_extrapolation_from_one_seed_not_measurement",
        "artifact_bytes_four_pairs": total_bytes,
        "full_raw_pair_progress": "4/120",
        "aggregation_status": "blocked_until_all_120_raw_pairs_exist",
        "figure_6_reproduced": False,
        "runs": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "recorded", "output": args.output.as_posix()}))


if __name__ == "__main__":
    main()
