from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str) -> object:
    path = ROOT / f"scripts/{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    scripts_dir = str(path.parent)
    original = sys.path.copy()
    sys.path[:] = [scripts_dir, *(entry for entry in sys.path if entry != scripts_dir)]
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = original
    return module


def test_all_three_comparators_are_pinned_and_reuse_only() -> None:
    runner = _load_script("run_stage15m1b_pilot")
    baseline, repair, provenance = runner._find_reused_comparators(  # type: ignore[attr-defined]
        ROOT / "tests/fixtures/stage15e_reused_baselines.json",
        ROOT / "tests/fixtures/stage15e_seed_one_reuse.json",
    )
    permanent = runner._find_permanent_comparator(  # type: ignore[attr-defined]
        ROOT / "tests/fixtures/stage15m1_assump054_reuse.json"
    )

    assert provenance["baseline_recomputed"] is False
    assert provenance["repair_only_recomputed"] is False
    assert baseline["source_result_sha256"] == provenance["baseline_source_result_sha256"]
    assert repair["source_artifact_sha256"] == provenance["repair_source_artifact_sha256"]
    assert permanent["validation"]["replay_exact"] is True
    assert permanent["source"]["artifact_zip_sha256"] == runner.PERMANENT_SOURCE_ZIP_SHA256  # type: ignore[attr-defined]


def test_assump054_fixture_is_sanitized_and_records_failed_pilot() -> None:
    runner = _load_script("run_stage15m1b_pilot")
    permanent = runner._find_permanent_comparator(  # type: ignore[attr-defined]
        ROOT / "tests/fixtures/stage15m1_assump054_reuse.json"
    )
    assert permanent["validation"]["sanitized"] is True
    assert permanent["validation"]["pilot_success"] is False
    assert permanent["publication"] == {
        "task_identifiers": False,
        "raw_edges": False,
        "chromosomes": False,
        "raw_workload": False,
        "official_pipeline_changed": False,
        "figure_6_status": "بازتولید نشد",
    }


def test_workflow_scope_is_one_pair_two_replays_and_reuse_only() -> None:
    text = (ROOT / ".github/workflows/stage15m1b-one-auction-cooldown.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch" in text
    assert "timeout-minutes: 90" in text
    assert "contents: read" in text
    assert "actions: read" not in text
    assert "run_stage15m1b_pilot.py" in text
    assert "stage15m1_assump054_reuse.json" in text
    assert "run_full_pair" not in text
    assert "run_stage13" not in text.lower()
    assert "matrix:" not in text
    assert "replay_count" not in text


def test_workflow_actions_are_sha_pinned_without_secrets() -> None:
    text = (ROOT / ".github/workflows/stage15m1b-one-auction-cooldown.yml").read_text(
        encoding="utf-8"
    )
    refs = [
        line.strip().split("@", 1)[1].split()[0]
        for line in text.splitlines()
        if "uses:" in line
    ]
    assert refs
    assert all(len(ref) == 40 and all(char in "0123456789abcdef" for char in ref) for ref in refs)
    assert "retention-days: 14" in text
    assert "secrets." not in text


def test_validator_rejects_any_recomputed_comparator() -> None:
    validator = _load_script("validate_stage15m1b_public")
    payload = {
        "schema_version": "stage15m1b-one-auction-cooldown-pilot-v1",
        "logical_pairs": 1,
        "replay_count": 2,
        "replay_exact": True,
        "baseline_recomputed": True,
    }
    try:
        validator.validate(payload)  # type: ignore[attr-defined]
    except ValueError as error:
        assert "reuse-only" in str(error)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("validator accepted a recomputed comparator")


def test_publication_scan_rejects_private_task_payload() -> None:
    validator = _load_script("validate_stage15m1b_public")
    try:
        validator._assert_no_private_payload({"nested": {"task_ids": ["private"]}})  # type: ignore[attr-defined]
    except ValueError as error:
        assert "private public-artifact keys" in str(error)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("publication scan accepted private task identifiers")


def test_runner_import_is_scoped_and_restores_sys_path() -> None:
    original = sys.path.copy()
    runner = _load_script("run_stage15m1b_pilot")
    assert callable(runner.run_pilot)  # type: ignore[attr-defined]
    assert sys.path == original


def test_guard_module_has_no_random_dependency_or_rerun_hook() -> None:
    text = (
        ROOT / "src/edge_reproduction/modified_methods/one_auction_cooldown_dkp.py"
    ).read_text(encoding="utf-8")
    assert "import random" not in text
    assert "rerun" not in text.lower()
    assert "selector.select" in text
    assert text.count("selector.select") == 1
