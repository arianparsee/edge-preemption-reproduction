"""Execute one sanitized, two-replay Oracle retain branch in GitHub Actions."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, cast

from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY_SEED,
    assert_public_safe,
)
from run_stage15n1b1r_suffix_hash_coverage import file_sha256
from run_stage15n1b2_oracle_retain import (
    _execute_branch,
    _private_branch_result,
    _replays_equal,
)

from edge_reproduction.diagnostics.oracle_checkpoint import (
    SEMANTIC_SCHEMA_VERSION,
    SemanticRestorableTransactionCheckpoint,
    public_payload_is_sanitized,
    write_atomic_new,
)

ALLOWED_SEQUENCES = tuple(range(4, 28))


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _verify_manifest(root: Path) -> str:
    manifest_path = root / "sha256_manifest.json"
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError("bootstrap manifest must be a list")
    for row in rows:
        path = root / cast(str, row["logical_name"])
        if (
            not path.is_file()
            or path.stat().st_size != int(row["size_bytes"])
            or file_sha256(path) != row["sha256"]
        ):
            raise ValueError("bootstrap manifest member mismatch")
    return file_sha256(manifest_path)


def _sanitize(
    *,
    private: dict[str, Any],
    package: SemanticRestorableTransactionCheckpoint,
    bootstrap_manifest_sha256: str,
) -> dict[str, object]:
    decision = {
        key: value
        for key, value in cast(dict[str, Any], private["decision_features"]).items()
        if key != "task_features"
    }
    terminal = {
        key: value
        for key, value in cast(dict[str, Any], private["terminal"]).items()
        if key not in {"incoming_outcomes", "victim_outcomes"}
    }
    validation = cast(dict[str, Any], private["validation"])
    if not all(
        validation.get(key) is True
        for key in (
            "factual_history_checkpoint_verified",
            "intervention_exactly_once",
            "replay_exact",
            "rng_option_a",
            "scientific_fingerprint_exact_between_replays",
            "terminal_partition",
        )
    ) or abs(float(validation["utility_conservation_residual"])) > 1e-9:
        raise ValueError("Oracle branch did not pass every scientific gate")
    locator = package.transaction_locator
    public: dict[str, object] = {
        "schema_version": "stage15n1b2g-public-oracle-branch-v1",
        "sequence": int(cast(int | str, locator["sequence"])),
        "epoch": int(cast(int | str, locator["epoch"])),
        "bootstrap_manifest_sha256": bootstrap_manifest_sha256,
        "semantic_closure_sha256": package.semantic_closure_sha256,
        "rng_state_sha256": package.rng_state_sha256,
        "workload_sha256": package.workload_sha256,
        "config_sha256": package.config_sha256,
        "policy_seed": str(package.policy_seed),
        "decision_features": decision,
        "intervention": private["intervention"],
        "terminal": terminal,
        "divergence": private["divergence"],
        "validation": validation,
        "runtime_seconds_two_replays": private["runtime_seconds_two_replays"],
        "publication": {
            "task_ids": False,
            "snapshots": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "victim_edges": False,
            "traces": False,
            "personal_paths": False,
        },
    }
    assert_public_safe(public)
    public_payload_is_sanitized(public)
    return public


def run_branch(*, bootstrap_root: Path, sequence: int, output_root: Path) -> None:
    if sequence not in ALLOWED_SEQUENCES:
        raise ValueError("sequence is outside the approved 4-27 matrix")
    if output_root.exists():
        raise FileExistsError("branch output root already exists")
    manifest_sha = _verify_manifest(bootstrap_root)
    package_path = bootstrap_root / "payloads" / f"transaction-{sequence:03d}.pkl"
    package = SemanticRestorableTransactionCheckpoint.deserialize(package_path.read_bytes())
    if (
        package.semantic_schema_version != SEMANTIC_SCHEMA_VERSION
        or package.workload_sha256 != EXPECTED_WORKLOAD_SHA256
        or package.config_sha256 != EXPECTED_CONFIG_SHA256
        or package.policy_seed != POLICY_SEED
        or int(cast(int | str, package.transaction_locator["sequence"])) != sequence
    ):
        raise ValueError("Oracle checkpoint identity mismatch")
    package.restore()
    factual_path = bootstrap_root / "factual_bootstrap_private.json"
    factual = cast(dict[str, Any], json.loads(factual_path.read_text(encoding="utf-8")))
    records = cast(list[dict[str, Any]], factual["transaction_records"])
    factual_record = records[sequence]
    if factual_record["transaction_key"] != package.transaction_locator:
        raise ValueError("checkpoint/factual transaction mismatch")
    started = time.perf_counter()
    first = _execute_branch(package, factual)
    second = _execute_branch(package, factual)
    _replays_equal(first, second)
    private = _private_branch_result(
        sequence=sequence,
        package=package,
        factual=factual,
        factual_record=factual_record,
        first=first,
        runtime_seconds=time.perf_counter() - started,
    )
    public = _sanitize(
        private=cast(dict[str, Any], private),
        package=package,
        bootstrap_manifest_sha256=manifest_sha,
    )
    output_root.mkdir(parents=True, exist_ok=False)
    result_path = output_root / "oracle_branch.json"
    write_atomic_new(result_path, _json_bytes(public))
    manifest = {
        "schema_version": "stage15n1b2g-branch-checksum-v1",
        "files": [
            {
                "name": result_path.name,
                "size_bytes": result_path.stat().st_size,
                "sha256": file_sha256(result_path),
            }
        ],
    }
    write_atomic_new(output_root / "sha256_manifest.json", _json_bytes(manifest))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-root", type=Path, required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    run_branch(
        bootstrap_root=args.bootstrap_root,
        sequence=args.sequence,
        output_root=args.output_root,
    )
    print(json.dumps({"status": "complete", "sequence": args.sequence}))


if __name__ == "__main__":
    main()
