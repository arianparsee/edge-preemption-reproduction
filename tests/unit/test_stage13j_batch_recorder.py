import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

POLICIES = (
    "knapsack_greedy_retention",
    "knapsack_greedy_preemption",
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def test_record_batch_validates_exactly_twenty_pairs(tmp_path: Path) -> None:
    seeds = (11, 12, 13, 14, 15)
    config_path = tmp_path / "config.json"
    plan_path = tmp_path / "plan.json"
    _write_json(
        config_path,
        {
            "runs": [
                {
                    "workload_seed": seed,
                    "policy_seeds": {
                        policy: seed * 100 + index for index, policy in enumerate(POLICIES)
                    },
                }
                for seed in seeds
            ]
        },
    )
    _write_json(plan_path, {"batches": [{"batch": 1, "workload_seeds": seeds}]})

    for seed in seeds:
        workload = {"tasks": [{"task_id": f"task-{seed}"}]}
        workload_bytes = (json.dumps(workload, sort_keys=True) + "\n").encode()
        workload_hash = sha256(workload_bytes).hexdigest()
        for index, policy in enumerate(POLICIES):
            pair = (
                tmp_path
                / "results/raw/stage13f/PIPE-NORMAL"
                / f"seed-{seed}"
                / policy
            )
            pair.mkdir(parents=True)
            (pair / "workload.json").write_bytes(workload_bytes)
            result = {
                "workload_seed": seed,
                "policy": policy,
                "policy_seed": seed * 100 + index,
                "run": {
                    "final_task_states": {f"task-{seed}": "completed"},
                    "outcome": {
                        "completed_task_ids": [f"task-{seed}"],
                        "rejected_task_ids": [],
                        "ever_preempted_task_ids": [],
                        "completed_jobs": 1,
                        "rejected_jobs": 0,
                        "ever_preempted_jobs": 0,
                    },
                },
            }
            _write_json(pair / "result.json", result)
            result_hash = sha256((pair / "result.json").read_bytes()).hexdigest()
            _write_json(
                pair / "manifest.json",
                {
                    "result_sha256": result_hash,
                    "workload_sha256": workload_hash,
                },
            )
            (tmp_path / f"timing-{seed}-{policy}.txt").write_text(
                f"{10 + index}.0\n", encoding="utf-8"
            )

    output = tmp_path / "summary.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/record_stage13j_batch.py",
            "--root",
            str(tmp_path),
            "--config",
            str(config_path),
            "--batch-plan",
            str(plan_path),
            "--batch",
            "1",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"pairs": 20' in completed.stdout
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["workload_count"] == 5
    assert summary["pair_count"] == 20
    assert len(summary["runs"]) == 20
    assert len(summary["workloads"]) == 5
    assert summary["full_30_repeat_run_completed"] is False
