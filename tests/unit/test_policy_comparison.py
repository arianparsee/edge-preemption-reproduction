from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pytest

from edge_reproduction.evaluation.policy_comparison import (
    PolicyComparisonRecord,
    PolicyRunSpec,
    run_policy_comparison,
)
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True)
class FakeResult:
    final_state: SimulationState
    accepted_task_ids: tuple[str, ...] = ()
    rejected_task_ids: tuple[str, ...] = ()


class MutatingPolicy:
    name = "mutating"

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> FakeResult:
        del requesting_task_ids, time_remaining_by_task, epoch
        state.current_slot += 1
        return FakeResult(state)


def empty_state() -> SimulationState:
    server = Server("server", ResourceVector(1.0, 1.0, 1.0, 1.0))
    return SimulationState(0, {}, {server.server_id: server})


def test_record_serialization_marks_auxiliary_metric_and_enums() -> None:
    record = PolicyComparisonRecord(
        method="example",
        accepted_task_ids=("task",),
        rejected_task_ids=(),
        retained_task_ids=(),
        preempted_task_ids=(),
        active_task_ids=("task",),
        active_utility_after_auction=2.0,
        residual_by_server={"server": ResourceVector.zero()},
        final_task_states={"task": TaskState.ACCEPTED},
        metadata={"role": "auxiliary"},
    )

    serialized = record.as_dict()

    assert serialized["metric_warning"] == (
        "active_utility_after_auction_is_not_completed_paper_utility"
    )
    assert serialized["final_task_states"] == {"task": "accepted"}
    assert serialized["residual_by_server"] == {
        "server": {"storage": 0.0, "computation": 0.0, "upload": 0.0, "download": 0.0}
    }


def test_comparison_rejects_policy_that_mutates_shared_input() -> None:
    state = empty_state()

    with pytest.raises(StateValidationError, match="mutated the shared input"):
        run_policy_comparison(
            state,
            requesting_task_ids=(),
            time_remaining_by_task={},
            specs=(PolicyRunSpec(MutatingPolicy()),),
        )


def test_comparison_requires_at_least_one_policy() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        run_policy_comparison(
            empty_state(),
            requesting_task_ids=(),
            time_remaining_by_task={},
            specs=(),
        )


def test_policy_run_spec_rejects_nonpolicy_object() -> None:
    with pytest.raises(TypeError, match="must satisfy AllocationPolicy"):
        PolicyRunSpec(object())  # type: ignore[arg-type]
