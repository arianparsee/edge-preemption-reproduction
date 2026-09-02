from __future__ import annotations

import errno
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _script(name: str) -> ModuleType:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / name
    spec = importlib.util.spec_from_file_location(f"stage15k1_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_all_reuse_inputs_are_pinned_and_scientifically_identified() -> None:
    module = _script("run_stage15k1_pilot.py")
    config = ROOT / "configs/experiments/pipe_normal_full_stage13f.json"
    baselines = ROOT / "tests/fixtures/stage15e_reused_baselines.json"
    prior = ROOT / "tests/fixtures/stage15e_seed_one_reuse.json"
    diagnostic = ROOT / "tests/fixtures/stage15k1_baseline_diagnostics.json"

    assert module.normalized_text_sha256(config) == module.EXPECTED_CONFIG_SHA256
    assert (
        module.normalized_text_sha256(baselines)
        == module.EXPECTED_BASELINE_FIXTURE_SHA256
    )
    assert (
        module.normalized_text_sha256(prior)
        == module.EXPECTED_PRIOR_REPAIR_FIXTURE_SHA256
    )
    assert (
        module.normalized_text_sha256(diagnostic)
        == module.EXPECTED_BASELINE_DIAGNOSTICS_SHA256
    )
    prior_payload = json.loads(prior.read_text(encoding="utf-8"))
    for policy in module.DK_POLICIES:
        pair = module._find_prior_pair(prior_payload, policy)
        assert pair["workload_seed"] == module.WORKLOAD_SEED
        assert pair["variant"] == "initial_population_repair"
        assert pair["replay_exact"] is True


def test_transient_failure_retries_once_but_scientific_failure_never_retries() -> None:
    module = _script("run_stage15k1_pilot.py")
    calls = 0

    def transient() -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError(errno.ETIMEDOUT, "temporary")
        return {"ok": True}

    value, _runtime, retries = module._execute_with_one_transient_retry(transient)
    assert value == {"ok": True}
    assert retries == 1
    assert calls == 2

    calls = 0

    def scientific() -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise ValueError("invariant")

    with pytest.raises(ValueError, match="invariant"):
        module._execute_with_one_transient_retry(scientific)
    assert calls == 1


def test_public_validator_rejects_task_identifiers() -> None:
    module = _script("validate_stage15k1_public_pair.py")

    with pytest.raises(ValueError, match="banned key"):
        module._walk({"nested": {"task_ids": ["private"]}})
