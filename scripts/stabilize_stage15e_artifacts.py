"""Validate and inventory an already-completed Stage 15-E cloud run.

This script never invokes the simulator. It validates the sixteen downloaded
pair artifacts, reconstructs the approved twenty-pair summary using the four
reused Stage 15-D.1 pairs, and writes a fail-closed SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from merge_stage15e_validation import merge
from validate_stage15e_public_pair import validate

PAIR_EXCLUSIONS = {"stage15e-summary.json", "stage15e-inventory.json"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _stringify_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    return [{key: str(value) for key, value in row.items()} for row in rows]


def _locate_merged(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name}; found {len(matches)}")
    return matches[0]


def stabilize(
    *,
    artifact_root: Path,
    seed_one_fixture: Path,
    baseline_fixture: Path,
    run_id: int,
    output_manifest: Path,
) -> dict[str, object]:
    """Validate existing artifacts and write a non-overwriting inventory."""

    if output_manifest.exists():
        raise FileExistsError(f"refusing to overwrite manifest: {output_manifest}")
    pair_paths = sorted(
        path
        for path in artifact_root.rglob("stage15e-*.json")
        if path.name not in PAIR_EXCLUSIONS
    )
    if len(pair_paths) != 16:
        raise ValueError(f"expected 16 new pair JSON files; found {len(pair_paths)}")
    for path in pair_paths:
        validate(path)

    reconstructed = merge(pair_paths, seed_one_fixture)
    cloud_summary_path = _locate_merged(artifact_root, "stage15e-summary.json")
    cloud_per_seed_path = _locate_merged(artifact_root, "stage15e-per-seed.csv")
    cloud_aggregate_path = _locate_merged(artifact_root, "stage15e-aggregate.csv")
    cloud_inventory_path = _locate_merged(artifact_root, "stage15e-inventory.json")

    if _json_object(cloud_summary_path) != reconstructed:
        raise ValueError("downloaded summary differs from local no-recompute merge")
    expected_rows = _stringify_rows(reconstructed["rows"])  # type: ignore[arg-type]
    expected_aggregate = _stringify_rows(reconstructed["aggregate"])  # type: ignore[arg-type]
    if _csv_rows(cloud_per_seed_path) != expected_rows:
        raise ValueError("downloaded per-seed CSV differs from reconstructed rows")
    if _csv_rows(cloud_aggregate_path) != expected_aggregate:
        raise ValueError("downloaded aggregate CSV differs from reconstructed rows")

    cloud_inventory = _json_object(cloud_inventory_path)
    cloud_hashes = {
        str(item["name"]): str(item["sha256"])
        for item in cloud_inventory.get("files", [])
    }
    for path in (cloud_summary_path, cloud_per_seed_path, cloud_aggregate_path):
        if cloud_hashes.get(path.name) != _sha256(path):
            raise ValueError(f"cloud inventory SHA-256 mismatch: {path.name}")

    files = sorted(path for path in artifact_root.rglob("*") if path.is_file())
    inventory = [
        {
            "path": path.relative_to(artifact_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in files
    ]
    report: dict[str, object] = {
        "schema_version": "stage15e-stable-manifest-v1",
        "run_id": run_id,
        "status": "validated_20_of_20",
        "simulation_recomputed": False,
        "new_pair_count": 16,
        "reused_pair_count": 4,
        "matrix_pair_count": 20,
        "seed_count": 5,
        "all_replays_exact": reconstructed["all_replays_exact"],
        "baseline_rng_option": reconstructed["baseline_rng_option"],
        "downloaded_file_count": len(files),
        "downloaded_total_bytes": sum(path.stat().st_size for path in files),
        "seed_one_fixture": {
            "path": seed_one_fixture.as_posix(),
            "sha256": _sha256(seed_one_fixture),
        },
        "baseline_fixture": {
            "path": baseline_fixture.as_posix(),
            "sha256": _sha256(baseline_fixture),
        },
        "checks": {
            "public_pair_validation": "passed_16_of_16",
            "matrix_completeness": "passed_20_of_20",
            "summary_semantic_match": "passed",
            "per_seed_csv_match": "passed",
            "aggregate_csv_match": "passed",
            "cloud_inventory_sha256": "passed",
        },
        "files": inventory,
    }
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--seed-one-fixture", type=Path, required=True)
    parser.add_argument("--baseline-fixture", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    report = stabilize(
        artifact_root=args.artifact_root.resolve(),
        seed_one_fixture=args.seed_one_fixture.resolve(),
        baseline_fixture=args.baseline_fixture.resolve(),
        run_id=args.run_id,
        output_manifest=args.output_manifest.resolve(),
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "files": report["downloaded_file_count"],
                "bytes": report["downloaded_total_bytes"],
            }
        )
    )


if __name__ == "__main__":
    main()
