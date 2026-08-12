import pytest

from edge_reproduction.evaluation.utility import (
    all_or_nothing_utility,
    total_served_utility,
    validate_binary,
)
from edge_reproduction.models.enums import DeadlineBoundary
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.time import elapsed_slots, meets_deadline


def make_task(task_id: str = "job-1", utility: float = 10.0) -> Task:
    return Task(task_id, 2, 3, utility, ResourceVector(1.0, 1.0, 0.0, 0.0))


def test_deadline_boundary_must_be_explicit_at_exact_endpoint() -> None:
    task = make_task()

    assert meets_deadline(task, 5, boundary=DeadlineBoundary.INCLUSIVE)
    assert not meets_deadline(task, 5, boundary=DeadlineBoundary.EXCLUSIVE)


def test_completion_after_deadline_fails_under_both_boundaries() -> None:
    task = make_task()

    assert not meets_deadline(task, 6, boundary=DeadlineBoundary.INCLUSIVE)
    assert not meets_deadline(task, 6, boundary=DeadlineBoundary.EXCLUSIVE)


def test_elapsed_slots_exposes_endpoint_interpretation() -> None:
    assert elapsed_slots(2, 5, boundary=DeadlineBoundary.INCLUSIVE) == 4
    assert elapsed_slots(2, 5, boundary=DeadlineBoundary.EXCLUSIVE) == 3


def test_all_or_nothing_utility_matches_objective_term() -> None:
    task = make_task(utility=12.0)

    assert (
        all_or_nothing_utility(task, assignment=1, completion_indicator=1, deadline_met=True)
        == 12.0
    )
    assert (
        all_or_nothing_utility(task, assignment=1, completion_indicator=0, deadline_met=True) == 0.0
    )
    assert (
        all_or_nothing_utility(task, assignment=0, completion_indicator=1, deadline_met=True) == 0.0
    )
    assert (
        all_or_nothing_utility(task, assignment=1, completion_indicator=1, deadline_met=False)
        == 0.0
    )


@pytest.mark.parametrize("invalid", [-1, 2, 0.5, True])
def test_binary_domain_rejects_invalid_values(invalid: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        validate_binary("x", invalid)  # type: ignore[arg-type]


def test_total_served_utility_sums_tasks() -> None:
    first = make_task("job-1", 10.0)
    second = make_task("job-2", 20.0)

    total = total_served_utility(
        (first, second),
        assignment_by_task={"job-1": 1, "job-2": 1},
        completion_by_task={"job-1": 1, "job-2": 0},
        deadline_met_by_task={"job-1": True, "job-2": True},
    )

    assert total == 10.0
