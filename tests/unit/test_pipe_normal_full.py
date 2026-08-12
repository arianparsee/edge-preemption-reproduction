import json
from pathlib import Path

import pytest

from edge_reproduction.experiments.orchestration import file_sha256
from edge_reproduction.experiments.pipe_normal_full import (
    POLICY_NAMES,
    aggregate_complete_full_run,
    load_full_config,
    materialized_config,
    write_materialized_config,
)


def test_materialized_assump_033_matrix_has_30_sorted_paired_workloads() -> None:
    config = materialized_config()
    runs = config["runs"]
    assert isinstance(runs, list)
    assert len(runs) == 30
    seeds = [run["workload_seed"] for run in runs]
    assert seeds == sorted(seeds)
    assert len(set(seeds)) == 30
    assert all(tuple(run["policy_seeds"]) == POLICY_NAMES for run in runs)
    assert all(len(set(run["policy_seeds"].values())) == 4 for run in runs)
    assert config["assumptions"] == [f"ASSUMP-{number:03d}" for number in range(33, 44)]
    settings = config["policy_ga_settings"]
    assert isinstance(settings, dict)
    assert all(isinstance(value, dict) for value in settings.values())
    assert settings[POLICY_NAMES[0]]["generations"] == 30
    assert settings[POLICY_NAMES[2]]["generations"] == 50


def test_materialized_config_round_trip_and_tamper_guard(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    write_materialized_config(path)
    assert load_full_config(path) == materialized_config()
    with pytest.raises(FileExistsError, match="overwrite"):
        write_materialized_config(path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["runs"][0]["policy_seeds"][POLICY_NAMES[0]] += 1
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        load_full_config(path)


def test_aggregation_fails_before_all_120_raw_runs_exist(tmp_path: Path) -> None:
    config_path = tmp_path / "full.json"
    write_materialized_config(config_path)
    with pytest.raises(FileNotFoundError, match="missing 120"):
        aggregate_complete_full_run(Path("full.json"), project_root=tmp_path)


def test_resume_verifies_existing_result_without_executing_full_run(tmp_path: Path) -> None:
    from edge_reproduction.experiments.pipe_normal_full import run_full_pair

    config_path = tmp_path / "full.json"
    write_materialized_config(config_path)
    config = load_full_config(config_path)
    runs = config["runs"]
    assert isinstance(runs, list)
    descriptor = runs[0]
    assert isinstance(descriptor, dict)
    seed = descriptor["workload_seed"]
    assert isinstance(seed, int)
    policy = POLICY_NAMES[0]
    run_directory = (
        tmp_path / "results" / "raw" / "stage13f" / "PIPE-NORMAL"
        / f"seed-{seed}" / policy
    )
    run_directory.mkdir(parents=True)
    result_path = run_directory / "result.json"
    result_path.write_text("{}\n", encoding="utf-8")
    manifest = {
        "result_sha256": file_sha256(result_path),
        "config_sha256": file_sha256(config_path),
    }
    (run_directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    outcome = run_full_pair(
        Path("full.json"),
        workload_seed=seed,
        policy_name=policy,
        project_root=tmp_path,
        resume=True,
    )

    assert outcome.status == "skipped_existing_verified"
