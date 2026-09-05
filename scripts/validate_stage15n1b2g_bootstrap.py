"""Validate a prior raw bootstrap bundle without scientific execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY_SEED,
    assert_public_safe,
)
from run_stage15n1b1r_suffix_hash_coverage import file_sha256
from run_stage15n1b2g_bootstrap import (
    EXPECTED_COMPLETED_JOBS,
    EXPECTED_COMPLETED_UTILITY,
    EXPECTED_EVENT_COUNT,
    EXPECTED_PREEMPTED_JOBS,
    EXPECTED_REJECTED_UTILITY,
    EXPECTED_ROUND_TWO_ADMISSION,
    EXPECTED_SELECTOR_CALL_COUNT,
    EXPECTED_TRANSACTION_COUNT,
    _json_bytes,
    _load_comparator,
)

from edge_reproduction.diagnostics.oracle_checkpoint import (
    SEMANTIC_SCHEMA_VERSION,
    SemanticRestorableTransactionCheckpoint,
    public_payload_is_sanitized,
    write_atomic_new,
)


def validate_bundle(
    *, private_root: Path, comparator_path: Path, public_root: Path
) -> dict[str, object]:
    manifest_path = private_root / "sha256_manifest.json"
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError("bootstrap manifest must be a list")
    for row in rows:
        path = private_root / cast(str, row["logical_name"])
        if (
            not path.is_file()
            or path.stat().st_size != int(row["size_bytes"])
            or file_sha256(path) != row["sha256"]
        ):
            raise ValueError("bootstrap manifest member mismatch")
    comparator = _load_comparator(comparator_path)
    factual = cast(
        dict[str, Any],
        json.loads(
            (private_root / "factual_bootstrap_private.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    run = cast(dict[str, Any], factual["run"])
    outcome = cast(dict[str, Any], run["outcome"])
    if factual["scientific_fingerprint"] != comparator["scientific_fingerprint"]:
        raise ValueError("bootstrap fingerprint differs from comparator")
    if factual["selector_funnel"] != comparator["selector_funnel"]:
        raise ValueError("bootstrap selector funnel differs from comparator")
    if factual["auction_funnel"] != comparator["auction_funnel"]:
        raise ValueError("bootstrap auction funnel differs from comparator")
    if factual["lifecycle_funnel"] != comparator["lifecycle_funnel"]:
        raise ValueError("bootstrap lifecycle funnel differs from comparator")
    if factual["counterfactual"] != comparator["counterfactual"]:
        raise ValueError("bootstrap GA counters differ from comparator")
    round_two = cast(dict[str, Any], factual["auction_funnel"])["totals"]
    if not all(
        (
            float(outcome["completed_utility"]) == EXPECTED_COMPLETED_UTILITY,
            float(outcome["rejected_utility"]) == EXPECTED_REJECTED_UTILITY,
            int(outcome["completed_jobs"]) == EXPECTED_COMPLETED_JOBS,
            int(outcome["ever_preempted_jobs"]) == EXPECTED_PREEMPTED_JOBS,
            int(round_two["round_2_accepted"]) == EXPECTED_ROUND_TWO_ADMISSION,
            len(cast(list[object], run["events"])) == EXPECTED_EVENT_COUNT,
            len(cast(list[object], factual["selector_calls"]))
            == EXPECTED_SELECTOR_CALL_COUNT,
            abs(float(factual["utility_conservation_residual"])) <= 1e-9,
        )
    ):
        raise ValueError("bootstrap factual scalar gate failed")
    inventory_payload = json.loads(
        (private_root / "checkpoint_inventory_private.json").read_text(encoding="utf-8")
    )
    inventory = cast(list[dict[str, Any]], inventory_payload["rows"])
    if [int(row["sequence"]) for row in inventory] != list(
        range(EXPECTED_TRANSACTION_COUNT)
    ):
        raise ValueError("bootstrap inventory is incomplete")
    for sequence, expected in enumerate(inventory):
        path = private_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        package = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        package.restore()
        if (
            package.semantic_schema_version != SEMANTIC_SCHEMA_VERSION
            or package.semantic_closure_sha256
            != expected["semantic_closure_sha256"]
            or package.rng_state_sha256 != expected["rng_state_sha256"]
            or package.workload_sha256 != EXPECTED_WORKLOAD_SHA256
            or package.config_sha256 != EXPECTED_CONFIG_SHA256
            or package.policy_seed != POLICY_SEED
        ):
            raise ValueError("bootstrap checkpoint restore/identity mismatch")
    public: dict[str, object] = {
        "schema_version": "stage15n1b2g-public-bootstrap-v1",
        "label": "[پیشنهاد فنی تشخیصی]",
        "scope": {
            "workload_seed": "541501192080118187",
            "policy": "DK-P",
            "variant": "ASSUMP-046",
            "factual_bootstrap_runs": 0,
            "bootstrap_bundle_reused": True,
            "baseline_or_comparator_runs": 0,
        },
        "coverage": {
            "checkpoints": "28/28",
            "duplicate": 0,
            "missing": 0,
            "orphan": 0,
            "semantic_schema": SEMANTIC_SCHEMA_VERSION,
        },
        "validation": {
            "comparator_checksum": True,
            "scientific_fingerprint": True,
            "rng_option_a": True,
            "terminal_partition": True,
            "funnel_and_ga_counters": True,
            "utility_conservation": True,
            "all_payloads_restored": True,
        },
        "scientific": {
            "completed_utility": outcome["completed_utility"],
            "rejected_utility": outcome["rejected_utility"],
            "completed_jobs": outcome["completed_jobs"],
            "preempted_jobs": outcome["ever_preempted_jobs"],
            "round_two_admission": round_two["round_2_accepted"],
        },
        "inventory": inventory,
        "private_manifest": {
            "sha256": file_sha256(manifest_path),
            "entry_count": len(rows),
        },
        "publication": {
            "task_ids": False,
            "snapshots": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "personal_paths": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
    }
    assert_public_safe(public)
    public_payload_is_sanitized(public)
    public_root.mkdir(parents=True, exist_ok=False)
    validation_path = public_root / "bootstrap_validation.json"
    write_atomic_new(validation_path, _json_bytes(public))
    public_manifest = [
        {
            "logical_name": validation_path.name,
            "size_bytes": validation_path.stat().st_size,
            "sha256": file_sha256(validation_path),
        }
    ]
    write_atomic_new(
        public_root / "sha256_manifest.json", _json_bytes(public_manifest)
    )
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--comparator", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    args = parser.parse_args()
    validate_bundle(
        private_root=args.private_root,
        comparator_path=args.comparator,
        public_root=args.public_root,
    )
    print(json.dumps({"status": "valid"}))


if __name__ == "__main__":
    main()
