from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/stage15c-dk-funnel.yml")


def test_stage15c_workflow_is_read_only_pinned_and_bounded() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "541501192080118187" in text
    assert "retention-days: 7" in text
    assert text.count("timeout-minutes:") == 2
    uses = re.findall(r"uses:\s*([^\s#]+)", text)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)


def test_stage15c_workflow_rejects_detailed_public_artifacts() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert '"chromosome_bits\\\": true"' in text
    assert '"task_identifiers_in_artifact\\\": true"' in text
    assert "baseline_recomputed" in text
    assert "scientific_fingerprint_equal" in text
