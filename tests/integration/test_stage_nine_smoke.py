import pytest

from edge_reproduction.models.enums import (
    AssignmentFlowSemantics,
    DeadlineBoundary,
    EventType,
    TaskState,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.engine import SimulationRun, run_scripted_simulation
from edge_reproduction.simulation.invariants import remaining_resources
from edge_reproduction.simulation.scenarios import stage_nine_smoke_scenario


def run_smoke() -> SimulationRun:
    state, commands, config = stage_nine_smoke_scenario()
    return run_scripted_simulation(
        state,
        commands,
        config,
        deadline_boundary=DeadlineBoundary.INCLUSIVE,
        assignment_semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )


def test_manual_task_outcomes_and_utility_match_program() -> None:
    run = run_smoke()

    assert run.final_state.task_states == {
        "task-a": TaskState.PREEMPTED,
        "task-b": TaskState.REJECTED,
        "task-c": TaskState.COMPLETED,
        "task-d": TaskState.EXPIRED,
    }
    assert run.experiment_result.completed_task_ids == ("task-c",)
    assert run.experiment_result.rejected_task_ids == ("task-b",)
    assert run.experiment_result.ever_preempted_task_ids == ("task-a",)
    assert run.expired_task_ids == ("task-d",)
    assert run.experiment_result.completed_utility == 30.0
    assert run.experiment_result.event_count == 11


def test_manual_resource_ledger_matches_every_decision() -> None:
    run = run_smoke()
    events = run.events

    assert events[3].resources_before == ResourceVector(10.0, 10.0, 10.0, 10.0)
    assert events[3].resources_after == ResourceVector(4.0, 6.0, 8.0, 8.0)
    assert events[4].resources_after == ResourceVector.zero()
    assert events[7].event_type is EventType.PREEMPTED
    assert events[7].resources_after == ResourceVector(10.0, 10.0, 10.0, 10.0)
    assert events[8].event_type is EventType.ACCEPTED
    assert events[8].resources_after == ResourceVector(3.0, 5.0, 8.0, 8.0)
    assert events[9].event_type is EventType.EXPIRED
    assert events[9].resources_after == ResourceVector(4.0, 4.0, 4.0, 4.0)
    assert events[10].event_type is EventType.COMPLETED
    assert events[10].earned_utility == 30.0
    assert events[10].resources_after == ResourceVector(10.0, 10.0, 10.0, 10.0)


def test_final_resources_are_fully_released() -> None:
    run = run_smoke()

    assert remaining_resources(run.final_state, "server-1") == ResourceVector(
        10.0, 10.0, 10.0, 10.0
    )
    assert remaining_resources(run.final_state, "server-2") == ResourceVector(4.0, 4.0, 4.0, 4.0)


def test_task_c_completion_at_exact_deadline_uses_approved_inclusive_boundary() -> None:
    run = run_smoke()
    completed = next(event for event in run.events if event.event_type is EventType.COMPLETED)

    assert completed.task_id == "task-c"
    assert completed.time == 3
    assert run.final_state.tasks["task-c"].absolute_deadline_slot == 3


def test_engine_rejects_unapproved_deadline_semantics() -> None:
    state, commands, config = stage_nine_smoke_scenario()

    with pytest.raises(ValueError, match="ASSUMP-001"):
        run_scripted_simulation(
            state,
            commands,
            config,
            deadline_boundary=DeadlineBoundary.EXCLUSIVE,
            assignment_semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
        )
