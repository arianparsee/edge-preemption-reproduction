from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
)

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, relative: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old = sys.path.copy()
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module


def _context() -> DKPPreCommitContext:
    fixture = _module(
        "stage15n1b2r_fixture", "tests/unit/test_stage15n1b2r_materialization.py"
    )
    return fixture._fixture_checkpoint_and_context()[1]


def test_bootstrap_hook_is_noop_without_victims(tmp_path: Path) -> None:
    runner = _module("stage15n1b2g_bootstrap", "scripts/run_stage15n1b2g_bootstrap.py")
    context = _context()
    no_victim = DKPPreCommitContext(
        context.epoch,
        context.server_id,
        context.current_task_ids,
        context.returning_task_ids,
        context.knapsack_selected_task_ids,
        context.score_entries,
        context.retained_task_ids,
        (),
        context.accepted_task_ids,
        context.rejected_task_ids,
        context.planned_residual,
    )
    materializer = runner.BootstrapMaterializer(tmp_path, {context.server_id: 0})
    assert materializer(no_victim) is DKPPreCommitAction.COMMIT
    assert materializer.rows == []


def test_reuse_package_is_exactly_four_sanitized_branches() -> None:
    path = ROOT / "tests/fixtures/stage15n1b2g_reused_oracle_branches.json"
    digest = (path.with_suffix(path.suffix + ".sha256")).read_text().strip()
    aggregator = _module(
        "stage15n1b2g_aggregate", "scripts/aggregate_stage15n1b2g_oracle.py"
    )
    assert digest == aggregator.EXPECTED_REUSE_SHA256
    rows = aggregator._load_reuse(path)
    assert [row["sequence"] for row in rows] == [0, 1, 2, 3]
    encoded = json.dumps(rows)
    assert "job-" not in encoded
    assert "task_features" not in encoded
    assert "incoming_outcomes" not in encoded
    assert "victim_outcomes" not in encoded


def test_planner_initial_run_targets_only_4_through_27(tmp_path: Path) -> None:
    planner = _module("stage15n1b2g_plan", "scripts/plan_stage15n1b2g_matrix.py")
    assert tuple(range(4, 28)) == planner.APPROVED
    assert planner.valid_sequences(tmp_path) == []


def test_local_guard_confusion_uses_oracle_terminal_label() -> None:
    aggregator = _module(
        "stage15n1b2g_confusion", "scripts/aggregate_stage15n1b2g_oracle.py"
    )
    rows = [
        {"decision_features": {"local_net_utility": 1.0}, "terminal": {"oracle_label": "HARMFUL"}},
        {
            "decision_features": {"local_net_utility": -1.0},
            "terminal": {"oracle_label": "BENEFICIAL"},
        },
        {"decision_features": {"local_net_utility": -1.0}, "terminal": {"oracle_label": "HARMFUL"}},
    ]
    assert aggregator._confusion(rows) == {
        "false_veto": 1,
        "missed_veto": 1,
        "true_commit": 0,
        "true_veto": 1,
    }


def test_workflow_scope_security_and_retention() -> None:
    text = (ROOT / ".github/workflows/stage15n1b2g-oracle.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in text
    assert "max-parallel: 8" in text
    assert "fail-fast: false" in text
    assert "range(4, 28)" not in text
    assert "--sequence ${{ matrix.sequence }}" in text
    assert "retention-days: 7" in text
    assert text.count("retention-days: 14") >= 3
    assert "permissions:\n  contents: read\n  actions: read" in text
    assert "secrets." not in text
    assert "run_stage15n1b2g_bootstrap.py" in text
    assert "tests/fixtures/stage15n1b2g_reused_oracle_branches.json" in text


def test_workflow_actions_are_full_sha_pinned() -> None:
    text = (ROOT / ".github/workflows/stage15n1b2g-oracle.yml").read_text(
        encoding="utf-8"
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("uses:"):
            revision = stripped.split("@", 1)[1].split()[0]
            assert len(revision) == 40
            assert all(char in "0123456789abcdef" for char in revision)


def test_no_local_oracle_or_full_workload_command_in_workflow() -> None:
    text = (ROOT / ".github/workflows/stage15n1b2g-oracle.yml").read_text(
        encoding="utf-8"
    )
    assert "runs-on: self-hosted" not in text
    assert "run_stage13" not in text
    assert "pipeline_double_knapsack_retention" not in text
    assert "ASSUMP-054" not in text
    assert "ASSUMP-055" not in text
    assert "PYTHONHASHSEED" not in text
