"""Execute the hand-sized Stage-10B KnapsackGreedy Retention example."""

from __future__ import annotations

import json
from pathlib import Path

from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    KnapsackGreedyRetentionPolicy,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def run_example() -> dict[str, object]:
    """Return the deterministic auxiliary result used by the manual oracle."""

    current = _task("current", 4.0, 5.0)
    auto = _task("auto", 6.0, 15.0)
    rejected_high = _task("rejected-high", 4.0, 10.0)
    rejected_low = _task("rejected-low", 2.0, 4.0)
    impossible = _task("impossible", 11.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    tasks = (current, auto, rejected_high, rejected_low, impossible)
    state = SimulationState(
        0,
        {task.task_id: task for task in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)
    policy = KnapsackGreedyRetentionPolicy(ExactUtilityKnapsackSelector())
    result = policy.run(
        state,
        requesting_task_ids=(
            auto.task_id,
            rejected_high.task_id,
            rejected_low.task_id,
            impossible.task_id,
        ),
        time_remaining_by_task={
            current.task_id: 4.0,
            auto.task_id: 5.0,
            rejected_high.task_id: 4.0,
            rejected_low.task_id: 4.0,
        },
    )
    return {
        "label": "auxiliary_test_not_paper_result",
        "method_control_flow": policy.name,
        "selector": "exact_utility_auxiliary_not_paper_ga",
        "assumptions": ["ASSUMP-007", "ASSUMP-008", "ASSUMP-009"],
        "round_one_bids": [
            {
                "task_id": bid.task_id,
                "server_id": bid.server_id,
                "price": bid.price,
                "feasible": bid.feasible,
                "auto_fit": bid.auto_fit,
            }
            for bid in result.round_one.bids
        ],
        "selected_server_by_task": dict(result.selected_server_by_task),
        "accepted_task_ids": list(result.accepted_task_ids),
        "rejected_task_ids": list(result.rejected_task_ids),
        "final_task_states": {
            task_id: task_state.value
            for task_id, task_state in sorted(result.final_state.task_states.items())
        },
        "residual_before": remaining_resources(state, server.server_id).as_dict(),
        "residual_after": remaining_resources(result.final_state, server.server_id).as_dict(),
        "preempted_task_ids": [
            task_id
            for task_id, task_state in result.final_state.task_states.items()
            if task_state.value == "preempted"
        ],
    }


def main() -> None:
    output_path = Path("results/raw/stage10b/kg_retention_example.json")
    result = run_example()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"output_path={output_path}")


if __name__ == "__main__":
    main()
