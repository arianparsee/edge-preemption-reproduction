"""Run the deterministic auxiliary example for approved Stage-10A decisions."""

from __future__ import annotations

import json
from pathlib import Path

from edge_reproduction.algorithms.feasibility import meets_preemption_threshold
from edge_reproduction.algorithms.knapsack_greedy import preempt_first_eligible_and_admit
from edge_reproduction.algorithms.pricing import (
    algorithm_one_congestion,
    algorithm_one_congestion_factor,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.state import SimulationState


def run_example() -> dict[str, object]:
    """Return an auditable hand-sized execution of ASSUMP-003 to ASSUMP-006."""

    victim = Task("victim", 0, 5, 5.0, ResourceVector(6.0, 4.0, 2.0, 2.0))
    incoming = Task("incoming", 1, 2, 30.0, ResourceVector(7.0, 5.0, 2.0, 2.0))
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        1,
        {victim.task_id: victim, incoming.task_id: incoming},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim.task_id, server_id=server.server_id)
    residual_before = remaining_resources(state, server.server_id)
    congestion = algorithm_one_congestion(incoming.demand, residual_before, server.capacity)
    if congestion is None:  # pragma: no cover - fixed fixture is feasible on an empty server
        raise RuntimeError("example task unexpectedly entered the impossible branch")

    threshold_met = meets_preemption_threshold(
        incoming_utility=incoming.utility,
        incoming_time=incoming.deadline_slots,
        current_utility=victim.utility,
        current_time_remaining=4.0,
    )
    updated, selected_victim = preempt_first_eligible_and_admit(
        state,
        incoming_task=incoming,
        server_id=server.server_id,
        victim_time_remaining={victim.task_id: 4.0},
    )
    return {
        "label": "auxiliary_test_not_paper_result",
        "assumptions": ["ASSUMP-003", "ASSUMP-004", "ASSUMP-005", "ASSUMP-006"],
        "congestion": congestion,
        "congestion_factor": algorithm_one_congestion_factor(congestion),
        "new_ratio": incoming.utility / incoming.deadline_slots,
        "victim_ratio": victim.utility / 4.0,
        "threshold_met": threshold_met,
        "selected_victim": selected_victim,
        "final_task_states": {
            task_id: task_state.value for task_id, task_state in sorted(updated.task_states.items())
        },
        "residual_before": residual_before.as_dict(),
        "residual_after": remaining_resources(updated, server.server_id).as_dict(),
    }


def main() -> None:
    output_path = Path("results/raw/stage10a/approved_primitives_example.json")
    result = run_example()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"output_path={output_path}")


if __name__ == "__main__":
    main()
