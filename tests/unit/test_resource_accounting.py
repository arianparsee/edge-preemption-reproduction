import pytest

from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import (
    allocate_now,
    preempt_and_allocate_now,
    release_now,
)
from edge_reproduction.simulation.invariants import (
    check_server_capacity_invariant,
    check_task_allocation_state_invariant,
    has_sufficient_resources,
    remaining_resources,
    used_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


def task(task_id: str, storage: float, utility: float = 10.0) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(storage, 1.0, 1.0, 1.0))


def base_state() -> SimulationState:
    first = task("job-1", 4.0)
    second = task("job-2", 7.0)
    server = Server("server-1", ResourceVector(10.0, 10.0, 10.0, 10.0))
    return SimulationState(
        current_slot=2,
        tasks={first.task_id: first, second.task_id: second},
        servers={server.server_id: server},
    )


def test_used_remaining_and_sufficiency_are_component_wise() -> None:
    state = allocate_now(base_state(), task_id="job-1", server_id="server-1")

    assert used_resources(state, "server-1") == ResourceVector(4.0, 1.0, 1.0, 1.0)
    assert remaining_resources(state, "server-1") == ResourceVector(6.0, 9.0, 9.0, 9.0)
    assert not has_sufficient_resources(state, "server-1", state.tasks["job-2"].demand)


def test_allocate_is_transactional_and_sets_accepted_state() -> None:
    original = base_state()
    updated = allocate_now(original, task_id="job-1", server_id="server-1")

    assert "job-1" not in original.allocations
    assert updated.allocations["job-1"].is_active
    assert updated.task_states["job-1"] is TaskState.ACCEPTED


def test_allocation_rejects_insufficient_resources_without_mutation() -> None:
    original = allocate_now(base_state(), task_id="job-1", server_id="server-1")

    with pytest.raises(StateValidationError, match="insufficient"):
        allocate_now(original, task_id="job-2", server_id="server-1")
    assert set(original.allocations) == {"job-1"}


def test_release_frees_resources_and_sets_terminal_state() -> None:
    allocated = allocate_now(base_state(), task_id="job-1", server_id="server-1")
    released = release_now(allocated, task_id="job-1", terminal_state=TaskState.COMPLETED)

    assert remaining_resources(released, "server-1") == released.servers["server-1"].capacity
    assert released.task_states["job-1"] is TaskState.COMPLETED
    assert not released.allocations["job-1"].is_active


def test_assump_038_a_expiration_atomically_frees_all_resources() -> None:
    allocated = allocate_now(base_state(), task_id="job-1", server_id="server-1")
    released = release_now(allocated, task_id="job-1", terminal_state=TaskState.EXPIRED)

    assert released.task_states["job-1"] is TaskState.EXPIRED
    assert not released.allocations["job-1"].is_active
    assert remaining_resources(released, "server-1") == released.servers["server-1"].capacity


def test_reallocation_after_ended_record_is_explicitly_unresolved() -> None:
    allocated = allocate_now(base_state(), task_id="job-1", server_id="server-1")
    released = release_now(allocated, task_id="job-1", terminal_state=TaskState.PREEMPTED)

    with pytest.raises(UnresolvedDecisionError, match="retry semantics"):
        allocate_now(released, task_id="job-1", server_id="server-1")


def test_preemption_transaction_releases_victim_and_admits_incoming() -> None:
    allocated = allocate_now(base_state(), task_id="job-1", server_id="server-1")
    updated = preempt_and_allocate_now(
        allocated,
        incoming_task_id="job-2",
        server_id="server-1",
        victim_task_ids=("job-1",),
    )

    assert updated.task_states["job-1"] is TaskState.PREEMPTED
    assert not updated.allocations["job-1"].is_active
    assert updated.task_states["job-2"] is TaskState.ACCEPTED
    assert updated.allocations["job-2"].is_active


def test_capacity_invariant_detects_invalid_external_state() -> None:
    state = base_state()
    first = state.tasks["job-1"]
    state.allocations[first.task_id] = Allocation(
        first.task_id,
        "server-1",
        ResourceVector(11.0, 1.0, 1.0, 1.0),
        start_slot=0,
    )
    state.task_states[first.task_id] = TaskState.ACCEPTED

    assert not check_server_capacity_invariant(state)
    with pytest.raises(StateValidationError, match="exceeds"):
        validate_state_invariants(state)


def test_terminal_task_cannot_hold_active_resources() -> None:
    state = allocate_now(base_state(), task_id="job-1", server_id="server-1")
    state.task_states["job-1"] = TaskState.COMPLETED

    assert not check_task_allocation_state_invariant(state)
