"""Validate one gated Stage-13J five-workload/twenty-pair batch."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from statistics import fmean
from typing import Any

from edge_reproduction.experiments.pipe_normal_full import POLICY_NAMES


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _selected_seeds(plan: dict[str, Any], batch: int) -> tuple[int, ...]:
    selected = next((item for item in plan["batches"] if item["batch"] == batch), None)
    if not isinstance(selected, dict):
        raise ValueError(f"unknown Stage-13J batch: {batch}")
    seeds = tuple(int(seed) for seed in selected["workload_seeds"])
    if len(seeds) != 5 or len(set(seeds)) != 5:
        raise ValueError("Stage-13J batch must contain five distinct workload seeds")
    return seeds


def record_batch(
    *, root: Path, config_path: Path, plan_path: Path, batch: int
) -> dict[str, object]:
    config = _object(config_path)
    plan = _object(plan_path)
    config_sha256 = _sha256(config_path)
    seeds = _selected_seeds(plan, batch)
    descriptors = {int(item["workload_seed"]): item for item in config["runs"]}
    rows: list[dict[str, object]] = []
    workload_rows: list[dict[str, object]] = []
    for seed in seeds:
        descriptor = descriptors[seed]
        workload_hashes: set[str] = set()
        task_counts: set[int] = set()
        wall_seconds: list[float] = []
        for policy in POLICY_NAMES:
            pair = root / "results/raw/stage13f/PIPE-NORMAL" / f"seed-{seed}" / policy
            result_path = pair / "result.json"
            workload_path = pair / "workload.json"
            manifest_path = pair / "manifest.json"
            timing_path = root / f"timing-{seed}-{policy}.txt"
            for path in (result_path, workload_path, manifest_path, timing_path):
                if not path.is_file():
                    raise FileNotFoundError(f"missing Stage-13J artifact: {path}")
            result = _object(result_path)
            workload = _object(workload_path)
            manifest = _object(manifest_path)
            workload_hash = _sha256(workload_path)
            if manifest.get("config_sha256") != config_sha256:
                raise ValueError(f"config hash mismatch: {seed}/{policy}")
            if manifest.get("result_sha256") != _sha256(result_path):
                raise ValueError(f"result hash mismatch: {seed}/{policy}")
            if manifest.get("workload_sha256") != workload_hash:
                raise ValueError(f"workload hash mismatch: {seed}/{policy}")
            if result.get("workload_seed") != seed or result.get("policy") != policy:
                raise ValueError(f"result identity mismatch: {seed}/{policy}")
            expected_policy_seed = int(descriptor["policy_seeds"][policy])
            if result.get("policy_seed") != expected_policy_seed:
                raise ValueError(f"policy seed mismatch: {seed}/{policy}")
            outcome = result["run"]["outcome"]
            states = result["run"]["final_task_states"]
            completed = set(outcome["completed_task_ids"])
            rejected = set(outcome["rejected_task_ids"])
            preempted = set(outcome["ever_preempted_task_ids"])
            all_tasks = set(states)
            if completed & rejected or completed | rejected != all_tasks:
                raise ValueError(f"outcome partition failed: {seed}/{policy}")
            if not preempted <= rejected:
                raise ValueError(f"preempted subset failed: {seed}/{policy}")
            seconds = float(timing_path.read_text(encoding="utf-8").strip())
            if seconds <= 0:
                raise ValueError(f"non-positive timing: {seed}/{policy}")
            workload_hashes.add(workload_hash)
            task_counts.add(len(workload["tasks"]))
            wall_seconds.append(seconds)
            rows.append(
                {
                    "workload_seed": seed,
                    "policy": policy,
                    "policy_seed": expected_policy_seed,
                    "result_sha256": manifest["result_sha256"],
                    "workload_sha256": workload_hash,
                    "wall_seconds": seconds,
                    "completed_jobs": outcome["completed_jobs"],
                    "rejected_jobs": outcome["rejected_jobs"],
                    "ever_preempted_jobs": outcome["ever_preempted_jobs"],
                }
            )
        if len(workload_hashes) != 1 or len(task_counts) != 1:
            raise ValueError(f"policies did not share one workload: {seed}")
        workload_rows.append(
            {
                "workload_seed": seed,
                "task_count": next(iter(task_counts)),
                "shared_workload_sha256": next(iter(workload_hashes)),
                "parallel_policy_wall_seconds": max(wall_seconds),
                "serial_equivalent_wall_seconds": sum(wall_seconds),
            }
        )
    if len(rows) != 20:
        raise ValueError("Stage-13J batch must contain exactly twenty pairs")
    parallel_times = [
        value
        for item in workload_rows
        if isinstance(value := item["parallel_policy_wall_seconds"], float)
    ]
    if len(parallel_times) != 5:
        raise TypeError("parallel workload timings must be floats")
    return {
        "schema_version": "stage13j-five-workload-batch-summary-v1",
        "baseline": "arXiv:2403.15665v2_2024",
        "scientific_label": "partial_batch_not_30_repeat_aggregation",
        "batch": batch,
        "workload_count": 5,
        "pair_count": 20,
        "full_30_repeat_run_completed": False,
        "figure_6_reproduced": False,
        "mean_parallel_policy_wall_seconds": fmean(parallel_times),
        "workloads": workload_rows,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--batch-plan", type=Path, required=True)
    parser.add_argument("--batch", type=int, choices=range(1, 6), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite batch summary: {args.output}")
    summary = record_batch(
        root=args.root,
        config_path=args.config,
        plan_path=args.batch_plan,
        batch=args.batch,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "recorded", "batch": args.batch, "pairs": 20}))


if __name__ == "__main__":
    main()
