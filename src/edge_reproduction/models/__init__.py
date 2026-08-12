"""Domain models extracted from the paper's system and mathematical models."""

from edge_reproduction.models.allocation import Allocation
from edge_reproduction.models.bid import AuctionRound, Bid
from edge_reproduction.models.config import ExperimentConfig
from edge_reproduction.models.enums import (
    ActivityKind,
    AssignmentFlowSemantics,
    AuctionRoundNumber,
    CongestionPriceSemantics,
    DeadlineBoundary,
    PreemptionThresholdSemantics,
    ProcessingMode,
    ResultStatus,
    TaskState,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.result import ExperimentResult
from edge_reproduction.models.schedule import TaskSchedule
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task

__all__ = [
    "Allocation",
    "ActivityKind",
    "AuctionRound",
    "AuctionRoundNumber",
    "AssignmentFlowSemantics",
    "Bid",
    "CongestionPriceSemantics",
    "DeadlineBoundary",
    "ExperimentConfig",
    "ExperimentResult",
    "PreemptionThresholdSemantics",
    "ProcessingMode",
    "ResourceVector",
    "ResultStatus",
    "Server",
    "Task",
    "TaskSchedule",
    "TaskState",
]
