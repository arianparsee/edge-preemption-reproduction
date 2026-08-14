from __future__ import annotations

import json
from pathlib import Path

from prepare_stage15h_matrix import build
from validate_stage15h_public_pair import validate


def test_stage15h_pinned_manifests_are_complete_and_exactly_scoped() -> None:
    baseline = json.loads(
        Path("configs/experiments/stage15h_baseline_reuse_manifest.json").read_text()
    )
    repairs = json.loads(
        Path("configs/experiments/stage15h_repair_reuse_manifest.json").read_text()
    )
    assert baseline["validated_pair_count"] == 120
    assert len(baseline["entries"]) == 120
    assert len({(r["workload_seed"], r["policy"]) for r in baseline["entries"]}) == 120
    assert repairs["validated_pair_count"] == 20
    assert len(repairs["entries"]) == 20
    assert len({(r["workload_seed"], r["variant"], r["policy"]) for r in repairs["entries"]}) == 20
    assert all(len(r["file_sha256"]) == 64 for r in repairs["entries"])


def test_stage15h_fresh_matrix_has_only_the_100_approved_new_pairs(tmp_path: Path) -> None:
    report = build(
        Path("configs/experiments/pipe_normal_full_stage13f.json"), None, tmp_path / "resumed"
    )
    assert report["expected_pair_count"] == 100
    assert report["resumed_valid_pair_count"] == 0
    assert report["new_pair_count"] == 100
    rows = report["include"]
    assert len(rows) == 100
    assert len({(r["workload_seed"], r["variant"], r["policy"]) for r in rows}) == 100


def test_stage15h_resume_skips_only_a_fully_valid_pair(tmp_path: Path) -> None:
    resume = tmp_path / "resume"
    resume.mkdir()
    payload = {
        "schema_version": "stage15h-counterfactual-pair-v1",
        "workload_seed": "3972957962913175742",
        "policy": "pipeline_double_knapsack_retention",
        "variant": "initial_population_repair",
        "baseline_recomputed": False,
        "replay_count": 2,
        "replay_exact": True,
        "rng_gate": {
            "passed_within_variant": True,
            "initial_rng_state_matches_policy_seed": True,
            "same_variant_final_rng_state_replay_exact": True,
            "same_variant_primitive_counts_replay_exact": True,
            "same_variant_call_shape_replay_exact": True,
        },
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "official_algorithm_changed": False,
        "figure_6_overwritten": False,
        "scientific_failure_retry_allowed": False,
    }
    pair = resume / "stage15h-valid.json"
    pair.write_text(json.dumps(payload), encoding="utf-8")
    assert validate(pair)["replay_exact"] is True
    report = build(
        Path("configs/experiments/pipe_normal_full_stage13f.json"),
        resume,
        tmp_path / "copied",
    )
    assert report["resumed_valid_pair_count"] == 1
    assert report["new_pair_count"] == 99


def test_stage15h_workflow_security_and_execution_contract() -> None:
    text = Path(".github/workflows/stage15h-thirty-workload-repairs.yml").read_text()
    assert "workflow_dispatch:" in text
    assert "max-parallel: 8" in text
    assert "fail-fast: false" in text
    assert "permissions:\n  contents: read\n  actions: read" in text
    assert "retention-days: 14" in text
    assert "if: always()" in text
    assert "secrets." not in text
    assert "31644121025" in text and "31716969817" in text and "31729227438" in text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in text
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert "run_stage15h_counterfactual.py" in text
    assert "run_stage15e_counterfactual.py" not in text


def test_stage15h_dispatch_sentinel_is_exact() -> None:
    assert Path(".github/stage15h-dispatch").read_text().strip() == (
        "stage15h-30-workload-two-repair-validation-approved-2026-08-15"
    )
