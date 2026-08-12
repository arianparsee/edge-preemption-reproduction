"""Immutable edge-server specification."""

from dataclasses import dataclass

from edge_reproduction.models._validation import ensure_identifier
from edge_reproduction.models.resources import ResourceVector


@dataclass(frozen=True, slots=True)
class Server:
    """An independent edge server with four resource capacities.

    The vector maps to ``S_i``, ``C_i``, ``B_{u,i}`` and ``B_{d,i}``. Zero
    capacity is valid so the required boundary case can be represented. Dynamic
    residual capacity and current jobs belong to ``SimulationState``.
    """

    server_id: str
    capacity: ResourceVector

    def __post_init__(self) -> None:
        ensure_identifier("server_id", self.server_id)
        if not isinstance(self.capacity, ResourceVector):
            raise TypeError("capacity must be a ResourceVector")
