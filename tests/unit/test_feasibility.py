import pytest

from edge_reproduction.algorithms.feasibility import (
    can_admit_after_preemptions,
    can_preempt_single_victim,
    can_retain_and_admit,
    meets_preemption_threshold,
    resources_available_after_preemptions,
    utility_time_ratio,
)
from edge_reproduction.models.enums import PreemptionThresholdSemantics
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.state import SimulationState


def make_task(task_id: str, storage: float, utility: float) -> Task:
    return Task(task_id, 0, 10, utility, ResourceVector(storage, 1.0, 1.0, 1.0))


def state_with_victim() -> tuple[SimulationState, Task, Task]:
    victim = make_task("victim", 6.0, 10.4)
    incoming = make_task("incoming", 7.0, 100.0)
    server = Server("server-1", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        1,
        {victim.task_id: victim, incoming.task_id: incoming},
        {server.server_id: server},
    )
    return allocate_now(state, task_id=victim.task_id, server_id=server.server_id), victim, incoming


def test_retention_checks_only_residual_resources() -> None:
    state, _, incoming = state_with_victim()

    assert not can_retain_and_admit(state, incoming, "server-1")


def test_preemption_resources_include_explicit_victim() -> None:
    state, victim, incoming = state_with_victim()

    assert resources_available_after_preemptions(
        state, "server-1", (victim.task_id,)
    ) == ResourceVector(10.0, 10.0, 10.0, 10.0)
    assert can_admit_after_preemptions(state, incoming, "server-1", (victim.task_id,))


def test_five_percent_prose_and_algorithm_two_can_disagree() -> None:
    arguments = {
        "incoming_utility": 100.0,
        "incoming_time": 10.0,
        "current_utility": 10.4,
        "current_time_remaining": 1.0,
    }

    assert not meets_preemption_threshold(**arguments, semantics=PreemptionThresholdSemantics.PROSE)
    assert meets_preemption_threshold(
        **arguments, semantics=PreemptionThresholdSemantics.ALGORITHM_TWO
    )


def test_assump_004_uses_prose_rule_by_default_and_includes_exact_boundary() -> None:
    assert meets_preemption_threshold(
        incoming_utility=105.0,
        incoming_time=10.0,
        current_utility=10.0,
        current_time_remaining=1.0,
    )
    assert not meets_preemption_threshold(
        incoming_utility=104.999,
        incoming_time=10.0,
        current_utility=10.0,
        current_time_remaining=1.0,
    )


def test_single_victim_feasibility_combines_threshold_and_fit() -> None:
    state, victim, incoming = state_with_victim()

    assert can_preempt_single_victim(
        state,
        incoming_task=incoming,
        victim_task=victim,
        server_id="server-1",
        incoming_time=10.0,
        victim_time_remaining=1.0,
        semantics=PreemptionThresholdSemantics.ALGORITHM_TWO,
    )
    assert not can_preempt_single_victim(
        state,
        incoming_task=incoming,
        victim_task=victim,
        server_id="server-1",
        incoming_time=10.0,
        victim_time_remaining=1.0,
        semantics=PreemptionThresholdSemantics.PROSE,
    )


def test_utility_time_ratio_rejects_zero_remaining_time() -> None:
    with pytest.raises(ValueError, match="positive"):
        utility_time_ratio(10.0, 0.0)
