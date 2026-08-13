from __future__ import annotations

import errno
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _script() -> ModuleType:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / "run_stage15e_counterfactual.py"
    spec = importlib.util.spec_from_file_location("stage15e_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-E runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_transient_error_is_retried_exactly_once() -> None:
    module = _script()
    calls = 0

    def operation() -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError(errno.ETIMEDOUT, "temporary")
        return {"ok": True}

    value, retries = module._execute_with_one_transient_retry(operation)

    assert value == {"ok": True}
    assert retries == 1
    assert calls == 2


def test_scientific_failure_is_never_retried() -> None:
    module = _script()
    calls = 0

    def operation() -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise ValueError("invariant")

    with pytest.raises(ValueError, match="invariant"):
        module._execute_with_one_transient_retry(operation)
    assert calls == 1


def test_nontransient_os_error_is_never_retried() -> None:
    module = _script()
    calls = 0

    def operation() -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise OSError(errno.EINVAL, "config")

    with pytest.raises(OSError):
        module._execute_with_one_transient_retry(operation)
    assert calls == 1


def test_fixture_exposes_option_a_missing_baseline_rng() -> None:
    data = __import__("json").loads(
        (ROOT / "tests/fixtures/stage15e_reused_baselines.json").read_text(encoding="utf-8")
    )
    records = list(data["records"].values())

    assert data["baseline_recomputed"] is False
    assert len(records) == 10
    assert sum(row["baseline_rng_status"] == "available_reused_stage15c" for row in records) == 2
    assert sum(row["baseline_rng_status"] == "unavailable_not_recorded" for row in records) == 8
    assert all(
        row["baseline_rng"] is None
        for row in records
        if row["baseline_rng_status"] == "unavailable_not_recorded"
    )
