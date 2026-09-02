from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/stage15k1-r2-initialization-repair.yml")


def test_workflow_is_manual_read_only_pinned_and_two_pair_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "permissions:\n  contents: read" in text
    assert "actions: read" not in text
    assert "secrets." not in text
    assert "max-parallel: 2" in text
    assert "fail-fast: false" in text
    assert "timeout-minutes: 90" in text
    assert "retention-days: 14" in text
    assert text.count("- pipeline_double_knapsack_retention") == 1
    assert text.count("- pipeline_double_knapsack_preemption") == 1
    assert "offspring_repair" not in text
    assert "five" not in text.lower()
    assert "thirty" not in text.lower()
    uses = re.findall(r"uses:\s*([^\s#]+)", text)
    assert uses and all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)


def test_workflow_never_executes_or_downloads_a_baseline() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "baseline_control" not in text
    assert "download-artifact" not in text
    assert "stage15e_reused_baselines.json" in text
    assert "stage15e_seed_one_reuse.json" in text
    assert "--variant" not in text
