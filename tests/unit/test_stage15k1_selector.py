from __future__ import annotations

from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import InstrumentedKnapsackSelector
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def _tasks() -> tuple[Task, ...]:
    return tuple(
        Task(
            f"task-{index:02d}",
            0,
            10,
            float(index + 1),
            ResourceVector(2.0, 2.0, 2.0, 2.0),
        )
        for index in range(30)
    )


def test_round_one_matches_baseline_control_exactly() -> None:
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)
    control = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1543), CounterfactualVariant.BASELINE_CONTROL
    )
    changed = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1543),
        CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR,
    )
    control.set_diagnostic_round("round_1")
    changed.set_diagnostic_round("round_1")

    assert changed.select(capacity=capacity, tasks=_tasks()) == control.select(
        capacity=capacity, tasks=_tasks()
    )
    assert changed.primitive_counts() == control.primitive_counts()
    assert changed._rng.getstate() == control._rng.getstate()  # noqa: SLF001
    summary = changed.counterfactual_summary()
    assert summary["initial_chromosomes_repaired"] == 0
    assert summary["initial_bits_removed"] == 0


def test_round_two_repairs_initial_population_without_extra_rng_calls() -> None:
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)
    control = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1601), CounterfactualVariant.BASELINE_CONTROL
    )
    changed = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1601),
        CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR,
    )
    control.set_diagnostic_round("round_2")
    changed.set_diagnostic_round("round_2")

    control.select(capacity=capacity, tasks=_tasks())
    changed.select(capacity=capacity, tasks=_tasks())

    assert changed.primitive_counts() == control.primitive_counts()
    assert changed._rng.getstate() == control._rng.getstate()  # noqa: SLF001
    summary = changed.counterfactual_summary()
    assert int(summary["initial_chromosomes_repaired"]) > 0
    assert int(summary["initial_bits_removed"]) > 0
    assert summary["offspring_repaired"] == 0
    assert summary["repair_scope"] == "round_2_only"


def test_instrumented_call_order_applies_repair_only_to_round_two() -> None:
    delegate = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1667),
        CounterfactualVariant.ROUND_TWO_INITIAL_POPULATION_REPAIR,
    )
    selector = InstrumentedKnapsackSelector(
        delegate, server_count=1, diagnostic_stage="stage15k1"
    )
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)

    selector.select(capacity=capacity, tasks=_tasks())
    selector.select(capacity=capacity, tasks=_tasks())

    calls = delegate.call_observations()
    assert calls[0].initial_chromosomes_repaired == 0
    assert calls[0].initial_bits_removed == 0
    assert calls[1].initial_chromosomes_repaired > 0
    assert calls[1].initial_bits_removed > 0
