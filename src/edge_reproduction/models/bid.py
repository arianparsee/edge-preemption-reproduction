"""Auction records for the paper's two-round mechanism."""

from __future__ import annotations

from dataclasses import dataclass, field

from edge_reproduction.models._validation import (
    ensure_finite_number,
    ensure_identifier,
    ensure_nonnegative_integer,
    ensure_unique,
)
from edge_reproduction.models.enums import AuctionRoundNumber


@dataclass(frozen=True, slots=True)
class Bid:
    """A server price for one task in an auction round.

    ``auto_fit`` and ``marked_task_ids`` preserve information used by Algorithm 1.
    No non-negative price domain or impossible-price sentinel is imposed because
    arXiv v2 does not specify either formally; only finiteness is structural here.
    """

    task_id: str
    server_id: str
    round_number: AuctionRoundNumber
    price: float
    feasible: bool = True
    auto_fit: bool = False
    marked_task_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_identifier("task_id", self.task_id)
        ensure_identifier("server_id", self.server_id)
        if not isinstance(self.round_number, AuctionRoundNumber):
            raise TypeError("round_number must be an AuctionRoundNumber")
        ensure_finite_number("price", self.price)
        if not isinstance(self.feasible, bool) or not isinstance(self.auto_fit, bool):
            raise TypeError("feasible and auto_fit must be booleans")
        marked_task_ids = tuple(self.marked_task_ids)
        for task_id in marked_task_ids:
            ensure_identifier("marked task_id", task_id)
        ensure_unique("marked_task_ids", marked_task_ids)
        object.__setattr__(self, "marked_task_ids", marked_task_ids)
        if self.auto_fit and not self.feasible:
            raise ValueError("an auto-fit bid cannot be infeasible")


@dataclass(frozen=True, slots=True)
class AuctionRound:
    """Immutable snapshot of one of the paper's two auction rounds."""

    round_number: AuctionRoundNumber
    epoch: int
    task_ids: tuple[str, ...]
    bids: tuple[Bid, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.round_number, AuctionRoundNumber):
            raise TypeError("round_number must be an AuctionRoundNumber")
        ensure_nonnegative_integer("epoch", self.epoch)
        task_ids = tuple(self.task_ids)
        bids = tuple(self.bids)
        for task_id in task_ids:
            ensure_identifier("task_id", task_id)
        ensure_unique("task_ids", task_ids)
        seen_pairs: set[tuple[str, str]] = set()
        for bid in bids:
            if not isinstance(bid, Bid):
                raise TypeError("bids must contain only Bid instances")
            if bid.round_number is not self.round_number:
                raise ValueError("each bid must belong to this auction round")
            if bid.task_id not in task_ids:
                raise ValueError("each bid task must be listed in task_ids")
            pair = (bid.task_id, bid.server_id)
            if pair in seen_pairs:
                raise ValueError("duplicate bid for the same task and server")
            seen_pairs.add(pair)
        object.__setattr__(self, "task_ids", task_ids)
        object.__setattr__(self, "bids", bids)
