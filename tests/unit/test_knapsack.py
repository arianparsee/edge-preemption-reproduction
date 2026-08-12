import pytest

from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def test_exact_auxiliary_selector_returns_unique_utility_maximum() -> None:
    tasks = (task("a", 6.0, 9.0), task("b", 4.0, 5.0), task("c", 7.0, 12.0))

    selected = ExactUtilityKnapsackSelector().select(
        capacity=ResourceVector(10.0, 10.0, 10.0, 10.0), tasks=tasks
    )

    assert selected == ("a", "b")


def test_exact_auxiliary_selector_refuses_equal_optimal_subsets() -> None:
    tasks = (task("a", 1.0, 1.0), task("b", 1.0, 1.0))

    with pytest.raises(UnresolvedDecisionError, match="tie-break"):
        ExactUtilityKnapsackSelector().select(
            capacity=ResourceVector(1.0, 1.0, 1.0, 1.0), tasks=tasks
        )
