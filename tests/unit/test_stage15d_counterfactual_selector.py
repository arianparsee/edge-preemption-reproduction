from __future__ import annotations

import random

import pytest

from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.diagnostics.ga_counterfactual import (
    RNG_PRIMITIVES,
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 10, utility, ResourceVector(demand, demand, demand, demand))


def _tasks() -> tuple[Task, ...]:
    return (
        _task("task-a", 3.0, 15.0),
        _task("task-b", 2.0, 10.0),
        _task("task-c", 4.0, 8.0),
        _task("task-d", 1.0, 4.0),
    )


def test_baseline_control_matches_official_selector_and_rng_state() -> None:
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)
    official = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=701))
    control = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=701), CounterfactualVariant.BASELINE_CONTROL
    )
    random.seed(991)
    caller_state = random.getstate()

    official_selected = official.select(capacity=capacity, tasks=_tasks())
    control_selected = control.select(capacity=capacity, tasks=_tasks())

    assert control_selected == official_selected
    assert control._rng.getstate() == official._rng.getstate()  # noqa: SLF001
    assert random.getstate() == caller_state


@pytest.mark.parametrize(
    "variant",
    [
        CounterfactualVariant.FIXED_PENALTY,
        CounterfactualVariant.INITIAL_POPULATION_REPAIR,
        CounterfactualVariant.OFFSPRING_REPAIR,
    ],
)
def test_variant_preserves_fixed_selector_call_rng_shape(
    variant: CounterfactualVariant,
) -> None:
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)
    control = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=811), CounterfactualVariant.BASELINE_CONTROL
    )
    changed = CounterfactualKnapsackSelector(PyeasygaConfig(seed=811), variant)

    control.select(capacity=capacity, tasks=_tasks())
    changed.select(capacity=capacity, tasks=_tasks())

    assert changed.primitive_counts() == control.primitive_counts()
    assert changed._rng.getstate() == control._rng.getstate()  # noqa: SLF001
    assert changed.call_observations()[0].rng_counts == control.call_observations()[0].rng_counts
    assert set(changed.primitive_counts()) == set(RNG_PRIMITIVES)


@pytest.mark.parametrize(
    "variant",
    [
        CounterfactualVariant.FIXED_PENALTY,
        CounterfactualVariant.INITIAL_POPULATION_REPAIR,
        CounterfactualVariant.OFFSPRING_REPAIR,
    ],
)
def test_variant_preserves_multi_call_shape_including_uniform_choice(
    variant: CounterfactualVariant,
) -> None:
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)
    control = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=887), CounterfactualVariant.BASELINE_CONTROL
    )
    changed = CounterfactualKnapsackSelector(PyeasygaConfig(seed=887), variant)

    control.select(capacity=capacity, tasks=_tasks())
    changed.select(capacity=capacity, tasks=_tasks())
    control_choice = control.choose_uniform(("server-a", "server-b", "server-c"))
    changed_choice = changed.choose_uniform(("server-a", "server-b", "server-c"))
    control.select(capacity=capacity, tasks=_tasks())
    changed.select(capacity=capacity, tasks=_tasks())

    assert changed_choice == control_choice
    assert changed.primitive_counts() == control.primitive_counts()
    assert changed._rng.getstate() == control._rng.getstate()  # noqa: SLF001
    assert changed.call_observations()[0].rng_counts == control.call_observations()[0].rng_counts
    assert changed.call_observations()[1].rng_counts == control.call_observations()[1].rng_counts


def test_zero_and_single_candidate_paths_consume_no_random_primitive() -> None:
    selector = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=907), CounterfactualVariant.INITIAL_POPULATION_REPAIR
    )
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)

    assert selector.select(capacity=capacity, tasks=()) == ()
    assert selector.select(capacity=capacity, tasks=(_task("task-a", 1.0, 1.0),)) == (
        "task-a",
    )

    assert all(value == 0 for value in selector.primitive_counts().values())
    assert [row.call_kind for row in selector.call_observations()] == [
        "empty",
        "single_candidate",
    ]


@pytest.mark.parametrize(
    "variant, repair_field",
    [
        (CounterfactualVariant.INITIAL_POPULATION_REPAIR, "initial_chromosomes_repaired"),
        (CounterfactualVariant.OFFSPRING_REPAIR, "offspring_repaired"),
    ],
)
def test_repair_variants_record_repairs_without_exposing_bits(
    variant: CounterfactualVariant, repair_field: str
) -> None:
    selector = CounterfactualKnapsackSelector(PyeasygaConfig(seed=1013), variant)
    capacity = ResourceVector(1.0, 1.0, 1.0, 1.0)
    selector.select(capacity=capacity, tasks=_tasks())

    summary = selector.counterfactual_summary()
    repair_count = summary[repair_field]
    assert isinstance(repair_count, int)
    assert repair_count > 0
    assert summary["task_identifiers_recorded"] is False
    assert summary["chromosome_bits_recorded"] is False


def test_fixed_penalty_rejects_negative_utility_without_rng_draw() -> None:
    selector = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1103), CounterfactualVariant.FIXED_PENALTY
    )
    tasks = (_task("task-a", 1.0, -1.0), _task("task-b", 1.0, 2.0))

    with pytest.raises(ValueError, match="finite non-negative"):
        selector.select(capacity=ResourceVector(2.0, 2.0, 2.0, 2.0), tasks=tasks)

    assert all(value == 0 for value in selector.primitive_counts().values())


def test_identical_variant_replay_is_exact() -> None:
    capacity = ResourceVector(5.0, 5.0, 5.0, 5.0)
    first = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1217), CounterfactualVariant.OFFSPRING_REPAIR
    )
    second = CounterfactualKnapsackSelector(
        PyeasygaConfig(seed=1217), CounterfactualVariant.OFFSPRING_REPAIR
    )

    first_result = first.select(capacity=capacity, tasks=_tasks())
    second_result = second.select(capacity=capacity, tasks=_tasks())

    assert first_result == second_result
    assert first.call_observations() == second.call_observations()
    assert first.counterfactual_summary() == second.counterfactual_summary()
    assert first._rng.getstate() == second._rng.getstate()  # noqa: SLF001
