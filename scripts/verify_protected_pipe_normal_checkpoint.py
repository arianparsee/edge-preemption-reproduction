"""Verify the protected Stage-13H/I checkpoint and its no-recompute resume path."""

from __future__ import annotations

import argparse
import csv
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from edge_reproduction.experiments.pipe_normal_full import POLICY_NAMES, run_full_pair

STAGE_SEEDS = {
    "stage13h": (541501192080118187,),
    "stage13i": (
        2074092324964443463,
        2218754797665862270,
        2997476077322633071,
        3782887846963969634,
    ),
}
CONFIG = Path("configs/experiments/pipe_normal_full_stage13f.json")
INVENTORY_NAME = "inventory.csv"
REPORT_NAME = "verification_report.json"


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _payload_hashes(root: Path) -> dict[str, tuple[int, str]]:
    excluded = {INVENTORY_NAME, REPORT_NAME}
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, _file_sha256(path))
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in excluded
    }


def _validate_pair(
    *, stage_root: Path, seed: int, policy: str, config_sha256: str
) -> dict[str, object]:
    pair_root = (
        stage_root
        / "results/raw/stage13f/PIPE-NORMAL"
        / f"seed-{seed}"
        / policy
    )
    required = {
        name: pair_root / name
        for name in ("manifest.json", "result.json", "workload.json")
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"incomplete pair {seed}/{policy}: {missing}")

    manifest = _load_object(required["manifest.json"])
    result = _load_object(required["result.json"])
    if manifest.get("config_sha256") != config_sha256:
        raise ValueError(f"config hash mismatch: {seed}/{policy}")
    if manifest.get("result_sha256") != _file_sha256(required["result.json"]):
        raise ValueError(f"result hash mismatch: {seed}/{policy}")
    workload_sha256 = _file_sha256(required["workload.json"])
    if manifest.get("workload_sha256") != workload_sha256:
        raise ValueError(f"workload hash mismatch: {seed}/{policy}")

    for name, expected in (
        ("workload_seed", seed),
        ("policy", policy),
        ("policy_seed", manifest.get("policy_seed")),
    ):
        if result.get(name) != expected:
            raise ValueError(f"result {name} mismatch: {seed}/{policy}")
    if result.get("workload_sha256") != workload_sha256:
        raise ValueError(f"result workload hash mismatch: {seed}/{policy}")

    run = result.get("run")
    if not isinstance(run, dict):
        raise TypeError(f"missing run object: {seed}/{policy}")
    outcome = run.get("outcome")
    states = run.get("final_task_states")
    if not isinstance(outcome, dict) or not isinstance(states, dict):
        raise TypeError(f"missing outcome/final states: {seed}/{policy}")
    completed = set(outcome.get("completed_task_ids", []))
    rejected = set(outcome.get("rejected_task_ids", []))
    preempted = set(outcome.get("ever_preempted_task_ids", []))
    all_tasks = set(states)
    if completed & rejected or completed | rejected != all_tasks:
        raise ValueError(f"outcome partition invariant failed: {seed}/{policy}")
    if not preempted <= rejected:
        raise ValueError(f"preempted subset invariant failed: {seed}/{policy}")
    if len(completed) != outcome.get("completed_jobs"):
        raise ValueError(f"completed count mismatch: {seed}/{policy}")
    if len(rejected) != outcome.get("rejected_jobs"):
        raise ValueError(f"rejected count mismatch: {seed}/{policy}")

    return {
        "stage": stage_root.name,
        "workload_seed": seed,
        "policy": policy,
        "policy_seed": manifest["policy_seed"],
        "task_count": len(all_tasks),
        "workload_sha256": workload_sha256,
        "result_sha256": manifest["result_sha256"],
        "completed_jobs": len(completed),
        "rejected_jobs": len(rejected),
        "ever_preempted_jobs": len(preempted),
    }


def _write_inventory(root: Path) -> tuple[int, int, str]:
    records: list[dict[str, str | int]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == INVENTORY_NAME:
            continue
        records.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    inventory = root / INVENTORY_NAME
    with inventory.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("relative_path", "size_bytes", "sha256"))
        writer.writeheader()
        writer.writerows(records)
    total_bytes = sum(
        size for row in records if isinstance(size := row["size_bytes"], int)
    )
    return len(records), total_bytes, _file_sha256(inventory)


def verify(root: Path) -> dict[str, object]:
    before = _payload_hashes(root)
    pair_records: list[dict[str, object]] = []
    resume_records: list[dict[str, object]] = []
    workload_hashes: dict[int, set[str]] = {}
    for stage, seeds in STAGE_SEEDS.items():
        stage_root = root / stage
        config_path = stage_root / CONFIG
        config_sha256 = _file_sha256(config_path)
        for seed in seeds:
            for policy in POLICY_NAMES:
                record = _validate_pair(
                    stage_root=stage_root,
                    seed=seed,
                    policy=policy,
                    config_sha256=config_sha256,
                )
                pair_records.append(record)
                workload_hashes.setdefault(seed, set()).add(str(record["workload_sha256"]))
                outcome = run_full_pair(
                    CONFIG,
                    workload_seed=seed,
                    policy_name=policy,
                    project_root=stage_root,
                    resume=True,
                )
                if outcome.status != "skipped_existing_verified":
                    raise ValueError(f"resume recomputed pair: {seed}/{policy}")
                resume_records.append(
                    {
                        "stage": stage,
                        "workload_seed": seed,
                        "policy": policy,
                        "status": outcome.status,
                    }
                )

    if len(pair_records) != 20 or len(resume_records) != 20:
        raise ValueError("protected checkpoint must contain exactly 20 pairs")
    if any(len(hashes) != 1 for hashes in workload_hashes.values()):
        raise ValueError("policies do not share one workload hash per seed")
    after = _payload_hashes(root)
    if before != after:
        raise ValueError("resume changed protected payload files")

    report: dict[str, object] = {
        "schema_version": "stage13-protected-checkpoint-verification-v1",
        "baseline": "arXiv:2403.15665v2_2024",
        "protected_pair_count": len(pair_records),
        "protected_workload_count": len(workload_hashes),
        "payload_unchanged_by_resume": True,
        "resume_status": "20_of_20_skipped_existing_verified",
        "full_30_repeat_run_completed": False,
        "figure_6_reproduced": False,
        "pairs": pair_records,
        "resume": resume_records,
    }
    report_path = root / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    count, total_bytes, inventory_sha256 = _write_inventory(root)
    report["inventory"] = {
        "listed_file_count": count,
        "listed_total_bytes": total_bytes,
        "inventory_sha256": inventory_sha256,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.root.resolve())
    print(json.dumps(report["inventory"], sort_keys=True))
    print(report["resume_status"])


if __name__ == "__main__":
    main()
