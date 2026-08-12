"""Immutable task specification extracted from Section IV."""

from __future__ import annotations

from dataclasses import dataclass

from edge_reproduction.models._validation import (
    ensure_finite_number,
    ensure_identifier,
    ensure_nonnegative_integer,
    ensure_positive_integer,
)
from edge_reproduction.models.resources import ResourceVector


@dataclass(frozen=True, slots=True)
class Task:
    """A task/job and its paper-defined static attributes.

    ``arrival_slot``, ``deadline_slots`` and ``utility`` map to ``a_j``, ``d_j``
    and ``U_j``. ``demand.storage`` and ``demand.computation`` represent ``s_j``
    and ``K_j``; upload/download components retain the heuristic demands reported
    in Tables I-II. ``output_size`` represents ``s'_j`` and may be ``None`` because
    arXiv v2 does not provide its synthetic-data distribution.

    The numerical value ``arrival_slot + deadline_slots`` is exposed, but this
    class does not decide whether that boundary is inclusive. That event-ordering
    question remains unresolved for the simulator.
    """

    task_id: str
    arrival_slot: int
    deadline_slots: int
    utility: float
    demand: ResourceVector
    output_size: float | None = None

    def __post_init__(self) -> None:
        ensure_identifier("task_id", self.task_id)
        ensure_nonnegative_integer("arrival_slot", self.arrival_slot)
        ensure_positive_integer("deadline_slots", self.deadline_slots)
        ensure_finite_number("utility", self.utility)
        if not isinstance(self.demand, ResourceVector):
            raise TypeError("demand must be a ResourceVector")
        # Positive input and compute totals are required by the denominators in
        # equations (8)-(10). Upload/download may be zero at the data-model level.
        if self.demand.storage <= 0:
            raise ValueError("task storage/input demand must be positive")
        if self.demand.computation <= 0:
            raise ValueError("task computation demand must be positive")
        if self.output_size is not None:
            ensure_finite_number("output_size", self.output_size)
            if self.output_size <= 0:
                raise ValueError("output_size must be positive when provided")

    @property
    def absolute_deadline_slot(self) -> int:
        """Return the numerical arrival-plus-relative-deadline endpoint."""

        return self.arrival_slot + self.deadline_slots
