from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/stage15d-penalty-recovery.yml")


def test_penalty_recovery_is_read_only_pinned_and_two_pair_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "541501192080118187" in text
    assert "max-parallel: 2" in text
    assert "fail-fast: false" in text
    assert text.count("timeout-minutes:") == 1
    assert "retention-days: 7" in text
    assert "--variant fixed_penalty" in text
    assert "initial_population_repair" not in text
    assert "offspring_repair" not in text
    uses = re.findall(r"uses:\s*([^\s#]+)", text)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)


def test_penalty_recovery_preserves_public_and_scientific_boundaries() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert '"job-"' in text
    assert '"chromosome_bits\\\": true"' in text
    assert '"task_identifiers_in_artifact\\\": true"' in text
    assert "baseline_recomputed" in text
    assert "replay_exact" in text
    assert "rng_gate" in text
    assert "thirty_workloads_executed" in text
