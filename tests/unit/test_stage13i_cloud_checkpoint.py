import importlib.util
import json
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest

from edge_reproduction.experiments.pipe_normal_full import (
    POLICY_NAMES,
    write_materialized_config,
)


def _load_recorder() -> ModuleType:
    path = Path("scripts/record_stage13i_cloud_checkpoint.py")
    spec = importlib.util.spec_from_file_location("stage13i_recorder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Stage-13I recorder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECORDER = _load_recorder()
SEEDS = (
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _fixture(root: Path, config_path: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    descriptors = {run["workload_seed"]: run for run in config["runs"]}
    for seed_index, seed in enumerate(SEEDS):
        workload = {
            "tasks": [{"task_id": "a"}, {"task_id": "b"}],
            "synthetic_seed_marker": seed,
        }
        for policy_index, policy in enumerate(POLICY_NAMES):
            directory = (
                root
                / "results"
                / "raw"
                / "stage13f"
                / "PIPE-NORMAL"
                / f"seed-{seed}"
                / policy
            )
            workload_path = directory / "workload.json"
            result_path = directory / "result.json"
            manifest_path = directory / "manifest.json"
            _write(workload_path, workload)
            result = {
                "workload_seed": seed,
                "policy": policy,
                "policy_seed": descriptors[seed]["policy_seeds"][policy],
                "run": {
                    "outcome": {
                        "completed_task_ids": ["a"],
                        "rejected_task_ids": ["b"],
                        "ever_preempted_task_ids": [],
                        "completed_jobs": 1,
                        "rejected_jobs": 1,
                        "ever_preempted_jobs": 0,
                        "completed_utility": 10.0 + seed_index,
                        "rejected_utility": 5.0,
                        "ever_preempted_utility": 0.0,
                        "raw_auction_rejection_count": 2,
                    },
                    "metadata": {
                        "ga.zero_fitness_feasibility_repairs": str(policy_index),
                        "client.equal_minimum_price_ties": "0",
                    },
                },
            }
            _write(result_path, result)
            _write(
                manifest_path,
                {
                    "result_sha256": _hash(result_path),
                    "workload_sha256": _hash(workload_path),
                },
            )
            (root / f"timing-{seed}-{policy}.txt").write_text(
                f"{100 + seed_index + policy_index}.0\n", encoding="utf-8"
            )


def test_stage13i_recorder_requires_and_validates_exactly_sixteen_pairs(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "full.json"
    write_materialized_config(config_path)
    _fixture(tmp_path, config_path)

    summary = RECORDER.record_checkpoint(root=tmp_path, config_path=config_path)

    assert summary["checkpoint_workload_count"] == 4
    assert summary["checkpoint_pair_count"] == 16
    assert summary["cumulative_pairs_executed_including_stage13h"] == "20/120"
    assert summary["full_30_repeat_run_completed"] is False
    assert summary["scientific_aggregation_performed"] is False
    assert summary["figure_6_reproduced"] is False
    assert len(summary["runs"]) == 16
    assert len(summary["workloads"]) == 4
    assert all(row["task_count"] == 2 for row in summary["workloads"])


def test_stage13i_recorder_fails_on_missing_or_tampered_pair(tmp_path: Path) -> None:
    config_path = tmp_path / "full.json"
    write_materialized_config(config_path)
    _fixture(tmp_path, config_path)
    timing = tmp_path / f"timing-{SEEDS[0]}-{POLICY_NAMES[0]}.txt"
    timing.unlink()

    with pytest.raises(FileNotFoundError, match="missing Stage-13I artifact"):
        RECORDER.record_checkpoint(root=tmp_path, config_path=config_path)


def test_workflow_quotes_all_uint64_matrix_seeds_to_prevent_float_coercion() -> None:
    workflow = Path(
        ".github/workflows/stage13i-four-workload-checkpoint.yml"
    ).read_text(encoding="utf-8")

    for seed in SEEDS:
        assert f'- "{seed}"' in workflow
        assert f"- {seed}\n" not in workflow
