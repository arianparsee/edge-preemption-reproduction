import json
import shutil
from hashlib import sha256
from pathlib import Path

import pytest

from edge_reproduction.experiments.orchestration import run_experiment, run_registry

SOURCE_EXECUTION_CONFIG = Path("configs/experiments/auxiliary_stage13b_four_policy_smoke.json")
SOURCE_SCENARIO_CONFIG = Path("configs/stage10j_four_policy_regression.json")
SOURCE_REGISTRY = Path("configs/experiments/auxiliary_stage13b_registry.json")


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def prepare_project(root: Path) -> None:
    experiment_directory = root / "configs" / "experiments"
    experiment_directory.mkdir(parents=True)
    shutil.copyfile(
        SOURCE_EXECUTION_CONFIG,
        experiment_directory / SOURCE_EXECUTION_CONFIG.name,
    )
    shutil.copyfile(SOURCE_REGISTRY, experiment_directory / SOURCE_REGISTRY.name)
    shutil.copyfile(SOURCE_SCENARIO_CONFIG, root / "configs" / SOURCE_SCENARIO_CONFIG.name)


def test_one_run_is_isolated_labeled_and_resume_safe(tmp_path: Path) -> None:
    prepare_project(tmp_path)
    relative_config = Path("configs/experiments") / SOURCE_EXECUTION_CONFIG.name

    first = run_experiment(relative_config, project_root=tmp_path)
    result_hash = file_hash(first.result_path)
    manifest_hash = file_hash(first.manifest_path)
    result = json.loads(first.result_path.read_text(encoding="utf-8"))
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))

    assert first.status == "succeeded"
    assert result["scientific_label"] == ("auxiliary_single_auction_smoke_not_paper_experiment")
    assert result["payload"]["metric_warning"] == (
        "active_utility_after_auction_is_not_completed_paper_utility"
    )
    assert len(result["payload"]["records"]) == 4
    assert manifest["paper_experiment_claimed"] is False
    assert manifest["runtime_measurement_recorded"] is False
    assert manifest["result_sha256"] == result_hash
    assert manifest["unresolved_decisions"] == []

    with pytest.raises(FileExistsError, match="use resume"):
        run_experiment(relative_config, project_root=tmp_path)
    resumed = run_experiment(relative_config, project_root=tmp_path, resume=True)

    assert resumed.status == "skipped_existing_verified"
    assert file_hash(first.result_path) == result_hash
    assert file_hash(first.manifest_path) == manifest_hash


def test_resume_rejects_corrupted_existing_artifact(tmp_path: Path) -> None:
    prepare_project(tmp_path)
    relative_config = Path("configs/experiments") / SOURCE_EXECUTION_CONFIG.name
    outcome = run_experiment(relative_config, project_root=tmp_path)
    outcome.result_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="existing run provenance mismatch"):
        run_experiment(relative_config, project_root=tmp_path, resume=True)


def test_registry_writes_aggregate_index_and_verified_resume(tmp_path: Path) -> None:
    prepare_project(tmp_path)
    relative_registry = Path("configs/experiments") / SOURCE_REGISTRY.name

    first = run_registry(relative_registry, project_root=tmp_path)
    resumed = run_registry(relative_registry, project_root=tmp_path, resume=True)

    assert first["run_count"] == 1
    assert first["succeeded_count"] == 1
    assert first["verified_skip_count"] == 0
    assert resumed["succeeded_count"] == 0
    assert resumed["verified_skip_count"] == 1
    assert resumed["paper_experiment_claimed"] is False
    assert Path(str(first["summary_path"])).is_file()


def test_raw_result_and_manifest_are_byte_stable_across_clean_roots(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    prepare_project(first_root)
    prepare_project(second_root)
    relative_config = Path("configs/experiments") / SOURCE_EXECUTION_CONFIG.name

    first = run_experiment(relative_config, project_root=first_root)
    second = run_experiment(relative_config, project_root=second_root)

    assert file_hash(first.result_path) == file_hash(second.result_path)
    assert file_hash(first.manifest_path) == file_hash(second.manifest_path)
