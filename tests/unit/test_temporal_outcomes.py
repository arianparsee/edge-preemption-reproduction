import pytest

from edge_reproduction.evaluation.temporal_outcomes import aggregate_temporal_outcome
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.state import SimulationState


def make_state() -> SimulationState:
    tasks = {
        task_id: Task(task_id, 0, 4, utility, ResourceVector(1.0, 1.0, 1.0, 1.0), 1.0)
        for task_id, utility in (("completed", 5.0), ("expired", 7.0), ("preempted", 11.0))
    }
    return SimulationState(
        4,
        tasks,
        {"server": Server("server", ResourceVector(3.0, 3.0, 3.0, 3.0))},
        {
            "completed": TaskState.COMPLETED,
            "expired": TaskState.EXPIRED,
            "preempted": TaskState.PREEMPTED,
        },
    )


def test_assump_040_partition_and_preemption_overlay() -> None:
    outcome = aggregate_temporal_outcome(
        make_state(),
        ever_preempted_task_ids={"preempted"},
        raw_auction_rejection_count=4,
    )
    assert outcome.completed_task_ids == ("completed",)
    assert outcome.rejected_task_ids == ("expired", "preempted")
    assert outcome.ever_preempted_task_ids == ("preempted",)
    assert outcome.completed_utility == 5.0
    assert outcome.rejected_utility == 18.0
    assert outcome.ever_preempted_utility == 11.0
    assert outcome.raw_auction_rejection_count == 4


def test_outcome_fails_with_nonterminal_task() -> None:
    state = make_state()
    state.task_states["expired"] = TaskState.WAITING_RETRY
    with pytest.raises(StateValidationError, match="nonterminal"):
        aggregate_temporal_outcome(
            state,
            ever_preempted_task_ids={"preempted"},
            raw_auction_rejection_count=0,
        )


def test_completed_task_cannot_be_in_preemption_overlay() -> None:
    with pytest.raises(StateValidationError, match="subset"):
        aggregate_temporal_outcome(
            make_state(),
            ever_preempted_task_ids={"completed"},
            raw_auction_rejection_count=0,
        )
