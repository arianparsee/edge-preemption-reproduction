"""Round-1 price calculations stated in Section V-A1."""

from math import inf, isfinite, nextafter

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.enums import CongestionPriceSemantics
from edge_reproduction.models.resources import ResourceVector


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _unit_interval(name: str, value: float) -> None:
    _finite(name, value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


def fit_price(utility: float) -> float:
    """Return the explicit 10%-discount price ``0.9 * utility``."""

    _finite("utility", utility)
    return float(0.9 * utility)


def normalized_congestion(demand: ResourceVector, residual: ResourceVector) -> float:
    """Return the ASSUMP-003 mean of four clipped demand/residual ratios.

    A zero demand contributes zero. A positive demand against zero residual
    contributes one. This function deliberately knows nothing about total server
    capacity; callers must use :func:`algorithm_one_congestion` when pricing.
    """

    if not isinstance(demand, ResourceVector):
        raise TypeError("demand must be a ResourceVector")
    if not isinstance(residual, ResourceVector):
        raise TypeError("residual must be a ResourceVector")

    shares: list[float] = []
    for resource_name in ("storage", "computation", "upload", "download"):
        requested = getattr(demand, resource_name)
        available = getattr(residual, resource_name)
        if requested == 0.0:
            shares.append(0.0)
        elif available == 0.0:
            shares.append(1.0)
        else:
            shares.append(min(requested / available, 1.0))
    return float(sum(shares) / len(shares))


def algorithm_one_congestion(
    demand: ResourceVector,
    residual: ResourceVector,
    total_capacity: ResourceVector,
) -> float | None:
    """Apply the ASSUMP-003 total-capacity guard before congestion.

    ``None`` identifies the paper's impossible branch. Its numerical price is
    still unspecified and therefore is not invented here.
    """

    if not isinstance(total_capacity, ResourceVector):
        raise TypeError("total_capacity must be a ResourceVector")
    if not demand.fits_within(total_capacity):
        return None
    return normalized_congestion(demand, residual)


def algorithm_one_congestion_factor(congestion: float) -> float:
    """Return the approved Algorithm-1 factor ``0.025 * (1-congestion)``."""

    _unit_interval("congestion", congestion)
    return float(0.025 * (1.0 - congestion))


def utility_time_percentile(
    *,
    new_utility: float,
    new_time_remaining: float,
    current_utility_time_pairs: tuple[tuple[float, float], ...],
) -> float:
    """Return the strict empirical percentile approved in ASSUMP-008."""

    from edge_reproduction.algorithms.feasibility import utility_time_ratio

    new_ratio = utility_time_ratio(new_utility, new_time_remaining)
    if not current_utility_time_pairs:
        return 0.0
    current_ratios = tuple(
        utility_time_ratio(utility, time_remaining)
        for utility, time_remaining in current_utility_time_pairs
    )
    lower_count = sum(ratio < new_ratio for ratio in current_ratios)
    result = lower_count / len(current_ratios)
    _unit_interval("percentile", result)
    return float(result)


def preemption_price(
    utility: float,
    *,
    percentile: float,
    congestion: float,
    percentile_weight: float = 0.025,
    congestion_weight: float = 0.025,
    semantics: CongestionPriceSemantics = CongestionPriceSemantics.ALGORITHM_ONE,
) -> float:
    """Calculate the Round-1 preemption price under an explicit interpretation.

    The approved reproduction default is the Algorithm-1 expression from
    ASSUMP-003. The prose alternative remains available only for discrepancy
    analysis. The two default weights are explicit in the paper.
    """

    _finite("utility", utility)
    _unit_interval("percentile", percentile)
    _unit_interval("congestion", congestion)
    _unit_interval("percentile_weight", percentile_weight)
    _unit_interval("congestion_weight", congestion_weight)
    if percentile_weight + congestion_weight > 0.1:
        raise ValueError("the paper requires total preemption discount weights not to exceed 0.1")
    if not isinstance(semantics, CongestionPriceSemantics):
        raise TypeError("semantics must be a CongestionPriceSemantics")

    congestion_value = (
        congestion if semantics is CongestionPriceSemantics.PROSE else 1.0 - congestion
    )
    discount = percentile_weight * percentile + congestion_weight * congestion_value
    return float(utility * (1.0 - discount))


def impossible_price(utility: float) -> float:
    """Return the ASSUMP-007 minimal finite float greater than utility."""

    _finite("utility", utility)
    price = nextafter(float(utility), inf)
    if not isfinite(price):
        raise UnresolvedDecisionError(
            "ASSUMP-007 nextafter sentinel is non-finite; no hidden fallback is allowed"
        )
    return price


def double_knapsack_violation(
    demand: ResourceVector,
    selected_subset_demand: ResourceVector,
    total_capacity: ResourceVector,
    *,
    scaling_factor: float,
) -> float:
    """Return the ASSUMP-012 four-resource extension of reference-[4] Eq. (11)."""

    if not isinstance(demand, ResourceVector):
        raise TypeError("demand must be a ResourceVector")
    if not isinstance(selected_subset_demand, ResourceVector):
        raise TypeError("selected_subset_demand must be a ResourceVector")
    if not isinstance(total_capacity, ResourceVector):
        raise TypeError("total_capacity must be a ResourceVector")
    _finite("scaling_factor", scaling_factor)
    if scaling_factor <= 0.0:
        raise ValueError("scaling_factor must be positive")

    ratios: list[float] = []
    for resource_name in ("storage", "computation", "upload", "download"):
        numerator = getattr(demand, resource_name) + getattr(selected_subset_demand, resource_name)
        denominator = getattr(total_capacity, resource_name)
        if denominator == 0.0:
            if numerator != 0.0:
                raise ValueError("positive violation demand cannot use zero total capacity")
            ratios.append(0.0)
        else:
            ratios.append(numerator / denominator)
    violation = 1.0 + scaling_factor * sum(ratios)
    if not isfinite(violation) or violation < 1.0:
        raise ValueError("violation must be finite and at least one")
    return float(violation)


def double_knapsack_round_one_price(
    utility: float,
    *,
    selected: bool,
    individually_feasible: bool,
    violation: float | None = None,
    alpha: float = 0.1,
) -> float:
    """Apply reference-[4] Case-3 R1 pricing with ASSUMP-011 branches."""

    _finite("utility", utility)
    _finite("alpha", alpha)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between zero and one")
    if selected:
        if not individually_feasible:
            raise ValueError("a selected task must be individually feasible")
        return float(utility * (1.0 - alpha))
    if not individually_feasible:
        return impossible_price(utility)
    if violation is None:
        raise ValueError("violation is required for a feasible non-selected task")
    _finite("violation", violation)
    if violation < 1.0:
        raise ValueError("violation must be at least one")
    discount = min(1.0 / violation, alpha / 2.0)
    return float(utility * (1.0 - discount))


def double_knapsack_round_two_price(utility: float, *, violation: float) -> float:
    """Return reference-[4] Case-3 accepted R2 price ``U - U/violation``."""

    _finite("utility", utility)
    _finite("violation", violation)
    if violation < 1.0:
        raise ValueError("violation must be at least one")
    return float(utility * (1.0 - 1.0 / violation))
