"""Plan only missing or invalid Stage 15-N Oracle branches for a resumed run."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, cast

from aggregate_stage15n1b2g_oracle import _branch_gate
from run_stage15n1b1r_suffix_hash_coverage import file_sha256

APPROVED = tuple(range(4, 28))


def valid_sequences(root: Path, *, staging_root: Path | None = None) -> list[int]:
    valid: list[int] = []
    if not root.exists():
        return valid
    for path in root.rglob("oracle_branch.json"):
        try:
            manifest = json.loads(
                (path.parent / "sha256_manifest.json").read_text(encoding="utf-8")
            )
            expected = next(
                row
                for row in cast(list[dict[str, Any]], manifest["files"])
                if row["name"] == path.name
            )
            if file_sha256(path) != expected["sha256"]:
                continue
            row = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
            if row.get("schema_version") != "stage15n1b2g-public-oracle-branch-v1":
                continue
            _branch_gate(row)
            sequence = int(row["sequence"])
            if sequence in APPROVED and sequence not in valid:
                valid.append(sequence)
                if staging_root is not None:
                    target = staging_root / f"transaction-{sequence:03d}"
                    if target.exists():
                        raise ValueError("duplicate valid prior branch")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(path.parent, target)
        except (KeyError, StopIteration, TypeError, ValueError, OSError, json.JSONDecodeError):
            continue
    return sorted(valid)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    valid = valid_sequences(args.prior_root, staging_root=args.staging_root)
    missing = [sequence for sequence in APPROVED if sequence not in valid]
    with args.github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"matrix={json.dumps(missing, separators=(',', ':'))}\n")
        handle.write(f"valid_count={len(valid)}\n")
        handle.write(f"missing_count={len(missing)}\n")
    print(json.dumps({"valid": valid, "missing": missing}))


if __name__ == "__main__":
    main()
