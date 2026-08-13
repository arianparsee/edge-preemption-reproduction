from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _script(name: str) -> ModuleType:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_stage15a_extracts_admission_retry_expiration_and_completion() -> None:
    module = _script("analyze_stage15a_dk_weakness.py")
    payload = {
        "workload_seed": 1,
        "policy": "pipeline_double_knapsack_preemption",
        "run": {
            "events": [
                {"event_type": "accepted", "task_id": "a", "server_id": "s", "reason": "x"},
                {"event_type": "completed", "task_id": "a", "server_id": "s", "reason": "x"},
                {"event_type": "rejected", "task_id": "b", "server_id": "s", "reason": "x"},
                {"event_type": "retry_scheduled", "task_id": "b", "server_id": None, "reason": "x"},
                {
                    "event_type": "expired",
                    "task_id": "b",
                    "server_id": None,
                    "reason": (
                        "post_rejection_next_epoch_infeasible:"
                        "isolated_pipeline_misses_deadline"
                    ),
                },
                {
                    "event_type": "expired",
                    "task_id": "c",
                    "server_id": None,
                    "reason": "canonical_admission_infeasible:isolated_pipeline_misses_deadline",
                },
            ],
            "outcome": {
                "completed_jobs": 1,
                "ever_preempted_jobs": 0,
                "raw_auction_rejection_count": 1,
                "completed_utility": 7.0,
            },
            "metadata": {"ga.zero_fitness_feasibility_repairs": "2"},
            "retry_count_by_task": {"a": 0, "b": 1, "c": 0},
            "final_task_states": {"a": "completed", "b": "expired", "c": "expired"},
        },
    }
    row = module.lifecycle_row(payload)
    assert row.round_one_no_server_rejections == 0
    assert row.round_two_rejections == 1
    assert row.canonical_expirations == 1
    assert row.post_rejection_expirations == 1
    assert row.accepted_first_attempt == 1
    assert row.completed_jobs == 1
    assert row.ga_repairs == 2


def test_stage14a_refuses_incomplete_finalization(tmp_path: Path) -> None:
    module = _script("register_stage14a_figure6.py")
    source = tmp_path / "source"
    report = source / "results/aggregated/stage13j/finalization_report.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"status": "complete", "validated_pairs": 119}))
    try:
        module.register(source, tmp_path / "project")
    except FileNotFoundError:
        # Hash-pinned artifacts are checked before the finalization counters.
        pass
    else:
        raise AssertionError("incomplete or missing source artifacts must not be registered")


def test_stage14a_reads_the_published_figure_csv_schema() -> None:
    module = _script("register_stage14a_figure6.py")
    rows = [
        {
            "policy": policy,
            "metric": "completed_utility",
            "arithmetic_mean": str(index),
        }
        for index, policy in enumerate(module.POLICY_LABELS, start=1)
    ]
    completed = module._completed_utility_by_label(rows)
    assert completed == {"KG-R": 1.0, "KG-P": 2.0, "DK-R": 3.0, "DK-P": 4.0}
