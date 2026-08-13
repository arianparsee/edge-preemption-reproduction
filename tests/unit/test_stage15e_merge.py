from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SEEDS = (2074092324964443463, 2218754797665862270, 2997476077322633071, 3782887846963969634)
POLICIES = ("pipeline_double_knapsack_retention", "pipeline_double_knapsack_preemption")
VARIANTS = ("initial_population_repair", "offspring_repair")


def _script() -> ModuleType:
    path = ROOT / "scripts/merge_stage15e_validation.py"
    spec = importlib.util.spec_from_file_location("stage15e_merge", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-E merge")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _new_pair(seed: int, policy: str, variant: str) -> dict[str, object]:
    outcome = {
        "completed_jobs": 10,
        "completed_utility": 20.0,
        "rejected_jobs": 90,
        "rejected_utility": 80.0,
        "ever_preempted_jobs": 0,
        "ever_preempted_utility": 0.0,
        "raw_auction_rejection_count": 120,
    }
    return {
        "schema_version": "stage15e-counterfactual-pair-v1",
        "workload_seed": seed,
        "policy": policy,
        "variant": variant,
        "baseline_recomputed": False,
        "replay_exact": True,
        "rng_gate": {
            "option": "A",
            "passed_within_variant": True,
            "baseline_rng_gate_claimed": False,
            "baseline_final_rng_comparison": "unknown_not_recorded_in_stage13_baseline",
        },
        "variant_replay": {
            "scientific_fingerprint": {"outcome": outcome},
            "lifecycle_funnel": {
                "accepted": 10,
                "retry_scheduled": 5,
                "expired": 90,
                "completed": 10,
                "rejected": 120,
            },
            "selector_funnel": {
                "by_round": {"round_1": {"ga_calls": 2}, "round_2": {"ga_calls": 1}}
            },
            "counterfactual": {
                "initial_chromosomes_repaired": 3 if variant.startswith("initial") else 0,
                "offspring_repaired": 3 if variant.startswith("offspring") else 0,
            },
        },
        "outcome_delta_from_baseline": {key: 1.0 for key in outcome},
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "official_algorithm_changed": False,
        "figure_6_overwritten": False,
        "thirty_workloads_executed": False,
    }


def _paths(tmp_path: Path) -> list[Path]:
    paths = []
    for seed in SEEDS:
        for policy in POLICIES:
            for variant in VARIANTS:
                path = tmp_path / f"{seed}-{policy}-{variant}.json"
                path.write_text(json.dumps(_new_pair(seed, policy, variant)), encoding="utf-8")
                paths.append(path)
    return paths


def test_merge_combines_sixteen_new_and_four_reused_pairs(tmp_path: Path) -> None:
    report = _script().merge(
        _paths(tmp_path), ROOT / "tests/fixtures/stage15e_seed_one_reuse.json"
    )

    assert report["new_pair_count"] == 16
    assert report["reused_pair_count"] == 4
    assert report["seed_count"] == 5
    assert report["baseline_recomputed"] is False
    assert len(report["rows"]) == 20
    assert len(report["aggregate"]) == 4


def test_merge_rejects_incomplete_new_matrix(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exactly 16"):
        _script().merge(
            _paths(tmp_path)[:-1], ROOT / "tests/fixtures/stage15e_seed_one_reuse.json"
        )
