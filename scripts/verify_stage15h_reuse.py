"""Verify pinned Stage-15H baseline/repair reuse without executing simulations."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(path)
    return value


def verify_repairs(
    manifest_path: Path, roots: list[Path], copy_to: Path | None = None
) -> list[dict[str, object]]:
    manifest = _load(manifest_path)
    files = [path for root in roots for path in root.rglob("*.json")]
    by_hash = {_hash(path): path for path in files}
    rows: list[dict[str, object]] = []
    for entry in manifest["entries"]:
        expected_hash = str(entry["file_sha256"])
        path = by_hash.get(expected_hash)
        if path is None:
            raise ValueError(f"missing pinned repair artifact: {entry['artifact_pattern']}")
        data = _load(path)
        for field in ("workload_seed", "policy", "variant", "policy_seed"):
            if str(data[field]) != str(entry[field]):
                raise ValueError(f"repair reuse {field} mismatch")
        if data.get("baseline_recomputed") is not False or data.get("replay_exact") is not True:
            raise ValueError("repair reuse scientific gate failed")
        rows.append({**entry, "validation": "passed"})
        if copy_to is not None:
            copy_to.mkdir(parents=True, exist_ok=True)
            target = copy_to / (
                f"reuse-{entry['workload_seed']}-{entry['variant']}-{entry['policy']}.json"
            )
            shutil.copyfile(path, target)
    if len(rows) != 20:
        raise ValueError("repair reuse matrix is not 20/20")
    return rows


def verify_baselines(manifest_path: Path, assembled_root: Path) -> list[dict[str, object]]:
    manifest = _load(manifest_path)
    result_files = list(assembled_root.rglob("result.json"))
    workload_files = list(assembled_root.rglob("workload.json"))
    result_hashes = {_hash(path) for path in result_files}
    workload_hashes = {_hash(path) for path in workload_files}
    rows: list[dict[str, object]] = []
    for entry in manifest["entries"]:
        if (
            entry["result_sha256"] not in result_hashes
            or entry["workload_sha256"] not in workload_hashes
        ):
            raise ValueError("pinned baseline source checksum is missing")
        rows.append({**entry, "validation": "passed"})
    if len(rows) != 120:
        raise ValueError("baseline reuse matrix is not 120/120")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-manifest", type=Path)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--repair-manifest", type=Path, required=True)
    parser.add_argument("--repair-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--copy-repairs-to", type=Path)
    args = parser.parse_args()
    repairs = verify_repairs(args.repair_manifest, args.repair_root, args.copy_repairs_to)
    baselines = []
    if args.baseline_manifest and args.baseline_root:
        baselines = verify_baselines(args.baseline_manifest, args.baseline_root)
    report = {
        "schema_version": "stage15h-reuse-validation-v1",
        "simulation_recomputed": False,
        "baseline_pair_count": len(baselines),
        "repair_pair_count": len(repairs),
        "status": "validated",
        "repairs": repairs,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "validated", "baselines": len(baselines), "repairs": len(repairs)}))


if __name__ == "__main__":
    main()
