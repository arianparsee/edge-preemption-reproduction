"""Knapsack selector contract plus a small exact auxiliary implementation."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from typing import Protocol

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


class KnapsackSelector(Protocol):
    """Dependency boundary for the paper's unresolved Round-1 GA knapsack."""

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        """Return identifiers of one jointly feasible selected subset."""


class ExactUtilityKnapsackSelector:
    """Exhaustive utility-maximizing selector for hand-sized auxiliary tests.

    This is an ``[ابزار کمکی]`` and is not represented as the paper's pyeasyga
    implementation. Equal best subsets fail fast because their tie-breaking is
    not reported.
    """

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        if not isinstance(capacity, ResourceVector):
            raise TypeError("capacity must be a ResourceVector")
        candidates = tuple(tasks)
        if any(not isinstance(task, Task) for task in candidates):
            raise TypeError("tasks must contain only Task instances")
        task_ids = tuple(task.task_id for task in candidates)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("tasks must have unique identifiers")

        best_utility = float("-inf")
        best_subsets: list[tuple[str, ...]] = []
        for subset_size in range(len(candidates) + 1):
            for subset in combinations(candidates, subset_size):
                demand = ResourceVector.zero()
                for task in subset:
                    demand = demand + task.demand
                if not demand.fits_within(capacity):
                    continue
                utility = float(sum(task.utility for task in subset))
                selected = tuple(task.task_id for task in subset)
                if utility > best_utility:
                    best_utility = utility
                    best_subsets = [selected]
                elif utility == best_utility:
                    best_subsets.append(selected)
        if len(best_subsets) != 1:
            raise UnresolvedDecisionError(
                "equal-utility optimal knapsack subsets require an unreported tie-break"
            )
        return best_subsets[0]
