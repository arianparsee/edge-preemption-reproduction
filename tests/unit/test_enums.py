from edge_reproduction.models.enums import AuctionRoundNumber, ProcessingMode, TaskState


def test_paper_processing_modes_are_distinct() -> None:
    assert {mode.value for mode in ProcessingMode} == {"batch", "pipeline"}


def test_auction_has_exactly_two_round_numbers() -> None:
    assert list(AuctionRoundNumber) == [
        AuctionRoundNumber.ROUND_ONE,
        AuctionRoundNumber.ROUND_TWO,
    ]


def test_stage_two_task_states_are_all_represented() -> None:
    assert len(TaskState) == 15
    assert TaskState.COMPLETED.value == "completed"
    assert TaskState.PREEMPTED.value == "preempted"
