from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import materialize_stage15h_baseline_lifecycle as lifecycle_recovery
from analyze_stage15a_dk_weakness import LifecycleRow
from prepare_stage15h_matrix import build
from pytest import MonkeyPatch
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
    assert {r["batch_id"] for r in rows} == {1, 2, 3, 4, 5}


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
    assert "31644121025" in text and "31847136180" in text
    assert "31716969817" not in text and "31729227438" not in text
    assert "302b6b88083d51c84bd14abbf7415466b91b81f48bd32d120f19188080a4bc8b" in text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in text
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert "download_github_run_artifacts.py" in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "run_stage15h_counterfactual.py" in text
    assert "run_stage15e_counterfactual.py" not in text
    assert "id: baseline_metrics" in text
    assert "find baseline-aggregate -type f -name raw_run_metrics.csv" in text
    assert "baseline-aggregate/results/aggregated/stage13j/raw_run_metrics.csv" not in text
    assert text.count("if: ${{ inputs.resume_run_id != '32474360245' }}") == 2
    assert "if: ${{ always() && inputs.resume_run_id != '32474360245' }}" in text
    assert "aggregate-only:" in text
    recovery = text.split("  aggregate-only:\n", maxsplit=1)[1]
    assert "if: ${{ inputs.resume_run_id == '32474360245' }}" in recovery
    assert "strategy:" not in recovery
    assert "matrix:" not in recovery
    assert "run_stage15h_counterfactual.py" not in recovery
    assert "run_stage15e_counterfactual.py" not in recovery
    assert "pipe_normal_full.py" not in recovery
    assert "workload_or_policy_executed=false" in recovery
    assert "materialize_stage15h_baseline_lifecycle.py" in recovery
    assert "fac98f37a6faf23bdb91387498ed11008611adef29b383d24f1c866f8504610a" in recovery
    assert "e17e18cd10760a6f004424905e9dcfd617b950aa334d0498f11dfe722cfad179" in recovery
    assert "results/aggregated/stage15a/per_run_lifecycle.csv" not in recovery


def test_stage15i_aggregation_only_workflow_cannot_execute_a_workload() -> None:
    text = Path(
        ".github/workflows/stage15i-stage15h-aggregation-only.yml"
    ).read_text()
    assert "workflow_dispatch:" in text
    assert "permissions:\n  contents: read\n  actions: read" in text
    assert "timeout-minutes: 45" in text
    assert "32474360245" in text and "31644121025" in text
    assert "4c84c1a479f5fdc6d89c4c573e9a6d690d299cec5d473771bb9ab9a9af6bd4b6" in text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in text
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert "finalize_stage15h_validation.py" in text
    assert "stage15i_delivery.sha256" in text
    assert "repair-pair:" not in text
    assert "strategy:" not in text
    assert "matrix:" not in text
    assert "run_stage15h_counterfactual.py" not in text
    assert "run_stage15e_counterfactual.py" not in text
    assert "pipe_normal_full.py" not in text
    assert "secrets." not in text
    assert "materialize_stage15h_baseline_lifecycle.py" in text
    assert "results/aggregated/stage15a/per_run_lifecycle.csv" not in text


def test_stage15i_lifecycle_recovery_validates_120_pinned_results(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    baseline_root = tmp_path / "baseline"
    entries: list[dict[str, object]] = []
    payloads: dict[str, dict[str, object]] = {}
    policies = (
        "knapsack_greedy_retention",
        "knapsack_greedy_preemption",
        "pipeline_double_knapsack_retention",
        "pipeline_double_knapsack_preemption",
    )
    for index in range(120):
        seed = str(10_000 + index // 4)
        policy = policies[index % 4]
        payload: dict[str, object] = {
            "workload_seed": seed,
            "policy": policy,
            "policy_seed": str(20_000 + index),
            "workload_sha256": hashlib.sha256(seed.encode()).hexdigest(),
        }
        target = baseline_root / f"pair-{index:03d}" / "result.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(payload), encoding="utf-8")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        entries.append({**payload, "result_sha256": digest})
        payloads[f"{seed}:{policy}"] = payload

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "source_run_id": 31644121025,
                "validated_pair_count": 120,
                "entries": entries,
            }
        ),
        encoding="utf-8",
    )

    def fake_row(payload: dict[str, object]) -> LifecycleRow:
        return LifecycleRow(
            workload_seed=int(str(payload["workload_seed"])),
            policy=str(payload["policy"]),
            generated_jobs=1,
            round_one_no_server_rejections=0,
            round_two_rejections=0,
            retry_scheduled=0,
            retry_attempts=0,
            canonical_expirations=0,
            post_rejection_expirations=0,
            waiting_deadline_expirations=0,
            active_deadline_expirations=0,
            accepted_jobs=1,
            accepted_first_attempt=1,
            accepted_after_retry=0,
            completed_jobs=1,
            preempted_jobs=0,
            ga_repairs=0,
            completed_utility=1.0,
        )

    monkeypatch.setattr(lifecycle_recovery, "lifecycle_row", fake_row)
    trial_output = tmp_path / "trial.csv"
    try:
        lifecycle_recovery.materialize(
            baseline_root=baseline_root,
            manifest_path=manifest,
            output_path=trial_output,
            report_path=tmp_path / "unused-report.json",
            expected_output_sha256="0" * 64,
        )
    except ValueError as error:
        assert "differs from the pinned" in str(error)
    else:
        raise AssertionError("checksum mismatch must fail")

    # Materialize an equivalent reference once to obtain the expected digest.
    rows = sorted(
        (fake_row(payload) for payload in payloads.values()),
        key=lambda row: (str(row.workload_seed), row.policy),
    )
    reference = tmp_path / "reference.csv"
    with reference.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    expected = hashlib.sha256(reference.read_bytes()).hexdigest()
    output = tmp_path / "lifecycle.csv"
    report_path = tmp_path / "report.json"
    report = lifecycle_recovery.materialize(
        baseline_root=baseline_root,
        manifest_path=manifest,
        output_path=output,
        report_path=report_path,
        expected_output_sha256=expected,
    )
    assert report["baseline_pair_count"] == 120
    assert report["simulation_or_policy_executed"] is False
    assert hashlib.sha256(output.read_bytes()).hexdigest() == expected


def test_stage15h_dispatch_sentinel_is_exact() -> None:
    assert Path(".github/stage15h-dispatch").read_text().strip() == (
        "stage15h-30-workload-two-repair-validation-approved-2026-08-15"
    )
