import math

import pytest

from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.bid import AuctionRound, Bid
from edge_reproduction.models.enums import AuctionRoundNumber
from edge_reproduction.models.resources import ResourceVector


def resources() -> ResourceVector:
    return ResourceVector(1.0, 2.0, 3.0, 4.0)


def test_bid_preserves_algorithm_one_metadata() -> None:
    bid = Bid(
        task_id="job-1",
        server_id="server-1",
        round_number=AuctionRoundNumber.ROUND_ONE,
        price=12.5,
        auto_fit=True,
        marked_task_ids=("job-2",),
    )

    assert bid.auto_fit
    assert bid.marked_task_ids == ("job-2",)


def test_bid_allows_finite_negative_price_because_domain_is_unreported() -> None:
    bid = Bid("job-1", "server-1", AuctionRoundNumber.ROUND_ONE, -0.5)

    assert bid.price == -0.5


@pytest.mark.parametrize("price", [math.inf, -math.inf, math.nan])
def test_bid_rejects_non_finite_price(price: float) -> None:
    with pytest.raises(ValueError):
        Bid("job-1", "server-1", AuctionRoundNumber.ROUND_ONE, price)


def test_infeasible_bid_cannot_be_auto_fit() -> None:
    with pytest.raises(ValueError, match="auto-fit"):
        Bid(
            "job-1",
            "server-1",
            AuctionRoundNumber.ROUND_ONE,
            1.0,
            feasible=False,
            auto_fit=True,
        )


def test_auction_round_validates_bid_membership_and_round() -> None:
    valid_bid = Bid("job-1", "server-1", AuctionRoundNumber.ROUND_ONE, 1.0)
    auction_round = AuctionRound(
        AuctionRoundNumber.ROUND_ONE,
        epoch=2,
        task_ids=("job-1",),
        bids=(valid_bid,),
    )

    assert auction_round.bids == (valid_bid,)

    wrong_round_bid = Bid("job-1", "server-1", AuctionRoundNumber.ROUND_TWO, 1.0)
    with pytest.raises(ValueError, match="auction round"):
        AuctionRound(
            AuctionRoundNumber.ROUND_ONE,
            epoch=2,
            task_ids=("job-1",),
            bids=(wrong_round_bid,),
        )


def test_auction_round_rejects_duplicate_task_server_bid() -> None:
    bid = Bid("job-1", "server-1", AuctionRoundNumber.ROUND_ONE, 1.0)
    with pytest.raises(ValueError, match="duplicate bid"):
        AuctionRound(
            AuctionRoundNumber.ROUND_ONE,
            epoch=0,
            task_ids=("job-1",),
            bids=(bid, bid),
        )


def test_active_and_ended_allocation() -> None:
    active = Allocation("job-1", "server-1", resources(), start_slot=3)
    ended = Allocation("job-1", "server-1", resources(), start_slot=3, end_slot=5)

    assert active.is_active
    assert not ended.is_active


def test_allocation_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="precede"):
        Allocation("job-1", "server-1", resources(), start_slot=3, end_slot=2)
