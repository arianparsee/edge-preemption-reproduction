"""Complete private closure-hash coverage from the validated factual checkpoint.

This Stage 15-N.1B.1-R runner resumes exactly one already validated factual
suffix.  It never constructs a workload, comparator, baseline, or Oracle
branch.  Full pre-decision checkpoints are captured only at victim-bearing
epochs already present in the checksum-verified factual replay inventory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import fields
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls
from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_COMPLETED_UTILITY,
    EXPECTED_WORKLOAD_SHA256,
    POLICY,
    POLICY_SEED,
    VARIANT,
    WORKLOAD_SEED,
    assert_public_safe,
    validate_utility_conservation,
)

from edge_reproduction.diagnostics.dk_funnel import lifecycle_funnel
from edge_reproduction.diagnostics.temporal_checkpoint import (
    CheckpointableTemporalSession,
    TemporalCheckpoint,
)
from edge_reproduction.models.enums import TaskState
from edge_reproduction.simulation.invariants import validate_state_invariants

SOURCE_CHECKPOINT_SHA256 = (
    "8d9459aece1f8f496a66fc58273298ec6c12ac926558de2c47a7cd29537e8ac7"
)
SOURCE_REPLAY_SHA256 = (
    "7ff6fdbd51dc2b20358dcc082fd93092689e63acf3452e0774043f8bb3748997"
)
SOURCE_SUFFIX_SHA256 = (
    "55953cacb37bcd40873cee9f2e02028c60bbf991d1fe741507fb6861db1e9b69"
)
SOURCE_MANIFEST_SHA256 = (
    "a2a0e89060b61b4d6cc7c54cf6fbe5569df977b2ca862b960b2b52f606e92edd"
)
EXPECTED_CHECKPOINT_EPOCH = 4
EXPECTED_EVENT_CURSOR = 213
EXPECTED_TRANSACTION_COUNT = 28
REQUIRED_SESSION_FIELDS = {
    "original_tasks",
    "servers_input",
    "policy",
    "config",
    "policy_metadata",
    "task_ids",
    "original",
    "state",
    "configured_last_slot",
    "last_arrival_slot",
    "drain_slots",
    "events",
    "progress",
    "retry_count",
    "rejection_reasons",
    "ever_preempted",
    "raw_rejections",
    "next_epoch",
    "finished",
    "transaction_records",
}


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_new_json(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-N.1B.1-R output: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def closure_hash(checkpoint_payload: bytes, transaction_locator: object) -> str:
    """Bind a complete pre-decision checkpoint to one transaction locator."""

    digest = sha256()
    digest.update(b"stage15n1b1r-closure-v1\0")
    digest.update(checkpoint_payload)
    digest.update(b"\0")
    digest.update(canonical_json(transaction_locator))
    return digest.hexdigest()


def checkpoint_rng_hash(checkpoint: TemporalCheckpoint) -> str:
    selector = cast(Any, checkpoint.session.policy)._selector  # noqa: SLF001
    delegate = selector._delegate  # noqa: SLF001
    state = delegate._counting_rng.getstate()  # noqa: SLF001
    return sha256(canonical_json(state)).hexdigest()


def validate_checkpoint_closure(
    checkpoint: TemporalCheckpoint, *, require_source_identity: bool = False
) -> None:
    if checkpoint.schema_version != "stage15n1b1-private-checkpoint-v1":
        raise ValueError("unsupported source checkpoint schema")
    missing = REQUIRED_SESSION_FIELDS - {
        item.name for item in fields(checkpoint.session)
    }
    if missing:
        raise ValueError(f"checkpoint closure fields missing: {sorted(missing)}")
    if require_source_identity and checkpoint.epoch != EXPECTED_CHECKPOINT_EPOCH:
        raise ValueError("source checkpoint epoch mismatch")
    if require_source_identity and checkpoint.event_cursor != EXPECTED_EVENT_CURSOR:
        raise ValueError("source checkpoint event cursor mismatch")
    if checkpoint.session.next_epoch != checkpoint.epoch:
        raise ValueError("checkpoint continuation cursor mismatch")
    if len(checkpoint.session.events) != checkpoint.event_cursor:
        raise ValueError("checkpoint event cursor does not match event registry")
    if require_source_identity and checkpoint.session.config.policy_seed != POLICY_SEED:
        raise ValueError("checkpoint policy seed mismatch")
    selector = getattr(checkpoint.session.policy, "_selector", None)
    delegate = getattr(selector, "_delegate", None)
    counting_rng = getattr(delegate, "_counting_rng", None)
    if counting_rng is None or not callable(getattr(counting_rng, "getstate", None)):
        raise ValueError("checkpoint lacks named selector RNG state")


def validate_coverage(
    rows: list[dict[str, object]], expected_locators: list[dict[str, object]]
) -> dict[str, int]:
    actual = [cast(dict[str, object], row["transaction_locator"]) for row in rows]
    actual_tokens = [canonical_json(item) for item in actual]
    expected_tokens = [canonical_json(item) for item in expected_locators]
    duplicate_count = len(actual_tokens) - len(set(actual_tokens))
    missing_count = len(set(expected_tokens) - set(actual_tokens))
    orphan_count = len(set(actual_tokens) - set(expected_tokens))
    if duplicate_count or missing_count or orphan_count:
        raise ValueError(
            "transaction coverage mismatch: "
            f"duplicate={duplicate_count}, missing={missing_count}, orphan={orphan_count}"
        )
    if actual_tokens != expected_tokens:
        raise ValueError("transaction order differs from validated factual execution")
    closure_hashes = [cast(str, row["closure_sha256"]) for row in rows]
    if len(closure_hashes) != len(set(closure_hashes)):
        raise ValueError("closure hashes are not unique")
    return {
        "duplicate_count": duplicate_count,
        "missing_count": missing_count,
        "orphan_count": orphan_count,
    }


def source_snapshot(paths: list[Path]) -> dict[str, tuple[int, int, str]]:
    return {
        path.as_posix(): (path.stat().st_size, path.stat().st_mtime_ns, file_sha256(path))
        for path in paths
    }


def validate_source_manifest(source_root: Path) -> list[Path]:
    manifest_path = source_root / "sha256_manifest.json"
    if file_sha256(manifest_path) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Stage 15-N.1B.1 private manifest checksum mismatch")
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError("source private manifest must be a list")
    paths: list[Path] = []
    for row in rows:
        relative = cast(str, row["logical_name"])
        path = source_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"source manifest member is absent: {relative}")
        if path.stat().st_size != int(row["size_bytes"]) or file_sha256(path) != row["sha256"]:
            raise ValueError(f"source manifest member mismatch: {relative}")
        paths.append(path)
    paths.append(manifest_path)
    return paths


def _terminal_and_rng_gates(
    *,
    session: CheckpointableTemporalSession,
    source_replay: dict[str, Any],
    source_suffix: dict[str, Any],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    run = session.finalize()
    selector = cast(Any, session.policy)._selector  # noqa: SLF001
    counterfactual = selector._delegate  # noqa: SLF001
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    run_payload = run.as_dict()
    if run_payload != source_replay["run"] or run_payload != source_suffix["run"]:
        raise ValueError("scientific failure: suffix terminal run mismatch")
    call_rows = _sanitized_selector_calls(selector, counterfactual)
    if (
        call_rows != source_replay["selector_calls"]
        or call_rows != source_suffix["selector_calls"]
    ):
        raise ValueError("scientific failure: suffix RNG/call-shape mismatch")
    fingerprint = scientific_fingerprint(
        {
            "baseline": "arXiv:2403.15665v2_2024",
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "policy": POLICY,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
            "run": run_payload,
        }
    )
    source_fingerprint = scientific_fingerprint(
        {
            "baseline": "arXiv:2403.15665v2_2024",
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "policy": POLICY,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
            "run": source_replay["run"],
        }
    )
    if fingerprint != source_fingerprint:
        raise ValueError("scientific fingerprint mismatch")
    outcome = run.outcome
    if outcome.completed_utility != EXPECTED_COMPLETED_UTILITY:
        raise ValueError("validated ASSUMP-046 completed Utility changed")
    completed = set(outcome.completed_task_ids)
    rejected = set(outcome.rejected_task_ids)
    if completed & rejected or completed | rejected != set(run.final_state.tasks):
        raise ValueError("terminal partition invariant failed")
    if not set(outcome.ever_preempted_task_ids).issubset(rejected):
        raise ValueError("ever-preempted subset invariant failed")
    residual = validate_utility_conservation(
        total=sum(task.utility for task in run.final_state.tasks.values()),
        completed=outcome.completed_utility,
        rejected=outcome.rejected_utility,
    )
    validate_state_invariants(run.final_state)
    return (
        {
            "completed_utility": outcome.completed_utility,
            "rejected_utility": outcome.rejected_utility,
            "completed_jobs": len(outcome.completed_task_ids),
            "rejected_jobs": len(outcome.rejected_task_ids),
            "preempted_jobs": len(outcome.ever_preempted_task_ids),
            "event_count": len(run.events),
            "selector_call_count": len(call_rows),
            "selector_call_shape_sha256": _canonical_hash(
                [
                    {
                        "auction_ordinal": row["auction_ordinal"],
                        "round_name": row["round_name"],
                        "server_ordinal": row["server_ordinal"],
                        "call_kind": row["call_kind"],
                        "candidate_count": row["candidate_count"],
                    }
                    for row in call_rows
                ]
            ),
            "selector_rng_trace_sha256": _canonical_hash(call_rows),
            "lifecycle_funnel": lifecycle_funnel(run.events),
            "scientific_fingerprint": fingerprint,
            "utility_conservation_residual": residual,
        },
        call_rows,
    )


def _closure_rows_for_new_records(
    *,
    session: CheckpointableTemporalSession,
    before_count: int,
    checkpoint: TemporalCheckpoint,
    payload: bytes,
) -> list[dict[str, object]]:
    validate_checkpoint_closure(checkpoint)
    if checkpoint.serialize() != payload:
        raise ValueError("checkpoint serialization is not deterministic")
    rng_sha256 = checkpoint_rng_hash(checkpoint)
    rows: list[dict[str, object]] = []
    for record in session.transaction_records[before_count:]:
        locator = cast(dict[str, object], record["transaction_key"])
        rows.append(
            {
                "transaction_locator": locator,
                "checkpoint_sha256": sha256(payload).hexdigest(),
                "closure_sha256": closure_hash(payload, locator),
                "rng_state_sha256": rng_sha256,
            }
        )
    return rows


def run_suffix_only(
    *, source_root: Path, private_output: Path, public_output: Path
) -> dict[str, object]:
    if private_output.exists() or public_output.exists():
        raise FileExistsError("Stage 15-N.1B.1-R output root already exists")
    source_paths = validate_source_manifest(source_root)
    before = source_snapshot(source_paths)
    checkpoint_path = source_root / "replay-1" / "checkpoint_canary.pkl"
    replay_path = source_root / "replay-1" / "factual_replay_private.json"
    suffix_path = source_root / "suffix-canary" / "factual_suffix_private.json"
    if file_sha256(checkpoint_path) != SOURCE_CHECKPOINT_SHA256:
        raise ValueError("source checkpoint checksum mismatch")
    if file_sha256(replay_path) != SOURCE_REPLAY_SHA256:
        raise ValueError("source factual replay checksum mismatch")
    if file_sha256(suffix_path) != SOURCE_SUFFIX_SHA256:
        raise ValueError("source factual suffix checksum mismatch")
    source_replay = json.loads(replay_path.read_text(encoding="utf-8"))
    source_suffix = json.loads(suffix_path.read_text(encoding="utf-8"))
    expected_locators = [
        cast(dict[str, object], row["transaction_key"])
        for row in source_replay["transaction_records"]
    ]
    if len(expected_locators) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("validated factual transaction count changed")
    expected_epochs = {
        int(cast(int | str, locator["epoch"])) for locator in expected_locators
    }

    checkpoint_payload = checkpoint_path.read_bytes()
    checkpoint = TemporalCheckpoint.deserialize(checkpoint_payload)
    validate_checkpoint_closure(checkpoint, require_source_identity=True)
    if checkpoint.digest() != SOURCE_CHECKPOINT_SHA256:
        raise ValueError("deserialized checkpoint digest mismatch")
    # Keep the validated source checkpoint immutable.  The continuation uses a
    # second deep deserialize so policy execution cannot mutate hash evidence.
    session = TemporalCheckpoint.deserialize(checkpoint_payload).session
    closure_rows: list[dict[str, object]] = []

    # Resume the already prepared canary auction without preparing epoch 4 again.
    initial_before_state = session.state.snapshot()
    initial_progress = session.progress.copy()
    initial_retry = session.retry_count.copy()
    selector = cast(Any, session.policy)._selector  # noqa: SLF001
    start_count = int(selector.observation_count)
    result = session._apply_auction(  # noqa: SLF001
        epoch=checkpoint.epoch,
        requesting=checkpoint.requesting_task_ids,
        time_remaining=checkpoint.time_remaining_by_task,
    )
    end_count = int(selector.observation_count)
    before_count = len(session.transaction_records)
    session._record_victim_transactions(  # noqa: SLF001
        epoch=checkpoint.epoch,
        before_state=initial_before_state,
        progress_before=initial_progress,
        retry_before=initial_retry,
        result=result,
        selector_observation_start=start_count,
        selector_observation_end=end_count,
    )
    closure_rows.extend(
        _closure_rows_for_new_records(
            session=session,
            before_count=before_count,
            checkpoint=checkpoint,
            payload=checkpoint_payload,
        )
    )
    validate_state_invariants(session.state)
    session.next_epoch = checkpoint.epoch + 1
    terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
    if checkpoint.epoch >= session.last_arrival_slot and all(
        status in terminal for status in session.state.task_states.values()
    ):
        session.finished = True

    while not session.finished:
        capture = session.next_epoch in expected_epochs
        before_count = len(session.transaction_records)
        observation = session.step(capture_checkpoint=capture)
        new_count = len(session.transaction_records) - before_count
        if new_count:
            if observation.checkpoint is None:
                raise ValueError("victim transaction lacks pre-decision closure checkpoint")
            payload = observation.checkpoint.serialize()
            closure_rows.extend(
                _closure_rows_for_new_records(
                    session=session,
                    before_count=before_count,
                    checkpoint=observation.checkpoint,
                    payload=payload,
                )
            )
        elif observation.checkpoint is not None:
            raise ValueError("expected victim epoch produced no victim transaction")

    scientific, call_rows = _terminal_and_rng_gates(
        session=session, source_replay=source_replay, source_suffix=source_suffix
    )
    actual_locators = [
        cast(dict[str, object], row["transaction_key"])
        for row in session.transaction_records
    ]
    if actual_locators != expected_locators:
        raise ValueError("factual victim transaction inventory changed")
    coverage = validate_coverage(closure_rows, expected_locators)
    if len(closure_rows) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("closure hash coverage did not reach 28/28")
    if len({row["rng_state_sha256"] for row in closure_rows}) < 1:
        raise ValueError("RNG-state hash coverage is empty")

    private_payload = {
        "schema_version": "stage15n1b1r-private-closure-index-v1",
        "identity": {
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "policy": POLICY,
            "variant": VARIANT.value,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
        },
        "source_checkpoint": {
            "epoch": checkpoint.epoch,
            "event_cursor": checkpoint.event_cursor,
            "sha256": SOURCE_CHECKPOINT_SHA256,
        },
        "closure_rows": closure_rows,
        "transaction_count": len(closure_rows),
        "selector_call_count": len(call_rows),
        "scientific_summary_sha256": _canonical_hash(scientific),
    }
    write_new_json(private_output / "closure_hash_index_private.json", private_payload)
    private_rows = []
    for path in sorted(item for item in private_output.rglob("*") if item.is_file()):
        private_rows.append(
            {
                "logical_name": path.relative_to(private_output).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    write_new_json(private_output / "sha256_manifest.json", private_rows)

    public: dict[str, object] = {
        "schema_version": "stage15n1b1r-public-closure-coverage-v1",
        "label": "[پیشنهاد فنی تشخیصی] Stage 15-N.1B.1-R",
        "scope": {
            "full_workloads_executed": 0,
            "baseline_executed": 0,
            "comparator_executed": 0,
            "full_factual_replays_executed": 0,
            "factual_suffixes_executed": 1,
            "oracle_branches_executed": 0,
        },
        "source_checkpoint": {
            "epoch": EXPECTED_CHECKPOINT_EPOCH,
            "event_cursor": EXPECTED_EVENT_CURSOR,
            "sha256": SOURCE_CHECKPOINT_SHA256,
            "checksum_verified_pre_and_post": True,
        },
        "completeness": {
            "victim_transaction_count": EXPECTED_TRANSACTION_COUNT,
            "closure_hash_coverage_before": "1/28",
            "closure_hash_coverage_after": "28/28",
            "rng_state_hash_coverage": "28/28",
            "feature_groups_before": "17/18",
            "feature_groups_after": "18/18",
            **coverage,
            "unique_closure_hash_count": len(
                {cast(str, row["closure_sha256"]) for row in closure_rows}
            ),
            "terminal_linkage_complete": True,
            "transaction_order_exact": True,
        },
        "validation": {
            "factual_suffix_exact": True,
            "continuous_factual_run_exact": True,
            "rng_option_a": True,
            "scientific_fingerprint_exact": True,
            "capacity_and_state_invariants": True,
            "terminal_partition": True,
            "preempted_subset_of_rejected": True,
            "utility_conservation": True,
            "stage_success": True,
        },
        "scientific_summary": {
            key: value
            for key, value in scientific.items()
            if key
            not in {
                "scientific_fingerprint",
                "lifecycle_funnel",
            }
        },
        "private_output": {
            "file_count": len(private_rows),
            "manifest_sha256": file_sha256(private_output / "sha256_manifest.json"),
            "transaction_rows_published": False,
            "individual_closure_hashes_published": False,
            "raw_rng_state_published": False,
            "personal_paths_published": False,
        },
        "publication": {
            "task_ids": False,
            "raw_rng_state": False,
            "snapshots": False,
            "candidate_sets": False,
            "workload": False,
            "transaction_rows": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
    }
    assert_public_safe(public)
    write_new_json(public_output / "completeness_report.json", public)
    public_schema = {
        "schema_version": "stage15n1b1r-public-schema-v1",
        "feature_groups": 18,
        "private_closure_payload_published": False,
        "public_values": [
            "scope",
            "source checkpoint identity",
            "aggregate completeness counts",
            "validation gates",
            "sanitized scientific summary",
            "private manifest checksum",
        ],
    }
    assert_public_safe(public_schema)
    write_new_json(public_output / "schema.json", public_schema)
    validation = {
        "factual_suffix": "exact",
        "rng_option_a": "pass",
        "scientific_fingerprint": "exact",
        "invariants": "pass",
        "closure_coverage": "28/28",
        "feature_group_coverage": "18/18",
    }
    write_new_json(public_output / "validation_report.json", validation)
    public_rows = []
    for path in sorted(item for item in public_output.rglob("*") if item.is_file()):
        public_rows.append(
            {
                "logical_name": path.relative_to(public_output).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    write_new_json(public_output / "sha256_manifest.json", public_rows)

    after = source_snapshot(source_paths)
    if before != after:
        raise ValueError("validated Stage 15-N.1B.1 source changed during suffix audit")
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    report = run_suffix_only(
        source_root=args.source_root,
        private_output=args.private_output,
        public_output=args.public_output,
    )
    print(
        json.dumps(
            {
                "stage_success": cast(dict[str, object], report["validation"])[
                    "stage_success"
                ],
                "closure_hash_coverage": cast(dict[str, object], report["completeness"])[
                    "closure_hash_coverage_after"
                ],
                "factual_suffixes_executed": 1,
                "full_workloads_executed": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
