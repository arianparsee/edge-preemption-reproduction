"""Integration test for the approved Stage-10A KnapsackGreedy primitives."""

from edge_reproduction.algorithms.knapsack_greedy import preempt_first_eligible_and_admit
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import (
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


def test_approved_single_victim_flow_preserves_full_state_invariants() -> None:
    victim = Task("victim", 0, 5, 5.0, ResourceVector(6.0, 4.0, 2.0, 2.0))
    incoming = Task("incoming", 1, 2, 30.0, ResourceVector(7.0, 5.0, 2.0, 2.0))
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        1,
        {victim.task_id: victim, incoming.task_id: incoming},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=victim.task_id, server_id=server.server_id)

    updated, victim_id = preempt_first_eligible_and_admit(
        state,
        incoming_task=incoming,
        server_id=server.server_id,
        victim_time_remaining={victim.task_id: 4.0},
    )

    validate_state_invariants(updated)
    assert victim_id == victim.task_id
    assert updated.task_states[victim.task_id] is TaskState.PREEMPTED
    assert updated.task_states[incoming.task_id] is TaskState.ACCEPTED
    assert remaining_resources(updated, server.server_id) == ResourceVector(3.0, 5.0, 8.0, 8.0)
