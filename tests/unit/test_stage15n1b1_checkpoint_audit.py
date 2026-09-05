from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import (
    PipelineDKPConfig,
    PipelineDoubleKnapsackPreemptionPolicy,
)
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy
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
from edge_reproduction.experiments.temporal_smoke import _build_workload, _load_config
from edge_reproduction.simulation.temporal_engine import TemporalRunConfig, run_temporal_policy

ROOT = Path(__file__).resolve().parents[2]


def _load_runner() -> Any:
    path = ROOT / "scripts/run_stage15n1b1_checkpoint_audit.py"
    spec = importlib.util.spec_from_file_location("run_stage15n1b1_checkpoint_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old = sys.path.copy()
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module


def _inputs() -> tuple[Any, ...]:
    raw = _load_config(ROOT / "configs/stage13d_temporal_smoke.json")
    tasks, servers = _build_workload(raw)
    seed = 6893869117720259993
    ga = PyeasygaConfig(seed=seed)
    selector_base = CounterfactualKnapsackSelector(
        ga, CounterfactualVariant.INITIAL_POPULATION_REPAIR
    )
    selector = InstrumentedKnapsackSelector(
        selector_base, server_count=len(servers), diagnostic_stage="stage15d"
    )
    config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
    policy = InstrumentedDKPolicy(
        PipelineDoubleKnapsackPreemptionPolicy(config, selector), selector
    )
    run_config = TemporalRunConfig(
        run_id="stage15n1b1-fixture", policy_seed=seed, arrival_slots=2
    )
    return tasks, servers, policy, selector, selector_base, config, run_config


def _session() -> tuple[CheckpointableTemporalSession, Any, Any]:
    tasks, servers, policy, selector, selector_base, config, run_config = _inputs()
    return (
        CheckpointableTemporalSession.create(
            original_tasks=tasks,
            servers=servers,
            policy=policy,
            config=run_config,
            policy_metadata=config.as_metadata(),
        ),
        selector,
        selector_base,
    )


def test_mirror_matches_official_engine_on_small_fixture() -> None:
    session, selector, selector_base = _session()
    mirrored, checkpoint = session.run_to_completion(capture_until_victim=True)
    mirrored.metadata = MappingProxyType(
        dict(mirrored.metadata) | selector.runtime_metadata() | selector_base.runtime_metadata()
    )
    tasks, servers, policy, selector2, selector_base2, config, run_config = _inputs()
    official = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=run_config,
        policy_metadata=config.as_metadata(),
    )
    official.metadata = MappingProxyType(
        dict(official.metadata) | selector2.runtime_metadata() | selector_base2.runtime_metadata()
    )
    assert checkpoint is not None
    assert mirrored.as_dict() == official.as_dict()


def test_checkpoint_round_trip_is_deep_and_suffix_is_exact() -> None:
    session, _, _ = _session()
    uninterrupted, checkpoint = session.run_to_completion(capture_until_victim=True)
    assert checkpoint is not None
    checkpoint_alias_gate(checkpoint)
    restored = TemporalCheckpoint.deserialize(checkpoint.serialize())
    assert restored.digest() == checkpoint.digest()
    resumed, _ = session.resume_checkpoint(checkpoint)
    assert resumed.as_dict() == uninterrupted.as_dict()


def test_checkpoint_capture_does_not_draw_rng() -> None:
    session, _, selector_base = _session()
    while session.next_epoch < 2:
        session.step(capture_checkpoint=False)
    requesting, remaining = session._prepare_epoch(session.next_epoch)  # noqa: SLF001
    before = selector_base._counting_rng.getstate()  # noqa: SLF001
    checkpoint = session.checkpoint(
        epoch=session.next_epoch,
        requesting_task_ids=requesting,
        time_remaining_by_task=remaining,
    )
    after = selector_base._counting_rng.getstate()  # noqa: SLF001
    assert before == after
    assert checkpoint.requesting_task_ids == requesting


def test_checkpoint_is_not_aliased_to_later_live_mutation() -> None:
    session, _, _ = _session()
    observation = None
    while observation is None or observation.checkpoint is None:
        observation = session.step(capture_checkpoint=True)
    checkpoint = observation.checkpoint
    assert checkpoint is not None
    frozen_slot = checkpoint.session.state.current_slot
    session.state.current_slot += 1
    assert checkpoint.session.state.current_slot == frozen_slot


def test_private_transaction_row_links_decision_and_terminal_outcome() -> None:
    session, _, _ = _session()
    run, _ = session.run_to_completion(capture_until_victim=True)
    assert session.transaction_records
    row = session.transaction_records[0]
    assert row["planned"]["preempted"]
    assert row["planned"]["accepted"]
    assert set(row["candidate_pool_task_ids"]) == set(row["task_features"])
    assert set(run.outcome.ever_preempted_task_ids)


def test_checkpoint_captures_required_execution_closure() -> None:
    session, _, _ = _session()
    _, checkpoint = session.run_to_completion(capture_until_victim=True)
    assert checkpoint is not None
    captured = checkpoint.session
    assert captured.original
    assert captured.state.allocations
    assert captured.progress
    assert captured.retry_count
    assert captured.rejection_reasons
    assert captured.events
    assert captured.policy is not session.policy
    assert captured.config.numerical_tolerance == 1e-9


def test_publication_scan_rejects_private_identifiers_and_paths() -> None:
    runner = _load_runner()
    runner.assert_public_safe({"task_ids": False, "count": 2})
    with pytest.raises(ValueError, match="private field"):
        runner.assert_public_safe({"task_ids": ["private"]})
    with pytest.raises(ValueError, match="personal path"):
        runner.assert_public_safe({"path": "C:" + "/Users/example/private.json"})


def test_utility_conservation_positive_and_negative() -> None:
    runner = _load_runner()
    assert runner.validate_utility_conservation(total=10.0, completed=4.0, rejected=6.0) == 0
    with pytest.raises(ValueError, match="conservation"):
        runner.validate_utility_conservation(total=10.0, completed=4.0, rejected=5.0)


def test_runner_scope_is_one_seed_one_policy_two_factual_replays() -> None:
    runner = _load_runner()
    assert runner.WORKLOAD_SEED == 541501192080118187
    assert runner.POLICY == "pipeline_double_knapsack_preemption"
    assert runner.VARIANT is CounterfactualVariant.INITIAL_POPULATION_REPAIR
    source = (ROOT / "scripts/run_stage15n1b1_checkpoint_audit.py").read_text(
        encoding="utf-8"
    )
    assert "replay-1" in source and "replay-2" in source
    assert "retain" not in source.lower()
    assert "workflow_dispatch" not in source


def test_public_schema_contains_no_task_level_values(tmp_path: Path) -> None:
    runner = _load_runner()
    payload = {
        "schema_version": "test",
        "task_ids": False,
        "raw_rng_state": False,
        "logical_pairs": 1,
    }
    runner.assert_public_safe(payload)
    path = tmp_path / "public.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert "task-current" not in path.read_text(encoding="utf-8")
