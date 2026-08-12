"""Four-dimensional resource vectors used by tasks and edge servers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _validate_component(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class ResourceVector:
    """Storage, computation, upload and download quantities.

    Paper mapping:
    - storage: ``s_j`` for a task or ``S_i`` for a server;
    - computation: task computation demand or ``C_i`` capacity;
    - upload: task upload demand or ``B_{u,i}`` capacity;
    - download: task download demand or ``B_{d,i}`` capacity.

    The paper is inconsistent about MB versus GB and does not fully specify
    rate-to-slot conversion. Consequently this class performs no unit conversion.
    All operands in one operation must already use the same experiment-specific
    canonical units.
    """

    storage: float
    computation: float
    upload: float
    download: float

    def __post_init__(self) -> None:
        for name in ("storage", "computation", "upload", "download"):
            _validate_component(name, getattr(self, name))

    @classmethod
    def zero(cls) -> ResourceVector:
        """Return a zero vector without introducing experiment-specific defaults."""

        return cls(storage=0.0, computation=0.0, upload=0.0, download=0.0)

    def __add__(self, other: ResourceVector) -> ResourceVector:
        if not isinstance(other, ResourceVector):
            return NotImplemented
        return ResourceVector(
            storage=self.storage + other.storage,
            computation=self.computation + other.computation,
            upload=self.upload + other.upload,
            download=self.download + other.download,
        )

    def subtract(self, other: ResourceVector, *, tolerance: float = 0.0) -> ResourceVector:
        """Subtract component-wise, rejecting capacity underflow.

        ``tolerance`` defaults to exactly zero because the paper reports no
        feasibility tolerance. A non-zero tolerance must be an explicit caller
        decision and is not silently applied.
        """

        if not isinstance(other, ResourceVector):
            raise TypeError("other must be a ResourceVector")
        _validate_component("tolerance", tolerance)
        differences = (
            self.storage - other.storage,
            self.computation - other.computation,
            self.upload - other.upload,
            self.download - other.download,
        )
        if any(value < -tolerance for value in differences):
            raise ValueError("resource subtraction would create a negative component")
        normalized = tuple(0.0 if value < 0.0 else value for value in differences)
        return ResourceVector(*normalized)

    def fits_within(self, capacity: ResourceVector, *, tolerance: float = 0.0) -> bool:
        """Return whether all four components fit component-wise."""

        if not isinstance(capacity, ResourceVector):
            raise TypeError("capacity must be a ResourceVector")
        _validate_component("tolerance", tolerance)
        return (
            self.storage <= capacity.storage + tolerance
            and self.computation <= capacity.computation + tolerance
            and self.upload <= capacity.upload + tolerance
            and self.download <= capacity.download + tolerance
        )

    def is_zero(self) -> bool:
        """Return whether every resource component is exactly zero."""

        return self == self.zero()

    def as_dict(self) -> dict[str, float]:
        """Return a serialization-friendly representation."""

        return {
            "storage": float(self.storage),
            "computation": float(self.computation),
            "upload": float(self.upload),
            "download": float(self.download),
        }
