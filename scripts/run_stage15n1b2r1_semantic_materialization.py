"""Complete semantic, restorable transaction checkpoints from a factual suffix.

This trusted-local runner resumes the newest checksum-verified factual checkpoint.
It executes no full workload, comparator, baseline, Oracle, retain, or veto branch.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY_SEED,
)
from run_stage15n1b1r_suffix_hash_coverage import (
    EXPECTED_TRANSACTION_COUNT,
    SOURCE_MANIFEST_SHA256,
    SOURCE_REPLAY_SHA256,
    SOURCE_SUFFIX_SHA256,
    _terminal_and_rng_gates,
    file_sha256,
    source_snapshot,
    validate_checkpoint_closure,
    validate_source_manifest,
    write_new_json,
)
from run_stage15n1b2r_materialize_checkpoints import (
    EXPECTED_STAGE15N1B1R_MANIFEST_SHA256,
    _advance_after_auction,
    _load_approved_closures,
)

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
    dkp_pre_commit_diagnostic_hook,
)
from edge_reproduction.diagnostics.oracle_checkpoint import (
    SEMANTIC_PAYLOAD_SCHEMA_VERSION,
    SEMANTIC_SCHEMA_VERSION,
    RestorableTransactionCheckpoint,
    SemanticRestorableTransactionCheckpoint,
    context_digest,
    public_payload_is_sanitized,
    semantic_closure_sha256,
    write_atomic_new,
)
from edge_reproduction.diagnostics.temporal_checkpoint import (
    CheckpointableTemporalSession,
    TemporalCheckpoint,
)

EXPECTED_PRIOR_PARTIAL_MANIFEST_SHA256 = (
    "d9bef0df8d6cd26127def3d1e6164fd4310255a007c324c5c1f9cd9770fd3f92"
)
EXPECTED_PRIOR_PAYLOAD_SHA256 = (
    "07917ba98071dc240425af499e21d032697b5f50d9f87a241872bb999398da41",
    "fd5f22a021f4e00f6570b4851b298cc4ffce62629405f39598dc90770044718e",
)
RESUME_SEQUENCE = 1


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _manifest_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "sha256_manifest.json":
            continue
        rows.append(
            {
                "logical_name": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return rows


def _load_prior_payloads(
    prior_root: Path, expected_rows: list[dict[str, Any]]
) -> tuple[RestorableTransactionCheckpoint, RestorableTransactionCheckpoint]:
    manifest = prior_root / "sha256_manifest.json"
    if file_sha256(manifest) != EXPECTED_PRIOR_PARTIAL_MANIFEST_SHA256:
        raise ValueError("prior partial payload manifest checksum mismatch")
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    by_name = {cast(str, row["logical_name"]): row for row in rows}
    packages: list[RestorableTransactionCheckpoint] = []
    for sequence, approved_sha in enumerate(EXPECTED_PRIOR_PAYLOAD_SHA256):
        relative = f"payloads/transaction-{sequence:03d}.pkl"
        row = by_name.get(relative)
        path = prior_root / relative
        if row is None or not path.is_file():
            raise FileNotFoundError(f"prior payload absent: {relative}")
        if file_sha256(path) != approved_sha or row["sha256"] != approved_sha:
            raise ValueError(f"prior payload checksum mismatch: {relative}")
        package = RestorableTransactionCheckpoint.deserialize(path.read_bytes())
        expected = expected_rows[sequence]
        if package.transaction_locator != expected["transaction_locator"]:
            raise ValueError("prior payload transaction identity mismatch")
        if package.expected_closure_sha256 != expected["closure_sha256"]:
            raise ValueError("prior payload legacy closure mismatch")
        package.restore()
        packages.append(package)
    return packages[0], packages[1]


def _semantic_package(
    *,
    checkpoint_payload: bytes,
    context: DKPPreCommitContext,
    expected: dict[str, Any],
) -> SemanticRestorableTransactionCheckpoint:
    locator = cast(dict[str, object], expected["transaction_locator"])
    return SemanticRestorableTransactionCheckpoint.create(
        checkpoint_payload=checkpoint_payload,
        transaction_locator=locator,
        precommit_context=context,
        legacy_raw_pickle_sha256=cast(str, expected["closure_sha256"]),
        legacy_raw_checkpoint_sha256=cast(str, expected["checkpoint_sha256"]),
        rng_state_sha256=cast(str, expected["rng_state_sha256"]),
        workload_sha256=EXPECTED_WORKLOAD_SHA256,
        config_sha256=EXPECTED_CONFIG_SHA256,
        policy_seed=POLICY_SEED,
    )


@dataclass(slots=True)
class SemanticMaterializer:
    expected_rows: list[dict[str, Any]]
    output_root: Path
    current_checkpoint_payload: bytes | None = None
    victim_sequence: int = RESUME_SEQUENCE
    hook_call_count: int = 0

    def arm(self, checkpoint_payload: bytes) -> None:
        if self.current_checkpoint_payload is not None:
            raise RuntimeError("semantic materializer is already armed")
        self.current_checkpoint_payload = checkpoint_payload

    def disarm(self) -> None:
        self.current_checkpoint_payload = None

    def __call__(self, context: DKPPreCommitContext) -> DKPPreCommitAction:
        self.hook_call_count += 1
        if not context.preempted_task_ids:
            return DKPPreCommitAction.COMMIT
        if self.current_checkpoint_payload is None:
            raise ValueError("victim transaction reached without checkpoint closure")
        if self.victim_sequence >= len(self.expected_rows):
            raise ValueError("factual suffix produced orphan victim transaction")
        expected = self.expected_rows[self.victim_sequence]
        locator = cast(dict[str, object], expected["transaction_locator"])
        actual = {
            "epoch": context.epoch,
            "server_id": context.server_id,
            "server_ordinal": locator["server_ordinal"],
            "sequence": self.victim_sequence,
        }
        if actual != locator:
            raise ValueError("pre-commit transaction identity differs from inventory")
        package = _semantic_package(
            checkpoint_payload=self.current_checkpoint_payload,
            context=context,
            expected=expected,
        )
        path = (
            self.output_root
            / "payloads"
            / f"transaction-{self.victim_sequence:03d}.pkl"
        )
        write_atomic_new(path, package.serialize())
        restored = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        restored.restore()
        if restored.semantic_closure_sha256 != package.semantic_closure_sha256:
            raise ValueError("semantic hash changed after immediate restore")
        self.victim_sequence += 1
        return DKPPreCommitAction.COMMIT


def _apply_prepared_auction(
    *,
    session: CheckpointableTemporalSession,
    checkpoint: TemporalCheckpoint,
    materializer: SemanticMaterializer,
) -> None:
    before_state = session.state.snapshot()
    progress_before = session.progress.copy()
    retry_before = session.retry_count.copy()
    selector = cast(Any, session.policy)._selector  # noqa: SLF001
    start_count = int(selector.observation_count)
    materializer.arm(checkpoint.serialize())
    try:
        with dkp_pre_commit_diagnostic_hook(materializer):
            result = session._apply_auction(  # noqa: SLF001
                epoch=checkpoint.epoch,
                requesting=checkpoint.requesting_task_ids,
                time_remaining=checkpoint.time_remaining_by_task,
            )
    finally:
        materializer.disarm()
    end_count = int(selector.observation_count)
    session._record_victim_transactions(  # noqa: SLF001
        epoch=checkpoint.epoch,
        before_state=before_state,
        progress_before=progress_before,
        retry_before=retry_before,
        result=result,
        selector_observation_start=start_count,
        selector_observation_end=end_count,
    )
    _advance_after_auction(session, epoch=checkpoint.epoch)


def _continue_epoch(
    *,
    session: CheckpointableTemporalSession,
    materializer: SemanticMaterializer,
    expected_epochs: set[int],
) -> None:
    epoch = session.next_epoch
    requesting, time_remaining = session._prepare_epoch(epoch)  # noqa: SLF001
    if not requesting:
        _advance_after_auction(session, epoch=epoch)
        return
    checkpoint = session.checkpoint(
        epoch=epoch,
        requesting_task_ids=requesting,
        time_remaining_by_task=time_remaining,
    )
    if epoch not in expected_epochs:
        before = materializer.victim_sequence
        _apply_prepared_auction(
            session=session, checkpoint=checkpoint, materializer=materializer
        )
        if materializer.victim_sequence != before:
            raise ValueError("unexpected victim transaction outside approved epoch")
        return
    _apply_prepared_auction(session=session, checkpoint=checkpoint, materializer=materializer)


def _restore_all(
    *, output_root: Path, expected_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, object]], dict[str, int]]:
    inventory: list[dict[str, object]] = []
    locators: list[bytes] = []
    for sequence, expected in enumerate(expected_rows):
        path = output_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        package = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        restored = package.restore()
        expected_semantic = semantic_closure_sha256(
            checkpoint=restored,
            transaction_locator=package.transaction_locator,
            precommit_context=package.precommit_context,
        )
        if expected_semantic != package.semantic_closure_sha256:
            raise ValueError("semantic hash changed after final restore")
        if package.legacy_raw_pickle_sha256 != expected["closure_sha256"]:
            raise ValueError("legacy closure provenance changed")
        locator_token = _json_bytes(package.transaction_locator)
        locators.append(locator_token)
        inventory.append(
            {
                "transaction_locator": package.transaction_locator,
                "legacy_raw_pickle_sha256": package.legacy_raw_pickle_sha256,
                "legacy_raw_checkpoint_sha256": package.legacy_raw_checkpoint_sha256,
                "canonical_semantic_closure_sha256": package.semantic_closure_sha256,
                "restorable_payload_sha256": file_sha256(path),
                "rng_state_sha256": package.rng_state_sha256,
                "schema_version": package.semantic_schema_version,
                "context_sha256": context_digest(package.precommit_context),
            }
        )
    expected_tokens = [
        _json_bytes(cast(dict[str, object], row["transaction_locator"]))
        for row in expected_rows
    ]
    duplicate = len(locators) - len(set(locators))
    missing = len(set(expected_tokens) - set(locators))
    orphan = len(set(locators) - set(expected_tokens))
    if duplicate or missing or orphan or locators != expected_tokens:
        raise ValueError("semantic checkpoint inventory is incomplete or out of order")
    return inventory, {
        "duplicate_count": duplicate,
        "missing_count": missing,
        "orphan_count": orphan,
    }


def run_semantic_materialization(
    *,
    source_root: Path,
    prior_root: Path,
    private_output: Path,
    public_output: Path,
) -> dict[str, object]:
    if private_output.exists() or public_output.exists():
        raise FileExistsError("Stage 15-N.1B.2-R.1 output root already exists")
    source_paths = validate_source_manifest(source_root)
    prior_paths = [
        prior_root / "sha256_manifest.json",
        prior_root / "partial_failure_manifest.json",
        prior_root / "payloads" / "transaction-000.pkl",
        prior_root / "payloads" / "transaction-001.pkl",
    ]
    before = source_snapshot(source_paths + prior_paths)
    if file_sha256(source_root / "sha256_manifest.json") != SOURCE_MANIFEST_SHA256:
        raise ValueError("Stage 15-N.1B.1 source manifest mismatch")
    approved_root = source_root / "stage15n1b1r-suffix-only"
    if file_sha256(approved_root / "sha256_manifest.json") != (
        EXPECTED_STAGE15N1B1R_MANIFEST_SHA256
    ):
        raise ValueError("legacy closure manifest checksum mismatch")
    expected_rows = _load_approved_closures(approved_root)
    old_zero, old_one = _load_prior_payloads(prior_root, expected_rows)

    estimated_bytes = sum(path.stat().st_size for path in prior_paths[-2:]) * 16
    free_bytes = shutil.disk_usage(private_output.parent).free
    if free_bytes < estimated_bytes * 2:
        raise OSError("insufficient free space for atomic semantic checkpoints")

    zero_package = _semantic_package(
        checkpoint_payload=old_zero.checkpoint_payload,
        context=old_zero.precommit_context,
        expected=expected_rows[0],
    )
    zero_path = private_output / "payloads" / "transaction-000.pkl"
    write_atomic_new(zero_path, zero_package.serialize())

    resume_checkpoint = old_one.restore()
    validate_checkpoint_closure(resume_checkpoint)
    session = old_one.restore().session
    materializer = SemanticMaterializer(expected_rows, private_output)
    _apply_prepared_auction(
        session=session,
        checkpoint=resume_checkpoint,
        materializer=materializer,
    )
    while not session.finished:
        _continue_epoch(
            session=session,
            materializer=materializer,
            expected_epochs={
                int(cast(int | str, row["transaction_locator"]["epoch"]))
                for row in expected_rows
            },
        )
    if materializer.victim_sequence != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("semantic payload coverage did not reach 28/28")

    replay_path = source_root / "replay-1" / "factual_replay_private.json"
    suffix_path = source_root / "suffix-canary" / "factual_suffix_private.json"
    if file_sha256(replay_path) != SOURCE_REPLAY_SHA256:
        raise ValueError("source factual replay checksum mismatch")
    if file_sha256(suffix_path) != SOURCE_SUFFIX_SHA256:
        raise ValueError("source factual suffix checksum mismatch")
    source_replay = json.loads(replay_path.read_text(encoding="utf-8"))
    source_suffix = json.loads(suffix_path.read_text(encoding="utf-8"))
    scientific, call_rows = _terminal_and_rng_gates(
        session=session, source_replay=source_replay, source_suffix=source_suffix
    )
    expected_locators = [
        cast(dict[str, object], row["transaction_locator"]) for row in expected_rows
    ]
    actual_locators = [
        cast(dict[str, object], row["transaction_key"])
        for row in session.transaction_records
    ]
    if actual_locators != expected_locators:
        raise ValueError("factual transaction order changed under no-op hook")

    crosswalk, counts = _restore_all(
        output_root=private_output, expected_rows=expected_rows
    )
    write_new_json(
        private_output / "legacy_semantic_crosswalk_private.json",
        {
            "schema_version": "stage15n1b2r1-private-crosswalk-v1",
            "semantic_schema_version": SEMANTIC_SCHEMA_VERSION,
            "legacy_contract": "raw_pickle_bytes_plus_locator_sha256",
            "rows": crosswalk,
        },
    )
    private_manifest = _manifest_rows(private_output)
    write_new_json(private_output / "sha256_manifest.json", private_manifest)

    public: dict[str, object] = {
        "schema_version": "stage15n1b2r1-public-completeness-v1",
        "label": "[پیشنهاد فنی تشخیصی] Stage 15-N.1B.2-R.1",
        "scope": {
            "factual_suffixes_executed": 1,
            "full_workloads_executed": 0,
            "full_factual_replays_executed": 0,
            "baseline_or_comparator_executed": 0,
            "oracle_or_counterfactual_branches_executed": 0,
        },
        "resume": {
            "source_sequence": RESUME_SEQUENCE,
            "source_epoch": resume_checkpoint.epoch,
            "source_event_cursor": resume_checkpoint.event_cursor,
            "source_payload_checksum_verified": True,
        },
        "contracts": {
            "legacy_raw_pickle_preserved": True,
            "legacy_is_semantic_equality": False,
            "canonical_semantic_schema": SEMANTIC_SCHEMA_VERSION,
            "utf8_deterministic_serialization": True,
        },
        "coverage": {
            "victim_transactions": EXPECTED_TRANSACTION_COUNT,
            "legacy_closure_hash": "28/28",
            "canonical_semantic_hash": "28/28",
            "restorable_payload_before": "2/28",
            "restorable_payload_after": "28/28",
            "rng_state_hash": "28/28",
            "deserialize_restore": "28/28",
            **counts,
        },
        "validation": {
            "factual_suffix_exact": True,
            "noop_hook_scientific_and_rng_exact": True,
            "rng_option_a": True,
            "scientific_fingerprint_exact": True,
            "terminal_partition": True,
            "capacity_and_state_invariants": True,
            "utility_conservation": True,
            "semantic_hash_before_after_restore": True,
            "stage_success": True,
        },
        "scientific_summary": {
            key: value
            for key, value in scientific.items()
            if key not in {"scientific_fingerprint", "lifecycle_funnel"}
        },
        "technical_counts": {
            "event_count": scientific["event_count"],
            "selector_call_count": len(call_rows),
            "payload_count": len(crosswalk),
            "hook_calls_after_resume": materializer.hook_call_count,
        },
        "private_manifest": {
            "entry_count": len(private_manifest),
            "sha256": file_sha256(private_output / "sha256_manifest.json"),
            "individual_hashes_published": False,
            "personal_paths_published": False,
        },
        "publication": {
            "task_ids": False,
            "snapshots": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "workload": False,
            "transaction_rows": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
    }
    public_payload_is_sanitized(public)
    public_output.mkdir(parents=True, exist_ok=False)
    write_new_json(public_output / "completeness_report.json", public)
    schema = {
        "schema_version": "stage15n1b2r1-public-schema-v1",
        "canonical_semantic_schema": SEMANTIC_SCHEMA_VERSION,
        "private_payload_schema": SEMANTIC_PAYLOAD_SCHEMA_VERSION,
        "private_values_published": False,
        "public_content": [
            "aggregate coverage",
            "contract versions",
            "validation gates",
            "sanitized scientific summary",
            "private manifest digest",
        ],
    }
    public_payload_is_sanitized(schema)
    write_new_json(public_output / "schema.json", schema)
    validation = {
        "factual_suffix": "exact",
        "noop_hook": "scientific_and_rng_exact",
        "rng_option_a": "pass",
        "scientific_fingerprint": "exact",
        "invariants": "pass",
        "semantic_hash_restore": "28/28",
        "restorable_payload_coverage": "28/28",
        "oracle_branches": 0,
    }
    write_new_json(public_output / "validation_report.json", validation)
    public_manifest = _manifest_rows(public_output)
    write_new_json(public_output / "sha256_manifest.json", public_manifest)

    after = source_snapshot(source_paths + prior_paths)
    if before != after:
        raise ValueError("validated Stage 15-N inputs changed during semantic suffix")
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    report = run_semantic_materialization(
        source_root=args.source_root,
        prior_root=args.prior_root,
        private_output=args.private_output,
        public_output=args.public_output,
    )
    print(
        json.dumps(
            {
                "stage_success": cast(dict[str, object], report["validation"])[
                    "stage_success"
                ],
                "restorable_payload_coverage": cast(
                    dict[str, object], report["coverage"]
                )["restorable_payload_after"],
                "factual_suffixes_executed": 1,
                "oracle_branches_executed": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
