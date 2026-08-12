import json
import re
from pathlib import Path

FULL_CONFIG = Path("configs/experiments/pipe_normal_full_stage13f.json")
BATCH_PLAN = Path("configs/experiments/stage13j_five_batch_plan.json")


def test_stage13j_batches_partition_exactly_the_remaining_workloads() -> None:
    full = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
    plan = json.loads(BATCH_PLAN.read_text(encoding="utf-8"))
    all_seeds = [int(item["workload_seed"]) for item in full["runs"]]
    protected = set(all_seeds[:5])
    batches = plan["batches"]
    materialized = [int(seed) for batch in batches for seed in batch["workload_seeds"]]

    assert len(batches) == 5
    assert all(len(batch["workload_seeds"]) == 5 for batch in batches)
    assert len(materialized) == len(set(materialized)) == 25
    assert materialized == all_seeds[5:]
    assert not protected.intersection(materialized)
    assert plan["remaining_pairs"] == 100
    assert plan["execution_gate"] == "explicit_user_approval_required_before_each_batch"
    assert plan["artifact_policy"]["retention_days"] == 14
    assert plan["artifact_policy"]["public_git_commit_raw_data"] is False
    assert plan["workflow_resume_design"]["same_run_recovery"] == (
        "rerun failed jobs only so successful pair artifacts remain immutable"
    )
    assert plan["estimate_basis"]["estimated_actions_runner_minutes_per_batch"] > 0


def test_stage13j_workflow_is_manual_gated_and_does_not_auto_run() -> None:
    workflow = Path(".github/workflows/stage13j-five-workload-batch.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "\n  push:" not in workflow
    assert "RUN-STAGE13J-BATCH-" in workflow
    assert "max-parallel: 20" in workflow
    assert workflow.count("retention-days: 14") == 2
    assert "record_stage13j_batch.py" in workflow
    action_refs = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", workflow)
    assert len(action_refs) == 8
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs)
    assert "secrets." not in workflow
    assert "run_all" not in workflow
