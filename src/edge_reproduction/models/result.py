"""Experiment result records aligned with the paper's reported metrics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from edge_reproduction.models._validation import (
    ensure_finite_number,
    ensure_identifier,
    ensure_nonnegative_integer,
    ensure_unique,
)
from edge_reproduction.models.enums import ResultStatus


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """One method/seed run and the outcome categories used in Figs. 6-20.

    ``ever_preempted_task_ids`` is intentionally allowed to overlap completed or
    rejected identifiers. Stage 5 established that the paper's "Preempted"
    category means tasks preempted at least once and does not necessarily form a
    partition of final outcomes.
    """

    run_id: str
    experiment_id: str
    method: str
    random_seed: int | None
    completed_task_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_task_ids: tuple[str, ...] = field(default_factory=tuple)
    ever_preempted_task_ids: tuple[str, ...] = field(default_factory=tuple)
    completed_utility: float = 0.0
    rejected_utility: float = 0.0
    preempted_utility: float = 0.0
    event_count: int = 0
    status: ResultStatus = ResultStatus.SUCCEEDED
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure_identifier("run_id", self.run_id)
        ensure_identifier("experiment_id", self.experiment_id)
        ensure_identifier("method", self.method)
        if self.random_seed is not None and (
            isinstance(self.random_seed, bool) or not isinstance(self.random_seed, int)
        ):
            raise TypeError("random_seed must be an integer or None")
        if not isinstance(self.status, ResultStatus):
            raise TypeError("status must be a ResultStatus")
        ensure_nonnegative_integer("event_count", self.event_count)
        for name in ("completed_utility", "rejected_utility", "preempted_utility"):
            ensure_finite_number(name, getattr(self, name))

        for field_name in (
            "completed_task_ids",
            "rejected_task_ids",
            "ever_preempted_task_ids",
        ):
            identifiers = tuple(getattr(self, field_name))
            for task_id in identifiers:
                ensure_identifier(field_name, task_id)
            ensure_unique(field_name, identifiers)
            object.__setattr__(self, field_name, identifiers)

        metadata = dict(self.metadata)
        for key, value in metadata.items():
            ensure_identifier("metadata key", key)
            ensure_identifier("metadata value", value)
        object.__setattr__(self, "metadata", MappingProxyType(metadata))
