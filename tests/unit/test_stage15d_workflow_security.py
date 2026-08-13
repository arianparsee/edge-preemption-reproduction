from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/stage15d-counterfactual.yml")


def test_stage15d_workflow_is_read_only_pinned_bounded_and_single_seed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "541501192080118187" in text
    assert "max-parallel: 6" in text
    assert "fail-fast: false" in text
    assert text.count("timeout-minutes:") == 2
    assert "retention-days: 7" in text
    assert "run_stage13f_pipe_normal.py" not in text
    uses = re.findall(r"uses:\s*([^\s#]+)", text)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)


def test_stage15d_workflow_defines_exact_six_pair_matrix() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert text.count("- fixed_penalty") == 1
    assert text.count("- initial_population_repair") == 1
    assert text.count("- offspring_repair") == 1
    assert text.count("- pipeline_double_knapsack_retention") == 1
    assert text.count("- pipeline_double_knapsack_preemption") == 1
    assert "Expected six independent pair artifacts" in text
    assert '"${#files[@]}" -ne 6' in text


def test_stage15d_workflow_rejects_sensitive_and_scientific_boundary_fields() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert '"job-"' in text
    assert '"chromosome_bits\\\": true"' in text
    assert '"task_identifiers_in_artifact\\\": true"' in text
    assert "baseline_recomputed" in text
    assert "replay_exact" in text
    assert "rng_gate" in text
    assert "thirty_workloads_executed" in text
