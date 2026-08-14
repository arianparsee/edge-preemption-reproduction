"""Build the pinned 20-pair reuse manifest from already-downloaded artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(path)
    return value


def build(stage15d_root: Path, stage15e_root: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path in stage15d_root.rglob("stage15d-*.json"):
        data = _load(path)
        if data.get("variant") not in ("initial_population_repair", "offspring_repair"):
            continue
        entries.append(
            {
                "workload_seed": str(data["workload_seed"]),
                "policy": data["policy"],
                "variant": data["variant"],
                "policy_seed": str(data["policy_seed"]),
                "source_run_id": 31716969817,
                "artifact_pattern": f"stage15d-{data['variant']}-{data['policy']}-31716969817",
                "file_sha256": _hash(path),
            }
        )
    for path in stage15e_root.rglob("stage15e-*.json"):
        data = _load(path)
        if data.get("schema_version") != "stage15e-counterfactual-pair-v1":
            continue
        entries.append(
            {
                "workload_seed": str(data["workload_seed"]),
                "policy": data["policy"],
                "variant": data["variant"],
                "policy_seed": str(data["policy_seed"]),
                "source_run_id": 31729227438,
                "artifact_pattern": (
                    f"stage15e-{data['workload_seed']}-{data['variant']}-{data['policy']}-31729227438"
                ),
                "file_sha256": _hash(path),
            }
        )
    if len(entries) != 20:
        raise ValueError(f"expected 20 reuse pairs; found {len(entries)}")
    entries.sort(
        key=lambda row: (int(str(row["workload_seed"])), str(row["variant"]), str(row["policy"]))
    )
    return {
        "schema_version": "stage15h-pinned-repair-reuse-v1",
        "source_stages": ["Stage 15-D.1", "Stage 15-E"],
        "validated_pair_count": 20,
        "simulation_recomputed": False,
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage15d-root", type=Path, required=True)
    parser.add_argument("--stage15e-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(
        json.dumps(build(args.stage15d_root, args.stage15e_root), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
