"""Structural task-to-server allocation record."""

from dataclasses import dataclass

from edge_reproduction.models._validation import ensure_identifier, ensure_nonnegative_integer
from edge_reproduction.models.resources import ResourceVector


@dataclass(frozen=True, slots=True)
class Allocation:
    """A task's reservation on one server.

    This record captures admission-level assignment ``x_{i,j}`` and reserved
    resources. The slot-level variables ``sigma``, ``kappa`` and ``sigma'`` will
    be represented by the simulator in Stage 8/9; they are not guessed here.
    """

    task_id: str
    server_id: str
    resources: ResourceVector
    start_slot: int
    end_slot: int | None = None

    def __post_init__(self) -> None:
        ensure_identifier("task_id", self.task_id)
        ensure_identifier("server_id", self.server_id)
        if not isinstance(self.resources, ResourceVector):
            raise TypeError("resources must be a ResourceVector")
        ensure_nonnegative_integer("start_slot", self.start_slot)
        if self.end_slot is not None:
            ensure_nonnegative_integer("end_slot", self.end_slot)
            if self.end_slot < self.start_slot:
                raise ValueError("end_slot must not precede start_slot")

    @property
    def is_active(self) -> bool:
        """Return whether no release/end slot has been recorded."""

        return self.end_slot is None
