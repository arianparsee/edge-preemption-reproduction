"""Pure validators for objective constraints (2)-(31) in arXiv v2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite

from edge_reproduction.evaluation.utility import validate_binary
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models._validation import ensure_positive_integer
from edge_reproduction.models.enums import ActivityKind, AssignmentFlowSemantics
from edge_reproduction.models.schedule import TaskSchedule


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _positive(name: str, value: float) -> None:
    _finite(name, value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _nonnegative(name: str, value: float) -> None:
    _finite(name, value)
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _validate_assignments(assignments: Sequence[int]) -> tuple[int, ...]:
    normalized = tuple(assignments)
    if not normalized:
        raise ValueError("assignments must contain at least one server indicator")
    for value in normalized:
        validate_binary("assignment", value)
    return normalized


def _equal(left: float, right: float, tolerance: float) -> bool:
    _nonnegative("tolerance", tolerance)
    return abs(left - right) <= tolerance


def _flow_upper_bound(
    total: float,
    requirement: float,
    assignments: Sequence[int],
    semantics: AssignmentFlowSemantics,
    tolerance: float,
) -> bool:
    _nonnegative("total", total)
    _positive("requirement", requirement)
    indicators = _validate_assignments(assignments)
    if not isinstance(semantics, AssignmentFlowSemantics):
        raise TypeError("semantics must be an AssignmentFlowSemantics")
    if semantics is AssignmentFlowSemantics.LITERAL_ALL_SERVERS:
        return all(total <= requirement * indicator + tolerance for indicator in indicators)
    return (
        check_equation_19_single_assignment(indicators)
        and total <= requirement * sum(indicators) + tolerance
    )


def _completed_flow(
    total: float,
    requirement: float,
    assignments: Sequence[int],
    completion_indicator: int,
    semantics: AssignmentFlowSemantics,
    tolerance: float,
) -> bool:
    _nonnegative("total", total)
    _positive("requirement", requirement)
    validate_binary("completion_indicator", completion_indicator)
    indicators = _validate_assignments(assignments)
    if not isinstance(semantics, AssignmentFlowSemantics):
        raise TypeError("semantics must be an AssignmentFlowSemantics")
    if semantics is AssignmentFlowSemantics.LITERAL_ALL_SERVERS:
        return all(
            _equal(completion_indicator * (total - requirement * indicator), 0.0, tolerance)
            for indicator in indicators
        )
    return check_equation_19_single_assignment(indicators) and _equal(
        completion_indicator * (total - requirement * sum(indicators)), 0.0, tolerance
    )


def check_equation_2_upload_upper_bound(
    total_upload: float,
    input_size: float,
    assignments: Sequence[int],
    *,
    semantics: AssignmentFlowSemantics,
    tolerance: float = 0.0,
) -> bool:
    return _flow_upper_bound(total_upload, input_size, assignments, semantics, tolerance)


def check_equation_3_completed_upload(
    total_upload: float,
    input_size: float,
    assignments: Sequence[int],
    completion_indicator: int,
    *,
    semantics: AssignmentFlowSemantics,
    tolerance: float = 0.0,
) -> bool:
    return _completed_flow(
        total_upload,
        input_size,
        assignments,
        completion_indicator,
        semantics,
        tolerance,
    )


def check_equation_4_computation_upper_bound(
    total_computation: float,
    computation_requirement: float,
    assignments: Sequence[int],
    *,
    semantics: AssignmentFlowSemantics,
    tolerance: float = 0.0,
) -> bool:
    return _flow_upper_bound(
        total_computation, computation_requirement, assignments, semantics, tolerance
    )


def check_equation_5_completed_computation(
    total_computation: float,
    computation_requirement: float,
    assignments: Sequence[int],
    completion_indicator: int,
    *,
    semantics: AssignmentFlowSemantics,
    tolerance: float = 0.0,
) -> bool:
    return _completed_flow(
        total_computation,
        computation_requirement,
        assignments,
        completion_indicator,
        semantics,
        tolerance,
    )


def check_equation_6_download_upper_bound(
    total_download: float,
    output_size: float,
    assignments: Sequence[int],
    *,
    semantics: AssignmentFlowSemantics,
    tolerance: float = 0.0,
) -> bool:
    return _flow_upper_bound(total_download, output_size, assignments, semantics, tolerance)


def check_equation_7_completed_download(
    total_download: float,
    output_size: float,
    completion_indicator: int,
    *,
    tolerance: float = 0.0,
) -> bool:
    _nonnegative("total_download", total_download)
    _positive("output_size", output_size)
    validate_binary("completion_indicator", completion_indicator)
    return _equal(completion_indicator * (total_download - output_size), 0.0, tolerance)


def check_equation_8_preemption_before_full_download(
    total_download: float, output_size: float, completion_indicator: int
) -> bool:
    _nonnegative("total_download", total_download)
    _positive("output_size", output_size)
    validate_binary("completion_indicator", completion_indicator)
    return total_download / output_size < 1 + completion_indicator


def check_equation_9_upload_before_computation(
    schedule: TaskSchedule,
    *,
    input_size: float,
    computation_requirement: float,
    tolerance: float = 0.0,
) -> bool:
    _positive("input_size", input_size)
    _positive("computation_requirement", computation_requirement)
    _nonnegative("tolerance", tolerance)
    return all(
        schedule.cumulative_through("computation", slot)
        <= schedule.cumulative_through("upload", slot) / input_size * computation_requirement
        + tolerance
        for slot in range(1, schedule.horizon + 1)
    )


def check_equation_10_computation_before_download(
    schedule: TaskSchedule,
    *,
    computation_requirement: float,
    output_size: float,
    tolerance: float = 0.0,
) -> bool:
    _positive("computation_requirement", computation_requirement)
    _positive("output_size", output_size)
    _nonnegative("tolerance", tolerance)
    return all(
        schedule.cumulative_through("download", slot)
        <= schedule.cumulative_through("computation", slot) / computation_requirement * output_size
        + tolerance
        for slot in range(1, schedule.horizon + 1)
    )


def check_equation_11_stage_order(
    upload_end: int, processing_end: int, download_end: int, deadline: int
) -> bool:
    for name, value in (
        ("upload_end", upload_end),
        ("processing_end", processing_end),
        ("download_end", download_end),
        ("deadline", deadline),
    ):
        ensure_positive_integer(name, value)
    return upload_end <= processing_end <= download_end <= deadline


def check_equations_12_to_14_minimum_stage_spans(
    upload_end: int, processing_end: int, download_end: int
) -> bool:
    return all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 1
        for value in (upload_end, processing_end, download_end)
    )


def check_equation_15_storage_capacity(
    cumulative_upload_by_task: Mapping[str, float],
    assignment_by_task: Mapping[str, int],
    theta_by_task: Mapping[str, int],
    capacity: float,
    *,
    tolerance: float = 0.0,
) -> bool:
    _nonnegative("capacity", capacity)
    _nonnegative("tolerance", tolerance)
    if set(cumulative_upload_by_task) != set(assignment_by_task) or set(
        cumulative_upload_by_task
    ) != set(theta_by_task):
        raise ValueError("storage constraint mappings must have identical task IDs")
    total = 0.0
    for task_id, uploaded in cumulative_upload_by_task.items():
        _nonnegative(f"uploaded[{task_id}]", uploaded)
        validate_binary(f"assignment[{task_id}]", assignment_by_task[task_id])
        validate_binary(f"theta[{task_id}]", theta_by_task[task_id])
        total += uploaded * assignment_by_task[task_id] * theta_by_task[task_id]
    return total <= capacity + tolerance


def check_slot_capacity(
    allocation_by_task: Mapping[str, float],
    assignment_by_task: Mapping[str, int],
    capacity: float,
    *,
    tolerance: float = 0.0,
) -> bool:
    """Shared literal form of equations (16), (17) and (18) for one server/slot."""

    _nonnegative("capacity", capacity)
    _nonnegative("tolerance", tolerance)
    if set(allocation_by_task) != set(assignment_by_task):
        raise ValueError("allocation and assignment mappings must have identical task IDs")
    total = 0.0
    for task_id, allocation in allocation_by_task.items():
        _nonnegative(f"allocation[{task_id}]", allocation)
        validate_binary(f"assignment[{task_id}]", assignment_by_task[task_id])
        total += allocation * assignment_by_task[task_id]
    return total <= capacity + tolerance


def check_equation_16_computation_capacity(
    computation_by_task: Mapping[str, float],
    assignment_by_task: Mapping[str, int],
    capacity: float,
    *,
    tolerance: float = 0.0,
) -> bool:
    return check_slot_capacity(
        computation_by_task, assignment_by_task, capacity, tolerance=tolerance
    )


def check_equation_17_upload_capacity(
    upload_by_task: Mapping[str, float],
    assignment_by_task: Mapping[str, int],
    capacity: float,
    *,
    tolerance: float = 0.0,
) -> bool:
    return check_slot_capacity(upload_by_task, assignment_by_task, capacity, tolerance=tolerance)


def check_equation_18_download_capacity(
    download_by_task: Mapping[str, float],
    assignment_by_task: Mapping[str, int],
    capacity: float,
    *,
    tolerance: float = 0.0,
) -> bool:
    return check_slot_capacity(download_by_task, assignment_by_task, capacity, tolerance=tolerance)


def check_equation_19_single_assignment(assignments: Sequence[int]) -> bool:
    return sum(_validate_assignments(assignments)) <= 1


def check_equation_20_assignment_domain(value: int) -> bool:
    try:
        validate_binary("assignment", value)
    except (TypeError, ValueError):
        return False
    return True


def check_equation_21_completion_domain(value: int) -> bool:
    try:
        validate_binary("completion_indicator", value)
    except (TypeError, ValueError):
        return False
    return True


def literal_activity_slots(
    activity: ActivityKind,
    *,
    arrival_slot: int,
    stage_end_offset: int,
    stop_offset: int,
    horizon: int,
) -> frozenset[int]:
    """Return the exact 1-based active set printed in equations (22)-(27)."""

    if not isinstance(activity, ActivityKind):
        raise TypeError("activity must be an ActivityKind")
    for name, value in (
        ("arrival_slot", arrival_slot),
        ("stage_end_offset", stage_end_offset),
        ("stop_offset", stop_offset),
        ("horizon", horizon),
    ):
        ensure_positive_integer(name, value)
    start_shift = {
        ActivityKind.UPLOAD: 0,
        ActivityKind.COMPUTATION: 1,
        ActivityKind.DOWNLOAD: 2,
    }[activity]
    first = arrival_slot + start_shift
    last = arrival_slot + min(stage_end_offset, stop_offset) - 1
    return frozenset(slot for slot in range(first, last + 1) if 1 <= slot <= horizon)


def check_equations_22_to_27_activity_window(
    values: Sequence[float], allowed_slots: frozenset[int]
) -> bool:
    """Require zero outside and non-negative values inside a printed activity window."""

    normalized = tuple(values)
    if not normalized:
        raise ValueError("values must contain at least one horizon slot")
    if any(slot < 1 or slot > len(normalized) for slot in allowed_slots):
        raise ValueError("allowed_slots must be inside the 1-based horizon")
    for slot, value in enumerate(normalized, start=1):
        _finite(f"value[{slot}]", value)
        if slot in allowed_slots:
            if value < 0:
                return False
        elif value != 0:
            return False
    return True


def check_equation_28_stop_domain(stop_offset: int, download_end: int) -> bool:
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (stop_offset, download_end)
    ):
        return False
    return 1 <= stop_offset <= download_end


def check_equation_29_completion_stop_relation(
    completion_indicator: int, stop_offset: int, download_end: int
) -> bool:
    if not check_equation_21_completion_domain(completion_indicator):
        return False
    if not check_equation_28_stop_domain(stop_offset, download_end):
        return False
    return completion_indicator * (stop_offset - download_end) == 0


def check_equation_30_preemption_before_completion(
    completion_indicator: int, stop_offset: int, download_end: int
) -> bool:
    if not check_equation_21_completion_domain(completion_indicator):
        return False
    if not check_equation_28_stop_domain(stop_offset, download_end):
        return False
    return stop_offset / download_end < 1 + completion_indicator


def derive_equation_31_storage_indicator(computation: Sequence[float]) -> tuple[int, ...]:
    """Derive literal θ between the first and last positive computation slots.

    Equation (31) applies ``min`` and ``max`` to the set of positive-computation
    slots but defines no empty-set behavior. The empty case therefore raises an
    unresolved-decision error rather than inventing an all-zero indicator.
    """

    values = tuple(computation)
    if not values:
        raise ValueError("computation must contain at least one slot")
    for index, value in enumerate(values, start=1):
        _nonnegative(f"computation[{index}]", value)
    span = TaskSchedule.positive_span(values)
    if span is None:
        raise UnresolvedDecisionError(
            "equation (31) does not define theta when no computation slot is positive"
        )
    first, last = span
    return tuple(1 if first <= slot <= last else 0 for slot in range(1, len(values) + 1))
