"""Common policy contract used by staged paper-algorithm implementations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from edge_reproduction.simulation.state import SimulationState


@runtime_checkable
class AllocationPolicyResult(Protocol):
    """Minimum common result surface needed by the simulator/evaluator."""

    @property
    def final_state(self) -> SimulationState:
        """Return the immutable state produced by the policy."""

    @property
    def accepted_task_ids(self) -> tuple[str, ...]:
        """Return requesting tasks accepted during this auction."""

    @property
    def rejected_task_ids(self) -> tuple[str, ...]:
        """Return requesting tasks rejected during this auction."""


@runtime_checkable
class AllocationPolicy(Protocol):
    """Common two-round allocation-policy interface proposed in Stage 6."""

    @property
    def name(self) -> str:
        """Return the stable policy identifier."""

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> AllocationPolicyResult:
        """Run one auction epoch without mutating the input snapshot."""
