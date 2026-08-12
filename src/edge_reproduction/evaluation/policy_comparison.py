"""Common auxiliary regression schema for allocation-policy control flows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from edge_reproduction.algorithms.base import AllocationPolicy, AllocationPolicyResult
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.invariants import (
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


@runtime_checkable
class ResultWithMetadata(Protocol):
    """Optional metadata surface implemented by DK policies."""

    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PolicyRunSpec:
    """One policy plus explicit provenance for an auxiliary comparison."""

    policy: AllocationPolicy
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.policy, AllocationPolicy):
            raise TypeError("policy must satisfy AllocationPolicy")
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True, slots=True)
class PolicyComparisonRecord:
    """Normalized after-auction outcome; it is not a completed-utility metric."""

    method: str
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    active_task_ids: tuple[str, ...]
    active_utility_after_auction: float
    residual_by_server: Mapping[str, ResourceVector]
    final_task_states: Mapping[str, TaskState]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "residual_by_server", MappingProxyType(dict(self.residual_by_server))
        )
        object.__setattr__(
            self, "final_task_states", MappingProxyType(dict(self.final_task_states))
        )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def as_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        return {
            "method": self.method,
            "accepted_task_ids": list(self.accepted_task_ids),
            "rejected_task_ids": list(self.rejected_task_ids),
            "retained_task_ids": list(self.retained_task_ids),
            "preempted_task_ids": list(self.preempted_task_ids),
            "active_task_ids": list(self.active_task_ids),
            "active_utility_after_auction": self.active_utility_after_auction,
            "metric_warning": "active_utility_after_auction_is_not_completed_paper_utility",
            "residual_by_server": {
                server_id: residual.as_dict()
                for server_id, residual in self.residual_by_server.items()
            },
            "final_task_states": {
                task_id: task_state.value for task_id, task_state in self.final_task_states.items()
            },
            "metadata": dict(self.metadata),
        }


def _ensure_input_unchanged(state: SimulationState, before: SimulationState) -> None:
    if (
        state.current_slot != before.current_slot
        or state.tasks != before.tasks
        or state.servers != before.servers
        or state.task_states != before.task_states
        or state.allocations != before.allocations
        or state.auction_rounds != before.auction_rounds
    ):
        raise StateValidationError("a compared policy mutated the shared input state")


def summarize_policy_result(
    *,
    method: str,
    initial_state: SimulationState,
    result: AllocationPolicyResult,
    provenance: Mapping[str, str],
) -> PolicyComparisonRecord:
    """Normalize one result while deriving retain/preempt outcomes from state."""

    validate_state_invariants(result.final_state)
    initial_active = tuple(
        allocation.task_id
        for allocation in initial_state.allocations.values()
        if allocation.is_active
    )
    final_active = tuple(
        allocation.task_id
        for allocation in result.final_state.allocations.values()
        if allocation.is_active
    )
    final_active_set = set(final_active)
    retained = tuple(task_id for task_id in initial_active if task_id in final_active_set)
    preempted = tuple(
        task_id
        for task_id in initial_active
        if result.final_state.task_states[task_id] is TaskState.PREEMPTED
    )
    if set(initial_active) != set(retained) | set(preempted):
        raise StateValidationError(
            "every initially active task must be retained or preempted in this regression"
        )
    if not set(result.accepted_task_ids).issubset(final_active_set):
        raise StateValidationError("every accepted task must have a final active allocation")
    if any(
        result.final_state.task_states[task_id] is not TaskState.REJECTED
        for task_id in result.rejected_task_ids
    ):
        raise StateValidationError("every rejected task must have REJECTED final state")

    metadata = dict(provenance)
    if isinstance(result, ResultWithMetadata):
        metadata.update(result.metadata)
    metadata["comparison.metric"] = "active_utility_after_auction_not_completed_utility"
    active_utility = float(
        sum(result.final_state.tasks[task_id].utility for task_id in final_active)
    )
    return PolicyComparisonRecord(
        method,
        tuple(result.accepted_task_ids),
        tuple(result.rejected_task_ids),
        retained,
        preempted,
        final_active,
        active_utility,
        {
            server_id: remaining_resources(result.final_state, server_id)
            for server_id in result.final_state.servers
        },
        dict(sorted(result.final_state.task_states.items())),
        metadata,
    )


def run_policy_comparison(
    state: SimulationState,
    *,
    requesting_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    specs: Sequence[PolicyRunSpec],
    epoch: int = 0,
) -> tuple[PolicyComparisonRecord, ...]:
    """Run independent policies on one unchanged state and normalize outcomes."""

    validate_state_invariants(state)
    run_specs = tuple(specs)
    methods = tuple(spec.policy.name for spec in run_specs)
    if not run_specs:
        raise ValueError("specs must not be empty")
    if len(methods) != len(set(methods)):
        raise ValueError("compared policy names must be unique")

    original = state.snapshot()
    records: list[PolicyComparisonRecord] = []
    for spec in run_specs:
        result = spec.policy.run(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            epoch=epoch,
        )
        _ensure_input_unchanged(state, original)
        records.append(
            summarize_policy_result(
                method=spec.policy.name,
                initial_state=original,
                result=result,
                provenance=spec.provenance,
            )
        )
    return tuple(records)
