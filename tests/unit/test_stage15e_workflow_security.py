from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/stage15e-limited-multiseed.yml")


def test_workflow_is_read_only_pinned_bounded_and_exactly_sixteen_pairs() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "max-parallel: 8" in text
    assert "fail-fast: false" in text
    assert text.count("timeout-minutes:") == 2
    assert "retention-days: 7" in text
    assert "fixed_penalty" not in text
    assert "541501192080118187" not in text
    assert "Expected 16 independent new pair artifacts" in text
    uses = re.findall(r"uses:\s*([^\s#]+)", text)
    assert uses and all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)


def test_workflow_has_four_new_seeds_two_variants_and_two_policies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    for seed in SEEDS:
        assert text.count(f'"{seed}"') == 1
        assert f"- {seed}" not in text
    assert text.count("- initial_population_repair") == 1
    assert text.count("- offspring_repair") == 1
    assert text.count("- pipeline_double_knapsack_retention") == 1
    assert text.count("- pipeline_double_knapsack_preemption") == 1


SEEDS = (2074092324964443463, 2218754797665862270, 2997476077322633071, 3782887846963969634)
