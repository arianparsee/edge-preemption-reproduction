"""Time helpers that keep the paper's deadline-boundary ambiguity explicit."""

from edge_reproduction.models._validation import ensure_nonnegative_integer
from edge_reproduction.models.enums import DeadlineBoundary
from edge_reproduction.models.task import Task


def meets_deadline(
    task: Task,
    completion_slot: int,
    *,
    boundary: DeadlineBoundary,
) -> bool:
    """Check completion against ``a_j + d_j`` under an explicit boundary.

    arXiv v2 does not state whether completion exactly at the numerical deadline
    is allowed. The caller must therefore choose ``INCLUSIVE`` or ``EXCLUSIVE``;
    this function has no default interpretation.
    """

    if not isinstance(task, Task):
        raise TypeError("task must be a Task")
    ensure_nonnegative_integer("completion_slot", completion_slot)
    if not isinstance(boundary, DeadlineBoundary):
        raise TypeError("boundary must be a DeadlineBoundary")
    if boundary is DeadlineBoundary.INCLUSIVE:
        return completion_slot <= task.absolute_deadline_slot
    return completion_slot < task.absolute_deadline_slot


def elapsed_slots(start_slot: int, end_slot: int, *, boundary: DeadlineBoundary) -> int:
    """Calculate elapsed slots under an explicitly selected endpoint convention."""

    ensure_nonnegative_integer("start_slot", start_slot)
    ensure_nonnegative_integer("end_slot", end_slot)
    if end_slot < start_slot:
        raise ValueError("end_slot must not precede start_slot")
    if not isinstance(boundary, DeadlineBoundary):
        raise TypeError("boundary must be a DeadlineBoundary")
    if boundary is DeadlineBoundary.INCLUSIVE:
        return end_slot - start_slot + 1
    return end_slot - start_slot
