"""Structurally validated snapshot of tasks, servers and auction records."""

from __future__ import annotations

from dataclasses import dataclass, field

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models._validation import ensure_nonnegative_integer
from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.bid import AuctionRound
from edge_reproduction.models.enums import TaskState
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task


@dataclass(slots=True)
class SimulationState:
    """Mutable simulation registry with immutable domain records.

    The mapping keyed by task identifier enforces the paper's constraint that a
    task cannot have more than one server assignment at a time. Resource-capacity
    and task-state invariants are intentionally deferred to Stage 8, where every
    mathematical constraint will receive positive and negative tests.
    """

    current_slot: int
    tasks: dict[str, Task]
    servers: dict[str, Server]
    task_states: dict[str, TaskState] = field(default_factory=dict)
    allocations: dict[str, Allocation] = field(default_factory=dict)
    auction_rounds: tuple[AuctionRound, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_nonnegative_integer("current_slot", self.current_slot)
        self.tasks = dict(self.tasks)
        self.servers = dict(self.servers)
        self.task_states = dict(self.task_states)
        self.allocations = dict(self.allocations)
        self.auction_rounds = tuple(self.auction_rounds)

        for key, task in self.tasks.items():
            if not isinstance(task, Task):
                raise StateValidationError("tasks must contain only Task instances")
            if key != task.task_id:
                raise StateValidationError("task mapping key must equal Task.task_id")
        for key, server in self.servers.items():
            if not isinstance(server, Server):
                raise StateValidationError("servers must contain only Server instances")
            if key != server.server_id:
                raise StateValidationError("server mapping key must equal Server.server_id")

        if not self.task_states:
            self.task_states = {task_id: TaskState.CREATED for task_id in self.tasks}
        elif set(self.task_states) != set(self.tasks):
            raise StateValidationError("task_states must have exactly one entry per task")
        if any(not isinstance(state, TaskState) for state in self.task_states.values()):
            raise StateValidationError("task_states must contain only TaskState values")

        for key, allocation in self.allocations.items():
            if not isinstance(allocation, Allocation):
                raise StateValidationError("allocations must contain only Allocation instances")
            if key != allocation.task_id:
                raise StateValidationError("allocation mapping key must equal Allocation.task_id")
            if allocation.task_id not in self.tasks:
                raise StateValidationError("allocation references an unknown task")
            if allocation.server_id not in self.servers:
                raise StateValidationError("allocation references an unknown server")
        if any(not isinstance(item, AuctionRound) for item in self.auction_rounds):
            raise StateValidationError("auction_rounds must contain only AuctionRound instances")

    def snapshot(self) -> SimulationState:
        """Return an independent structural snapshot of mutable registries."""

        return SimulationState(
            current_slot=self.current_slot,
            tasks=self.tasks.copy(),
            servers=self.servers.copy(),
            task_states=self.task_states.copy(),
            allocations=self.allocations.copy(),
            auction_rounds=self.auction_rounds,
        )

    def active_allocations_for_server(self, server_id: str) -> tuple[Allocation, ...]:
        """Return active allocations for a known server in stable insertion order."""

        if server_id not in self.servers:
            raise KeyError(f"unknown server_id: {server_id}")
        return tuple(
            allocation
            for allocation in self.allocations.values()
            if allocation.server_id == server_id and allocation.is_active
        )
