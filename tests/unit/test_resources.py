import math

import pytest

from edge_reproduction.models.resources import ResourceVector


def test_zero_vector_is_valid() -> None:
    assert ResourceVector.zero().is_zero()


@pytest.mark.parametrize("invalid", [-1.0, math.inf, -math.inf, math.nan])
def test_invalid_components_are_rejected(invalid: float) -> None:
    with pytest.raises(ValueError):
        ResourceVector(invalid, 1.0, 1.0, 1.0)


def test_boolean_component_is_rejected() -> None:
    with pytest.raises(TypeError):
        ResourceVector(True, 1.0, 1.0, 1.0)


def test_fit_is_component_wise() -> None:
    demand = ResourceVector(2.0, 3.0, 4.0, 5.0)
    capacity = ResourceVector(2.0, 3.0, 4.0, 5.0)
    too_small_in_one_dimension = ResourceVector(2.0, 3.0, 3.9, 5.0)

    assert demand.fits_within(capacity)
    assert not demand.fits_within(too_small_in_one_dimension)


def test_add_and_subtract_round_trip() -> None:
    left = ResourceVector(1.0, 2.0, 3.0, 4.0)
    right = ResourceVector(4.0, 3.0, 2.0, 1.0)

    total = left + right

    assert total == ResourceVector(5.0, 5.0, 5.0, 5.0)
    assert total.subtract(right) == left


def test_subtraction_rejects_capacity_underflow() -> None:
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)
    demand = ResourceVector(1.0, 1.1, 1.0, 1.0)

    with pytest.raises(ValueError, match="negative component"):
        capacity.subtract(demand)


def test_tolerance_is_explicit_and_normalizes_small_underflow() -> None:
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)
    demand = ResourceVector(1.0 + 1e-12, 1.0, 1.0, 1.0)

    assert capacity.subtract(demand, tolerance=1e-9).storage == 0.0
