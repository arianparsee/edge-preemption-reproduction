from collections.abc import Mapping, Sequence
from typing import Protocol

import pytest

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.enums import ActivityKind, AssignmentFlowSemantics
from edge_reproduction.models.schedule import TaskSchedule
from edge_reproduction.optimization.constraints import (
    check_equation_2_upload_upper_bound,
    check_equation_3_completed_upload,
    check_equation_4_computation_upper_bound,
    check_equation_5_completed_computation,
    check_equation_6_download_upper_bound,
    check_equation_7_completed_download,
    check_equation_8_preemption_before_full_download,
    check_equation_9_upload_before_computation,
    check_equation_10_computation_before_download,
    check_equation_11_stage_order,
    check_equation_15_storage_capacity,
    check_equation_16_computation_capacity,
    check_equation_17_upload_capacity,
    check_equation_18_download_capacity,
    check_equation_19_single_assignment,
    check_equation_20_assignment_domain,
    check_equation_21_completion_domain,
    check_equation_28_stop_domain,
    check_equation_29_completion_stop_relation,
    check_equation_30_preemption_before_completion,
    check_equations_12_to_14_minimum_stage_spans,
    check_equations_22_to_27_activity_window,
    derive_equation_31_storage_indicator,
    literal_activity_slots,
)


class UpperBoundValidator(Protocol):
    def __call__(
        self,
        total: float,
        requirement: float,
        assignments: Sequence[int],
        *,
        semantics: AssignmentFlowSemantics,
        tolerance: float = 0.0,
    ) -> bool: ...


class CompletedFlowValidator(Protocol):
    def __call__(
        self,
        total: float,
        requirement: float,
        assignments: Sequence[int],
        completion_indicator: int,
        *,
        semantics: AssignmentFlowSemantics,
        tolerance: float = 0.0,
    ) -> bool: ...


class SlotCapacityValidator(Protocol):
    def __call__(
        self,
        allocation_by_task: Mapping[str, float],
        assignment_by_task: Mapping[str, int],
        capacity: float,
        *,
        tolerance: float = 0.0,
    ) -> bool: ...


@pytest.mark.parametrize(
    "validator",
    [
        check_equation_2_upload_upper_bound,
        check_equation_4_computation_upper_bound,
        check_equation_6_download_upper_bound,
    ],
)
def test_equations_2_4_6_positive_and_over_requirement_negative(
    validator: UpperBoundValidator,
) -> None:
    check = validator  # keep the parameterized function visible in failure output
    assert check(4.0, 4.0, (1,), semantics=AssignmentFlowSemantics.LITERAL_ALL_SERVERS)
    assert not check(4.1, 4.0, (1,), semantics=AssignmentFlowSemantics.LITERAL_ALL_SERVERS)


def test_equations_2_to_6_preserve_quantifier_inconsistency_without_default() -> None:
    assignments = (1, 0)

    assert not check_equation_2_upload_upper_bound(
        4.0,
        4.0,
        assignments,
        semantics=AssignmentFlowSemantics.LITERAL_ALL_SERVERS,
    )
    assert check_equation_2_upload_upper_bound(
        4.0,
        4.0,
        assignments,
        semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )


@pytest.mark.parametrize(
    "validator",
    [check_equation_3_completed_upload, check_equation_5_completed_computation],
)
def test_equations_3_and_5_completed_exact_and_partial(
    validator: CompletedFlowValidator,
) -> None:
    check = validator
    assert check(
        4.0,
        4.0,
        (1,),
        1,
        semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )
    assert not check(
        3.0,
        4.0,
        (1,),
        1,
        semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )
    assert check(
        3.0,
        4.0,
        (1,),
        0,
        semantics=AssignmentFlowSemantics.SELECTED_SERVER_ONLY,
    )


def test_equations_7_and_8_completed_and_preempted_download_boundaries() -> None:
    assert check_equation_7_completed_download(2.0, 2.0, 1)
    assert not check_equation_7_completed_download(1.0, 2.0, 1)
    assert check_equation_7_completed_download(1.0, 2.0, 0)
    assert check_equation_8_preemption_before_full_download(1.0, 2.0, 0)
    assert not check_equation_8_preemption_before_full_download(2.0, 2.0, 0)


def test_equations_9_and_10_pipeline_precedence_positive_and_negative() -> None:
    valid = TaskSchedule((6.0, 4.0), (6.0, 4.0), (3.0, 2.0))
    compute_ahead = TaskSchedule((6.0, 4.0), (6.1, 3.9), (3.0, 2.0))
    download_ahead = TaskSchedule((6.0, 4.0), (6.0, 4.0), (3.1, 1.9))

    assert check_equation_9_upload_before_computation(
        valid, input_size=10.0, computation_requirement=10.0
    )
    assert not check_equation_9_upload_before_computation(
        compute_ahead, input_size=10.0, computation_requirement=10.0
    )
    assert check_equation_10_computation_before_download(
        valid, computation_requirement=10.0, output_size=5.0
    )
    assert not check_equation_10_computation_before_download(
        download_ahead, computation_requirement=10.0, output_size=5.0
    )


def test_equation_11_stage_order_positive_and_negative() -> None:
    assert check_equation_11_stage_order(1, 2, 2, 3)
    assert not check_equation_11_stage_order(2, 1, 2, 3)


@pytest.mark.parametrize("invalid", [(0, 1, 1), (1, 0, 1), (1, 1, 0)])
def test_each_of_equations_12_to_14_has_positive_and_negative_case(
    invalid: tuple[int, int, int],
) -> None:
    assert check_equations_12_to_14_minimum_stage_spans(1, 1, 1)
    assert not check_equations_12_to_14_minimum_stage_spans(*invalid)


def test_equation_15_storage_capacity_positive_and_negative() -> None:
    uploaded = {"a": 3.0, "b": 2.0}
    assigned = {"a": 1, "b": 1}
    theta = {"a": 1, "b": 1}

    assert check_equation_15_storage_capacity(uploaded, assigned, theta, 5.0)
    assert not check_equation_15_storage_capacity(uploaded, assigned, theta, 4.9)


@pytest.mark.parametrize(
    "validator",
    [
        check_equation_16_computation_capacity,
        check_equation_17_upload_capacity,
        check_equation_18_download_capacity,
    ],
)
def test_each_of_equations_16_to_18_has_positive_and_negative_case(
    validator: SlotCapacityValidator,
) -> None:
    allocations = {"a": 2.0, "b": 3.0}
    assignments = {"a": 1, "b": 1}

    assert validator(allocations, assignments, 5.0)
    assert not validator(allocations, assignments, 4.9)


def test_equations_19_to_21_assignment_and_binary_domains() -> None:
    assert check_equation_19_single_assignment((1, 0, 0))
    assert not check_equation_19_single_assignment((1, 1, 0))
    assert check_equation_20_assignment_domain(0)
    assert not check_equation_20_assignment_domain(2)
    assert check_equation_21_completion_domain(1)
    assert not check_equation_21_completion_domain(0.5)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("activity", "expected"),
    [
        (ActivityKind.UPLOAD, frozenset({2, 3, 4})),
        (ActivityKind.COMPUTATION, frozenset({3, 4})),
        (ActivityKind.DOWNLOAD, frozenset({4})),
    ],
)
def test_equations_22_to_27_literal_windows(
    activity: ActivityKind, expected: frozenset[int]
) -> None:
    allowed = literal_activity_slots(
        activity, arrival_slot=2, stage_end_offset=3, stop_offset=4, horizon=6
    )

    assert allowed == expected
    valid = tuple(1.0 if slot in allowed else 0.0 for slot in range(1, 7))
    invalid = (1.0, *valid[1:])
    negative_inside = tuple(-1.0 if slot in allowed else 0.0 for slot in range(1, 7))
    assert check_equations_22_to_27_activity_window(valid, allowed)
    assert not check_equations_22_to_27_activity_window(invalid, allowed)
    assert not check_equations_22_to_27_activity_window(negative_inside, allowed)


def test_equations_28_to_30_preemption_timing_boundaries() -> None:
    assert check_equation_28_stop_domain(3, 4)
    assert not check_equation_28_stop_domain(5, 4)
    assert check_equation_29_completion_stop_relation(1, 4, 4)
    assert not check_equation_29_completion_stop_relation(1, 3, 4)
    assert check_equation_30_preemption_before_completion(0, 3, 4)
    assert not check_equation_30_preemption_before_completion(0, 4, 4)


def test_equation_31_indicator_and_undefined_empty_set() -> None:
    assert derive_equation_31_storage_indicator((0.0, 1.0, 0.0, 2.0, 0.0)) == (
        0,
        1,
        1,
        1,
        0,
    )
    with pytest.raises(UnresolvedDecisionError, match="no computation"):
        derive_equation_31_storage_indicator((0.0, 0.0))
