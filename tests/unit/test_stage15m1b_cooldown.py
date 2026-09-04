from __future__ import annotations

from collections.abc import Sequence

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import PipelineDKPConfig
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.modified_methods.one_auction_cooldown_dkp import (
    OneAuctionCooldownDKPPolicy,
    _maximum_chain_depth,
    assert_cooldown_summary,
    run_cooldown_dkp_round_two_for_server,
)
from edge_reproduction.simulation.accounting import allocate_now, release_now
from edge_reproduction.simulation.state import SimulationState


class SelectOnly:
    def __init__(self, *task_ids: str) -> None:
        self.task_ids = task_ids
        self.calls = 0

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        del capacity, tasks
        self.calls += 1
        return self.task_ids


class ScriptedSelector:
    def __init__(self, selections: Sequence[tuple[str, ...]]) -> None:
        self.selections = tuple(selections)
        self.calls = 0
        self.uniform_calls = 0

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        del capacity, tasks
        selected = self.selections[self.calls]
        self.calls += 1
        return selected

    def choose_uniform(self, values: Sequence[str]) -> str:
        self.uniform_calls += 1
        return values[0]


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 20, utility, ResourceVector(demand, demand, demand, demand))


def make_state(*, current: tuple[Task, ...], returning: tuple[Task, ...]) -> SimulationState:
    tasks = current + returning
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(3, {item.task_id: item for item in tasks}, {server.server_id: server})
    for item in current:
        state = allocate_now(state, task_id=item.task_id, server_id=server.server_id)
    return state


def test_threatened_cooldown_aborts_entire_post_selection_transaction() -> None:
    protected = task("protected", 6.0, 5.0)
    incoming = task("incoming", 6.0, 100.0)
    state = make_state(current=(protected,), returning=(incoming,))
    selector = SelectOnly(incoming.task_id)

    result = run_cooldown_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={protected.task_id: 10.0, incoming.task_id: 5.0},
        selector=selector,
        cooldown_task_ids=(protected.task_id,),
    )

    assert selector.calls == 1
    assert result.transaction_aborted is True
    assert result.threatened_cooldown_task_ids == (protected.task_id,)
    assert result.planned_preempted_task_ids == (protected.task_id,)
    assert result.preempted_task_ids == ()
    assert result.accepted_task_ids == ()
    assert result.rejected_task_ids == (incoming.task_id,)
    assert result.final_state.allocations[protected.task_id].is_active


def test_unthreatened_cooldown_does_not_change_transaction() -> None:
    protected = task("protected", 4.0, 10.0)
    incoming = task("incoming", 4.0, 100.0)
    state = make_state(current=(protected,), returning=(incoming,))

    result = run_cooldown_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={protected.task_id: 10.0, incoming.task_id: 5.0},
        selector=SelectOnly(protected.task_id, incoming.task_id),
        cooldown_task_ids=(protected.task_id,),
    )

    assert result.transaction_aborted is False
    assert result.retained_task_ids == (protected.task_id,)
    assert result.accepted_task_ids == (incoming.task_id,)


def test_abort_distinguishes_protected_and_unrelated_planned_victims() -> None:
    protected = task("protected", 5.0, 4.0)
    unrelated = task("unrelated", 5.0, 5.0)
    incoming = task("incoming", 6.0, 100.0)
    state = make_state(current=(protected, unrelated), returning=(incoming,))

    result = run_cooldown_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={
            protected.task_id: 10.0,
            unrelated.task_id: 10.0,
            incoming.task_id: 5.0,
        },
        selector=SelectOnly(incoming.task_id),
        cooldown_task_ids=(protected.task_id,),
    )

    assert result.transaction_aborted is True
    assert set(result.planned_preempted_task_ids) == {protected.task_id, unrelated.task_id}
    assert result.threatened_cooldown_task_ids == (protected.task_id,)
    assert set(result.retained_task_ids) == {protected.task_id, unrelated.task_id}


def test_preemptive_batch_creates_cooldown_but_nonpreemptive_batch_does_not() -> None:
    current = task("current", 6.0, 20.0)
    incoming = task("incoming", 6.0, 100.0)
    state = make_state(current=(current,), returning=(incoming,))
    selector = ScriptedSelector(((), (incoming.task_id,)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=17), workload_tasks=(current, incoming)
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)

    result = policy.run(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        epoch=3,
    )

    assert result.preempted_task_ids == (current.task_id,)
    assert policy.cooldown_task_ids == frozenset({incoming.task_id})
    assert selector.calls == 2


def test_nonpreemptive_admission_creates_no_cooldown() -> None:
    current = task("current", 2.0, 20.0)
    incoming = task("incoming", 2.0, 100.0)
    state = make_state(current=(current,), returning=(incoming,))
    selector = ScriptedSelector(((), (current.task_id, incoming.task_id)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=18), workload_tasks=(current, incoming)
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)

    result = policy.run(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        epoch=3,
    )

    assert result.accepted_task_ids == (incoming.task_id,)
    assert result.preempted_task_ids == ()
    assert policy.cooldown_task_ids == frozenset()


def test_first_later_auction_aborts_then_consumes_cooldown() -> None:
    current = task("current", 6.0, 20.0)
    protected = task("protected", 6.0, 100.0)
    challenger = task("challenger", 6.0, 200.0)
    state = make_state(current=(current,), returning=(protected, challenger))
    selector = ScriptedSelector(
        ((), (protected.task_id,), (), (challenger.task_id,))
    )
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=19), workload_tasks=(current, protected, challenger)
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)
    first = policy.run(
        state,
        requesting_task_ids=(protected.task_id,),
        time_remaining_by_task={
            current.task_id: 10.0,
            protected.task_id: 8.0,
            challenger.task_id: 7.0,
        },
        epoch=3,
    )
    later = first.final_state.snapshot()
    later.current_slot = 4

    second = policy.run(
        later,
        requesting_task_ids=(challenger.task_id,),
        time_remaining_by_task={protected.task_id: 7.0, challenger.task_id: 6.0},
        epoch=4,
    )

    assert second.preempted_task_ids == ()
    assert second.accepted_task_ids == ()
    assert second.rejected_task_ids == (challenger.task_id,)
    assert policy.cooldown_task_ids == frozenset()
    summary = policy.public_summary(second.final_state)
    assert summary["transactions"]["aborted"] == 1  # type: ignore[index]
    assert summary["cooldown"]["consumed"] == 1  # type: ignore[index]


def test_task_can_be_preempted_after_its_one_auction_cooldown_is_consumed() -> None:
    current = task("current", 6.0, 20.0)
    protected = task("protected", 6.0, 100.0)
    first_challenger = task("first_challenger", 6.0, 200.0)
    second_challenger = task("second_challenger", 6.0, 300.0)
    state = make_state(
        current=(current,), returning=(protected, first_challenger, second_challenger)
    )
    selector = ScriptedSelector(
        (
            (),
            (protected.task_id,),
            (),
            (first_challenger.task_id,),
            (),
            (second_challenger.task_id,),
        )
    )
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=23),
        workload_tasks=(current, protected, first_challenger, second_challenger),
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)
    first = policy.run(
        state,
        requesting_task_ids=(protected.task_id,),
        time_remaining_by_task={item.task_id: 10.0 for item in state.tasks.values()},
        epoch=3,
    )
    second_state = first.final_state.snapshot()
    second_state.current_slot = 4
    second = policy.run(
        second_state,
        requesting_task_ids=(first_challenger.task_id,),
        time_remaining_by_task={
            protected.task_id: 9.0,
            first_challenger.task_id: 9.0,
            second_challenger.task_id: 9.0,
        },
        epoch=4,
    )
    third_state = second.final_state.snapshot()
    third_state.current_slot = 5
    third = policy.run(
        third_state,
        requesting_task_ids=(second_challenger.task_id,),
        time_remaining_by_task={protected.task_id: 8.0, second_challenger.task_id: 8.0},
        epoch=5,
    )

    assert third.preempted_task_ids == (protected.task_id,)
    assert third.accepted_task_ids == (second_challenger.task_id,)


def test_terminal_before_next_auction_expires_cooldown_without_use() -> None:
    current = task("current", 6.0, 20.0)
    protected = task("protected", 6.0, 100.0)
    state = make_state(current=(current,), returning=(protected,))
    selector = ScriptedSelector(((), (protected.task_id,)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=29), workload_tasks=(current, protected)
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)
    result = policy.run(
        state,
        requesting_task_ids=(protected.task_id,),
        time_remaining_by_task={current.task_id: 10.0, protected.task_id: 5.0},
        epoch=3,
    )
    terminal = result.final_state.snapshot()
    terminal.current_slot = 4
    terminal = release_now(terminal, task_id=protected.task_id, terminal_state=TaskState.COMPLETED)

    summary = policy.public_summary(terminal)

    assert summary["cooldown"]["expired_without_evaluation"] == 1  # type: ignore[index]
    assert summary["cooldown"]["terminal_completed"] == 1  # type: ignore[index]


def test_cooldown_summary_contains_only_aggregate_public_fields() -> None:
    current = task("current", 6.0, 20.0)
    incoming = task("incoming", 6.0, 100.0)
    state = make_state(current=(current,), returning=(incoming,))
    selector = ScriptedSelector(((), (incoming.task_id,)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=31), workload_tasks=(current, incoming)
    )
    policy = OneAuctionCooldownDKPPolicy(config, selector)
    result = policy.run(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        epoch=3,
    )
    terminal = result.final_state.snapshot()
    terminal.current_slot = 4
    terminal = release_now(terminal, task_id=incoming.task_id, terminal_state=TaskState.COMPLETED)

    summary = policy.public_summary(terminal)
    encoded = repr(summary)

    assert summary["task_identifiers_recorded"] is False
    assert "incoming" not in encoded
    assert "current" not in encoded
    assert_cooldown_summary(summary)


def test_summary_rejects_incomplete_cooldown_accounting() -> None:
    with pytest.raises(StateValidationError, match="consumed or expire"):
        assert_cooldown_summary(
            {
                "cooldown": {
                    "created": 2,
                    "consumed": 1,
                    "expired_without_evaluation": 0,
                    "consumed_with_abort": 1,
                },
                "transactions": {
                    "suppressed_planned_admission_event_count": 0,
                    "returning_rejected_event_count": 0,
                },
            }
        )


def test_maximum_chain_depth_is_computed_without_public_edges() -> None:
    from edge_reproduction.modified_methods.one_auction_cooldown_dkp import PreemptionBatch

    batches = (
        PreemptionBatch(1, "server", ("a",), ("b",)),
        PreemptionBatch(2, "server", ("c",), ("a",)),
    )
    assert _maximum_chain_depth(batches) == 2
