import random
from typing import Any

import pytest

from edge_reproduction.algorithms.genetic_knapsack import (
    KGPyeasygaConfig,
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack import ExactUtilityKnapsackSelector
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 5, utility, ResourceVector(demand, demand, demand, demand))


def test_assump_015_requires_seed_and_rejects_auxiliary_population_in_official_config() -> None:
    with pytest.raises(TypeError, match="seed"):
        PyeasygaConfig()  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="population_size"):
        PyeasygaConfig(seed=1, population_size=50, tournament_size=5)


def test_assump_015_metadata_records_every_ga_setting() -> None:
    metadata = PyeasygaConfig(seed=20240810).as_metadata()

    assert metadata == {
        "ga.library": "pyeasyga",
        "ga.library_version": "0.3.1",
        "ga.population_size": "200",
        "ga.tournament_size": "20",
        "ga.generations": "50",
        "ga.seed": "20240810",
        "ga.crossover_probability": "0.8",
        "ga.mutation_probability": "0.2",
        "ga.elitism": "true",
        "ga.maximise_fitness": "true",
        "ga.selection_operator": "tournament",
        "ga.crossover_operator": "one_point",
        "ga.mutation_operator": "one_bit_flip",
        "ga.chromosome_representation": "binary_bit_array",
        "ga.infeasible_fitness": "0.0",
        "ga.provenance": "pyeasyga_0.3.1_audit_and_ASSUMP-013_ASSUMP-015",
    }


def test_assump_041_kg_configuration_is_separate_and_records_30_generations() -> None:
    with pytest.raises(TypeError, match="seed"):
        KGPyeasygaConfig()  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="generations"):
        KGPyeasygaConfig(seed=1, generations=50)

    metadata = KGPyeasygaConfig(seed=20240812).as_metadata()
    assert metadata["ga.population_size"] == "200"
    assert metadata["ga.tournament_size"] == "20"
    assert metadata["ga.generations"] == "30"
    assert metadata["ga.seed"] == "20240812"
    assert metadata["ga.provenance"] == "pyeasyga_0.3.1_audit_and_ASSUMP-041"
    assert PyeasygaConfig(seed=20240812).generations == 50


def test_single_candidate_compatibility_avoids_pyeasyga_crossover_crash() -> None:
    selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=7))
    candidate = task("only", 1.0, 2.0)
    assert selector.select(capacity=ResourceVector(1.0, 1.0, 1.0, 1.0), tasks=[candidate]) == (
        "only",
    )
    assert selector.select(capacity=ResourceVector.zero(), tasks=[candidate]) == ()


def test_single_candidate_zero_utility_tie_still_fails_fast() -> None:
    selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=7))
    candidate = task("only", 1.0, 0.0)
    with pytest.raises(StateValidationError, match="unresolved"):
        selector.select(capacity=ResourceVector(1.0, 1.0, 1.0, 1.0), tasks=[candidate])


def test_official_ga_matches_exact_auxiliary_on_unique_small_optimum() -> None:
    tasks = (
        task("a", 5.0, 20.0),
        task("b", 3.0, 12.0),
        task("c", 4.0, 11.0),
        task("impossible", 11.0, 30.0),
    )
    capacity = ResourceVector(8.0, 8.0, 8.0, 8.0)

    ga_selected = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=20240810)).select(
        capacity=capacity,
        tasks=tuple(reversed(tasks)),
    )
    exact_selected = ExactUtilityKnapsackSelector().select(capacity=capacity, tasks=tasks)

    assert ga_selected == exact_selected == ("a", "b")


def test_fixed_seed_is_reproducible_and_does_not_mutate_global_random_state() -> None:
    tasks = (
        task("a", 5.0, 20.0),
        task("b", 3.0, 12.0),
        task("c", 4.0, 11.0),
    )
    capacity = ResourceVector(8.0, 8.0, 8.0, 8.0)
    random.seed(77)
    caller_state = random.getstate()

    first = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=9)).select(
        capacity=capacity, tasks=tasks
    )
    assert random.getstate() == caller_state
    second = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=9)).select(
        capacity=capacity, tasks=tasks
    )

    assert first == second
    assert random.getstate() == caller_state


def test_assump_014_uniform_tie_choice_uses_the_same_seeded_run_stream() -> None:
    first = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=314))
    second = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=314))

    first_choices = tuple(first.choose_uniform(("server-a", "server-b")) for _ in range(8))
    second_choices = tuple(second.choose_uniform(("server-a", "server-b")) for _ in range(8))

    assert first_choices == second_choices
    assert set(first_choices) <= {"server-a", "server-b"}


def test_assump_043_kg_tie_choice_is_seeded_counted_and_requires_canonical_tie() -> None:
    first = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=314))
    second = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=314))

    first_choices = tuple(
        first.choose_kg_equal_minimum_server(("server-a", "server-b"))
        for _ in range(8)
    )
    second_choices = tuple(
        second.choose_kg_equal_minimum_server(("server-a", "server-b"))
        for _ in range(8)
    )

    assert first_choices == second_choices
    assert first.runtime_metadata()["client.equal_minimum_price_ties"] == "8"
    with pytest.raises(ValueError, match="at least two"):
        first.choose_kg_equal_minimum_server(("server-a",))
    with pytest.raises(ValueError, match="unique and sorted"):
        first.choose_kg_equal_minimum_server(("server-b", "server-a"))
    assert first.runtime_metadata()["client.equal_minimum_price_ties"] == "8"


class _FakeGeneticAlgorithm:
    """Minimal pyeasyga test double returning a controlled best chromosome."""

    result: tuple[float, list[int]] = (0.0, [1, 1])

    def __init__(self, data: list[Task], **_: Any) -> None:
        self.data = data
        self.tournament_size = 0
        self.fitness_function: Any = None

    def run(self) -> None:
        return None

    def best_individual(self) -> tuple[float, list[int]]:
        return self.result


def test_assump_042_repairs_only_infeasible_zero_fitness_best_and_counts_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "edge_reproduction.algorithms.genetic_knapsack.pyeasyga.GeneticAlgorithm",
        _FakeGeneticAlgorithm,
    )
    _FakeGeneticAlgorithm.result = (0.0, [1, 1])
    selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=11))
    candidates = (task("a", 0.75, 2.0), task("b", 0.75, 3.0))

    selected = selector.select(
        capacity=ResourceVector(1.0, 1.0, 1.0, 1.0), tasks=candidates
    )

    assert selected == ()
    assert selector.zero_fitness_feasibility_repairs == 1
    assert selector.runtime_metadata()["ga.zero_fitness_feasibility_repairs"] == "1"


def test_assump_042_does_not_mask_infeasible_nonzero_fitness_best(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "edge_reproduction.algorithms.genetic_knapsack.pyeasyga.GeneticAlgorithm",
        _FakeGeneticAlgorithm,
    )
    _FakeGeneticAlgorithm.result = (1.0, [1, 1])
    selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=11))
    candidates = (task("a", 0.75, 2.0), task("b", 0.75, 3.0))

    with pytest.raises(StateValidationError, match="nonzero fitness"):
        selector.select(
            capacity=ResourceVector(1.0, 1.0, 1.0, 1.0), tasks=candidates
        )
    assert selector.zero_fitness_feasibility_repairs == 0


def test_assump_042_leaves_feasible_zero_fitness_best_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "edge_reproduction.algorithms.genetic_knapsack.pyeasyga.GeneticAlgorithm",
        _FakeGeneticAlgorithm,
    )
    _FakeGeneticAlgorithm.result = (0.0, [0, 0])
    selector = PyeasygaUtilityKnapsackSelector(KGPyeasygaConfig(seed=11))

    assert selector.select(
        capacity=ResourceVector(1.0, 1.0, 1.0, 1.0),
        tasks=(task("a", 0.75, 2.0), task("b", 0.75, 3.0)),
    ) == ()
    assert selector.zero_fitness_feasibility_repairs == 0
