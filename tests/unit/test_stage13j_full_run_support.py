from __future__ import annotations

import importlib.util
import json
import shutil
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest


def _script(name: str) -> ModuleType:
    path = Path("scripts") / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_transient_retry_retries_only_allowlisted_failure(tmp_path: Path) -> None:
    module = _script("run_with_transient_retry.py")
    assert "connection reset" in module.TRANSIENT
    assert "invariant" in module.SCIENTIFIC
    assert not set(module.TRANSIENT) & set(module.SCIENTIFIC)


def test_batch_validator_does_not_call_missing_data_a_transient_failure() -> None:
    source = Path("scripts/validate_stage13j_batch_checkpoint.py").read_text(encoding="utf-8")
    assert "complete_result_count < 20 and bool(failed_metadata)" in source


def test_stage13j_workflows_keep_batches_sequential_and_bounded() -> None:
    caller = Path(".github/workflows/stage13j-full-run.yml").read_text(encoding="utf-8")
    reusable = Path(".github/workflows/stage13j-five-workload-batch.yml").read_text(
        encoding="utf-8"
    )
    assert caller.count("uses: ./.github/workflows/stage13j-five-workload-batch.yml") == 5
    for batch in range(2, 6):
        assert f"needs: batch-{batch - 1}" in caller
        assert f"needs.batch-{batch - 1}.outputs.continue_allowed == 'true'" in caller
    assert "max-parallel: 8" in reusable
    assert "fail-fast: false" in reusable
    assert "retention-days: 14" in reusable
    assert "retry-${{ env.WORKLOAD_SEED }}-${{ env.POLICY }}.json" in reusable


def test_finalizer_requires_exact_config_hash_before_aggregation(tmp_path: Path) -> None:
    module = _script("finalize_stage13j_full_run.py")
    root = tmp_path / "root"
    root.mkdir()
    config = root / "config.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "stage13f-pipe-normal-full-v1",
                "experiment_id": "PIPE-NORMAL",
                "baseline": "arXiv:2403.15665v2_2024",
                "root_seed": 20240812,
                "repeat_count": 30,
                "runs": [],
            }
        ),
        encoding="utf-8",
    )
    assert sha256(config.read_bytes()).hexdigest() == module._hash(config)
    with pytest.raises((KeyError, ValueError, TypeError)):
        module.finalize(root, config, root / "out", root / "figures")


def test_finalizer_accepts_exactly_120_small_valid_pairs(tmp_path: Path) -> None:
    module = _script("finalize_stage13j_full_run.py")
    root = tmp_path / "root"
    root.mkdir()
    config = root / "pipe_normal_full_stage13f.json"
    shutil.copyfile("configs/experiments/pipe_normal_full_stage13f.json", config)
    raw = json.loads(config.read_text(encoding="utf-8"))
    config_hash = sha256(config.read_bytes()).hexdigest()
    policies = tuple(module.POLICY_NAMES)
    for descriptor in raw["runs"]:
        seed = descriptor["workload_seed"]
        workload = {"tasks": [{"task_id": f"task-{seed}"}]}
        workload_bytes = (json.dumps(workload, sort_keys=True) + "\n").encode()
        workload_hash = sha256(workload_bytes).hexdigest()
        for index, policy in enumerate(policies):
            pair = root / "results/raw/stage13f/PIPE-NORMAL" / f"seed-{seed}" / policy
            pair.mkdir(parents=True)
            (pair / "workload.json").write_bytes(workload_bytes)
            result = {
                "workload_seed": seed,
                "policy_seed": descriptor["policy_seeds"][policy],
                "policy": policy,
                "workload_sha256": workload_hash,
                "run": {
                    "final_task_states": {f"task-{seed}": "COMPLETED"},
                    "outcome": {
                        "completed_task_ids": [f"task-{seed}"],
                        "rejected_task_ids": [],
                        "ever_preempted_task_ids": [],
                        "completed_utility": 100.0 - index,
                        "rejected_utility": 0.0,
                        "ever_preempted_utility": 0.0,
                        "completed_jobs": 1,
                        "rejected_jobs": 0,
                        "ever_preempted_jobs": 0,
                        "raw_auction_rejection_count": 0,
                    },
                },
            }
            result_bytes = (json.dumps(result, sort_keys=True) + "\n").encode()
            (pair / "result.json").write_bytes(result_bytes)
            (pair / "manifest.json").write_text(
                json.dumps(
                    {
                        "config_sha256": config_hash,
                        "workload_sha256": workload_hash,
                        "result_sha256": sha256(result_bytes).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
    report = module.finalize(root, config, root / "aggregate", root / "figures")
    assert report["validated_pairs"] == 120
    assert (root / "aggregate/figure6_reproduced_data.csv").is_file()
    assert (root / "figures/figure6_reproduced.png").is_file()
    assert (root / "figures/figure6_reproduced.pdf").is_file()
