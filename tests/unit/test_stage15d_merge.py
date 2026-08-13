from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)
VARIANTS = ("fixed_penalty", "initial_population_repair", "offspring_repair")


def _script() -> ModuleType:
    path = ROOT / "scripts/merge_stage15d_counterfactuals.py"
    spec = importlib.util.spec_from_file_location("stage15d_merge", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-D merge")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _payload(policy: str, variant: str) -> dict[str, object]:
    outcome = {
        "completed_jobs": 2,
        "completed_utility": 3.0,
        "rejected_jobs": 4,
        "rejected_utility": 5.0,
        "ever_preempted_jobs": 0,
        "ever_preempted_utility": 0.0,
        "raw_auction_rejection_count": 4,
    }
    round_values = {
        "ga_calls": 1,
        "candidate_entries": 2,
        "repair_count": 0,
    }
    return {
        "schema_version": "stage15d-counterfactual-pair-v1",
        "baseline_recomputed": False,
        "replay_exact": True,
        "workload_seed": 541501192080118187,
        "policy": policy,
        "variant": variant,
        "rng_gate": {
            "passed": True,
            "final_rng_state_equal": False,
            "recorded_call_shape_equal": False,
            "allowed_difference_reasons": ["round_1.ga_calls"],
        },
        "variant_replay": {
            "scientific_fingerprint": {"outcome": outcome},
            "selector_funnel": {
                "by_round": {"round_1": round_values, "round_2": round_values}
            },
            "auction_funnel": {
                "totals": {"round_2_accepted": 2, "round_2_rejected": 4}
            },
            "counterfactual": {
                "initial_chromosomes_repaired": 0,
                "initial_bits_removed": 0,
                "offspring_repaired": 0,
                "offspring_bits_removed": 0,
            },
            "selector_call_shape_sha256": "shape",
            "selector_rng_trace_sha256": "rng",
        },
        "task_identifiers_in_artifact": False,
        "chromosome_bits_in_artifact": False,
        "raw_workload_in_artifact": False,
        "raw_trace_in_artifact": False,
        "figure_6_overwritten": False,
        "thirty_workloads_executed": False,
    }


def _files(tmp_path: Path) -> list[Path]:
    paths = []
    for policy in POLICIES:
        for variant in VARIANTS:
            path = tmp_path / f"{policy}-{variant}.json"
            path.write_text(json.dumps(_payload(policy, variant)), encoding="utf-8")
            paths.append(path)
    return paths


def test_merge_requires_and_preserves_all_six_pairs(tmp_path: Path) -> None:
    module = _script()

    report = module.merge(_files(tmp_path))

    assert report["pair_count"] == 6
    assert report["all_replays_exact"] is True
    assert report["all_rng_gates_passed"] is True
    assert report["task_identifiers_in_artifact"] is False


def test_merge_rejects_incomplete_matrix(tmp_path: Path) -> None:
    module = _script()

    with pytest.raises(ValueError, match="exactly six"):
        module.merge(_files(tmp_path)[:-1])


def test_merge_rejects_sensitive_boundary_flag(tmp_path: Path) -> None:
    module = _script()
    paths = _files(tmp_path)
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    payload["task_identifiers_in_artifact"] = True
    paths[0].write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="public-boundary"):
        module.merge(paths)


def test_write_csv_emits_six_rows(tmp_path: Path) -> None:
    module = _script()
    report = module.merge(_files(tmp_path))
    output = tmp_path / "summary.csv"

    module.write_csv(report, output)

    assert len(output.read_text(encoding="utf-8").splitlines()) == 7
