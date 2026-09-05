"""Materialize Stage 15-N Oracle checkpoints from one factual ASSUMP-046 run.

The runner is intentionally cloud-only.  It executes exactly one approved factual
run, records immutable pre-auction checkpoints through a no-op post-selection
hook, and refuses to emit a bundle unless the factual result matches the pinned
ASSUMP-046 comparator.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls
from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY,
    POLICY_SEED,
    VARIANT,
    WORKLOAD_SEED,
    _build_session,
    _fingerprint,
    _terminal_linkage,
    assert_public_safe,
    validate_utility_conservation,
)
from run_stage15n1b1r_suffix_hash_coverage import (
    checkpoint_rng_hash,
    closure_hash,
    file_sha256,
)

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
    dkp_pre_commit_diagnostic_hook,
)
from edge_reproduction.diagnostics.dk_funnel import lifecycle_funnel
from edge_reproduction.diagnostics.oracle_checkpoint import (
    SEMANTIC_SCHEMA_VERSION,
    SemanticRestorableTransactionCheckpoint,
    public_payload_is_sanitized,
    write_atomic_new,
)
from edge_reproduction.diagnostics.temporal_checkpoint import (
    CheckpointableTemporalSession,
    TemporalCheckpoint,
)
from edge_reproduction.experiments.pipe_normal_full import load_full_config
from edge_reproduction.models.enums import TaskState
from edge_reproduction.simulation.invariants import validate_state_invariants

EXPECTED_COMPARATOR_FIXTURE_SHA256 = (
    "06eec52a4d346cb6014b8cd29e73323659a5c72c4e8ac86e81dac57932a25c12"
)
EXPECTED_SOURCE_ARTIFACT_SHA256 = (
    "e37204aa7fa8516db1224cd13c59076e52699647751be99672ad412fc37e7d4e"
)
EXPECTED_COMPLETED_UTILITY = 9541.426964770584
EXPECTED_REJECTED_UTILITY = 74460.00877807708
EXPECTED_COMPLETED_JOBS = 117
EXPECTED_PREEMPTED_JOBS = 29
EXPECTED_ROUND_TWO_ADMISSION = 146
EXPECTED_EVENT_COUNT = 15770
EXPECTED_SELECTOR_CALL_COUNT = 1744
EXPECTED_TRANSACTION_COUNT = 28


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _manifest(root: Path) -> list[dict[str, object]]:
    return [
        {
            "logical_name": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.name != "sha256_manifest.json"
    ]


def _load_comparator(path: Path) -> dict[str, Any]:
    if file_sha256(path) != EXPECTED_COMPARATOR_FIXTURE_SHA256:
        raise ValueError("ASSUMP-046 comparator fixture checksum mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = cast(list[dict[str, Any]], payload["pairs"])
    matches = [
        row
        for row in rows
        if row.get("workload_seed") == WORKLOAD_SEED
        and row.get("policy") == POLICY
        and row.get("variant") == VARIANT.value
    ]
    if len(matches) != 1:
        raise ValueError("pinned comparator pair is missing or duplicated")
    comparator = matches[0]
    if (
        comparator.get("source_artifact_sha256")
        != EXPECTED_SOURCE_ARTIFACT_SHA256
        or comparator.get("replay_exact") is not True
        or comparator.get("policy_seed") != POLICY_SEED
    ):
        raise ValueError("ASSUMP-046 comparator provenance mismatch")
    return comparator


@dataclass(slots=True)
class BootstrapMaterializer:
    output_root: Path
    server_ordinals: dict[str, int]
    current_checkpoint: TemporalCheckpoint | None = None
    rows: list[dict[str, object]] = field(default_factory=list)
    hook_calls: int = 0

    def arm(self, checkpoint: TemporalCheckpoint) -> None:
        if self.current_checkpoint is not None:
            raise RuntimeError("bootstrap materializer already armed")
        self.current_checkpoint = checkpoint

    def disarm(self) -> None:
        self.current_checkpoint = None

    def __call__(self, context: DKPPreCommitContext) -> DKPPreCommitAction:
        self.hook_calls += 1
        if not context.preempted_task_ids:
            return DKPPreCommitAction.COMMIT
        checkpoint = self.current_checkpoint
        if checkpoint is None:
            raise ValueError("victim transaction reached without checkpoint")
        sequence = len(self.rows)
        if sequence >= EXPECTED_TRANSACTION_COUNT:
            raise ValueError("orphan victim transaction in factual bootstrap")
        locator: dict[str, object] = {
            "epoch": context.epoch,
            "server_id": context.server_id,
            "server_ordinal": self.server_ordinals[context.server_id],
            "sequence": sequence,
        }
        checkpoint_payload = checkpoint.serialize()
        package = SemanticRestorableTransactionCheckpoint.create(
            checkpoint_payload=checkpoint_payload,
            transaction_locator=locator,
            precommit_context=context,
            legacy_raw_pickle_sha256=closure_hash(checkpoint_payload, locator),
            legacy_raw_checkpoint_sha256=checkpoint.digest(),
            rng_state_sha256=checkpoint_rng_hash(checkpoint),
            workload_sha256=EXPECTED_WORKLOAD_SHA256,
            config_sha256=EXPECTED_CONFIG_SHA256,
            policy_seed=POLICY_SEED,
        )
        path = self.output_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        write_atomic_new(path, package.serialize())
        restored = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        restored.restore()
        if restored.semantic_closure_sha256 != package.semantic_closure_sha256:
            raise ValueError("semantic closure changed after immediate restore")
        self.rows.append(
            {
                "sequence": sequence,
                "epoch": context.epoch,
                "event_cursor": checkpoint.event_cursor,
                "semantic_closure_sha256": package.semantic_closure_sha256,
                "rng_state_sha256": package.rng_state_sha256,
                "payload_sha256": file_sha256(path),
            }
        )
        return DKPPreCommitAction.COMMIT


def _advance(session: CheckpointableTemporalSession, epoch: int) -> None:
    validate_state_invariants(session.state)
    terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
    all_terminal = all(
        status in terminal for status in session.state.task_states.values()
    )
    session.next_epoch = epoch + 1
    if (epoch >= session.last_arrival_slot and all_terminal) or (
        epoch >= session.configured_last_slot
    ):
        session.finished = True


def _run_factual(
    config: dict[str, object], private_root: Path
) -> tuple[dict[str, Any], BootstrapMaterializer]:
    session, selector, counterfactual, workload_hash = _build_session(config)
    materializer = BootstrapMaterializer(
        private_root,
        {server_id: ordinal for ordinal, server_id in enumerate(session.state.servers)},
    )
    while not session.finished:
        epoch = session.next_epoch
        requesting, time_remaining = session._prepare_epoch(epoch)  # noqa: SLF001
        if not requesting:
            _advance(session, epoch)
            continue
        before_state = session.state.snapshot()
        progress_before = session.progress.copy()
        retry_before = session.retry_count.copy()
        selector_start = int(selector.observation_count)
        checkpoint = session.checkpoint(
            epoch=epoch,
            requesting_task_ids=requesting,
            time_remaining_by_task=time_remaining,
        )
        materializer.arm(checkpoint)
        try:
            with dkp_pre_commit_diagnostic_hook(materializer):
                result = session._apply_auction(  # noqa: SLF001
                    epoch=epoch,
                    requesting=requesting,
                    time_remaining=time_remaining,
                )
        finally:
            materializer.disarm()
        selector_end = int(selector.observation_count)
        session._record_victim_transactions(  # noqa: SLF001
            epoch=epoch,
            before_state=before_state,
            progress_before=progress_before,
            retry_before=retry_before,
            result=result,
            selector_observation_start=selector_start,
            selector_observation_end=selector_end,
        )
        _advance(session, epoch)

    run = session.finalize()
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    validate_state_invariants(run.final_state)
    call_rows = _sanitized_selector_calls(selector, counterfactual)
    _terminal_linkage(session.transaction_records, run, call_rows)
    outcome = run.outcome
    completed = set(outcome.completed_task_ids)
    rejected = set(outcome.rejected_task_ids)
    if completed & rejected or completed | rejected != set(run.final_state.tasks):
        raise ValueError("factual bootstrap terminal partition failed")
    if not set(outcome.ever_preempted_task_ids).issubset(rejected):
        raise ValueError("factual bootstrap preempted subset failed")
    residual = validate_utility_conservation(
        total=sum(task.utility for task in run.final_state.tasks.values()),
        completed=outcome.completed_utility,
        rejected=outcome.rejected_utility,
    )
    return (
        {
            "schema_version": "stage15n1b2g-private-factual-bootstrap-v1",
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "variant": VARIANT.value,
            "workload_sha256": workload_hash,
            "run": run.as_dict(),
            "transaction_records": session.transaction_records,
            "selector_calls": call_rows,
            "raw_final_rng_state": counterfactual._counting_rng.getstate(),  # noqa: SLF001
            "scientific_fingerprint": _fingerprint(run, workload_hash=workload_hash),
            "selector_funnel": selector.summary().as_dict(),
            "auction_funnel": cast(Any, session.policy).summary(),
            "lifecycle_funnel": lifecycle_funnel(run.events),
            "counterfactual": counterfactual.counterfactual_summary(),
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
            "utility_conservation_residual": residual,
        },
        materializer,
    )


def run_bootstrap(
    *, config_path: Path, comparator_path: Path, private_root: Path, public_root: Path
) -> dict[str, object]:
    if private_root.exists() or public_root.exists():
        raise FileExistsError("bootstrap output roots must not exist")
    if file_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved PIPE-NORMAL config checksum mismatch")
    comparator = _load_comparator(comparator_path)
    config = load_full_config(config_path)
    factual, materializer = _run_factual(config, private_root)
    run = cast(dict[str, Any], factual["run"])
    outcome = cast(dict[str, Any], run["outcome"])
    fingerprint = cast(dict[str, Any], factual["scientific_fingerprint"])
    expected_fingerprint = cast(dict[str, Any], comparator["scientific_fingerprint"])
    if fingerprint != expected_fingerprint:
        raise ValueError("factual bootstrap fingerprint differs from comparator")
    if factual["selector_funnel"] != comparator["selector_funnel"]:
        raise ValueError("factual bootstrap selector funnel differs from comparator")
    if factual["auction_funnel"] != comparator["auction_funnel"]:
        raise ValueError("factual bootstrap auction funnel differs from comparator")
    if factual["lifecycle_funnel"] != comparator["lifecycle_funnel"]:
        raise ValueError("factual bootstrap lifecycle funnel differs from comparator")
    if factual["counterfactual"] != comparator["counterfactual"]:
        raise ValueError("factual bootstrap GA counters differ from comparator")
    round_two = cast(dict[str, Any], factual["auction_funnel"])["totals"]
    expected_scalars = (
        float(outcome["completed_utility"]) == EXPECTED_COMPLETED_UTILITY,
        float(outcome["rejected_utility"]) == EXPECTED_REJECTED_UTILITY,
        int(outcome["completed_jobs"]) == EXPECTED_COMPLETED_JOBS,
        int(outcome["ever_preempted_jobs"]) == EXPECTED_PREEMPTED_JOBS,
        int(round_two["round_2_accepted"]) == EXPECTED_ROUND_TWO_ADMISSION,
        len(cast(list[object], run["events"])) == EXPECTED_EVENT_COUNT,
        len(cast(list[object], factual["selector_calls"]))
        == EXPECTED_SELECTOR_CALL_COUNT,
    )
    if not all(expected_scalars):
        raise ValueError("factual bootstrap scalar comparator mismatch")
    if len(materializer.rows) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("checkpoint coverage is not 28/28")
    sequences = [
        int(cast(int | str, row["sequence"])) for row in materializer.rows
    ]
    if sequences != list(range(EXPECTED_TRANSACTION_COUNT)):
        raise ValueError("checkpoint sequence has missing, duplicate, or orphan rows")
    for sequence in sequences:
        path = private_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        package = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        package.restore()
        if package.semantic_schema_version != SEMANTIC_SCHEMA_VERSION:
            raise ValueError("checkpoint semantic schema mismatch")

    write_atomic_new(private_root / "factual_bootstrap_private.json", _json_bytes(factual))
    write_atomic_new(
        private_root / "checkpoint_inventory_private.json",
        _json_bytes({"rows": materializer.rows}),
    )
    private_manifest = _manifest(private_root)
    write_atomic_new(private_root / "sha256_manifest.json", _json_bytes(private_manifest))
    public: dict[str, object] = {
        "schema_version": "stage15n1b2g-public-bootstrap-v1",
        "label": "[پیشنهاد فنی تشخیصی]",
        "scope": {
            "workload_seed": str(WORKLOAD_SEED),
            "policy": "DK-P",
            "variant": "ASSUMP-046",
            "factual_bootstrap_runs": 1,
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
        "inventory": materializer.rows,
        "private_manifest": {
            "sha256": file_sha256(private_root / "sha256_manifest.json"),
            "entry_count": len(private_manifest),
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
    write_atomic_new(public_root / "bootstrap_validation.json", _json_bytes(public))
    write_atomic_new(
        public_root / "sha256_manifest.json", _json_bytes(_manifest(public_root))
    )
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--comparator", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    args = parser.parse_args()
    report = run_bootstrap(
        config_path=args.config,
        comparator_path=args.comparator,
        private_root=args.private_root,
        public_root=args.public_root,
    )
    print(json.dumps({"status": "complete", "coverage": report["coverage"]}))


if __name__ == "__main__":
    main()
