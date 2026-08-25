"""Materialize Stage 15-H baseline lifecycle data from pinned prior results only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from analyze_stage15a_dk_weakness import lifecycle_row


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path.name}")
    return value


def materialize(
    *,
    baseline_root: Path,
    manifest_path: Path,
    output_path: Path,
    report_path: Path,
    expected_output_sha256: str,
) -> dict[str, object]:
    """Validate immutable baselines and derive the lifecycle CSV without simulation."""

    if output_path.exists() or report_path.exists():
        raise FileExistsError("refusing to overwrite lifecycle recovery output")
    manifest = _load_object(manifest_path)
    entries = manifest.get("entries")
    expected_count = manifest.get("validated_pair_count")
    if not isinstance(entries, list) or expected_count != 120 or len(entries) != 120:
        raise ValueError("baseline manifest is not the approved 120-pair matrix")

    result_files = sorted(baseline_root.rglob("result.json"))
    if len(result_files) != 120:
        raise ValueError(f"expected exactly 120 baseline results, found {len(result_files)}")
    by_hash: dict[str, list[Path]] = {}
    for path in result_files:
        by_hash.setdefault(_sha256(path), []).append(path)

    rows = []
    identities: set[tuple[str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise TypeError("baseline manifest entries must be objects")
        result_hash = str(entry["result_sha256"])
        matches = by_hash.get(result_hash, [])
        if len(matches) != 1:
            raise ValueError("a pinned baseline result is missing or duplicated")
        payload = _load_object(matches[0])
        for field in ("workload_seed", "policy", "policy_seed", "workload_sha256"):
            if str(payload.get(field)) != str(entry[field]):
                raise ValueError(f"baseline {field} differs from pinned manifest")
        identity = (str(entry["workload_seed"]), str(entry["policy"]))
        if identity in identities:
            raise ValueError("duplicate workload-policy identity in baseline manifest")
        identities.add(identity)
        rows.append(lifecycle_row(payload))

    if set(by_hash) != {str(entry["result_sha256"]) for entry in entries}:
        raise ValueError("baseline source contains an unapproved result checksum")
    # Preserve the original Stage 15-A path-lexicographic ordering so the
    # checksum is platform-independent and directly comparable to the trusted
    # derived artifact.
    rows.sort(key=lambda row: (str(row.workload_seed), row.policy))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]))
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)

    output_hash = _sha256(output_path)
    if output_hash != expected_output_sha256:
        output_path.unlink()
        raise ValueError("derived lifecycle CSV differs from the pinned Stage 15-A checksum")

    report = {
        "schema_version": "stage15i-baseline-lifecycle-recovery-v1",
        "classification": "[آزمون کمکی]",
        "source_stage": "Stage 13-J/13-K immutable baseline results",
        "source_run_id": int(manifest["source_run_id"]),
        "baseline_pair_count": len(rows),
        "baseline_manifest_sha256": _sha256(manifest_path),
        "lifecycle_csv_sha256": output_hash,
        "expected_lifecycle_csv_sha256": expected_output_sha256,
        "simulation_or_policy_executed": False,
        "status": "complete_and_checksum_matched",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-output-sha256", required=True)
    args = parser.parse_args()
    if len(args.expected_output_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in args.expected_output_sha256
    ):
        raise ValueError("expected output SHA-256 must be 64 lowercase hex characters")
    report = materialize(
        baseline_root=args.baseline_root,
        manifest_path=args.manifest,
        output_path=args.output,
        report_path=args.report,
        expected_output_sha256=args.expected_output_sha256,
    )
    # Keep public CI logs ASCII-only; the UTF-8 report retains the Persian label.
    print(json.dumps(report))


if __name__ == "__main__":
    main()
