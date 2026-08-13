from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _script() -> ModuleType:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / "run_stage15d_counterfactual.py"
    spec = importlib.util.spec_from_file_location("stage15d_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-D runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _baseline() -> dict[str, object]:
    return {
        "initial_rng_state_sha256": "initial",
        "final_rng_state_sha256": "baseline-final",
        "uniform_choice_calls": 3,
        "by_round": {
            "round_1": {
                "selector_calls": 2,
                "empty_calls": 0,
                "single_candidate_calls": 0,
                "ga_calls": 2,
                "candidate_entries": 8,
            },
            "round_2": {
                "selector_calls": 2,
                "empty_calls": 1,
                "single_candidate_calls": 0,
                "ga_calls": 1,
                "candidate_entries": 2,
            },
        },
    }


def _replay(final: str = "baseline-final", ga_calls: int = 2) -> dict[str, object]:
    return {
        "selector_funnel": {
            "initial_rng_state_sha256": "initial",
            "final_rng_state_sha256": final,
            "by_round": {
                "round_1": {
                    "selector_calls": 2,
                    "empty_calls": 0,
                    "single_candidate_calls": 0,
                    "ga_calls": ga_calls,
                    "candidate_entries": 8,
                },
                "round_2": {
                    "selector_calls": 2,
                    "empty_calls": 1,
                    "single_candidate_calls": 0,
                    "ga_calls": 1,
                    "candidate_entries": 2,
                },
            },
        },
        "counterfactual": {"uniform_choice_calls": 3},
    }


def test_rng_gate_accepts_equal_state_and_shape() -> None:
    module = _script()

    result = module._enforce_baseline_rng_gate(baseline=_baseline(), replay=_replay())

    assert result["passed"] is True
    assert result["final_rng_state_equal"] is True
    assert result["recorded_call_shape_equal"] is True


def test_rng_gate_rejects_state_difference_with_equal_shape() -> None:
    module = _script()

    with pytest.raises(ValueError, match="call shape stayed equal"):
        module._enforce_baseline_rng_gate(
            baseline=_baseline(), replay=_replay(final="different")
        )


def test_rng_gate_allows_state_difference_explained_by_shape() -> None:
    module = _script()

    result = module._enforce_baseline_rng_gate(
        baseline=_baseline(), replay=_replay(final="different", ga_calls=1)
    )

    assert result["passed"] is True
    assert result["final_rng_state_equal"] is False
    assert result["recorded_call_shape_equal"] is False
    assert result["allowed_difference_reasons"] == ["round_1.ga_calls:2->1"]


def test_rng_gate_rejects_initial_state_difference() -> None:
    module = _script()
    replay = _replay()
    selector = cast(dict[str, object], replay["selector_funnel"])
    selector["initial_rng_state_sha256"] = "wrong"

    with pytest.raises(ValueError, match="initial policy RNG"):
        module._enforce_baseline_rng_gate(baseline=_baseline(), replay=replay)
