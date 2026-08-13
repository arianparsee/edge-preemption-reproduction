from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_stage15b_workflow_has_minimal_permissions_and_pinned_actions() -> None:
    workflow = (ROOT / ".github/workflows/stage15b-ga-diagnostic.yml").read_text()

    assert "permissions:\n  contents: read" in workflow
    assert "secrets." not in workflow
    assert "github.token" not in workflow
    assert "timeout-minutes:" in workflow
    assert "retention-days: 7" in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in workflow


def test_stage15b_workflow_uploads_only_sanitized_diagnostics() -> None:
    workflow = (ROOT / ".github/workflows/stage15b-ga-diagnostic.yml").read_text()

    assert "results/raw" not in workflow
    assert "path: results" not in workflow
    assert "stage15b-${{ matrix.policy }}.json" in workflow
    assert "stage15b-summary.json" in workflow
