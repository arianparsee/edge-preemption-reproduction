"""Verify exactly sixteen Stage-13I cloud pairs and write one checkpoint summary."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from statistics import fmean, stdev
from typing import cast

POLICIES = (
    "knapsack_greedy_retention",
    "knapsack_greedy_preemption",
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
EXPECTED_WORKLOAD_SEEDS = (
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)


def file_sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of one artifact."""

    return sha256(path.read_bytes()).hexdigest()


def _object(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _array(value: object, *, name: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{name} must be an array")
    return cast(list[object], value)


def _integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a nonempty string")
    return value


def _load(path: Path) -> dict[str, object]:
    return _object(json.loads(path.read_text(encoding="utf-8")), name=str(path))


def _validate_config(config_path: Path) -> dict[int, dict[str, int]]:
    config = _load(config_path)
    if config.get("schema_version") != "stage13f-pipe-normal-full-v1":
        raise ValueError("unexpected full config schema")
    runs = _array(config.get("runs"), name="config.runs")
    selected: dict[int, dict[str, int]] = {}
    for raw_run in runs:
        run = _object(raw_run, name="run descriptor")
        seed = _integer(run.get("workload_seed"), name="workload_seed")
        if seed not in EXPECTED_WORKLOAD_SEEDS:
            continue
        raw_policy_seeds = _object(run.get("policy_seeds"), name="policy_seeds")
        if set(raw_policy_seeds) != set(POLICIES):
            raise ValueError("policy seed mapping does not name exactly four policies")
        selected[seed] = {
            policy: _integer(raw_policy_seeds[policy], name=f"policy_seeds.{policy}")
            for policy in POLICIES
        }
    if tuple(selected) != EXPECTED_WORKLOAD_SEEDS:
        raise ValueError("config does not contain exactly the four Stage-13I seeds")
    return selected


def _timing(path: Path) -> float:
    seconds = float(path.read_text(encoding="utf-8").strip())
    if seconds <= 0.0:
        raise ValueError(f"non-positive timing: {path}")
    return seconds


def record_checkpoint(*, root: Path, config_path: Path) -> dict[str, object]:
    """Validate all 16 pairs and return a JSON-compatible auxiliary summary."""

    materialized_policy_seeds = _validate_config(config_path)
    rows: list[dict[str, object]] = []
    workload_rows: list[dict[str, object]] = []
    total_artifact_bytes = 0
    all_wall_seconds: list[float] = []

    for workload_seed in EXPECTED_WORKLOAD_SEEDS:
        workload_hashes: set[str] = set()
        task_counts: set[int] = set()
        seed_rows: list[dict[str, object]] = []
        for policy in POLICIES:
            directory = (
                root
                / "results"
                / "raw"
                / "stage13f"
                / "PIPE-NORMAL"
                / f"seed-{workload_seed}"
                / policy
            )
            result_path = directory / "result.json"
            workload_path = directory / "workload.json"
            manifest_path = directory / "manifest.json"
            timing_path = root / f"timing-{workload_seed}-{policy}.txt"
            for path in (result_path, workload_path, manifest_path, timing_path):
                if not path.is_file():
                    raise FileNotFoundError(f"missing Stage-13I artifact: {path}")

            result = _load(result_path)
            workload = _load(workload_path)
            manifest = _load(manifest_path)
            if manifest.get("result_sha256") != file_sha256(result_path):
                raise ValueError(f"result hash mismatch: {workload_seed}/{policy}")
            workload_hash = file_sha256(workload_path)
            if manifest.get("workload_sha256") != workload_hash:
                raise ValueError(f"workload hash mismatch: {workload_seed}/{policy}")
            if result.get("workload_seed") != workload_seed or result.get("policy") != policy:
                raise ValueError(f"result identity mismatch: {workload_seed}/{policy}")
            expected_policy_seed = materialized_policy_seeds[workload_seed][policy]
            if result.get("policy_seed") != expected_policy_seed:
                raise ValueError(f"policy seed mismatch: {workload_seed}/{policy}")

            run = _object(result.get("run"), name="result.run")
            outcome = _object(run.get("outcome"), name="run.outcome")
            metadata = _object(run.get("metadata"), name="run.metadata")
            completed_ids = set(
                _text(item, name="completed task id")
                for item in _array(outcome.get("completed_task_ids"), name="completed ids")
            )
            rejected_ids = set(
                _text(item, name="rejected task id")
                for item in _array(outcome.get("rejected_task_ids"), name="rejected ids")
            )
            preempted_ids = set(
                _text(item, name="preempted task id")
                for item in _array(
                    outcome.get("ever_preempted_task_ids"), name="preempted ids"
                )
            )
            task_ids = {
                _text(_object(item, name="workload task").get("task_id"), name="task_id")
                for item in _array(workload.get("tasks"), name="workload.tasks")
            }
            if completed_ids & rejected_ids or completed_ids | rejected_ids != task_ids:
                raise ValueError(f"outcome partition failed: {workload_seed}/{policy}")
            if not preempted_ids <= rejected_ids:
                raise ValueError(f"preempted subset failed: {workload_seed}/{policy}")

            wall_seconds = _timing(timing_path)
            all_wall_seconds.append(wall_seconds)
            workload_hashes.add(workload_hash)
            task_counts.add(len(task_ids))
            pair_bytes = sum(
                path.stat().st_size for path in (result_path, workload_path, manifest_path)
            )
            total_artifact_bytes += pair_bytes + timing_path.stat().st_size
            row = {
                "workload_seed": workload_seed,
                "policy": policy,
                "policy_seed": expected_policy_seed,
                "wall_seconds": wall_seconds,
                "completed_jobs": _integer(
                    outcome.get("completed_jobs"), name="completed_jobs"
                ),
                "rejected_jobs": _integer(
                    outcome.get("rejected_jobs"), name="rejected_jobs"
                ),
                "ever_preempted_jobs": _integer(
                    outcome.get("ever_preempted_jobs"), name="ever_preempted_jobs"
                ),
                "completed_utility": _number(
                    outcome.get("completed_utility"), name="completed_utility"
                ),
                "rejected_utility": _number(
                    outcome.get("rejected_utility"), name="rejected_utility"
                ),
                "ever_preempted_utility": _number(
                    outcome.get("ever_preempted_utility"), name="ever_preempted_utility"
                ),
                "raw_auction_rejection_count": _integer(
                    outcome.get("raw_auction_rejection_count"),
                    name="raw_auction_rejection_count",
                ),
                "zero_fitness_repairs": int(
                    _text(
                        metadata.get("ga.zero_fitness_feasibility_repairs"),
                        name="zero_fitness_repairs",
                    )
                ),
                "equal_minimum_price_ties": int(
                    _text(
                        metadata.get("client.equal_minimum_price_ties"),
                        name="equal_minimum_price_ties",
                    )
                ),
                "result_sha256": _text(
                    manifest.get("result_sha256"), name="result_sha256"
                ),
                "pair_artifact_bytes": pair_bytes,
            }
            rows.append(row)
            seed_rows.append(row)

        if len(workload_hashes) != 1 or len(task_counts) != 1:
            raise ValueError(f"policies did not share one workload: {workload_seed}")
        seed_times = [_number(row["wall_seconds"], name="wall_seconds") for row in seed_rows]
        workload_rows.append(
            {
                "workload_seed": workload_seed,
                "task_count": next(iter(task_counts)),
                "shared_workload_sha256": next(iter(workload_hashes)),
                "parallel_policy_wall_seconds": max(seed_times),
                "serial_equivalent_wall_seconds": sum(seed_times),
            }
        )

    parallel_times = [
        _number(row["parallel_policy_wall_seconds"], name="parallel wall seconds")
        for row in workload_rows
    ]
    if len(rows) != 16:
        raise ValueError("Stage-13I checkpoint must contain exactly 16 pairs")
    return {
        "schema_version": "stage13i-four-workload-cloud-checkpoint-v1",
        "scientific_label": "auxiliary_checkpoint_not_30_repeat_result",
        "baseline": "arXiv:2403.15665v2_2024",
        "checkpoint_workload_count": 4,
        "checkpoint_pair_count": 16,
        "cumulative_workloads_executed_including_stage13h": "5/30",
        "cumulative_pairs_executed_including_stage13h": "20/120",
        "full_30_repeat_run_completed": False,
        "scientific_aggregation_performed": False,
        "figure_6_reproduced": False,
        "total_checkpoint_artifact_bytes": total_artifact_bytes,
        "timing_diagnostics": {
            "status": "auxiliary_not_paper_runtime",
            "parallel_policy_wall_seconds_by_workload": parallel_times,
            "parallel_policy_wall_seconds_mean": fmean(parallel_times),
            "parallel_policy_wall_seconds_sample_stdev": stdev(parallel_times),
            "parallel_policy_wall_seconds_min": min(parallel_times),
            "parallel_policy_wall_seconds_max": max(parallel_times),
            "serial_equivalent_seconds_all_16_pairs": sum(all_wall_seconds),
        },
        "workloads": workload_rows,
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite checkpoint summary: {args.output}")
    summary = record_checkpoint(root=args.root, config_path=args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "recorded", "output": args.output.as_posix()}))


if __name__ == "__main__":
    main()
