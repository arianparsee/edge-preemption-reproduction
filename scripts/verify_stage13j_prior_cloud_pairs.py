"""Validate the 20 cloud pairs from Stage 13-H and Stage 13-I."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

from edge_reproduction.experiments.pipe_normal_full import POLICY_NAMES, load_full_config


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_full_config(args.config)
    runs = _mapping(config, "config")["runs"]
    if not isinstance(runs, list):
        raise TypeError("runs must be a list")
    seeds = []
    for item in runs[:5]:
        value = _mapping(item, "run")["workload_seed"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("workload_seed must be an integer")
        seeds.append(value)
    config_hash = _hash(args.config)
    records = []
    for seed in seeds:
        workload_hashes: set[str] = set()
        for policy in POLICY_NAMES:
            root = args.root / "results/raw/stage13f/PIPE-NORMAL" / f"seed-{seed}" / policy
            result_path, workload_path, manifest_path = (
                root / name for name in ("result.json", "workload.json", "manifest.json")
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            workload_hash = _hash(workload_path)
            if manifest["config_sha256"] != config_hash:
                raise ValueError(f"config mismatch: {seed}/{policy}")
            if manifest["result_sha256"] != _hash(result_path):
                raise ValueError(f"result hash mismatch: {seed}/{policy}")
            if manifest["workload_sha256"] != workload_hash:
                raise ValueError(f"workload hash mismatch: {seed}/{policy}")
            if result["workload_seed"] != seed or result["policy"] != policy:
                raise ValueError(f"identity mismatch: {seed}/{policy}")
            outcome = result["run"]["outcome"]
            completed, rejected = (
                set(outcome["completed_task_ids"]),
                set(outcome["rejected_task_ids"]),
            )
            preempted, all_ids = (
                set(outcome["ever_preempted_task_ids"]),
                set(result["run"]["final_task_states"]),
            )
            if completed & rejected or completed | rejected != all_ids or not preempted <= rejected:
                raise ValueError(f"outcome invariant failed: {seed}/{policy}")
            workload_hashes.add(workload_hash)
            records.append(
                {
                    "workload_seed": seed,
                    "policy": policy,
                    "result_sha256": manifest["result_sha256"],
                    "workload_sha256": workload_hash,
                }
            )
        if len(workload_hashes) != 1:
            raise ValueError(f"shared workload mismatch: {seed}")
    if len(records) != 20:
        raise ValueError("exactly 20 prior pairs are required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    payload = {"status": "20_of_20_prior_cloud_pairs_verified", "pairs": records}
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
