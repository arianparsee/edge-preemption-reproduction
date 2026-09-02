import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]


def _script(name: str) -> ModuleType:
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prior_fixture_is_sanitized_and_complete() -> None:
    payload = json.loads(
        (ROOT / "tests/fixtures/stage15k2_prior_initialization_reuse.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["variant_recomputed"] is False
    assert payload["pair_count"] == 8
    assert len({(row["workload_seed"], row["policy"]) for row in payload["pairs"]}) == 8
    text = json.dumps(payload)
    assert '"task_id":' not in text
    assert '"chromosome_bits":' not in text


def test_runner_matrix_is_exactly_four_seeds_two_policies() -> None:
    module = _script("run_stage15k2_pair.py")
    assert len(module.SEEDS) == 4
    assert len(module.POLICIES) == 2
    assert module.VARIANT.value == "round_two_initial_population_repair"


def test_runner_rejects_seed_one_for_recomputation(tmp_path: Path) -> None:
    module = _script("run_stage15k2_pair.py")
    with pytest.raises(ValueError, match="outside"):
        module.run_pair(
            config_path=tmp_path / "c",
            baseline_path=tmp_path / "b",
            prior_path=tmp_path / "p",
            workload_seed=541501192080118187,
            policy_name=module.POLICIES[0],
        )


def test_public_validator_rejects_baseline_recomputation() -> None:
    module = _script("validate_stage15k2_pair.py")
    with pytest.raises(ValueError, match="baseline"):
        module.validate(
            {
                "schema_version": "stage15k2-r2-initialization-repair-pair-v1",
                "replay_exact": True,
                "replay_count": 2,
                "baseline_recomputed": True,
            }
        )


def test_workflow_has_exact_matrix_and_security_boundaries() -> None:
    text = (ROOT / ".github/workflows/stage15k2-five-seed-r2-repair.yml").read_text(
        encoding="utf-8"
    )
    assert "max-parallel: 8" in text
    assert "fail-fast: false" in text
    assert text.count("pipeline_double_knapsack_retention") >= 1
    assert text.count("pipeline_double_knapsack_preemption") >= 1
    for seed in (
        "2074092324964443463",
        "2218754797665862270",
        "2997476077322633071",
        "3782887846963969634",
    ):
        assert seed in text
    assert "541501192080118187" not in text
    assert "run-id: 33663692202" in text
    assert "secrets." not in text
    assert "actions: read" in text
    assert "retention-days: 14" in text


def test_workflow_actions_are_sha_pinned() -> None:
    text = (ROOT / ".github/workflows/stage15k2-five-seed-r2-repair.yml").read_text(
        encoding="utf-8"
    )
    uses = [
        line.split("@", 1)[1].split()[0] for line in text.splitlines() if "uses: actions/" in line
    ]
    assert uses and all(len(value) == 40 for value in uses)
