import math
import sys

import pytest

from edge_reproduction.algorithms.pricing import (
    algorithm_one_congestion,
    algorithm_one_congestion_factor,
    fit_price,
    impossible_price,
    normalized_congestion,
    preemption_price,
    utility_time_percentile,
)
from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.enums import CongestionPriceSemantics
from edge_reproduction.models.resources import ResourceVector


def test_fit_price_has_explicit_ten_percent_discount() -> None:
    assert fit_price(100.0) == 90.0


def test_preemption_price_preserves_prose_and_algorithm_one_difference() -> None:
    prose = preemption_price(
        100.0,
        percentile=0.8,
        congestion=0.2,
        semantics=CongestionPriceSemantics.PROSE,
    )
    algorithm = preemption_price(
        100.0,
        percentile=0.8,
        congestion=0.2,
        semantics=CongestionPriceSemantics.ALGORITHM_ONE,
    )

    assert prose == pytest.approx(97.5)
    assert algorithm == pytest.approx(96.0)


def test_assump_003_congestion_covers_zero_clipping_and_four_dimensions() -> None:
    demand = ResourceVector(0.0, 5.0, 4.0, 10.0)
    residual = ResourceVector(0.0, 10.0, 2.0, 0.0)

    congestion = normalized_congestion(demand, residual)

    assert congestion == pytest.approx((0.0 + 0.5 + 1.0 + 1.0) / 4.0)
    assert algorithm_one_congestion_factor(congestion) == pytest.approx(0.009375)


def test_assump_003_checks_total_capacity_before_congestion_pricing() -> None:
    demand = ResourceVector(11.0, 1.0, 1.0, 1.0)
    residual = ResourceVector.zero()
    capacity = ResourceVector(10.0, 10.0, 10.0, 10.0)

    assert algorithm_one_congestion(demand, residual, capacity) is None


def test_assump_003_algorithm_one_expression_is_the_approved_default() -> None:
    assert preemption_price(100.0, percentile=0.8, congestion=0.2) == pytest.approx(96.0)


def test_preemption_discount_weight_cap_is_enforced() -> None:
    with pytest.raises(ValueError, match="not to exceed 0.1"):
        preemption_price(
            100.0,
            percentile=0.5,
            congestion=0.5,
            percentile_weight=0.06,
            congestion_weight=0.05,
            semantics=CongestionPriceSemantics.PROSE,
        )


def test_normalized_price_inputs_are_validated() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        preemption_price(
            100.0,
            percentile=1.1,
            congestion=0.5,
            semantics=CongestionPriceSemantics.PROSE,
        )


def test_assump_007_impossible_price_is_the_next_float_above_utility() -> None:
    assert impossible_price(100.0) == math.nextafter(100.0, math.inf)
    assert impossible_price(100.0) > 100.0
    assert impossible_price(-100.0) > -100.0


def test_assump_007_fails_fast_when_nextafter_is_not_finite() -> None:
    with pytest.raises(UnresolvedDecisionError, match="non-finite"):
        impossible_price(sys.float_info.max)


def test_assump_008_empty_percentile_is_zero() -> None:
    assert (
        utility_time_percentile(
            new_utility=10.0,
            new_time_remaining=1.0,
            current_utility_time_pairs=(),
        )
        == 0.0
    )


def test_assump_008_percentile_counts_only_strictly_lower_ratios() -> None:
    percentile = utility_time_percentile(
        new_utility=10.0,
        new_time_remaining=1.0,
        current_utility_time_pairs=((5.0, 1.0), (10.0, 1.0), (15.0, 1.0)),
    )

    assert percentile == pytest.approx(1.0 / 3.0)


def test_assump_008_percentile_can_reach_one() -> None:
    assert utility_time_percentile(
        new_utility=20.0,
        new_time_remaining=1.0,
        current_utility_time_pairs=((5.0, 1.0), (10.0, 1.0)),
    ) == pytest.approx(1.0)
