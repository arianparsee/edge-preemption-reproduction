"""Controlled names for technical states and modes.

The paper explicitly describes the corresponding phases and outcomes, but most
state names are technical labels proposed during reproduction Stage 2. This
module deliberately does not define a transition policy because several
transition conditions remain unspecified in arXiv v2.
"""

from enum import IntEnum, StrEnum


class TaskState(StrEnum):
    """Technical task lifecycle labels mapped to the paper's described phases."""

    CREATED = "created"
    WAITING_FOR_BID = "waiting_for_bid"
    ROUND1_REQUESTED = "round1_requested"
    ROUND1_PRICED = "round1_priced"
    ROUND2_RETURNED = "round2_returned"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITING_RETRY = "waiting_retry"
    BATCH_UPLOADING = "batch_uploading"
    BATCH_PROCESSING = "batch_processing"
    BATCH_DOWNLOADING = "batch_downloading"
    PIPELINE_ACTIVE = "pipeline_active"
    COMPLETED = "completed"
    PREEMPTED = "preempted"
    EXPIRED = "expired"


class ProcessingMode(StrEnum):
    """Processing semantics explicitly distinguished in Section III."""

    BATCH = "batch"
    PIPELINE = "pipeline"


class AuctionRoundNumber(IntEnum):
    """The two auction rounds explicitly described in Section III."""

    ROUND_ONE = 1
    ROUND_TWO = 2


class ResultStatus(StrEnum):
    """Technical execution outcomes; these are not task outcomes from the paper."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeadlineBoundary(StrEnum):
    """Explicit interpretations of the paper's unreported deadline boundary."""

    INCLUSIVE = "inclusive"
    EXCLUSIVE = "exclusive"


class AssignmentFlowSemantics(StrEnum):
    """Alternative readings of the inconsistent quantifier in equations (2)-(6)."""

    LITERAL_ALL_SERVERS = "literal_all_servers"
    SELECTED_SERVER_ONLY = "selected_server_only"


class CongestionPriceSemantics(StrEnum):
    """Alternative congestion terms in the prose and Algorithm 1."""

    PROSE = "prose"
    ALGORITHM_ONE = "algorithm_one"


class PreemptionThresholdSemantics(StrEnum):
    """Alternative 5% comparisons in prose and Algorithm 2."""

    PROSE = "prose"
    ALGORITHM_TWO = "algorithm_two"


class ActivityKind(StrEnum):
    """The three pipeline activities in equations (22)-(27)."""

    UPLOAD = "upload"
    COMPUTATION = "computation"
    DOWNLOAD = "download"


class EventType(StrEnum):
    """Machine-readable events emitted by the base simulator."""

    ARRIVED = "arrived"
    ACTIVATED = "activated"
    PROGRESSED = "progressed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RETRY_SCHEDULED = "retry_scheduled"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ScriptedAction(StrEnum):
    """Explicit commands used before paper algorithms are implemented."""

    ARRIVE = "arrive"
    ACCEPT = "accept"
    REJECT = "reject"
    PREEMPT_AND_ACCEPT = "preempt_and_accept"
    COMPLETE = "complete"
