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
from edge_reproduction.modified_methods.no_cascading_dkp import (
    NoCascadingDKPPolicy,
    assert_no_cascading_summary,
    run_guarded_dkp_round_two_for_server,
    validate_utility_conservation,
)
from edge_reproduction.simulation.accounting import allocate_now, release_now
from edge_reproduction.simulation.invariants import remaining_resources
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

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        del capacity, tasks
        result = self.selections[self.calls]
        self.calls += 1
        return result

    def choose_uniform(self, values: Sequence[str]) -> str:
        return values[0]


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 20, utility, ResourceVector(demand, demand, demand, demand))


def state_with_active(*, current: tuple[Task, ...], returning: tuple[Task, ...]) -> SimulationState:
    tasks = current + returning
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(3, {item.task_id: item for item in tasks}, {server.server_id: server})
    for item in current:
        state = allocate_now(state, task_id=item.task_id, server_id=server.server_id)
    return state


def test_protected_allocation_is_pinned_and_never_becomes_actual_victim() -> None:
    protected = task("protected", 6.0, 2.0)
    incoming = task("incoming", 6.0, 100.0)
    state = state_with_active(current=(protected,), returning=(incoming,))
    selector = SelectOnly(incoming.task_id)

    result = run_guarded_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={protected.task_id: 10.0, incoming.task_id: 5.0},
        selector=selector,
        protected_task_ids=frozenset({protected.task_id}),
    )

    assert selector.calls == 1
    assert result.reference_preempted_task_ids == (protected.task_id,)
    assert result.preempted_task_ids == ()
    assert result.retained_task_ids == (protected.task_id,)
    assert result.rejected_task_ids == (incoming.task_id,)
    assert result.final_state.allocations[protected.task_id].is_active


def test_unprotected_current_task_remains_preemptible() -> None:
    current = task("current", 6.0, 2.0)
    incoming = task("incoming", 6.0, 100.0)
    state = state_with_active(current=(current,), returning=(incoming,))

    result = run_guarded_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        selector=SelectOnly(incoming.task_id),
        protected_task_ids=frozenset(),
    )

    assert result.preempted_task_ids == (current.task_id,)
    assert result.accepted_task_ids == (incoming.task_id,)


def test_multi_member_preemptive_batch_protects_every_accepted_incoming() -> None:
    current = task("current", 6.0, 40.0)
    first = task("first", 6.0, 100.0)
    second = task("second", 4.0, 80.0)
    state = state_with_active(current=(current,), returning=(first, second))
    selector = ScriptedSelector(((second.task_id,), (first.task_id, second.task_id)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=17), workload_tasks=(current, first, second)
    )
    policy = NoCascadingDKPPolicy(config, selector)

    result = policy.run(
        state,
        requesting_task_ids=(first.task_id, second.task_id),
        time_remaining_by_task={current.task_id: 10.0, first.task_id: 4.0, second.task_id: 5.0},
        epoch=3,
    )

    assert selector.calls == 2  # one unchanged R1 call and one unchanged R2 call
    assert result.preempted_task_ids == (current.task_id,)
    assert set(policy.protected_task_ids) == {first.task_id, second.task_id}


def test_nonpreemptive_admission_does_not_create_protection() -> None:
    current = task("current", 2.0, 10.0)
    incoming = task("incoming", 2.0, 100.0)
    state = state_with_active(current=(current,), returning=(incoming,))
    selector = ScriptedSelector(((incoming.task_id,), (current.task_id, incoming.task_id)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=19), workload_tasks=(current, incoming)
    )
    policy = NoCascadingDKPPolicy(config, selector)

    result = policy.run(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        epoch=3,
    )

    assert result.preempted_task_ids == ()
    assert policy.protected_task_ids == frozenset()


def test_protection_ends_only_when_task_becomes_terminal() -> None:
    current = task("current", 6.0, 50.0)
    incoming = task("incoming", 6.0, 100.0)
    state = state_with_active(current=(current,), returning=(incoming,))
    selector = ScriptedSelector(((), (incoming.task_id,)))
    config = PipelineDKPConfig.from_workload(
        ga=PyeasygaConfig(seed=23), workload_tasks=(current, incoming)
    )
    policy = NoCascadingDKPPolicy(config, selector)
    result = policy.run(
        state,
        requesting_task_ids=(incoming.task_id,),
        time_remaining_by_task={current.task_id: 10.0, incoming.task_id: 5.0},
        epoch=3,
    )
    terminal = result.final_state.snapshot()
    terminal.current_slot = 7
    terminal = release_now(terminal, task_id=incoming.task_id, terminal_state=TaskState.COMPLETED)

    policy._reconcile_terminal(terminal, 7)  # noqa: SLF001

    assert policy.protected_task_ids == frozenset()


def test_guard_keeps_atomic_capacity_invariants() -> None:
    protected = task("protected", 6.0, 2.0)
    incoming = task("incoming", 4.0, 100.0)
    state = state_with_active(current=(protected,), returning=(incoming,))
    result = run_guarded_dkp_round_two_for_server(
        state,
        server_id="server",
        returning_task_ids=(incoming.task_id,),
        time_remaining_by_task={protected.task_id: 10.0, incoming.task_id: 5.0},
        selector=SelectOnly(incoming.task_id),
        protected_task_ids=frozenset({protected.task_id}),
    )
    assert remaining_resources(result.final_state, "server").is_zero()


def test_assert_no_cascading_summary_accepts_conserved_local_utility() -> None:
    assert_no_cascading_summary(
        {
            "protection": {"preempted": 0},
            "preemption": {
                "direct_chain_maximum_depth": 1,
                "incoming_utility": 12.0,
                "victim_utility": 5.0,
                "local_net_utility": 7.0,
            },
        }
    )


def test_utility_conservation_positive_and_negative_cases() -> None:
    assert validate_utility_conservation(total=10.0, completed=4.0, rejected=6.0) == 0.0
    with pytest.raises(StateValidationError, match="Utility conservation"):
        validate_utility_conservation(total=10.0, completed=4.0, rejected=5.0)


@pytest.mark.parametrize(
    ("summary", "message"),
    [
        (
            {
                "protection": {"preempted": 1},
                "preemption": {
                    "direct_chain_maximum_depth": 1,
                    "incoming_utility": 1.0,
                    "victim_utility": 1.0,
                    "local_net_utility": 0.0,
                },
            },
            "never be preempted",
        ),
        (
            {
                "protection": {"preempted": 0},
                "preemption": {
                    "direct_chain_maximum_depth": 2,
                    "incoming_utility": 1.0,
                    "victim_utility": 1.0,
                    "local_net_utility": 0.0,
                },
            },
            "depth one",
        ),
        (
            {
                "protection": {"preempted": 0},
                "preemption": {
                    "direct_chain_maximum_depth": 1,
                    "incoming_utility": 3.0,
                    "victim_utility": 1.0,
                    "local_net_utility": 3.0,
                },
            },
            "does not conserve",
        ),
    ],
)
def test_assert_no_cascading_summary_rejects_invariant_breaks(
    summary: dict[str, object], message: str
) -> None:
    with pytest.raises(StateValidationError, match=message):
        assert_no_cascading_summary(summary)
