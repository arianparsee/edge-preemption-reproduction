"""All-or-nothing utility from objective equation (1)."""

from collections.abc import Mapping, Sequence

from edge_reproduction.models.task import Task


def validate_binary(name: str, value: int) -> None:
    """Validate the domains in equations (20) and (21)."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer binary value")
    if value not in (0, 1):
        raise ValueError(f"{name} must be either 0 or 1")


def all_or_nothing_utility(
    task: Task,
    *,
    assignment: int,
    completion_indicator: int,
    deadline_met: bool,
) -> float:
    """Return ``U_j * tau_j * x_ij`` when completion meets the deadline.

    ``completion_indicator`` is ``tau_j``: 0 for preempted and 1 for run-to-end.
    The explicit ``deadline_met`` argument prevents this function from silently
    selecting an inclusive or exclusive boundary.
    """

    if not isinstance(task, Task):
        raise TypeError("task must be a Task")
    validate_binary("assignment", assignment)
    validate_binary("completion_indicator", completion_indicator)
    if not isinstance(deadline_met, bool):
        raise TypeError("deadline_met must be a boolean")
    if not deadline_met:
        return 0.0
    return float(task.utility * assignment * completion_indicator)


def total_served_utility(
    tasks: Sequence[Task],
    *,
    assignment_by_task: Mapping[str, int],
    completion_by_task: Mapping[str, int],
    deadline_met_by_task: Mapping[str, bool],
) -> float:
    """Evaluate objective (1) for one selected-assignment indicator per task."""

    total = 0.0
    for task in tasks:
        try:
            assignment = assignment_by_task[task.task_id]
            completion = completion_by_task[task.task_id]
            deadline_met = deadline_met_by_task[task.task_id]
        except KeyError as error:
            raise KeyError(f"missing objective input for task {task.task_id}") from error
        total += all_or_nothing_utility(
            task,
            assignment=assignment,
            completion_indicator=completion,
            deadline_met=deadline_met,
        )
    return total
