"""Run the trusted-local Stage 15-N.1B.1 factual checkpoint audit."""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls

from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy, lifecycle_funnel
from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import InstrumentedKnapsackSelector
from edge_reproduction.diagnostics.temporal_checkpoint import (
    CheckpointableTemporalSession,
    TemporalCheckpoint,
    checkpoint_alias_gate,
)
from edge_reproduction.experiments.pipe_normal_full import (
    BASELINE,
    _descriptor,
    _mapping,
    _workload_payload,
    load_full_config,
)
from edge_reproduction.simulation.invariants import validate_state_invariants
from edge_reproduction.simulation.temporal_engine import (
    TemporalRun,
    TemporalRunConfig,
    synthetic_normal_temporal_tasks,
)

WORKLOAD_SEED = 541501192080118187
POLICY_SEED = 18158600156516774620
POLICY = "pipeline_double_knapsack_preemption"
VARIANT = CounterfactualVariant.INITIAL_POPULATION_REPAIR
EXPECTED_CONFIG_SHA256 = "b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963"
EXPECTED_WORKLOAD_SHA256 = "e571940d01f46f5251d62d89453099c7f466fda7e22ccd350f4aa05d3c4a1200"
EXPECTED_COMPARATOR_SHA256 = "e37204aa7fa8516db1224cd13c59076e52699647751be99672ad412fc37e7d4e"
EXPECTED_COMPLETED_UTILITY = 9541.426964770584
PRIVATE_KEYS = {
    "task_id", "task_ids", "transaction_key", "candidate_pool_task_ids",
    "current_task_ids", "returning_task_ids", "raw_final_rng_state",
    "checkpoint_raw_rng_state", "final_raw_rng_state",
}


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing Stage 15-N.1B.1 file: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_json(path: Path, value: object) -> None:
    _write_new(
        path,
        (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(),
    )


def assert_public_safe(value: object) -> None:
    """Reject private identifiers, raw RNG state and personal paths recursively."""

    if isinstance(value, dict):
        for key, child in value.items():
            if (
                str(key).lower() in PRIVATE_KEYS
                and child is not False
                and child is not None
                and child != 0
            ):
                raise ValueError(f"private field in public payload: {key}")
            assert_public_safe(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_public_safe(child)
    elif isinstance(value, str) and re.search(r"[A-Za-z]:[/\\]Users[/\\]", value):
        raise ValueError("personal path in public payload")


def validate_utility_conservation(*, total: float, completed: float, rejected: float) -> float:
    residual = float(total - completed - rejected)
    if abs(residual) > 1e-9:
        raise ValueError("utility conservation invariant failed")
    return residual


def _load_comparator(path: Path) -> tuple[dict[str, Any], dict[str, object]]:
    before = path.stat()
    digest = _file_sha256(path)
    if digest != EXPECTED_COMPARATOR_SHA256:
        raise ValueError("ASSUMP-046 comparator checksum mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("ASSUMP-046 comparator must be a JSON object")
    if (
        payload.get("workload_seed") != WORKLOAD_SEED
        or payload.get("policy_seed") != POLICY_SEED
        or payload.get("policy") != POLICY
        or payload.get("variant") != VARIANT.value
        or payload.get("replay_exact") is not True
    ):
        raise ValueError("ASSUMP-046 comparator identity mismatch")
    variant_payload = cast(dict[str, Any], payload.get("variant_replay"))
    if not isinstance(variant_payload, dict):
        raise ValueError("ASSUMP-046 comparator lacks its validated variant replay")
    fingerprint = cast(dict[str, Any], variant_payload["scientific_fingerprint"])
    if (
        fingerprint.get("workload_sha256") != EXPECTED_WORKLOAD_SHA256
        or cast(dict[str, Any], fingerprint["outcome"]).get("completed_utility")
        != EXPECTED_COMPLETED_UTILITY
    ):
        raise ValueError("ASSUMP-046 comparator scientific fingerprint mismatch")
    provenance = {
        "reuse_package_run_id": 31847136180,
        "stable_bundle_run_id": 32474360245,
        "sha256": digest,
        "size_bytes": before.st_size,
        "mtime_ns_before": before.st_mtime_ns,
        "replay_exact": True,
        "comparator_recomputed": False,
    }
    return variant_payload, provenance


def _build_session(config: dict[str, object]) -> tuple[
    CheckpointableTemporalSession,
    InstrumentedKnapsackSelector,
    CounterfactualKnapsackSelector,
    str,
]:
    descriptor = _descriptor(config, WORKLOAD_SEED)
    policy_seed = int(cast(int, _mapping(descriptor["policy_seeds"], "policy_seeds")[POLICY]))
    if policy_seed != POLICY_SEED:
        raise ValueError("materialized policy seed changed")
    workload, dataset = _workload_payload(WORKLOAD_SEED)
    workload_hash = sha256(
        (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    if workload_hash != EXPECTED_WORKLOAD_SHA256:
        raise ValueError("materialized workload hash changed")
    tasks = synthetic_normal_temporal_tasks(tuple(record.to_domain() for record in dataset.tasks))
    servers = tuple(record.to_domain() for record in dataset.servers)
    ga = PyeasygaConfig(seed=policy_seed)
    counterfactual = CounterfactualKnapsackSelector(ga, VARIANT)
    selector = InstrumentedKnapsackSelector(
        counterfactual, server_count=len(servers), diagnostic_stage="stage15d"
    )
    dkp_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
    delegate = PipelineDoubleKnapsackPreemptionPolicy(dkp_config, selector)
    policy = InstrumentedDKPolicy(delegate, selector)
    session = CheckpointableTemporalSession.create(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
            run_id=f"STAGE15N1B1.{WORKLOAD_SEED}.DKP",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=dkp_config.as_metadata()
        | {
            "scientific_status": "proposed_modified_method_auxiliary_checkpoint_audit",
            "assumptions": "ASSUMP-046",
        },
    )
    return session, selector, counterfactual, workload_hash


def _fingerprint(
    run: TemporalRun,
    *,
    workload_hash: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "baseline": BASELINE,
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": POLICY_SEED,
        "policy": POLICY,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    return scientific_fingerprint(payload)


def _terminal_linkage(
    records: list[dict[str, Any]], run: TemporalRun, call_rows: list[dict[str, object]]
) -> None:
    states = run.final_state.task_states
    preemption_events = tuple(
        event for event in run.events if event.event_type.value == "preempted"
    )
    edges: list[tuple[str, str]] = []
    for record in records:
        planned = cast(dict[str, tuple[str, ...]], record["planned"])
        incoming = tuple(planned["accepted"])
        victims = tuple(planned["preempted"])
        edges.extend((new, victim) for new in incoming for victim in victims)
        record["terminal_outcomes"] = {
            "incoming": {task_id: states[task_id].value for task_id in incoming},
            "victims": {task_id: states[task_id].value for task_id in victims},
        }
        epoch_value = cast(dict[str, Any], record["transaction_key"])["epoch"]
        epoch = int(cast(int, epoch_value))
        record["later_preemptions"] = {
            task_id: sum(
                event.task_id == task_id and event.time > epoch
                for event in preemption_events
            )
            for task_id in incoming
        }
        end = cast(tuple[int | None, int | None], record["selector_observation_range"])[1]
        record["subsequent_call_shape_sha256"] = _canonical_hash(
            [
                {
                    "round_name": row["round_name"],
                    "server_ordinal": row["server_ordinal"],
                    "call_kind": row["call_kind"],
                    "candidate_count": row["candidate_count"],
                }
                for row in call_rows[int(end or 0) :]
            ]
        )
    adjacency: dict[str, tuple[str, ...]] = {}
    for edge_incoming, edge_victim in edges:
        adjacency[edge_incoming] = adjacency.get(edge_incoming, ()) + (edge_victim,)

    def depth(task_id: str, seen: frozenset[str] = frozenset()) -> int:
        if task_id in seen:
            raise ValueError("preemption linkage contains a cycle")
        children = adjacency.get(task_id, ())
        return 0 if not children else 1 + max(depth(child, seen | {task_id}) for child in children)

    for record in records:
        incoming = cast(dict[str, tuple[str, ...]], record["planned"])["accepted"]
        record["preemption_chain_depth"] = max((depth(item) for item in incoming), default=0)


def _private_replay(
    *, config: dict[str, object], replay_dir: Path
) -> tuple[dict[str, object], TemporalCheckpoint, CheckpointableTemporalSession]:
    session, selector, counterfactual, workload_hash = _build_session(config)
    run, checkpoint = session.run_to_completion(capture_until_victim=True)
    if checkpoint is None:
        raise ValueError("official seed produced no victim transaction for checkpoint canary")
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    validate_state_invariants(run.final_state)
    checkpoint_alias_gate(checkpoint)
    call_rows = _sanitized_selector_calls(selector, counterfactual)
    _terminal_linkage(session.transaction_records, run, call_rows)
    private_payload = {
        "schema_version": "stage15n1b1-private-factual-replay-v1",
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": POLICY_SEED,
        "variant": VARIANT.value,
        "run": run.as_dict(),
        "transaction_records": session.transaction_records,
        "selector_calls": call_rows,
        "raw_final_rng_state": counterfactual._counting_rng.getstate(),  # noqa: SLF001
    }
    _write_json(replay_dir / "factual_replay_private.json", private_payload)
    _write_new(replay_dir / "checkpoint_canary.pkl", checkpoint.serialize())
    checkpoint_selector = cast(Any, checkpoint.session.policy)._selector  # noqa: SLF001
    checkpoint_counterfactual = checkpoint_selector._delegate  # noqa: SLF001
    _write_json(
        replay_dir / "rng_state_evidence_private.json",
        {
            "checkpoint_raw_rng_state": checkpoint_counterfactual._counting_rng.getstate(),  # noqa: SLF001
            "final_raw_rng_state": counterfactual._counting_rng.getstate(),  # noqa: SLF001
        },
    )
    completed = set(run.outcome.completed_task_ids)
    rejected = set(run.outcome.rejected_task_ids)
    total = sum(task.utility for task in run.final_state.tasks.values())
    residual = validate_utility_conservation(
        total=total,
        completed=run.outcome.completed_utility,
        rejected=run.outcome.rejected_utility,
    )
    if completed & rejected or completed | rejected != set(run.final_state.tasks):
        raise ValueError("terminal partition invariant failed")
    if not set(run.outcome.ever_preempted_task_ids).issubset(rejected):
        raise ValueError("ever-preempted subset invariant failed")
    public_evidence: dict[str, object] = {
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
        "selector_rng_trace_sha256": _canonical_hash(call_rows),
        "transaction_count": len(session.transaction_records),
        "checkpoint_epoch": checkpoint.epoch,
        "checkpoint_event_cursor": checkpoint.event_cursor,
        "checkpoint_sha256": checkpoint.digest(),
        "invariants": {
            "capacity_and_state": True,
            "terminal_partition": True,
            "preempted_subset_of_rejected": True,
            "utility_conservation": True,
            "utility_conservation_residual": residual,
        },
    }
    return public_evidence, checkpoint, session


def _manifest(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(
            {
                "logical_name": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return rows


def run_audit(
    *, config_path: Path, comparator_path: Path, private_root: Path, public_root: Path
) -> dict[str, object]:
    if _file_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved PIPE-NORMAL config checksum mismatch")
    comparator, provenance = _load_comparator(comparator_path)
    config = load_full_config(config_path)
    first, checkpoint, first_session = _private_replay(
        config=config, replay_dir=private_root / "replay-1"
    )
    second, _, _ = _private_replay(config=config, replay_dir=private_root / "replay-2")
    if first != second:
        raise ValueError("scientific failure: factual replay mismatch")
    expected_fingerprint = cast(dict[str, object], comparator["scientific_fingerprint"])
    if first["scientific_fingerprint"] != expected_fingerprint:
        raise ValueError("instrumented factual outcome differs from validated ASSUMP-046")
    for key in ("selector_funnel", "auction_funnel", "lifecycle_funnel", "counterfactual"):
        if first[key] != comparator[key]:
            raise ValueError(f"instrumented factual {key} differs from validated ASSUMP-046")

    suffix_run, suffix_session = first_session.resume_checkpoint(checkpoint)
    suffix_selector = cast(Any, suffix_session.policy)._selector  # noqa: SLF001
    suffix_counterfactual = suffix_selector._delegate  # noqa: SLF001
    suffix_run.metadata = MappingProxyType(
        dict(suffix_run.metadata)
        | suffix_selector.runtime_metadata()
        | suffix_counterfactual.runtime_metadata()
    )
    first_private = json.loads(
        (private_root / "replay-1" / "factual_replay_private.json").read_text(encoding="utf-8")
    )
    if suffix_run.as_dict() != first_private["run"]:
        raise ValueError("scientific failure: factual suffix terminal run mismatch")
    suffix_calls = _sanitized_selector_calls(suffix_selector, suffix_counterfactual)
    if suffix_calls != first_private["selector_calls"]:
        raise ValueError("scientific failure: factual suffix RNG/call-shape mismatch")
    _write_json(
        private_root / "suffix-canary" / "factual_suffix_private.json",
        {
            "schema_version": "stage15n1b1-private-factual-suffix-v1",
            "checkpoint_epoch": checkpoint.epoch,
            "event_cursor": checkpoint.event_cursor,
            "run": suffix_run.as_dict(),
            "selector_calls": suffix_calls,
            "raw_final_rng_state": suffix_counterfactual._counting_rng.getstate(),  # noqa: SLF001
        },
    )
    comparator_after = comparator_path.stat()
    if (
        _file_sha256(comparator_path) != EXPECTED_COMPARATOR_SHA256
        or comparator_after.st_size != provenance["size_bytes"]
        or comparator_after.st_mtime_ns != provenance["mtime_ns_before"]
    ):
        raise ValueError("read-only ASSUMP-046 comparator changed during audit")

    private_rows = _manifest(private_root)
    _write_json(private_root / "sha256_manifest.json", private_rows)
    public_root.mkdir(parents=True, exist_ok=True)
    public: dict[str, object] = {
        "schema_version": "stage15n1b1-public-checkpoint-audit-v1",
        "label": "[پیشنهاد فنی تشخیصی] Stage 15-N.1B.1",
        "scope": {
            "workload_count": 1,
            "policy_count": 1,
            "logical_pairs": 1,
            "factual_replays": 2,
            "factual_suffix_canaries": 1,
            "oracle_branches": 0,
        },
        "identity": {
            "workload_seed": str(WORKLOAD_SEED),
            "policy_seed": str(POLICY_SEED),
            "policy": POLICY,
            "variant": VARIANT.value,
            "workload_sha256": EXPECTED_WORKLOAD_SHA256,
            "config_sha256": EXPECTED_CONFIG_SHA256,
        },
        "comparator_provenance": {
            key: value for key, value in provenance.items() if key != "mtime_ns_before"
        },
        "validation": {
            "factual_replay_exact": True,
            "assump046_comparator_exact": True,
            "factual_suffix_exact": True,
            "rng_option_a": True,
            "checkpoint_deep_and_non_aliasing": True,
            "scientific_invariants": True,
            "public_private_scan": True,
            "stage_success": False,
            "stage_success_blocker": (
                "checkpoint hash is absent for non-canary victim transactions"
            ),
        },
        "checkpoint": {
            "count": 1,
            "first_victim_transaction_epoch": checkpoint.epoch,
            "event_cursor": checkpoint.event_cursor,
            "sha256": checkpoint.digest(),
        },
        "transaction_completeness": {
            "victim_transaction_count": len(first_session.transaction_records),
            "required_feature_groups": 18,
            "present_feature_groups": 17,
            "missing_feature_groups": 1,
            "checkpoint_hash_coverage": (
                f"1/{len(first_session.transaction_records)} canary transaction only"
            ),
            "rng_state_hash_coverage": (
                f"{len(first_session.transaction_records)}/"
                f"{len(first_session.transaction_records)} directly linked through "
                "selector call evidence"
            ),
            "terminal_linkage_complete": True,
            "candidate_call_shape_evolution_complete": True,
        },
        "scientific_summary": {
            "completed_utility": cast(dict[str, Any], first["scientific_fingerprint"])[
                "outcome"
            ]["completed_utility"],
            "transaction_count": first["transaction_count"],
            "selector_call_shape_sha256": first["selector_call_shape_sha256"],
            "selector_rng_trace_sha256": first["selector_rng_trace_sha256"],
        },
        "publication": {
            "task_ids": False,
            "raw_rng_state": False,
            "transaction_rows": False,
            "workload": False,
            "checkpoint": False,
            "personal_paths": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
        "private_manifest": [
            {
                "logical_artifact": f"private-file-{index + 1}",
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
            }
            for index, row in enumerate(private_rows)
        ],
    }
    assert_public_safe(public)
    public_schema: dict[str, object] = {
        "private_transaction_feature_groups": [
            "identity", "decision_features", "pipeline_progress", "resource_state",
            "prices", "ga_membership", "scores", "planned_sets", "planned_residual",
            "local_utility", "factual_result", "terminal_outcomes", "later_preemptions",
            "chain_depth", "candidate_pool", "call_shape_evolution", "checkpoint_hash",
            "rng_state_hash",
        ],
        "private_fields_published": False,
        "checkpoint_hash_status": (
            "canary checkpoint only; non-canary transaction rows lack a checkpoint hash"
        ),
        "rng_state_hash_status": (
            "available for every transaction through checksum-verified selector call linkage"
        ),
    }
    assert_public_safe(public_schema)
    _write_json(public_root / "schema.json", public_schema)
    _write_json(public_root / "completeness_report.json", public)
    public_rows = _manifest(public_root)
    _write_json(public_root / "sha256_manifest.json", public_rows)
    return public


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--comparator", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    args = parser.parse_args()
    if args.private_root.exists() or args.public_root.exists():
        raise FileExistsError("Stage 15-N.1B.1 output roots must not already exist")
    report = run_audit(
        config_path=args.config,
        comparator_path=args.comparator,
        private_root=args.private_root,
        public_root=args.public_root,
    )
    validation = cast(dict[str, object], report["validation"])
    print(
        json.dumps(
            {
                "status": "stage15n1b1_complete",
                "factual_replay_exact": validation["factual_replay_exact"],
                "factual_suffix_exact": validation["factual_suffix_exact"],
            }
        )
    )


if __name__ == "__main__":
    main()
