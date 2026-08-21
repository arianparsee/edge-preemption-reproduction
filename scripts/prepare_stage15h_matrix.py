"""Create a resume-safe matrix containing only missing/invalid Stage-15H pairs."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import cast

from validate_stage15h_public_pair import validate

from edge_reproduction.experiments.pipe_normal_full import (
    load_full_config,
)

POLICIES = ("pipeline_double_knapsack_retention", "pipeline_double_knapsack_preemption")
VARIANTS = ("initial_population_repair", "offspring_repair")


def build(config_path: Path, resume_root: Path | None, copy_to: Path) -> dict[str, object]:
    config = load_full_config(config_path)
    runs = cast(list[dict[str, object]], config["runs"])
    seeds = [str(run["workload_seed"]) for run in runs]
    if len(seeds) != 30:
        raise ValueError("ASSUMP-033 seed list must contain exactly 30 workloads")
    expected = {
        (seed, variant, policy) for seed in seeds[5:] for variant in VARIANTS for policy in POLICIES
    }
    valid: dict[tuple[str, str, str], Path] = {}
    if resume_root is not None and resume_root.exists():
        for path in resume_root.rglob("stage15h-*.json"):
            try:
                data = validate(path)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
            key = (str(data["workload_seed"]), str(data["variant"]), str(data["policy"]))
            if key in expected:
                if key in valid:
                    raise ValueError("duplicate valid pair in resume source")
                valid[key] = path
    copy_to.mkdir(parents=True, exist_ok=True)
    for (seed, variant, policy), path in valid.items():
        shutil.copyfile(path, copy_to / f"stage15h-{seed}-{variant}-{policy}.json")
    missing = sorted(expected - set(valid), key=lambda key: (seeds.index(key[0]), key[1], key[2]))
    batch_by_seed = {
        seed: ((ordinal - 5) // 5) + 1
        for ordinal, seed in enumerate(seeds[5:], start=5)
    }
    return {
        "include": [
            {
                "workload_seed": seed,
                "variant": variant,
                "policy": policy,
                "batch_id": batch_by_seed[seed],
            }
            for seed, variant, policy in missing
        ],
        "expected_pair_count": 100,
        "resumed_valid_pair_count": len(valid),
        "new_pair_count": len(missing),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resume-root", type=Path)
    parser.add_argument("--copy-to", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.config, args.resume_root, args.copy_to)
    args.output.write_text(
        json.dumps({"include": report["include"]}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "include"}))


if __name__ == "__main__":
    main()
