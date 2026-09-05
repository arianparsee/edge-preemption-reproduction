"""Run resume-safe trusted-local retain branches from semantic checkpoints.

This diagnostic runner never builds or executes a full workload, baseline,
comparator, factual replay, or factual suffix.  Each independent branch restores
one approved pre-commit checkpoint, vetoes exactly its factual transaction, and
then follows the unmodified temporal engine to termination.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import shutil
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import median
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls
from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY,
    POLICY_SEED,
    WORKLOAD_SEED,
    _terminal_linkage,
    validate_utility_conservation,
)
from run_stage15n1b1r_suffix_hash_coverage import (
    EXPECTED_TRANSACTION_COUNT,
    SOURCE_REPLAY_SHA256,
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
from edge_reproduction.models.enums import TaskState
from edge_reproduction.simulation.invariants import validate_state_invariants

EXPECTED_INPUT_MANIFEST_SHA256 = (
    "d33a657e55702c76f1aa15e0b8c1f26193c85ce52becc99a097223faecf9f4a7"
)
EXPECTED_COMPLETED_UTILITY = 9541.426964770584
EXPECTED_EVENT_COUNT = 15770
EXPECTED_SELECTOR_CALL_COUNT = 1744
TOLERANCE = 1e-9


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _compact_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _memory_status() -> tuple[int, int]:
    fields = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]
    status_type = type("MemoryStatusEx", (ctypes.Structure,), {"_fields_": fields})
    status = status_type()
    status.dwLength = ctypes.sizeof(status_type)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return int(status.ullTotalPhys), int(status.ullAvailPhys)


def _resource_gate(output_parent: Path, *, required_free_bytes: int) -> dict[str, int]:
    disk = shutil.disk_usage(output_parent)
    total_ram, available_ram = _memory_status()
    if disk.free < required_free_bytes:
        raise OSError("insufficient disk for resume-safe Oracle outputs")
    if available_ram < 2 * 1024**3:
        raise MemoryError("less than 2 GiB RAM available for sequential Oracle")
    return {
        "disk_free_bytes": disk.free,
        "disk_required_bytes": required_free_bytes,
        "ram_total_bytes": total_ram,
        "ram_available_bytes": available_ram,
    }


def _load_inputs(
    *, checkpoint_root: Path, source_root: Path
) -> tuple[list[SemanticRestorableTransactionCheckpoint], dict[str, Any]]:
    manifest_path = checkpoint_root / "sha256_manifest.json"
    if file_sha256(manifest_path) != EXPECTED_INPUT_MANIFEST_SHA256:
        raise ValueError("semantic checkpoint manifest checksum mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise TypeError("semantic checkpoint manifest must be a list")
    for row in manifest:
        relative = cast(str, row["logical_name"])
        path = checkpoint_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"checkpoint manifest member missing: {relative}")
        if path.stat().st_size != int(row["size_bytes"]):
            raise ValueError(f"checkpoint manifest size mismatch: {relative}")
        if file_sha256(path) != row["sha256"]:
            raise ValueError(f"checkpoint manifest hash mismatch: {relative}")
    packages: list[SemanticRestorableTransactionCheckpoint] = []
    for sequence in range(EXPECTED_TRANSACTION_COUNT):
        path = checkpoint_root / "payloads" / f"transaction-{sequence:03d}.pkl"
        package = SemanticRestorableTransactionCheckpoint.deserialize(path.read_bytes())
        if package.semantic_schema_version != SEMANTIC_SCHEMA_VERSION:
            raise ValueError("semantic checkpoint schema mismatch")
        if package.workload_sha256 != EXPECTED_WORKLOAD_SHA256:
            raise ValueError("checkpoint workload identity mismatch")
        if package.config_sha256 != EXPECTED_CONFIG_SHA256:
            raise ValueError("checkpoint config identity mismatch")
        if package.policy_seed != POLICY_SEED:
            raise ValueError("checkpoint policy seed mismatch")
        if int(cast(int | str, package.transaction_locator["sequence"])) != sequence:
            raise ValueError("checkpoint sequence mismatch")
        package.restore()
        packages.append(package)
    if len({item.semantic_closure_sha256 for item in packages}) != len(packages):
        raise ValueError("semantic checkpoint hashes are not unique")
    replay_path = source_root / "replay-1" / "factual_replay_private.json"
    if file_sha256(replay_path) != SOURCE_REPLAY_SHA256:
        raise ValueError("factual reference checksum mismatch")
    factual = json.loads(replay_path.read_text(encoding="utf-8"))
    records = cast(list[dict[str, Any]], factual["transaction_records"])
    if len(records) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("factual transaction inventory mismatch")
    for package, record in zip(packages, records, strict=True):
        if package.transaction_locator != record["transaction_key"]:
            raise ValueError("checkpoint/factual transaction identity mismatch")
    return packages, factual


class RetainExactlyOnce:
    def __init__(self, expected_context: DKPPreCommitContext) -> None:
        self.expected_context = expected_context
        self.calls = 0
        self.interventions = 0

    def __call__(self, context: DKPPreCommitContext) -> DKPPreCommitAction:
        self.calls += 1
        if self.interventions == 0 and context == self.expected_context:
            self.interventions = 1
            return DKPPreCommitAction.RETAIN_CURRENT_REJECT_RETURNING
        return DKPPreCommitAction.COMMIT


def _advance_after_prepared_auction(
    session: CheckpointableTemporalSession, *, epoch: int
) -> None:
    validate_state_invariants(session.state)
    terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
    session.next_epoch = epoch + 1
    if (
        epoch >= session.last_arrival_slot
        and all(status in terminal for status in session.state.task_states.values())
    ) or epoch >= session.configured_last_slot:
        session.finished = True


def _execute_branch(
    package: SemanticRestorableTransactionCheckpoint,
    factual: dict[str, Any],
) -> dict[str, Any]:
    checkpoint: TemporalCheckpoint = package.restore()
    session = checkpoint.session
    hook = RetainExactlyOnce(package.precommit_context)
    before_state = session.state.snapshot()
    progress_before = session.progress.copy()
    retry_before = session.retry_count.copy()
    selector = cast(Any, session.policy)._selector  # noqa: SLF001
    start_count = int(selector.observation_count)
    with dkp_pre_commit_diagnostic_hook(hook):
        result = session._apply_auction(  # noqa: SLF001
            epoch=checkpoint.epoch,
            requesting=checkpoint.requesting_task_ids,
            time_remaining=checkpoint.time_remaining_by_task,
        )
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
        _advance_after_prepared_auction(session, epoch=checkpoint.epoch)
        while not session.finished:
            session.step(capture_checkpoint=False)
    if hook.interventions != 1:
        raise ValueError("Oracle intervention did not occur exactly once")

    run = session.finalize()
    delegate = selector._delegate  # noqa: SLF001
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | delegate.runtime_metadata()
    )
    validate_state_invariants(run.final_state)
    call_rows = _sanitized_selector_calls(selector, delegate)
    _terminal_linkage(session.transaction_records, run, call_rows)
    run_payload = run.as_dict()
    outcome = run.outcome
    completed = set(outcome.completed_task_ids)
    rejected = set(outcome.rejected_task_ids)
    if completed & rejected or completed | rejected != set(run.final_state.tasks):
        raise ValueError("Oracle terminal partition invariant failed")
    if not set(outcome.ever_preempted_task_ids).issubset(rejected):
        raise ValueError("Oracle ever-preempted subset invariant failed")
    residual = validate_utility_conservation(
        total=sum(task.utility for task in run.final_state.tasks.values()),
        completed=outcome.completed_utility,
        rejected=outcome.rejected_utility,
    )
    events = tuple(run.events)
    funnel = lifecycle_funnel(events)
    accepted_ids = {
        event.task_id for event in events if event.event_type.value == "accepted"
    }
    expired_ids = {
        event.task_id for event in events if event.event_type.value == "expired"
    }
    never_admitted_expired = len(expired_ids - accepted_ids)
    fingerprint = scientific_fingerprint(
        {
            "workload_seed": WORKLOAD_SEED,
            "policy_seed": POLICY_SEED,
            "policy": POLICY,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
            "run": run_payload,
        }
    )
    rng_state = delegate._counting_rng.getstate()  # noqa: SLF001
    partition_hash = _canonical_hash(
        {
            "completed": outcome.completed_task_ids,
            "rejected": outcome.rejected_task_ids,
            "preempted": outcome.ever_preempted_task_ids,
        }
    )
    return {
        "run": run_payload,
        "selector_calls": call_rows,
        "raw_final_rng_state": rng_state,
        "scientific_fingerprint": fingerprint,
        "task_partition_sha256": partition_hash,
        "lifecycle_funnel": funnel,
        "never_admitted_expired": never_admitted_expired,
        "transaction_records": session.transaction_records,
        "hook_calls": hook.calls,
        "interventions": hook.interventions,
        "utility_conservation_residual": residual,
    }


def _call_shape(row: dict[str, object]) -> dict[str, object]:
    return {
        "auction_ordinal": row["auction_ordinal"],
        "round_name": row["round_name"],
        "server_ordinal": row["server_ordinal"],
        "call_kind": row["call_kind"],
        "candidate_count": row["candidate_count"],
    }


def _first_divergence(
    factual: list[dict[str, object]], branch: list[dict[str, object]]
) -> dict[str, object]:
    for index, (left, right) in enumerate(zip(factual, branch, strict=False)):
        if _call_shape(left) != _call_shape(right):
            return {
                "kind": "call_shape",
                "call_index": index,
                "factual_shape": _call_shape(left),
                "retain_shape": _call_shape(right),
            }
        if left != right:
            return {"kind": "rng_evidence", "call_index": index}
    if len(factual) != len(branch):
        return {
            "kind": "call_count",
            "call_index": min(len(factual), len(branch)),
            "factual_call_count": len(factual),
            "retain_call_count": len(branch),
        }
    return {"kind": "none", "call_index": None}


def _branch_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    run = cast(dict[str, Any], payload["run"])
    outcome = cast(dict[str, Any], run["outcome"])
    funnel = cast(dict[str, int], payload["lifecycle_funnel"])
    return {
        "completed_utility": float(outcome["completed_utility"]),
        "rejected_utility": float(outcome["rejected_utility"]),
        "completed_jobs": int(outcome["completed_jobs"]),
        "rejected_jobs": int(outcome["rejected_jobs"]),
        "preempted_jobs": int(outcome["ever_preempted_jobs"]),
        "retry_scheduled": int(funnel.get("retry_scheduled", 0)),
        "expired": int(funnel.get("expired", 0)),
        "never_admitted_expired": int(payload["never_admitted_expired"]),
        "event_count": len(cast(list[object], run["events"])),
        "selector_call_count": len(cast(list[object], payload["selector_calls"])),
    }


def _lifecycle_funnel_from_dicts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for event in events:
        event_type = str(event["event_type"])
        counts[event_type] += 1
        if event_type != "expired":
            continue
        reason = str(event["reason"])
        if reason.startswith("post_rejection_next_epoch_infeasible"):
            counts["expired_after_round_2_rejection"] += 1
        elif reason.startswith("canonical_admission_infeasible"):
            counts["expired_during_canonicalization"] += 1
        elif reason == "waiting_task_no_remaining_completion_opportunity":
            counts["expired_waiting_at_deadline"] += 1
        elif reason == "active_pipeline_incomplete_after_inclusive_deadline_opportunity":
            counts["expired_active_at_deadline"] += 1
    return dict(sorted(counts.items()))


def _maximum_chain_depth(records: list[dict[str, Any]]) -> int:
    return max(
        (int(record.get("preemption_chain_depth", 0)) for record in records),
        default=0,
    )


def _private_branch_result(
    *,
    sequence: int,
    package: SemanticRestorableTransactionCheckpoint,
    factual: dict[str, Any],
    factual_record: dict[str, Any],
    first: dict[str, Any],
    runtime_seconds: float,
) -> dict[str, object]:
    factual_run = cast(dict[str, Any], factual["run"])
    factual_outcome = cast(dict[str, Any], factual_run["outcome"])
    factual_calls = cast(list[dict[str, object]], factual["selector_calls"])
    branch_calls = cast(list[dict[str, object]], first["selector_calls"])
    divergence = _first_divergence(factual_calls, branch_calls)
    factual_rng_hash = _canonical_hash(factual["raw_final_rng_state"])
    branch_rng_hash = _canonical_hash(first["raw_final_rng_state"])
    shapes_equal = [_call_shape(row) for row in factual_calls] == [
        _call_shape(row) for row in branch_calls
    ]
    if shapes_equal and factual_rng_hash != branch_rng_hash:
        raise ValueError("RNG mismatch without candidate/call-shape divergence")
    branch_run = cast(dict[str, Any], first["run"])
    final_states = cast(dict[str, str], branch_run["final_task_states"])
    planned = cast(dict[str, Any], factual_record["planned"])
    incoming = tuple(cast(list[str], planned["accepted"]))
    victims = tuple(cast(list[str], planned["preempted"]))
    involved = incoming + victims
    task_features = cast(dict[str, dict[str, Any]], factual_record["task_features"])
    factual_states = cast(dict[str, str], factual_run["final_task_states"])

    def completed_utility(states: dict[str, str]) -> float:
        return float(
            sum(
                float(task_features[task_id]["utility"])
                for task_id in involved
                if states[task_id] == "completed"
            )
        )

    branch_metrics = _branch_metrics(first)
    factual_events = cast(list[dict[str, Any]], factual_run["events"])
    factual_funnel = _lifecycle_funnel_from_dicts(factual_events)
    factual_accepted = {
        cast(str, event["task_id"])
        for event in factual_events
        if event["event_type"] == "accepted"
    }
    factual_expired = {
        cast(str, event["task_id"])
        for event in factual_events
        if event["event_type"] == "expired"
    }
    factual_metrics = {
        "completed_utility": float(factual_outcome["completed_utility"]),
        "rejected_utility": float(factual_outcome["rejected_utility"]),
        "completed_jobs": int(factual_outcome["completed_jobs"]),
        "rejected_jobs": int(factual_outcome["rejected_jobs"]),
        "preempted_jobs": int(factual_outcome["ever_preempted_jobs"]),
        "retry_scheduled": int(factual_funnel.get("retry_scheduled", 0)),
        "expired": int(factual_funnel.get("expired", 0)),
        "never_admitted_expired": len(factual_expired - factual_accepted),
        "event_count": len(cast(list[object], factual_run["events"])),
        "selector_call_count": len(factual_calls),
    }
    delta = branch_metrics["completed_utility"] - factual_metrics["completed_utility"]
    label = "HARMFUL" if delta > TOLERANCE else "BENEFICIAL" if delta < -TOLERANCE else "NEUTRAL"
    local_incoming = float(factual_record["local_utility"]["incoming"])
    local_victim = float(factual_record["local_utility"]["victim"])
    direct_delta = completed_utility(final_states) - completed_utility(factual_states)
    return {
        "schema_version": "stage15n1b2-private-oracle-branch-v1",
        "sequence": sequence,
        "identity": {
            "transaction_locator": package.transaction_locator,
            "semantic_closure_sha256": package.semantic_closure_sha256,
            "restorable_checkpoint_sha256": sha256(package.checkpoint_payload).hexdigest(),
            "workload_sha256": package.workload_sha256,
            "config_sha256": package.config_sha256,
            "policy_seed": package.policy_seed,
        },
        "intervention": {
            "action": "retain_current_reject_returning",
            "count": first["interventions"],
            "hook_calls": first["hook_calls"],
            "ga_reruns": 0,
            "replacement_victims_or_subsets": 0,
        },
        "decision_features": {
            "current_count": len(package.precommit_context.current_task_ids),
            "returning_count": len(package.precommit_context.returning_task_ids),
            "incoming_count": len(incoming),
            "victim_count": len(victims),
            "local_incoming_utility": local_incoming,
            "local_victim_utility": local_victim,
            "local_net_utility": local_incoming - local_victim,
            "task_features": task_features,
            "planned_residual": package.precommit_context.planned_residual.as_dict(),
        },
        "terminal": {
            "factual_metrics": factual_metrics,
            "retain_metrics": branch_metrics,
            "oracle_delta": delta,
            "oracle_label": label,
            "involved_factual_completed_utility": completed_utility(factual_states),
            "involved_retain_completed_utility": completed_utility(final_states),
            "direct_involved_delta": direct_delta,
            "downstream_path_delta": delta - direct_delta,
            "incoming_outcomes": {task_id: final_states[task_id] for task_id in incoming},
            "victim_outcomes": {task_id: final_states[task_id] for task_id in victims},
            "chain_depth_factual": int(factual_record["preemption_chain_depth"]),
            "chain_depth_retain": _maximum_chain_depth(
                cast(list[dict[str, Any]], first["transaction_records"])
            ),
        },
        "divergence": divergence,
        "validation": {
            "replay_exact": True,
            "rng_option_a": True,
            "scientific_fingerprint_exact_between_replays": True,
            "terminal_partition": True,
            "utility_conservation_residual": first["utility_conservation_residual"],
            "intervention_exactly_once": True,
            "factual_history_checkpoint_verified": True,
        },
        "runtime_seconds_two_replays": runtime_seconds,
    }


def _replays_equal(first: dict[str, Any], second: dict[str, Any]) -> None:
    keys = (
        "run",
        "selector_calls",
        "raw_final_rng_state",
        "scientific_fingerprint",
        "task_partition_sha256",
        "lifecycle_funnel",
        "never_admitted_expired",
        "transaction_records",
        "hook_calls",
        "interventions",
        "utility_conservation_residual",
    )
    differences = [key for key in keys if first[key] != second[key]]
    if differences:
        raise ValueError(f"Oracle replay mismatch: {differences}")


def _branch_paths(output_root: Path, sequence: int) -> tuple[Path, Path]:
    branch = output_root / "branches" / f"transaction-{sequence:03d}.json"
    checksum = output_root / "branches" / f"transaction-{sequence:03d}.sha256"
    return branch, checksum


def _load_completed_branch(output_root: Path, sequence: int) -> dict[str, object] | None:
    branch, checksum = _branch_paths(output_root, sequence)
    if not branch.exists() and not checksum.exists():
        return None
    if not branch.is_file() or not checksum.is_file():
        raise ValueError("partial Oracle branch output exists")
    expected = checksum.read_text(encoding="ascii").strip()
    if expected != file_sha256(branch):
        raise ValueError("Oracle branch checksum mismatch")
    payload = json.loads(branch.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "stage15n1b2-private-oracle-branch-v1":
        raise ValueError("Oracle branch schema mismatch")
    if int(payload["sequence"]) != sequence:
        raise ValueError("Oracle branch sequence mismatch")
    return cast(dict[str, object], payload)


def _persist_branch(
    output_root: Path, sequence: int, payload: dict[str, object]
) -> None:
    branch, checksum = _branch_paths(output_root, sequence)
    raw = _json_bytes(payload)
    write_atomic_new(branch, raw)
    digest = file_sha256(branch)
    write_atomic_new(checksum, f"{digest}\n".encode("ascii"))
    if _load_completed_branch(output_root, sequence) is None:
        raise AssertionError("persisted Oracle branch cannot be restored")


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


def _aggregate(branches: list[dict[str, Any]]) -> dict[str, object]:
    labels = Counter(cast(str, item["terminal"]["oracle_label"]) for item in branches)
    deltas = [float(item["terminal"]["oracle_delta"]) for item in branches]
    local_nets = [float(item["decision_features"]["local_net_utility"]) for item in branches]
    oracle_labels = [cast(str, item["terminal"]["oracle_label"]) for item in branches]
    local_positive_terminal_negative = sum(
        local > TOLERANCE and label == "HARMFUL"
        for local, label in zip(local_nets, oracle_labels, strict=True)
    )
    local_prediction_matches = sum(
        (local > TOLERANCE and label == "BENEFICIAL")
        or (local < -TOLERANCE and label == "HARMFUL")
        or (abs(local) <= TOLERANCE and label == "NEUTRAL")
        for local, label in zip(local_nets, oracle_labels, strict=True)
    )
    divergence = Counter(cast(str, item["divergence"]["kind"]) for item in branches)
    direct = [float(item["terminal"]["direct_involved_delta"]) for item in branches]
    downstream = [float(item["terminal"]["downstream_path_delta"]) for item in branches]
    by_label: dict[str, object] = {}
    for label in ("HARMFUL", "BENEFICIAL", "NEUTRAL"):
        group = [item for item in branches if item["terminal"]["oracle_label"] == label]
        by_label[label] = {
            "count": len(group),
            "mean_local_net_utility": (
                sum(float(item["decision_features"]["local_net_utility"]) for item in group)
                / len(group)
                if group
                else None
            ),
            "mean_incoming_count": (
                sum(int(item["decision_features"]["incoming_count"]) for item in group)
                / len(group)
                if group
                else None
            ),
            "mean_victim_count": (
                sum(int(item["decision_features"]["victim_count"]) for item in group)
                / len(group)
                if group
                else None
            ),
        }
    return {
        "label_counts": dict(sorted(labels.items())),
        "oracle_delta": {
            "minimum": min(deltas),
            "maximum": max(deltas),
            "mean": sum(deltas) / len(deltas),
            "median": median(deltas),
        },
        "local_positive_terminal_negative_count": local_positive_terminal_negative,
        "local_utility_prediction_match_count": local_prediction_matches,
        "local_utility_prediction_mismatch_count": len(branches) - local_prediction_matches,
        "divergence_kind_counts": dict(sorted(divergence.items())),
        "direct_involved_delta_sum": sum(direct),
        "downstream_path_delta_sum": sum(downstream),
        "effects_are_independent_and_nonadditive": True,
        "descriptive_features_by_oracle_label": by_label,
    }


def run_oracle(
    *, checkpoint_root: Path, source_root: Path, private_output: Path, public_output: Path
) -> dict[str, object]:
    started = time.perf_counter()
    if public_output.exists():
        raise FileExistsError("public Oracle output already exists")
    resources = _resource_gate(private_output.parent, required_free_bytes=512 * 1024**2)
    packages, factual = _load_inputs(
        checkpoint_root=checkpoint_root, source_root=source_root
    )
    factual_run = cast(dict[str, Any], factual["run"])
    factual_outcome = cast(dict[str, Any], factual_run["outcome"])
    if float(factual_outcome["completed_utility"]) != EXPECTED_COMPLETED_UTILITY:
        raise ValueError("factual reference completed Utility mismatch")
    if len(cast(list[object], factual_run["events"])) != EXPECTED_EVENT_COUNT:
        raise ValueError("factual reference event count mismatch")
    if len(cast(list[object], factual["selector_calls"])) != EXPECTED_SELECTOR_CALL_COUNT:
        raise ValueError("factual selector call count mismatch")
    factual_records = cast(list[dict[str, Any]], factual["transaction_records"])

    private_output.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, Any]] = []
    canary_seconds: float | None = None
    for sequence, (package, factual_record) in enumerate(
        zip(packages, factual_records, strict=True)
    ):
        prior = _load_completed_branch(private_output, sequence)
        if prior is not None:
            completed.append(cast(dict[str, Any], prior))
            continue
        branch_started = time.perf_counter()
        first = _execute_branch(package, factual)
        second = _execute_branch(package, factual)
        _replays_equal(first, second)
        runtime = time.perf_counter() - branch_started
        payload = _private_branch_result(
            sequence=sequence,
            package=package,
            factual=factual,
            factual_record=factual_record,
            first=first,
            runtime_seconds=runtime,
        )
        _persist_branch(private_output, sequence, payload)
        completed.append(cast(dict[str, Any], payload))
        if sequence == 0:
            canary_seconds = runtime
            resources = _resource_gate(
                private_output.parent, required_free_bytes=384 * 1024**2
            )
    if len(completed) != EXPECTED_TRANSACTION_COUNT:
        raise ValueError("Oracle branch coverage incomplete")

    aggregate = _aggregate(completed)
    private_summary = {
        "schema_version": "stage15n1b2-private-oracle-summary-v1",
        "scope": {
            "logical_branches": 28,
            "replays_per_branch": 2,
            "suffix_executions": 56,
            "max_parallel": 1,
            "full_workloads": 0,
            "factual_or_comparator_replays": 0,
        },
        "input_manifest_sha256": EXPECTED_INPUT_MANIFEST_SHA256,
        "canary_seconds": canary_seconds,
        "total_seconds": time.perf_counter() - started,
        "resources": resources,
        "aggregate": aggregate,
    }
    write_atomic_new(
        private_output / "oracle_summary_private.json", _json_bytes(private_summary)
    )
    private_manifest = _manifest_rows(private_output)
    write_atomic_new(
        private_output / "sha256_manifest.json", _json_bytes(private_manifest)
    )

    public: dict[str, object] = {
        "schema_version": "stage15n1b2-public-oracle-summary-v1",
        "label": "[آزمون کمکی — Oracle آفلاین یک-seed]",
        "scope": private_summary["scope"],
        "status": "complete",
        "resource_preflight": {
            "disk_free_bytes": resources["disk_free_bytes"],
            "disk_required_bytes": resources["disk_required_bytes"],
            "ram_total_bytes": resources["ram_total_bytes"],
            "ram_available_bytes": resources["ram_available_bytes"],
            "estimated_peak_ram_bytes": 2 * 1024**3,
            "logical_cpu_count": 8,
        },
        "runtime": {
            "canary_two_replays_seconds": canary_seconds,
            "all_branches_seconds": private_summary["total_seconds"],
        },
        "coverage": {
            "successful": 28,
            "missing": 0,
            "invalid": 0,
            "checkpoint_manifest_verified": True,
        },
        "validation": {
            "all_replays_exact": True,
            "rng_option_a": True,
            "all_fingerprints_exact_between_replays": True,
            "all_invariants": True,
            "intervention_once_per_branch": True,
            "factual_reexecuted": False,
        },
        "aggregate": aggregate,
        "interpretation": {
            "causal_scope": "single_transaction_retain_branch_within_this_seed_and_simulator",
            "branch_deltas_additive": False,
            "classifier_or_threshold_trained": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
        "private_manifest": {
            "entry_count": len(private_manifest),
            "sha256": file_sha256(private_output / "sha256_manifest.json"),
            "individual_transaction_data_published": False,
        },
        "publication": {
            "task_ids": False,
            "checkpoints": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "victim_edges": False,
            "trace": False,
            "personal_paths": False,
        },
    }
    public_payload_is_sanitized(public)
    public_output.mkdir(parents=True, exist_ok=False)
    write_atomic_new(public_output / "oracle_summary.json", _json_bytes(public))
    write_atomic_new(
        public_output / "schema.json",
        _json_bytes(
            {
                "schema_version": "stage15n1b2-public-schema-v1",
                "private_transaction_rows_published": False,
                "public_content": [
                    "aggregate label counts",
                    "aggregate terminal effects",
                    "aggregate feature descriptives",
                    "validation and resource totals",
                ],
            }
        ),
    )
    public_manifest = _manifest_rows(public_output)
    write_atomic_new(
        public_output / "sha256_manifest.json", _json_bytes(public_manifest)
    )
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    result = run_oracle(
        checkpoint_root=args.checkpoint_root,
        source_root=args.source_root,
        private_output=args.private_output,
        public_output=args.public_output,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "successful_branches": cast(dict[str, object], result["coverage"])[
                    "successful"
                ],
                "oracle_branches": 28,
                "full_workloads": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
