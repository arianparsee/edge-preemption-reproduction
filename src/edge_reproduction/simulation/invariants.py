"""Resource and state invariants required after allocation or preemption."""

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.state import SimulationState

ACTIVE_ALLOCATION_STATES = frozenset(
    {
        TaskState.ACCEPTED,
        TaskState.BATCH_UPLOADING,
        TaskState.BATCH_PROCESSING,
        TaskState.BATCH_DOWNLOADING,
        TaskState.PIPELINE_ACTIVE,
    }
)

TERMINAL_STATES = frozenset({TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED})


def used_resources(state: SimulationState, server_id: str) -> ResourceVector:
    """Sum resources of active allocations on one known server."""

    total = ResourceVector.zero()
    for allocation in state.active_allocations_for_server(server_id):
        total = total + allocation.resources
    return total


def remaining_resources(state: SimulationState, server_id: str) -> ResourceVector:
    """Return total capacity minus active reservations, rejecting underflow."""

    try:
        server = state.servers[server_id]
    except KeyError as error:
        raise KeyError(f"unknown server_id: {server_id}") from error
    return server.capacity.subtract(used_resources(state, server_id))


def has_sufficient_resources(
    state: SimulationState, server_id: str, demand: ResourceVector
) -> bool:
    """Check component-wise fit against current residual capacity."""

    if not isinstance(demand, ResourceVector):
        raise TypeError("demand must be a ResourceVector")
    return demand.fits_within(remaining_resources(state, server_id))


def check_server_capacity_invariant(state: SimulationState) -> bool:
    """Return false if any active use exceeds any server capacity component."""

    try:
        for server_id in state.servers:
            remaining_resources(state, server_id)
    except ValueError:
        return False
    return True


def check_single_server_assignment_invariant(state: SimulationState) -> bool:
    """Validate the one-allocation-per-task representation of equation (19)."""

    return all(key == allocation.task_id for key, allocation in state.allocations.items())


def check_task_allocation_state_invariant(state: SimulationState) -> bool:
    """Check that active reservations and task lifecycle labels agree."""

    for task_id, task_state in state.task_states.items():
        allocation = state.allocations.get(task_id)
        active = allocation is not None and allocation.is_active
        if active and task_state not in ACTIVE_ALLOCATION_STATES:
            return False
        if task_state in TERMINAL_STATES and active:
            return False
    return True


def validate_state_invariants(state: SimulationState) -> None:
    """Raise a precise failure after any state-changing transaction."""

    if not check_server_capacity_invariant(state):
        raise StateValidationError("active resource use exceeds server capacity")
    if not check_single_server_assignment_invariant(state):
        raise StateValidationError("a task has an inconsistent server assignment")
    if not check_task_allocation_state_invariant(state):
        raise StateValidationError("task state and active allocation are inconsistent")
