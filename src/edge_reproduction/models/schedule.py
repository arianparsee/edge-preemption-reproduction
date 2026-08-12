"""Finite-horizon per-slot upload, computation and download allocations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import cast


def _normalize_series(name: str, values: tuple[float, ...]) -> tuple[float, ...]:
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must contain at least one slot")
    for value in normalized:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} values must be real numbers")
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} values must be finite and non-negative")
    return normalized


@dataclass(frozen=True, slots=True)
class TaskSchedule:
    """The three continuous allocation sequences in equations (2)-(10), (22)-(27).

    Python tuple index 0 corresponds to paper slot 1. This class validates only
    shape and non-negativity; activity windows are checked by the equation-specific
    validators because the printed windows contain known off-by-one issues.
    """

    upload: tuple[float, ...]
    computation: tuple[float, ...]
    download: tuple[float, ...]

    def __post_init__(self) -> None:
        upload = _normalize_series("upload", self.upload)
        computation = _normalize_series("computation", self.computation)
        download = _normalize_series("download", self.download)
        if not (len(upload) == len(computation) == len(download)):
            raise ValueError("upload, computation and download must share one horizon")
        object.__setattr__(self, "upload", upload)
        object.__setattr__(self, "computation", computation)
        object.__setattr__(self, "download", download)

    @property
    def horizon(self) -> int:
        """Return the number of slots in the finite horizon."""

        return len(self.upload)

    def total_upload(self) -> float:
        return float(sum(self.upload))

    def total_computation(self) -> float:
        return float(sum(self.computation))

    def total_download(self) -> float:
        return float(sum(self.download))

    def cumulative_through(self, activity: str, paper_slot: int) -> float:
        """Return a 1-based inclusive cumulative allocation through ``paper_slot``."""

        if isinstance(paper_slot, bool) or not isinstance(paper_slot, int):
            raise TypeError("paper_slot must be an integer")
        if not 1 <= paper_slot <= self.horizon:
            raise ValueError("paper_slot must be inside the schedule horizon")
        if activity not in {"upload", "computation", "download"}:
            raise ValueError("unknown activity")
        values = cast(tuple[float, ...], getattr(self, activity))
        return float(sum(values[:paper_slot]))

    @staticmethod
    def positive_span(values: tuple[float, ...]) -> tuple[int, int] | None:
        """Return first/last positive paper slots, or ``None`` for an empty set."""

        positive_slots = tuple(index for index, value in enumerate(values, start=1) if value > 0)
        if not positive_slots:
            return None
        return positive_slots[0], positive_slots[-1]
