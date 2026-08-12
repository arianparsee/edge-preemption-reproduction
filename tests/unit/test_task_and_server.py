import math

import pytest

from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task


def task_demand() -> ResourceVector:
    return ResourceVector(storage=20.0, computation=10.0, upload=4.0, download=3.0)


def test_task_maps_relative_deadline_without_boundary_assumption() -> None:
    task = Task(
        task_id="job-1",
        arrival_slot=3,
        deadline_slots=10,
        utility=60.0,
        demand=task_demand(),
        output_size=None,
    )

    assert task.absolute_deadline_slot == 13
    assert task.output_size is None


def test_task_accepts_negative_finite_utility_without_inventing_domain() -> None:
    task = Task("job-1", 0, 1, -1.0, task_demand())

    assert task.utility == -1.0


@pytest.mark.parametrize("utility", [math.inf, -math.inf, math.nan])
def test_task_rejects_non_finite_utility(utility: float) -> None:
    with pytest.raises(ValueError):
        Task("job-1", 0, 1, utility, task_demand())


@pytest.mark.parametrize(
    ("arrival", "deadline", "error"),
    [(-1, 1, ValueError), (0, 0, ValueError), (True, 1, TypeError)],
)
def test_task_rejects_invalid_time_fields(
    arrival: int, deadline: int, error: type[Exception]
) -> None:
    with pytest.raises(error):
        Task("job-1", arrival, deadline, 1.0, task_demand())


def test_task_requires_positive_storage_and_computation_totals() -> None:
    with pytest.raises(ValueError, match="storage"):
        Task("job-1", 0, 1, 1.0, ResourceVector(0.0, 1.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="computation"):
        Task("job-1", 0, 1, 1.0, ResourceVector(1.0, 0.0, 0.0, 0.0))


@pytest.mark.parametrize("output_size", [0.0, -1.0, math.nan])
def test_task_rejects_invalid_known_output_size(output_size: float) -> None:
    with pytest.raises(ValueError):
        Task("job-1", 0, 1, 1.0, task_demand(), output_size)


def test_zero_capacity_server_is_representable() -> None:
    server = Server("server-1", ResourceVector.zero())

    assert server.capacity.is_zero()


def test_identifiers_must_be_trimmed_and_nonempty() -> None:
    with pytest.raises(ValueError):
        Server(" server-1 ", ResourceVector.zero())
    with pytest.raises(ValueError):
        Task("", 0, 1, 1.0, task_demand())
