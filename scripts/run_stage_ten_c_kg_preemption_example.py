"""Execute the hand-sized Stage-10C KnapsackGreedy Preemption example."""

from __future__ import annotations

import json
from pathlib import Path

from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_preemption import (
    KnapsackGreedyPreemptionPolicy,
    capture_victim_snapshot,
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

    victim_low = _task("victim-low", 4.0, 4.0)
    victim_high = _task("victim-high", 4.0, 12.0)
    auto = _task("auto", 2.0, 8.0)
    incoming_first = _task("incoming-first", 4.0, 30.0)
    incoming_second = _task("incoming-second", 4.0, 20.0)
    rejected = _task("rejected", 4.0, 10.0)
    tasks = (
        victim_low,
        victim_high,
        auto,
        incoming_first,
        incoming_second,
        rejected,
    )
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        0,
        {task.task_id: task for task in tasks},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim_low.task_id, server_id=server.server_id)
    state = allocate_now(state, task_id=victim_high.task_id, server_id=server.server_id)
    times = {task.task_id: 4.0 for task in tasks}
    snapshot = capture_victim_snapshot(
        state, server_id=server.server_id, time_remaining_by_task=times
    )
    policy = KnapsackGreedyPreemptionPolicy(ExactUtilityKnapsackSelector())
    result = policy.run(
        state,
        requesting_task_ids=(
            auto.task_id,
            incoming_first.task_id,
            incoming_second.task_id,
            rejected.task_id,
        ),
        time_remaining_by_task=times,
    )
    return {
        "label": "auxiliary_test_not_paper_result",
        "method_control_flow": policy.name,
        "selector": "exact_utility_auxiliary_not_paper_ga",
        "assumptions": [
            "ASSUMP-004",
            "ASSUMP-005",
            "ASSUMP-006",
            "ASSUMP-010",
        ],
        "victim_snapshot": [
            {
                "task_id": entry.task_id,
                "utility_time_ratio": entry.utility_time_ratio,
                "time_remaining": entry.time_remaining,
            }
            for entry in snapshot
        ],
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
        "accepted_task_ids": list(result.accepted_task_ids),
        "rejected_task_ids": list(result.rejected_task_ids),
        "preempted_task_ids": list(result.preempted_task_ids),
        "final_task_states": {
            task_id: task_state.value
            for task_id, task_state in sorted(result.final_state.task_states.items())
        },
        "residual_before": remaining_resources(state, server.server_id).as_dict(),
        "residual_after": remaining_resources(result.final_state, server.server_id).as_dict(),
    }


def main() -> None:
    output_path = Path("results/raw/stage10c/kg_preemption_example.json")
    result = run_example()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"output_path={output_path}")


if __name__ == "__main__":
    main()
