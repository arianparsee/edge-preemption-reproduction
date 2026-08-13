from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/audit_stage15f_closure.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("audit_stage15f_closure", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-F closure audit")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_stage15f_closure_preserves_figure6_and_audits_remaining_targets() -> None:
    result = _module().audit(ROOT)

    assert result["status"] == "passed"
    assert result["simulator_executed"] is False
    assert result["figure6_reproduction_status"] == "not_reproduced"
    assert result["stage14a_inventory_files_verified"] == 6
    assert result["stage14a_hash_modes"]["docs/stage14a_figure6.md"] == (
        "legacy_markdown_crlf_digest"
    )
    assert all(
        mode == "exact_bytes"
        for path, mode in result["stage14a_hash_modes"].items()
        if path != "docs/stage14a_figure6.md"
    )
    assert result["evaluation_figures_audited"] == 18
    assert result["official_experiments_unblocked"] == 0
    assert result["closest_unblocked_paper_figure"] == "Fig1_conceptual_epoch_job_set"
    assert result["closest_auxiliary_evaluation_target"] == "R1-DIAG-AUX_near_Fig3"
