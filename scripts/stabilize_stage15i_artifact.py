"""Validate and inventory the completed Stage 15-I aggregation-only artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path.name}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _validate_download_report(
    path: Path, *, run_id: int, artifact_count: int, pinned: bool | None = None
) -> dict[str, Any]:
    report = _object(path)
    if report.get("run_id") != run_id or report.get("artifact_count") != artifact_count:
        raise ValueError(f"download report cardinality/provenance mismatch: {path.name}")
    if report.get("token_recorded") is not False:
        raise ValueError(f"download report token safety gate failed: {path.name}")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != artifact_count:
        raise ValueError(f"download report artifact list mismatch: {path.name}")
    if any(item.get("github_digest_checked") is not True for item in artifacts):
        raise ValueError(f"GitHub digest was not checked: {path.name}")
    if pinned is not None and report.get("pinned_archive_sha256_enforced") is not pinned:
        raise ValueError(f"archive pin status mismatch: {path.name}")
    return report


def _validate_delivery(root: Path) -> int:
    manifest = root / "stage15i_delivery.sha256"
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        name = Path(relative).name
        if name in entries:
            raise ValueError("duplicate Stage 15-I delivery entry")
        entries[name] = digest
    expected = {path.name for path in root.iterdir() if path.is_file() and path != manifest}
    if set(entries) != expected:
        raise ValueError("Stage 15-I delivery manifest is incomplete or has extra files")
    for name, digest in entries.items():
        if _sha256(root / name) != digest:
            raise ValueError(f"Stage 15-I delivery checksum mismatch: {name}")
    return len(entries)


def _validate_inner_manifest(root: Path) -> int:
    manifest = _object(root / "checksum_manifest.json")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise TypeError("Stage 15-H checksum manifest has no file list")
    for item in files:
        path = root / str(item["name"])
        if not path.is_file() or path.stat().st_size != int(item["bytes"]):
            raise ValueError(f"Stage 15-H manifest size mismatch: {path.name}")
        if _sha256(path) != str(item["sha256"]):
            raise ValueError(f"Stage 15-H manifest checksum mismatch: {path.name}")
    return len(files)


def stabilize(
    *, artifact_root: Path,
    download_report: Path,
    run_id: int,
    inventory_csv: Path,
    stable_manifest: Path,
) -> dict[str, object]:
    """Fail closed on provenance, completeness, checksums, or schema mismatch."""

    if inventory_csv.exists() or stable_manifest.exists():
        raise FileExistsError("refusing to overwrite stable Stage 15-I inventory")
    delivery_count = _validate_delivery(artifact_root)
    inner_count = _validate_inner_manifest(artifact_root)
    cloud_download = _validate_download_report(
        download_report, run_id=run_id, artifact_count=1
    )
    if cloud_download["artifacts"][0]["name"] != f"stage15i-stage15h-aggregation-only-{run_id}":
        raise ValueError("downloaded artifact name differs from approved Stage 15-I run")

    completeness = _object(artifact_root / "completeness_report.json")
    expected_completeness = {
        "status": "complete_and_valid",
        "baseline_pairs": 120,
        "repair_pairs": 120,
        "workloads": 30,
        "new_pairs": 100,
        "reused_pairs": 20,
        "all_replays_exact": True,
        "baseline_recomputed": False,
        "figure_6_status": "not_reproduced",
    }
    if any(completeness.get(key) != value for key, value in expected_completeness.items()):
        raise ValueError("Stage 15-I completeness or scientific guard failed")

    recovery = _object(artifact_root / "recovery-report.json")
    lifecycle_hash = "fac98f37a6faf23bdb91387498ed11008611adef29b383d24f1c866f8504610a"
    if (
        recovery.get("status") != "complete_and_checksum_matched"
        or recovery.get("baseline_pair_count") != 120
        or recovery.get("lifecycle_csv_sha256") != lifecycle_hash
        or recovery.get("simulation_or_policy_executed") is not False
    ):
        raise ValueError("baseline lifecycle recovery validation failed")

    current = _validate_download_report(
        artifact_root / "current-pairs-download-report.json",
        run_id=32474360245,
        artifact_count=100,
        pinned=False,
    )
    reused = _validate_download_report(
        artifact_root / "reuse-bundle-download-report.json",
        run_id=32474360245,
        artifact_count=1,
        pinned=True,
    )
    if reused["artifacts"][0]["archive_sha256"] != (
        "4c84c1a479f5fdc6d89c4c573e9a6d690d299cec5d473771bb9ab9a9af6bd4b6"
    ):
        raise ValueError("20-pair repair reuse bundle digest mismatch")
    prior = _validate_download_report(
        artifact_root / "baseline-prior-20-download-report.json",
        run_id=31644121025,
        artifact_count=1,
        pinned=True,
    )
    if prior["artifacts"][0]["archive_sha256"] != (
        "e17e18cd10760a6f004424905e9dcfd617b950aa334d0498f11dfe722cfad179"
    ):
        raise ValueError("20-pair baseline checkpoint digest mismatch")
    for batch in range(1, 6):
        _validate_download_report(
            artifact_root / f"baseline-batch-{batch}-download-report.json",
            run_id=31644121025,
            artifact_count=20,
            pinned=False,
        )

    if len(_rows(artifact_root / "pair_inventory.csv")) != 120:
        raise ValueError("repair pair inventory is not 120/120")
    if len(_rows(artifact_root / "repair_results_30_workloads.csv")) != 120:
        raise ValueError("repair result table is not 120/120")
    if len(_rows(artifact_root / "baseline_reuse_inventory.csv")) != 120:
        raise ValueError("baseline reuse inventory is not 120/120")

    files = sorted(
        path
        for path in artifact_root.parent.rglob("*")
        if path.is_file() and path not in {inventory_csv, stable_manifest}
    )
    inventory = [
        {
            "path": path.relative_to(artifact_root.parent).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in files
    ]
    inventory_csv.parent.mkdir(parents=True, exist_ok=True)
    with inventory_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("path", "bytes", "sha256"))
        writer.writeheader()
        writer.writerows(inventory)

    report: dict[str, object] = {
        "schema_version": "stage15i-stable-manifest-v1",
        "classification": "[آزمون کمکی]",
        "run_id": run_id,
        "status": "validated_and_stabilized",
        "workload_or_policy_executed": False,
        "repair_pairs": 120,
        "baseline_pairs": 120,
        "workloads": 30,
        "all_replays_exact": True,
        "figure_6_status": "not_reproduced",
        "downloaded_archive_sha256": cloud_download["artifacts"][0]["archive_sha256"],
        "downloaded_file_count": len(files),
        "downloaded_total_bytes": sum(path.stat().st_size for path in files),
        "delivery_manifest_entries": delivery_count,
        "inner_checksum_entries": inner_count,
        "lifecycle_csv_sha256": lifecycle_hash,
        "checks": {
            "github_archive_digest": "passed",
            "delivery_sha256": "passed",
            "inner_sha256": "passed",
            "repair_completeness": "passed_120_of_120",
            "baseline_reuse": "passed_120_of_120",
            "replay_gate": "passed_120_of_120",
            "source_pair_download": f"passed_{current['artifact_count']}_of_100",
        },
        "inventory_csv_sha256": _sha256(inventory_csv),
        "files": inventory,
    }
    stable_manifest.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--download-report", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--inventory-csv", type=Path, required=True)
    parser.add_argument("--stable-manifest", type=Path, required=True)
    args = parser.parse_args()
    report = stabilize(
        artifact_root=args.artifact_root.resolve(),
        download_report=args.download_report.resolve(),
        run_id=args.run_id,
        inventory_csv=args.inventory_csv.resolve(),
        stable_manifest=args.stable_manifest.resolve(),
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
