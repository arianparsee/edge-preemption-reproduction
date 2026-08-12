"""ASSUMP-040 terminal outcome aggregation for temporal PIPE-NORMAL runs."""

from __future__ import annotations

from dataclasses import dataclass

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class TemporalOutcome:
    """Completed/rejected partition plus the deduplicated preemption overlay."""

    completed_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    ever_preempted_task_ids: tuple[str, ...]
    completed_utility: float
    rejected_utility: float
    ever_preempted_utility: float
    completed_jobs: int
    rejected_jobs: int
    ever_preempted_jobs: int
    raw_auction_rejection_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "completed_task_ids": list(self.completed_task_ids),
            "rejected_task_ids": list(self.rejected_task_ids),
            "ever_preempted_task_ids": list(self.ever_preempted_task_ids),
            "completed_utility": self.completed_utility,
            "rejected_utility": self.rejected_utility,
            "ever_preempted_utility": self.ever_preempted_utility,
            "completed_jobs": self.completed_jobs,
            "rejected_jobs": self.rejected_jobs,
            "ever_preempted_jobs": self.ever_preempted_jobs,
            "raw_auction_rejection_count": self.raw_auction_rejection_count,
        }


def aggregate_temporal_outcome(
    state: SimulationState,
    *,
    ever_preempted_task_ids: set[str] | frozenset[str],
    raw_auction_rejection_count: int,
) -> TemporalOutcome:
    """Aggregate and validate the exact ASSUMP-040 task-ID invariants."""

    if raw_auction_rejection_count < 0:
        raise ValueError("raw_auction_rejection_count must be non-negative")
    all_ids = set(state.tasks)
    completed = {
        task_id
        for task_id, status in state.task_states.items()
        if status is TaskState.COMPLETED
    }
    nonterminal = {
        task_id
        for task_id, status in state.task_states.items()
        if status not in {TaskState.COMPLETED, TaskState.EXPIRED, TaskState.PREEMPTED}
    }
    if nonterminal:
        raise StateValidationError(
            f"temporal outcome contains nonterminal tasks: {sorted(nonterminal)}"
        )
    rejected = all_ids - completed
    preempted = set(ever_preempted_task_ids)
    if completed & rejected or completed | rejected != all_ids:
        raise StateValidationError("completed/rejected outcome partition is invalid")
    if not preempted <= rejected:
        raise StateValidationError("ever-preempted tasks must be a subset of rejected tasks")

    completed_ids = tuple(sorted(completed))
    rejected_ids = tuple(sorted(rejected))
    preempted_ids = tuple(sorted(preempted))
    return TemporalOutcome(
        completed_ids,
        rejected_ids,
        preempted_ids,
        float(sum(state.tasks[task_id].utility for task_id in completed_ids)),
        float(sum(state.tasks[task_id].utility for task_id in rejected_ids)),
        float(sum(state.tasks[task_id].utility for task_id in preempted_ids)),
        len(completed_ids),
        len(rejected_ids),
        len(preempted_ids),
        raw_auction_rejection_count,
    )
