from types import SimpleNamespace
from typing import Any, cast

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import DKPScoreEntry
from edge_reproduction.diagnostics.stage15k2_preemption import (
    Stage15K2PreemptionObserver,
    terminal_preemption_summary,
)
from edge_reproduction.models.enums import EventType
from edge_reproduction.simulation.state import SimulationState


class Delegate:
    name = "pipeline_double_knapsack_preemption"

    def __init__(self, result: object) -> None:
        self.result = result
        self.calls = 0

    def run(self, state: object, **kwargs: object) -> object:
        self.calls += 1
        return self.result


def _entry(task_id: str, current: bool, ratio: float) -> DKPScoreEntry:
    return DKPScoreEntry(task_id, current, True, 1.0, ratio, 1000.0 + ratio)


def test_observer_returns_exact_delegate_result_and_aggregates() -> None:
    result = SimpleNamespace(
        accepted_task_ids=("new",),
        preempted_task_ids=("old",),
        round_two_scores_by_server={"s": (_entry("new", False, 2.1), _entry("old", True, 2.0))},
    )
    delegate = Delegate(result)
    observer = Stage15K2PreemptionObserver(delegate)
    state = SimpleNamespace(
        tasks={"new": SimpleNamespace(utility=12.0), "old": SimpleNamespace(utility=10.0)}
    )
    returned = observer.run(
        cast(SimulationState, state),
        requesting_task_ids=("new",),
        time_remaining_by_task={},
        epoch=3,
    )
    assert returned is result
    assert delegate.calls == 1
    summary = cast(dict[str, Any], observer.summary())
    assert summary["counts"]["positive_net_batches"] == 1
    assert summary["counts"]["five_percent_pass"] == 1
    assert summary["net_utility"] == 2.0
    assert summary["random_draws_added"] == 0


def test_observer_records_negative_batch_without_ids() -> None:
    result = SimpleNamespace(
        accepted_task_ids=("new",),
        preempted_task_ids=("old",),
        round_two_scores_by_server={"s": (_entry("new", False, 1.0), _entry("old", True, 2.0))},
    )
    observer = Stage15K2PreemptionObserver(Delegate(result))
    state = SimpleNamespace(
        tasks={"new": SimpleNamespace(utility=5.0), "old": SimpleNamespace(utility=9.0)}
    )
    observer.run(
        cast(SimulationState, state),
        requesting_task_ids=("new",),
        time_remaining_by_task={},
    )
    summary = cast(dict[str, Any], observer.summary())
    assert summary["counts"]["negative_net_batches"] == 1
    assert summary["counts"]["five_percent_fail"] == 1
    assert summary["task_identifiers_recorded"] is False


def test_observer_rejects_nonstandard_tolerance() -> None:
    with pytest.raises(ValueError, match="tolerance"):
        Stage15K2PreemptionObserver(Delegate(object()), tolerance=1e-8)


def test_retention_result_has_zero_preemption_diagnostics() -> None:
    result = SimpleNamespace(accepted_task_ids=(), preempted_task_ids=())
    observer = Stage15K2PreemptionObserver(Delegate(result))
    assert (
        observer.run(
            cast(SimulationState, SimpleNamespace(tasks={})),
            requesting_task_ids=(),
            time_remaining_by_task={},
        )
        is result
    )
    assert observer.summary()["counts"] == {}


def test_terminal_preemption_summary_is_aggregate_only() -> None:
    events = [
        SimpleNamespace(task_id="a", event_type=EventType.ACCEPTED),
        SimpleNamespace(task_id="a", event_type=EventType.PREEMPTED),
        SimpleNamespace(task_id="b", event_type=EventType.ACCEPTED),
        SimpleNamespace(task_id="b", event_type=EventType.COMPLETED),
    ]
    summary = terminal_preemption_summary(events)
    assert summary == {
        "unique_admitted_tasks": 2,
        "admissions_eventually_preempted": 1,
        "completed_admissions": 1,
        "completion_per_admission": 0.5,
        "task_identifiers_recorded": False,
    }
