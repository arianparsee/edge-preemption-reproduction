"""Materialize 28 restorable factual checkpoints without running an Oracle branch."""

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
    POLICY,
    POLICY_SEED,
    VARIANT,
    WORKLOAD_SEED,
)
from run_stage15n1b1r_suffix_hash_coverage import (
    EXPECTED_CHECKPOINT_EPOCH,
    EXPECTED_EVENT_CURSOR,
    EXPECTED_TRANSACTION_COUNT,
    SOURCE_CHECKPOINT_SHA256,
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

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
    dkp_pre_commit_diagnostic_hook,
)
from edge_reproduction.diagnostics.oracle_checkpoint import (
    RestorableTransactionCheckpoint,
    checkpoint_identity_summary,
    public_payload_is_sanitized,
    validate_payload_inventory,
    write_atomic_new,
)
from edge_reproduction.diagnostics.temporal_checkpoint import (
    CheckpointableTemporalSession,
    TemporalCheckpoint,
)
from edge_reproduction.models.enums import TaskState
from edge_reproduction.simulation.invariants import validate_state_invariants

EXPECTED_STAGE15N1B1R_MANIFEST_SHA256 = (
    "8b401664a9d1b927b1a084243fda5f7d613690da74eee3f18411b82563ec24d4"
)


@dataclass(slots=True)
class FactualCheckpointMaterializer:
    expected_rows: list[dict[str, Any]]
    output_root: Path
    current_checkpoint_payload: bytes | None = None
    pending: list[RestorableTransactionCheckpoint] | None = None
    victim_sequence: int = 0
    hook_call_count: int = 0

    def __post_init__(self) -> None:
        self.pending = []

    def arm(self, checkpoint_payload: bytes) -> None:
        if self.current_checkpoint_payload is not None:
            raise RuntimeError("checkpoint materializer is already armed")
        self.current_checkpoint_payload = checkpoint_payload

    def disarm(self) -> None:
        self.current_checkpoint_payload = None

    def __call__(self, context: DKPPreCommitContext) -> DKPPreCommitAction:
        self.hook_call_count += 1
        if not context.preempted_task_ids:
            return DKPPreCommitAction.COMMIT
        if self.current_checkpoint_payload is None:
            raise ValueError("victim transaction reached without an armed checkpoint")
        if self.victim_sequence >= len(self.expected_rows):
            raise ValueError("factual suffix produced an orphan victim transaction")
        expected = self.expected_rows[self.victim_sequence]
        locator = cast(dict[str, object], expected["transaction_locator"])
        if (
            int(cast(int | str, locator["epoch"])) != context.epoch
            or cast(str, locator["server_id"]) != context.server_id
            or int(cast(int | str, locator["sequence"])) != self.victim_sequence
        ):
            raise ValueError("pre-commit transaction identity differs from factual inventory")
        package = RestorableTransactionCheckpoint.create(
            checkpoint_payload=self.current_checkpoint_payload,
            transaction_locator=locator,
            precommit_context=context,
            expected_closure_sha256=cast(str, expected["closure_sha256"]),
            workload_sha256=EXPECTED_WORKLOAD_SHA256,
            config_sha256=EXPECTED_CONFIG_SHA256,
            policy_seed=POLICY_SEED,
        )
        assert self.pending is not None
        self.pending.append(package)
        self.victim_sequence += 1
        return DKPPreCommitAction.COMMIT

    def flush(self) -> list[dict[str, object]]:
        assert self.pending is not None
        written: list[dict[str, object]] = []
        for package in self.pending:
            sequence = int(cast(int | str, package.transaction_locator["sequence"]))
            path = self.output_root / "payloads" / f"transaction-{sequence:03d}.pkl"
            payload = package.serialize()
            created = write_atomic_new(path, payload)
            written.append(
                {
                    "logical_name": path.relative_to(self.output_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                    "created": created,
                    "transaction_locator": package.transaction_locator,
                    "closure_sha256": package.expected_closure_sha256,
                    "context_sha256": package.expected_context_sha256,
                }
            )
        self.pending.clear()
        self.disarm()
        return written


def _load_approved_closures(stage_r_root: Path) -> list[dict[str, Any]]:
    manifest_path = stage_r_root / "sha256_manifest.json"
    if file_sha256(manifest_path) != EXPECTED_STAGE15N1B1R_MANIFEST_SHA256:
        raise ValueError("Stage 15-N.1B.1-R private manifest checksum mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list) or len(manifest) != 1:
        raise ValueError("unexpected Stage 15-N.1B.1-R private manifest shape")
    row = manifest[0]
    index_path = stage_r_root / cast(str, row["logical_name"])
    if (
        not index_path.is_file()
        or index_path.stat().st_size != int(row["size_bytes"])
        or file_sha256(index_path) != row["sha256"]
    ):
        raise ValueError("Stage 15-N.1B.1-R closure index checksum mismatch")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    rows = cast(list[dict[str, Any]], index["closure_rows"])
    if len(rows) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("approved closure index is incomplete")
    return rows


def _advance_after_auction(session: CheckpointableTemporalSession, *, epoch: int) -> None:
    validate_state_invariants(session.state)
    terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
    all_terminal = all(status in terminal for status in session.state.task_states.values())
    session.next_epoch = epoch + 1
    if (epoch >= session.last_arrival_slot and all_terminal) or (
        epoch >= session.configured_last_slot
    ):
        session.finished = True


def _apply_prepared_auction(
    *,
    session: CheckpointableTemporalSession,
    epoch: int,
    requesting: tuple[str, ...],
    time_remaining: dict[str, float],
    materializer: FactualCheckpointMaterializer,
) -> None:
    before_state = session.state.snapshot()
    progress_before = session.progress.copy()
    retry_before = session.retry_count.copy()
    selector = cast(Any, session.policy)._selector  # noqa: SLF001
    start_count = int(selector.observation_count)
    with dkp_pre_commit_diagnostic_hook(materializer):
        result = session._apply_auction(  # noqa: SLF001
            epoch=epoch,
            requesting=requesting,
            time_remaining=time_remaining,
        )
    end_count = int(selector.observation_count)
    session._record_victim_transactions(  # noqa: SLF001
        epoch=epoch,
        before_state=before_state,
        progress_before=progress_before,
        retry_before=retry_before,
        result=result,
        selector_observation_start=start_count,
        selector_observation_end=end_count,
    )
    _advance_after_auction(session, epoch=epoch)


def _restore_gate(
    *, output_root: Path, expected_rows: list[dict[str, Any]]
) -> tuple[list[RestorableTransactionCheckpoint], list[dict[str, object]]]:
    packages: list[RestorableTransactionCheckpoint] = []
    private_rows: list[dict[str, object]] = []
    for sequence, expected in enumerate(expected_rows):
        path = output_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        raw = path.read_bytes()
        package = RestorableTransactionCheckpoint.deserialize(raw)
        if package.expected_closure_sha256 != expected["closure_sha256"]:
            raise ValueError("persisted payload closure differs from approved index")
        first = package.restore()
        second = package.restore()
        if first.session is second.session or first.session.state is second.session.state:
            raise ValueError("restored checkpoint payloads alias each other")
        if first.serialize() != package.checkpoint_payload:
            raise ValueError("restored checkpoint serialization changed")
        packages.append(package)
        private_rows.append(
            {
                "logical_name": path.relative_to(output_root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "identity": checkpoint_identity_summary(package),
                "transaction_locator": package.transaction_locator,
            }
        )
    return packages, private_rows


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


def run_materialization(
    *, source_root: Path, private_output: Path, public_output: Path
) -> dict[str, object]:
    if public_output.exists():
        raise FileExistsError("public Stage 15-N.1B.2-R output already exists")
    if (private_output / "sha256_manifest.json").exists():
        raise FileExistsError("completed private Stage 15-N.1B.2-R output already exists")
    source_paths = validate_source_manifest(source_root)
    before = source_snapshot(source_paths)
    if file_sha256(source_root / "sha256_manifest.json") != SOURCE_MANIFEST_SHA256:
        raise ValueError("Stage 15-N.1B.1 source manifest mismatch")
    checkpoint_path = source_root / "replay-1" / "checkpoint_canary.pkl"
    replay_path = source_root / "replay-1" / "factual_replay_private.json"
    suffix_path = source_root / "suffix-canary" / "factual_suffix_private.json"
    if file_sha256(checkpoint_path) != SOURCE_CHECKPOINT_SHA256:
        raise ValueError("source checkpoint checksum mismatch")
    if file_sha256(replay_path) != SOURCE_REPLAY_SHA256:
        raise ValueError("source factual replay checksum mismatch")
    if file_sha256(suffix_path) != SOURCE_SUFFIX_SHA256:
        raise ValueError("source factual suffix checksum mismatch")
    expected_rows = _load_approved_closures(source_root / "stage15n1b1r-suffix-only")
    expected_locators = [
        cast(dict[str, object], row["transaction_locator"]) for row in expected_rows
    ]
    expected_epochs = {
        int(cast(int | str, locator["epoch"])) for locator in expected_locators
    }
    estimated_bytes = replay_path.stat().st_size * EXPECTED_TRANSACTION_COUNT * 5 // 4
    free_bytes = shutil.disk_usage(private_output.parent).free
    if free_bytes < estimated_bytes * 2:
        raise OSError("insufficient free space for atomic restorable checkpoint materialization")

    checkpoint_payload = checkpoint_path.read_bytes()
    source_checkpoint = TemporalCheckpoint.deserialize(checkpoint_payload)
    validate_checkpoint_closure(source_checkpoint, require_source_identity=True)
    session = TemporalCheckpoint.deserialize(checkpoint_payload).session
    materializer = FactualCheckpointMaterializer(expected_rows, private_output)
    inventory_rows: list[dict[str, object]] = []

    materializer.arm(checkpoint_payload)
    _apply_prepared_auction(
        session=session,
        epoch=source_checkpoint.epoch,
        requesting=source_checkpoint.requesting_task_ids,
        time_remaining=source_checkpoint.time_remaining_by_task,
        materializer=materializer,
    )
    inventory_rows.extend(materializer.flush())

    while not session.finished:
        epoch = session.next_epoch
        requesting, time_remaining = session._prepare_epoch(epoch)  # noqa: SLF001
        if requesting:
            if epoch in expected_epochs:
                checkpoint = session.checkpoint(
                    epoch=epoch,
                    requesting_task_ids=requesting,
                    time_remaining_by_task=time_remaining,
                )
                materializer.arm(checkpoint.serialize())
            _apply_prepared_auction(
                session=session,
                epoch=epoch,
                requesting=requesting,
                time_remaining=time_remaining,
                materializer=materializer,
            )
            inventory_rows.extend(materializer.flush())
        else:
            _advance_after_auction(session, epoch=epoch)

    if materializer.victim_sequence != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("factual materialization did not observe all 28 transactions")
    source_replay = json.loads(replay_path.read_text(encoding="utf-8"))
    source_suffix = json.loads(suffix_path.read_text(encoding="utf-8"))
    scientific, call_rows = _terminal_and_rng_gates(
        session=session, source_replay=source_replay, source_suffix=source_suffix
    )
    actual_locators = [
        cast(dict[str, object], row["transaction_key"])
        for row in session.transaction_records
    ]
    if actual_locators != expected_locators:
        raise ValueError("factual transaction inventory changed under no-op hook")

    packages, restored_rows = _restore_gate(
        output_root=private_output, expected_rows=expected_rows
    )
    coverage = validate_payload_inventory(packages, expected_locators)
    if len(packages) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("restorable payload coverage did not reach 28/28")
    if len(inventory_rows) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("atomic materialization inventory is incomplete")
    private_inventory = {
        "schema_version": "stage15n1b2r-private-inventory-v1",
        "identity": {
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "policy": POLICY,
            "variant": VARIANT.value,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
            "config_sha256": EXPECTED_CONFIG_SHA256,
        },
        "source_checkpoint": {
            "epoch": EXPECTED_CHECKPOINT_EPOCH,
            "event_cursor": EXPECTED_EVENT_CURSOR,
            "sha256": SOURCE_CHECKPOINT_SHA256,
        },
        "payloads": restored_rows,
        "hook_call_count": materializer.hook_call_count,
        "oracle_branches_executed": 0,
    }
    write_new_json(
        private_output / "restorable_checkpoint_inventory_private.json",
        private_inventory,
    )
    private_manifest = _manifest_rows(private_output)
    write_new_json(private_output / "sha256_manifest.json", private_manifest)

    public: dict[str, object] = {
        "schema_version": "stage15n1b2r-public-materialization-v1",
        "label": "[پیشنهاد فنی تشخیصی] Stage 15-N.1B.2-R",
        "scope": {
            "factual_suffixes_executed": 1,
            "full_workloads_executed": 0,
            "full_factual_replays_executed": 0,
            "comparators_executed": 0,
            "oracle_branches_executed": 0,
        },
        "source_checkpoint": {
            "epoch": EXPECTED_CHECKPOINT_EPOCH,
            "event_cursor": EXPECTED_EVENT_CURSOR,
            "sha256": SOURCE_CHECKPOINT_SHA256,
            "checksum_verified_pre_and_post": True,
        },
        "storage": {
            "estimated_bytes": estimated_bytes,
            "free_bytes_before": free_bytes,
            "payload_count": len(packages),
            "payload_bytes": sum(
                (private_output / cast(str, row["logical_name"])).stat().st_size
                for row in private_manifest
                if cast(str, row["logical_name"]).startswith("payloads/")
            ),
        },
        "coverage": {
            "closure_hash_before": "28/28",
            "closure_hash_after": "28/28",
            "restorable_payload_before": "1/28",
            "restorable_payload_after": "28/28",
            "rng_state_hash": "28/28",
            "deserialize_restore": "28/28",
            **coverage,
            "transaction_order_exact": True,
        },
        "validation": {
            "factual_suffix_exact": True,
            "noop_hook_scientific_exact": True,
            "noop_hook_rng_exact": True,
            "scientific_fingerprint_exact": True,
            "terminal_partition": True,
            "capacity_and_state_invariants": True,
            "utility_conservation": True,
            "stage_success": True,
        },
        "scientific_summary": {
            key: value
            for key, value in scientific.items()
            if key not in {"scientific_fingerprint", "lifecycle_funnel"}
        },
        "hook": {
            "default_disabled": True,
            "stage_action": "commit_no_intervention",
            "precommit_victim_context_count": EXPECTED_TRANSACTION_COUNT,
            "oracle_interventions_executed": 0,
        },
        "private_manifest": {
            "entry_count": len(private_manifest),
            "sha256": file_sha256(private_output / "sha256_manifest.json"),
            "personal_paths_published": False,
            "checkpoint_payloads_published": False,
        },
        "publication": {
            "task_ids": False,
            "snapshots": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "workload": False,
            "personal_paths": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
    }
    public_payload_is_sanitized(public)
    public_output.mkdir(parents=True, exist_ok=False)
    write_new_json(public_output / "completeness_report.json", public)
    schema = {
        "schema_version": "stage15n1b2r-public-schema-v1",
        "private_payload_fields_published": False,
        "public_content": [
            "aggregate coverage",
            "validation gates",
            "storage totals",
            "sanitized scientific summary",
            "private manifest digest",
        ],
    }
    public_payload_is_sanitized(schema)
    write_new_json(public_output / "schema.json", schema)
    validation = {
        "restorable_payload_coverage": "28/28",
        "factual_suffix": "exact",
        "noop_hook": "scientific_and_rng_exact",
        "deserialize_restore": "28/28",
        "invariants": "pass",
        "oracle_branches": 0,
    }
    write_new_json(public_output / "validation_report.json", validation)
    public_manifest = _manifest_rows(public_output)
    write_new_json(public_output / "sha256_manifest.json", public_manifest)

    after = source_snapshot(source_paths)
    if before != after:
        raise ValueError("validated Stage 15-N.1B.1 inputs changed during materialization")
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    result = run_materialization(
        source_root=args.source_root,
        private_output=args.private_output,
        public_output=args.public_output,
    )
    print(
        json.dumps(
            {
                "stage_success": cast(dict[str, object], result["validation"])[
                    "stage_success"
                ],
                "restorable_payload_coverage": cast(
                    dict[str, object], result["coverage"]
                )["restorable_payload_after"],
                "factual_suffixes_executed": 1,
                "oracle_branches_executed": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
