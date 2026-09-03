import importlib.util
import inspect
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
APPROVED_SEED_STRINGS = (
    "541501192080118187",
    "2074092324964443463",
    "2218754797665862270",
    "2997476077322633071",
    "3782887846963969634",
)


def _script(name: str) -> ModuleType:
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_five_approved_seed_strings_round_trip_without_float() -> None:
    module = _script("finalize_stage15k2.py")

    assert tuple(module.SEED_STRINGS) == APPROVED_SEED_STRINGS
    for seed_string in APPROVED_SEED_STRINGS:
        assert module._exact_decimal_seed(seed_string) == int(seed_string, 10)
        assert str(module._exact_decimal_seed(seed_string)) == seed_string

    source = inspect.getsource(module._exact_decimal_seed)
    assert "float(" not in source
    assert "_num(" not in source


@pytest.mark.parametrize(
    "invalid",
    [
        2.0740923249644434e18,
        "2.0740923249644434E+18",
        "2074092324964443463.0",
        "02074092324964443463",
        True,
    ],
)
def test_exact_seed_parser_rejects_float_and_noncanonical_notation(invalid: object) -> None:
    module = _script("finalize_stage15k2.py")
    with pytest.raises((TypeError, ValueError)):
        module._exact_decimal_seed(invalid)


def test_completeness_and_sorting_do_not_use_numeric_metric_float_parser() -> None:
    module = _script("finalize_stage15k2.py")
    source = inspect.getsource(module.finalize)

    assert '_exact_decimal_seed(row["workload_seed"])' in source
    assert 'int(_num(row["workload_seed"]))' not in source
    assert 'float(row["workload_seed"])' not in source


def test_aggregation_only_workflow_is_pinned_and_has_no_scientific_runner() -> None:
    workflow = ROOT / ".github/workflows/stage15k2r1-aggregation-only.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "run-id: 33688857517" in text
    assert "run-id: 33663692202" in text
    assert "stage15k2-*-33688857517" in text
    assert "stage15k1-*-33663692202" in text
    assert "run_stage15k2_pair.py" not in text
    assert "run_stage15k1_pilot.py" not in text
    assert "matrix:" not in text
    assert '"scientific_executions": 0' in text
    assert "secrets." not in text
    assert "contents: read" in text and "actions: read" in text

    pins = [
        line.split("@", 1)[1].split()[0]
        for line in text.splitlines()
        if "uses: actions/" in line
    ]
    assert pins and all(re.fullmatch(r"[0-9a-f]{40}", pin) for pin in pins)


def test_input_validator_uses_exact_parser_and_pinned_sources() -> None:
    module = _script("validate_stage15k2r1_inputs.py")
    source = inspect.getsource(module)

    assert module.K1_RUN_ID == "33663692202"
    assert module.K2_RUN_ID == "33688857517"
    assert "_exact_decimal_seed" in source
    assert "float(" not in source
    assert "expected 10/10 logical pairs" in source
