"""Single-factor auxiliary GA counterfactuals approved for Stage 15-D.

This module never replaces the official Pipeline DK selector.  It is imported
only by Stage-15D diagnostics and preserves the audited pyeasyga 0.3.1 random
call structure for any fixed candidate sequence.
"""

from __future__ import annotations

import copy
import random
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any

from pyeasyga import pyeasyga  # type: ignore[import-untyped]

from edge_reproduction.algorithms.genetic_knapsack import (
    GASelectionObservation,
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task

RNG_PRIMITIVES = (
    "choice",
    "getrandbits",
    "randint",
    "random",
    "randrange",
    "sample",
)


class CounterfactualVariant(StrEnum):
    """Approved Stage-15D selector modes.

    ``BASELINE_CONTROL`` exists only for fixed-call-shape unit tests. It must
    never be used to recompute the Stage-15C temporal baseline.
    """

    BASELINE_CONTROL = "baseline_control"
    FIXED_PENALTY = "fixed_penalty"
    INITIAL_POPULATION_REPAIR = "initial_population_repair"
    OFFSPRING_REPAIR = "offspring_repair"


class CountingRandom(random.Random):
    """A state-compatible Random that observes calls without adding draws."""

    def __init__(self) -> None:
        super().__init__()
        self.counts: Counter[str] = Counter()

    def random(self) -> float:
        self.counts["random"] += 1
        return super().random()

    def getrandbits(self, k: int) -> int:
        self.counts["getrandbits"] += 1
        return super().getrandbits(k)

    def randrange(
        self,
        start: int,
        stop: int | None = None,
        step: int = 1,
    ) -> int:
        self.counts["randrange"] += 1
        return super().randrange(start, stop, step)

    def randint(self, a: int, b: int) -> int:
        self.counts["randint"] += 1
        return super().randint(a, b)

    def choice(self, seq: Sequence[Any]) -> Any:  # type: ignore[override]
        self.counts["choice"] += 1
        return super().choice(seq)

    def sample(  # type: ignore[override]
        self,
        population: Sequence[Any],
        k: int,
        *,
        counts: Sequence[int] | None = None,
    ) -> list[Any]:
        self.counts["sample"] += 1
        return super().sample(population, k, counts=counts)


@contextmanager
def _patched_module_random(source: CountingRandom) -> Iterator[None]:
    """Route pyeasyga's module-level calls through one observed private RNG."""

    originals: dict[str, Callable[..., Any]] = {
        name: getattr(random, name) for name in RNG_PRIMITIVES
    }
    try:
        for name in RNG_PRIMITIVES:
            setattr(random, name, getattr(source, name))
        yield
    finally:
        for name, original in originals.items():
            setattr(random, name, original)


def _counts_delta(after: Counter[str], before: Counter[str]) -> dict[str, int]:
    return {name: int(after[name] - before[name]) for name in RNG_PRIMITIVES}


def _chromosome_demand(genes: Sequence[int], tasks: Sequence[Task]) -> ResourceVector:
    demand = ResourceVector.zero()
    for selected, task in zip(genes, tasks, strict=True):
        if selected:
            demand = demand + task.demand
    return demand


def _repair_from_canonical_end(
    genes: list[int], tasks: Sequence[Task], capacity: ResourceVector
) -> int:
    """Clear selected bits from the canonical tail, consuming no randomness."""

    removed = 0
    while not _chromosome_demand(genes, tasks).fits_within(capacity):
        index = next((i for i in range(len(genes) - 1, -1, -1) if genes[i]), None)
        if index is None:
            raise StateValidationError("empty chromosome must be feasible")
        genes[index] = 0
        removed += 1
    return removed


@dataclass(frozen=True, slots=True)
class CounterfactualSelectorCall:
    """Sanitized per-selector-call RNG and deterministic-repair counters."""

    call_kind: str
    candidate_count: int
    rng_counts: dict[str, int]
    initial_chromosomes_repaired: int
    initial_bits_removed: int
    offspring_repaired: int
    offspring_bits_removed: int

    def as_dict(self) -> dict[str, object]:
        return {
            "call_kind": self.call_kind,
            "candidate_count": self.candidate_count,
            "rng_primitive_calls": dict(self.rng_counts),
            "initial_chromosomes_repaired": self.initial_chromosomes_repaired,
            "initial_bits_removed": self.initial_bits_removed,
            "offspring_repaired": self.offspring_repaired,
            "offspring_bits_removed": self.offspring_bits_removed,
        }


class CounterfactualKnapsackSelector(PyeasygaUtilityKnapsackSelector):
    """Auxiliary single-factor selector with exhaustive RNG observations."""

    def __init__(self, config: PyeasygaConfig, variant: CounterfactualVariant) -> None:
        if not isinstance(variant, CounterfactualVariant):
            raise TypeError("variant must be a CounterfactualVariant")
        super().__init__(config)
        observed_rng = CountingRandom()
        observed_rng.setstate(self._rng.getstate())
        self._rng = observed_rng
        self.variant = variant
        self._calls: list[CounterfactualSelectorCall] = []
        self._initial_chromosomes_repaired = 0
        self._initial_bits_removed = 0
        self._offspring_repaired = 0
        self._offspring_bits_removed = 0
        self._uniform_choice_option_counts: Counter[int] = Counter()

    @property
    def _counting_rng(self) -> CountingRandom:
        if not isinstance(self._rng, CountingRandom):
            raise TypeError("Stage-15D selector lost its counting RNG")
        return self._rng

    def choose_uniform(self, values: Sequence[str]) -> str:
        choices = tuple(values)
        if not choices:
            raise ValueError("values must not be empty")
        self._uniform_choice_option_counts[len(choices)] += 1
        return str(self._counting_rng.choice(choices))

    def call_observations(self) -> tuple[CounterfactualSelectorCall, ...]:
        return tuple(self._calls)

    def primitive_counts(self) -> dict[str, int]:
        return {name: int(self._counting_rng.counts[name]) for name in RNG_PRIMITIVES}

    def counterfactual_summary(self) -> dict[str, object]:
        return {
            "label": "[آزمون کمکی] Stage 15-D single-factor GA counterfactual",
            "variant": self.variant.value,
            "rng_primitive_calls": self.primitive_counts(),
            "uniform_choice_calls": int(sum(self._uniform_choice_option_counts.values())),
            "uniform_choice_option_count_histogram": {
                str(size): count
                for size, count in sorted(self._uniform_choice_option_counts.items())
            },
            "initial_chromosomes_repaired": self._initial_chromosomes_repaired,
            "initial_bits_removed": self._initial_bits_removed,
            "offspring_repaired": self._offspring_repaired,
            "offspring_bits_removed": self._offspring_bits_removed,
            "task_identifiers_recorded": False,
            "chromosome_bits_recorded": False,
        }

    def runtime_metadata(self) -> dict[str, str]:
        return super().runtime_metadata() | {
            "diagnostic.stage15d.variant": self.variant.value,
            "diagnostic.stage15d.random_draw_padding": "false",
            "diagnostic.stage15d.reseed_per_call": "false",
        }

    def _append_call(
        self,
        *,
        call_kind: str,
        candidate_count: int,
        before_rng: Counter[str],
        before_initial_repaired: int,
        before_initial_bits: int,
        before_offspring_repaired: int,
        before_offspring_bits: int,
    ) -> None:
        self._calls.append(
            CounterfactualSelectorCall(
                call_kind=call_kind,
                candidate_count=candidate_count,
                rng_counts=_counts_delta(self._counting_rng.counts, before_rng),
                initial_chromosomes_repaired=(
                    self._initial_chromosomes_repaired - before_initial_repaired
                ),
                initial_bits_removed=self._initial_bits_removed - before_initial_bits,
                offspring_repaired=self._offspring_repaired - before_offspring_repaired,
                offspring_bits_removed=self._offspring_bits_removed - before_offspring_bits,
            )
        )

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        """Run one approved auxiliary mode without changing the fixed RNG shape."""

        if not isinstance(capacity, ResourceVector):
            raise TypeError("capacity must be a ResourceVector")
        raw_candidates = tuple(tasks)
        if any(not isinstance(task, Task) for task in raw_candidates):
            raise TypeError("tasks must contain only Task instances")
        candidates = tuple(sorted(raw_candidates, key=lambda task: task.task_id))
        task_ids = tuple(task.task_id for task in candidates)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("tasks must have unique identifiers")
        if self.variant is CounterfactualVariant.FIXED_PENALTY and any(
            not isfinite(task.utility) or task.utility < 0.0 for task in candidates
        ):
            raise ValueError("fixed -1 penalty requires finite non-negative utilities")

        before_rng = self._counting_rng.counts.copy()
        before_initial_repaired = self._initial_chromosomes_repaired
        before_initial_bits = self._initial_bits_removed
        before_offspring_repaired = self._offspring_repaired
        before_offspring_bits = self._offspring_bits_removed

        if not candidates:
            self._observe(GASelectionObservation("empty", 0, None, 0, True, False, 0))
            self._append_call(
                call_kind="empty",
                candidate_count=0,
                before_rng=before_rng,
                before_initial_repaired=before_initial_repaired,
                before_initial_bits=before_initial_bits,
                before_offspring_repaired=before_offspring_repaired,
                before_offspring_bits=before_offspring_bits,
            )
            return ()
        if len(candidates) == 1:
            candidate = candidates[0]
            if candidate.utility == 0.0 and candidate.demand.fits_within(capacity):
                raise StateValidationError(
                    "one-candidate zero-utility knapsack has an unresolved empty/subset tie"
                )
            selected = (
                (candidate.task_id,)
                if candidate.utility > 0.0 and candidate.demand.fits_within(capacity)
                else ()
            )
            self._observe(
                GASelectionObservation(
                    "single_candidate", 1, None, len(selected), True, False, len(selected)
                )
            )
            self._append_call(
                call_kind="single_candidate",
                candidate_count=1,
                before_rng=before_rng,
                before_initial_repaired=before_initial_repaired,
                before_initial_bits=before_initial_bits,
                before_offspring_repaired=before_offspring_repaired,
                before_offspring_bits=before_offspring_bits,
            )
            return selected

        ga = pyeasyga.GeneticAlgorithm(
            list(candidates),
            population_size=self.config.population_size,
            generations=self.config.generations,
            crossover_probability=self.config.crossover_probability,
            mutation_probability=self.config.mutation_probability,
            elitism=self.config.elitism,
            maximise_fitness=self.config.maximise_fitness,
        )
        ga.tournament_size = self.config.tournament_size

        infeasible_fitness = (
            -1.0
            if self.variant is CounterfactualVariant.FIXED_PENALTY
            else self.config.infeasible_fitness
        )

        def fitness(individual: list[int], data: list[Task]) -> float:
            demand = _chromosome_demand(individual, data)
            if not demand.fits_within(capacity):
                return infeasible_fitness
            utility = float(
                sum(
                    task.utility
                    for selected, task in zip(individual, data, strict=True)
                    if selected
                )
            )
            if not isfinite(utility):
                raise ValueError("knapsack utility must be finite")
            return utility

        ga.fitness_function = fitness

        if self.variant is CounterfactualVariant.INITIAL_POPULATION_REPAIR:

            def create_individual(seed_data: list[Task]) -> list[int]:
                genes = [random.randint(0, 1) for _ in range(len(seed_data))]
                removed = _repair_from_canonical_end(genes, seed_data, capacity)
                if removed:
                    self._initial_chromosomes_repaired += 1
                    self._initial_bits_removed += removed
                return genes

            ga.create_individual = create_individual

        if self.variant is CounterfactualVariant.OFFSPRING_REPAIR:

            def create_new_population() -> None:
                new_population: list[Any] = []
                elite = copy.deepcopy(ga.current_generation[0])
                selection = ga.selection_function
                while len(new_population) < ga.population_size:
                    parent_1 = copy.deepcopy(selection(ga.current_generation))
                    parent_2 = copy.deepcopy(selection(ga.current_generation))
                    child_1, child_2 = parent_1, parent_2
                    child_1.fitness, child_2.fitness = 0, 0
                    can_crossover = random.random() < ga.crossover_probability
                    can_mutate = random.random() < ga.mutation_probability
                    if can_crossover:
                        child_1.genes, child_2.genes = ga.crossover_function(
                            parent_1.genes, parent_2.genes
                        )
                    if can_mutate:
                        ga.mutate_function(child_1.genes)
                        ga.mutate_function(child_2.genes)
                    for child in (child_1, child_2):
                        removed = _repair_from_canonical_end(
                            child.genes, ga.seed_data, capacity
                        )
                        if removed:
                            self._offspring_repaired += 1
                            self._offspring_bits_removed += removed
                    new_population.append(child_1)
                    if len(new_population) < ga.population_size:
                        new_population.append(child_2)
                if ga.elitism:
                    new_population[0] = elite
                ga.current_generation = new_population

            ga.create_new_population = create_new_population

        with _patched_module_random(self._counting_rng):
            ga.run()

        best_fitness, genes = ga.best_individual()
        if len(genes) != len(candidates) or any(gene not in (0, 1) for gene in genes):
            raise StateValidationError("pyeasyga returned an invalid binary chromosome")
        selected_tasks = tuple(
            task for selected, task in zip(genes, candidates, strict=True) if selected
        )
        selected_demand = _chromosome_demand(genes, candidates)
        if not selected_demand.fits_within(capacity):
            if best_fitness != infeasible_fitness:
                raise StateValidationError(
                    "pyeasyga returned an infeasible best chromosome with unexpected fitness"
                )
            self._zero_fitness_feasibility_repairs += 1
            self._observe(
                GASelectionObservation(
                    "ga",
                    len(candidates),
                    float(best_fitness),
                    len(selected_tasks),
                    False,
                    True,
                    0,
                )
            )
            selected_ids: tuple[str, ...] = ()
        else:
            self._observe(
                GASelectionObservation(
                    "ga",
                    len(candidates),
                    float(best_fitness),
                    len(selected_tasks),
                    True,
                    False,
                    len(selected_tasks),
                )
            )
            selected_ids = tuple(task.task_id for task in selected_tasks)

        self._append_call(
            call_kind="ga",
            candidate_count=len(candidates),
            before_rng=before_rng,
            before_initial_repaired=before_initial_repaired,
            before_initial_bits=before_initial_bits,
            before_offspring_repaired=before_offspring_repaired,
            before_offspring_bits=before_offspring_bits,
        )
        return selected_ids
