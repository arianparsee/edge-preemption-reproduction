import pytest

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.state import SimulationState


def make_task(task_id: str = "job-1") -> Task:
    return Task(task_id, 0, 3, 10.0, ResourceVector(2.0, 3.0, 1.0, 1.0))


def make_server(server_id: str = "server-1") -> Server:
    return Server(server_id, ResourceVector(10.0, 10.0, 10.0, 10.0))


def test_state_initializes_every_task_as_created() -> None:
    task = make_task()
    server = make_server()
    state = SimulationState(0, {task.task_id: task}, {server.server_id: server})

    assert state.task_states == {"job-1": TaskState.CREATED}


def test_state_copies_input_registries() -> None:
    task = make_task()
    server = make_server()
    tasks = {task.task_id: task}
    state = SimulationState(0, tasks, {server.server_id: server})
    tasks.clear()

    assert set(state.tasks) == {"job-1"}


def test_state_rejects_mapping_key_mismatch() -> None:
    with pytest.raises(StateValidationError, match="task mapping key"):
        SimulationState(0, {"wrong": make_task()}, {"server-1": make_server()})


def test_state_rejects_partial_task_state_registry() -> None:
    first = make_task("job-1")
    second = make_task("job-2")
    with pytest.raises(StateValidationError, match="exactly one"):
        SimulationState(
            0,
            {first.task_id: first, second.task_id: second},
            {"server-1": make_server()},
            task_states={"job-1": TaskState.CREATED},
        )


def test_state_rejects_allocation_to_unknown_server() -> None:
    task = make_task()
    allocation = Allocation(task.task_id, "missing", task.demand, start_slot=0)
    with pytest.raises(StateValidationError, match="unknown server"):
        SimulationState(
            0,
            {task.task_id: task},
            {"server-1": make_server()},
            allocations={task.task_id: allocation},
        )


def test_active_allocations_are_filtered_by_server_and_end_slot() -> None:
    first = make_task("job-1")
    second = make_task("job-2")
    server = make_server()
    active = Allocation(first.task_id, server.server_id, first.demand, start_slot=0)
    ended = Allocation(second.task_id, server.server_id, second.demand, 0, end_slot=1)
    state = SimulationState(
        1,
        {first.task_id: first, second.task_id: second},
        {server.server_id: server},
        allocations={first.task_id: active, second.task_id: ended},
    )

    assert state.active_allocations_for_server(server.server_id) == (active,)


def test_snapshot_has_independent_mutable_registries() -> None:
    task = make_task()
    server = make_server()
    state = SimulationState(0, {task.task_id: task}, {server.server_id: server})
    snapshot = state.snapshot()
    snapshot.task_states[task.task_id] = TaskState.WAITING_FOR_BID

    assert state.task_states[task.task_id] is TaskState.CREATED
    assert snapshot.task_states[task.task_id] is TaskState.WAITING_FOR_BID
