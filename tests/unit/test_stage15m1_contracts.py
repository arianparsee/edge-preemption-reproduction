from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _runner() -> object:
    path = ROOT / "scripts/run_stage15m1_pilot.py"
    spec = importlib.util.spec_from_file_location("run_stage15m1_pilot", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_comparator_fixtures_are_exact_and_reuse_only() -> None:
    runner = _runner()
    baseline, repair, provenance = runner._find_reused_comparators(  # type: ignore[attr-defined]
        ROOT / "tests/fixtures/stage15e_reused_baselines.json",
        ROOT / "tests/fixtures/stage15e_seed_one_reuse.json",
    )
    assert provenance["baseline_recomputed"] is False
    assert provenance["repair_only_recomputed"] is False
    assert baseline["source_result_sha256"] == runner.BASELINE_SOURCE_RESULT_SHA256  # type: ignore[attr-defined]
    assert repair["source_artifact_sha256"] == runner.REPAIR_SOURCE_ARTIFACT_SHA256  # type: ignore[attr-defined]


def test_workflow_is_one_pair_two_replays_and_no_baseline_execution() -> None:
    text = (ROOT / ".github/workflows/stage15m1-no-cascading-pilot.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "timeout-minutes: 90" in text
    assert "contents: read" in text
    assert "actions: read" not in text
    assert "run_stage15m1_pilot.py" in text
    assert text.count("pipeline_double_knapsack_preemption") == 0
    assert "run_full_pair" not in text
    assert "run_stage13" not in text.lower()
    assert "replay_count" not in text  # two replays are enforced inside the runner


def test_workflow_actions_are_full_sha_pinned_and_retention_is_bounded() -> None:
    text = (ROOT / ".github/workflows/stage15m1-no-cascading-pilot.yml").read_text(encoding="utf-8")
    uses = [
        line.strip().split("@", 1)[1].split()[0] for line in text.splitlines() if "uses:" in line
    ]
    assert uses
    assert all(len(ref) == 40 and all(char in "0123456789abcdef" for char in ref) for ref in uses)
    assert "retention-days: 14" in text
    assert "secrets." not in text
