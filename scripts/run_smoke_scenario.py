"""Execute Stage 9's deterministic smoke scenario and persist real artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from edge_reproduction.models.enums import AssignmentFlowSemantics, DeadlineBoundary
from edge_reproduction.simulation.engine import run_scripted_simulation
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.scenarios import stage_nine_smoke_scenario


def main() -> int:
    state, commands, config = stage_nine_smoke_scenario()
    run = run_scripted_simulation(
        state,
        commands,
        config,
        deadline_boundary=DeadlineBoundary.INCLUSIVE,
        assignment_semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )

    expected_states = {
        "task-a": "preempted",
        "task-b": "rejected",
        "task-c": "completed",
        "task-d": "expired",
    }
    actual_states = {
        task_id: task_state.value for task_id, task_state in run.final_state.task_states.items()
    }
    if actual_states != expected_states:
        raise RuntimeError(f"smoke state mismatch: {actual_states!r}")
    if run.experiment_result.completed_utility != 30.0:
        raise RuntimeError("smoke completed utility mismatch")
    if len(run.events) != 11:
        raise RuntimeError(f"smoke event-count mismatch: {len(run.events)}")

    output_dir = Path("results/raw/stage9_smoke")
    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = output_dir / "events.jsonl"
    events_text = "".join(
        json.dumps(event.as_dict(), sort_keys=True) + "\n" for event in run.events
    )
    events_path.write_text(events_text, encoding="utf-8")

    summary = {
        "run_id": run.experiment_result.run_id,
        "experiment_id": run.experiment_result.experiment_id,
        "method": run.experiment_result.method,
        "seed": run.experiment_result.random_seed,
        "event_count": run.experiment_result.event_count,
        "completed_task_ids": run.experiment_result.completed_task_ids,
        "rejected_task_ids": run.experiment_result.rejected_task_ids,
        "ever_preempted_task_ids": run.experiment_result.ever_preempted_task_ids,
        "expired_task_ids": run.expired_task_ids,
        "completed_utility": run.experiment_result.completed_utility,
        "rejected_utility": run.experiment_result.rejected_utility,
        "preempted_utility": run.experiment_result.preempted_utility,
        "final_task_states": actual_states,
        "final_remaining_resources": {
            server_id: remaining_resources(run.final_state, server_id).as_dict()
            for server_id in run.final_state.servers
        },
        "metadata": dict(run.experiment_result.metadata),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"events={len(run.events)}")
    print(f"completed_utility={run.experiment_result.completed_utility}")
    print(f"states={json.dumps(actual_states, sort_keys=True)}")
    print(f"events_path={events_path}")
    print(f"summary_path={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
