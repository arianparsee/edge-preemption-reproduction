"""Small runtime validators shared by immutable domain records."""

from math import isfinite


def ensure_identifier(name: str, value: str) -> None:
    """Require a non-empty, whitespace-trimmed identifier."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be non-empty and must not have surrounding whitespace")


def ensure_nonnegative_integer(name: str, value: int) -> None:
    """Require an integer greater than or equal to zero, excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def ensure_positive_integer(name: str, value: int) -> None:
    """Require an integer greater than zero, excluding booleans."""

    ensure_nonnegative_integer(name, value)
    if value == 0:
        raise ValueError(f"{name} must be positive")


def ensure_finite_number(name: str, value: float) -> None:
    """Require a finite real number, excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def ensure_unique[T](name: str, values: tuple[T, ...]) -> None:
    """Require hashable values to be unique while preserving their order."""

    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")
