"""Immutable, serialization-friendly discrete-event log records."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from edge_reproduction.models._validation import ensure_identifier, ensure_nonnegative_integer
from edge_reproduction.models.enums import EventType
from edge_reproduction.models.resources import ResourceVector


def _optional_finite(name: str, value: float | None) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number or None")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """One audited state transition in the base simulator."""

    sequence: int
    time: int
    event_type: EventType
    task_id: str
    server_id: str | None
    resources_before: ResourceVector | None
    resources_after: ResourceVector | None
    utility: float
    earned_utility: float
    price: float | None
    reason: str

    def __post_init__(self) -> None:
        ensure_nonnegative_integer("sequence", self.sequence)
        ensure_nonnegative_integer("time", self.time)
        if not isinstance(self.event_type, EventType):
            raise TypeError("event_type must be an EventType")
        ensure_identifier("task_id", self.task_id)
        if self.server_id is not None:
            ensure_identifier("server_id", self.server_id)
        for name, resources in (
            ("resources_before", self.resources_before),
            ("resources_after", self.resources_after),
        ):
            if resources is not None and not isinstance(resources, ResourceVector):
                raise TypeError(f"{name} must be a ResourceVector or None")
        _finite("utility", self.utility)
        _finite("earned_utility", self.earned_utility)
        _optional_finite("price", self.price)
        ensure_identifier("reason", self.reason)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable event representation."""

        return {
            "sequence": self.sequence,
            "time": self.time,
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "server_id": self.server_id,
            "resources_before": (
                None if self.resources_before is None else self.resources_before.as_dict()
            ),
            "resources_after": (
                None if self.resources_after is None else self.resources_after.as_dict()
            ),
            "utility": self.utility,
            "earned_utility": self.earned_utility,
            "price": self.price,
            "reason": self.reason,
        }
