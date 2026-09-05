from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
)

ROOT = Path(__file__).resolve().parents[2]


def _runner() -> Any:
    path = ROOT / "scripts" / "run_stage15n1b2_oracle_retain.py"
    spec = importlib.util.spec_from_file_location("stage15n1b2_oracle", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old = sys.path.copy()
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module


def _context() -> DKPPreCommitContext:
    fixture_path = ROOT / "tests/unit/test_stage15n1b2r_materialization.py"
    spec = importlib.util.spec_from_file_location("stage15n1b2r_fixture", fixture_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old = sys.path.copy()
    sys.path.insert(0, str(fixture_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module._fixture_checkpoint_and_context()[1]


def test_oracle_hook_intervenes_exactly_once() -> None:
    runner = _runner()
    context = _context()
    hook = runner.RetainExactlyOnce(context)
    assert hook(context) is DKPPreCommitAction.RETAIN_CURRENT_REJECT_RETURNING
    assert hook(context) is DKPPreCommitAction.COMMIT
    assert hook.interventions == 1


def test_oracle_hook_does_not_intervene_on_other_context() -> None:
    runner = _runner()
    context = _context()
    other = DKPPreCommitContext(
        context.epoch + 1,
        context.server_id,
        context.current_task_ids,
        context.returning_task_ids,
        context.knapsack_selected_task_ids,
        context.score_entries,
        context.retained_task_ids,
        context.preempted_task_ids,
        context.accepted_task_ids,
        context.rejected_task_ids,
        context.planned_residual,
    )
    hook = runner.RetainExactlyOnce(context)
    assert hook(other) is DKPPreCommitAction.COMMIT
    assert hook.interventions == 0


def test_replay_gate_reports_differences() -> None:
    runner = _runner()
    base = {
        "run": {},
        "selector_calls": [],
        "raw_final_rng_state": (),
        "scientific_fingerprint": {},
        "task_partition_sha256": "a",
        "lifecycle_funnel": {},
        "never_admitted_expired": 0,
        "transaction_records": [],
        "hook_calls": 1,
        "interventions": 1,
        "utility_conservation_residual": 0.0,
    }
    runner._replays_equal(base, dict(base))
    with pytest.raises(ValueError, match="selector_calls"):
        runner._replays_equal(base, dict(base) | {"selector_calls": [{}]})


def test_first_divergence_distinguishes_shape_and_rng() -> None:
    runner = _runner()
    base = {
        "auction_ordinal": 1,
        "round_name": "round_2",
        "server_ordinal": 0,
        "call_kind": "multi",
        "candidate_count": 3,
        "rng_state_after_sha256": "a",
    }
    assert runner._first_divergence([base], [dict(base)])["kind"] == "none"
    changed_rng = dict(base) | {"rng_state_after_sha256": "b"}
    assert runner._first_divergence([base], [changed_rng])["kind"] == "rng_evidence"
    changed_shape = dict(base) | {"candidate_count": 2}
    assert runner._first_divergence([base], [changed_shape])["kind"] == "call_shape"


def test_resume_rejects_partial_or_invalid_branch(tmp_path: Path) -> None:
    runner = _runner()
    branch, _ = runner._branch_paths(tmp_path, 0)
    branch.parent.mkdir(parents=True)
    branch.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="partial"):
        runner._load_completed_branch(tmp_path, 0)


def test_runner_is_local_sequential_and_does_not_execute_factual() -> None:
    source = (ROOT / "scripts/run_stage15n1b2_oracle_retain.py").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch" not in source
    assert "run_temporal_policy(" not in source
    assert "synthetic_normal_temporal_tasks" not in source
    assert '"max_parallel": 1' in source
    assert '"full_workloads": 0' in source
