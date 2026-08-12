"""Audited pyeasyga 0.3.1 adapter for official Pipeline DK-R knapsacks."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from math import isfinite

from pyeasyga import pyeasyga  # type: ignore[import-untyped]

from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task

PYEASYGA_VERSION = "0.3.1"


@dataclass(frozen=True, slots=True)
class PyeasygaConfig:
    """Complete official GA configuration approved in ASSUMP-013/015.

    ``seed`` has intentionally no default. All other values are explicit even
    when they match pyeasyga defaults so every run can serialize the complete
    scientific configuration.
    """

    seed: int
    population_size: int = 200
    tournament_size: int = 20
    generations: int = 50
    crossover_probability: float = 0.8
    mutation_probability: float = 0.2
    elitism: bool = True
    maximise_fitness: bool = True
    selection_operator: str = "tournament"
    crossover_operator: str = "one_point"
    mutation_operator: str = "one_bit_flip"
    chromosome_representation: str = "binary_bit_array"
    infeasible_fitness: float = 0.0
    library: str = "pyeasyga"
    library_version: str = PYEASYGA_VERSION

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        official = {
            "population_size": (self.population_size, 200),
            "tournament_size": (self.tournament_size, 20),
            "generations": (self.generations, 50),
            "crossover_probability": (self.crossover_probability, 0.8),
            "mutation_probability": (self.mutation_probability, 0.2),
            "elitism": (self.elitism, True),
            "maximise_fitness": (self.maximise_fitness, True),
            "selection_operator": (self.selection_operator, "tournament"),
            "crossover_operator": (self.crossover_operator, "one_point"),
            "mutation_operator": (self.mutation_operator, "one_bit_flip"),
            "chromosome_representation": (
                self.chromosome_representation,
                "binary_bit_array",
            ),
            "infeasible_fitness": (self.infeasible_fitness, 0.0),
            "library": (self.library, "pyeasyga"),
            "library_version": (self.library_version, PYEASYGA_VERSION),
        }
        for name, (actual, expected) in official.items():
            if actual != expected:
                raise ValueError(
                    f"{name} must be {expected!r} for official Pipeline DK-R; "
                    "population-50 sensitivity requires a separate auxiliary path"
                )
        if self.tournament_size != self.population_size // 10:
            raise ValueError("tournament_size must follow audited population_size // 10")

    def as_metadata(self) -> dict[str, str]:
        """Return every audited setting in a serialization-safe form."""

        return {
            "ga.library": self.library,
            "ga.library_version": self.library_version,
            "ga.population_size": str(self.population_size),
            "ga.tournament_size": str(self.tournament_size),
            "ga.generations": str(self.generations),
            "ga.seed": str(self.seed),
            "ga.crossover_probability": str(self.crossover_probability),
            "ga.mutation_probability": str(self.mutation_probability),
            "ga.elitism": str(self.elitism).lower(),
            "ga.maximise_fitness": str(self.maximise_fitness).lower(),
            "ga.selection_operator": self.selection_operator,
            "ga.crossover_operator": self.crossover_operator,
            "ga.mutation_operator": self.mutation_operator,
            "ga.chromosome_representation": self.chromosome_representation,
            "ga.infeasible_fitness": str(self.infeasible_fitness),
            "ga.provenance": "pyeasyga_0.3.1_audit_and_ASSUMP-013_ASSUMP-015",
        }


@dataclass(frozen=True, slots=True)
class KGPyeasygaConfig:
    """ASSUMP-041 pyeasyga configuration for KG Round 1.

    This is deliberately separate from :class:`PyeasygaConfig`, whose 50
    generations remain the approved Pipeline DK-R/DK-P setting.
    """

    seed: int
    population_size: int = 200
    tournament_size: int = 20
    generations: int = 30
    crossover_probability: float = 0.8
    mutation_probability: float = 0.2
    elitism: bool = True
    maximise_fitness: bool = True
    selection_operator: str = "tournament"
    crossover_operator: str = "one_point"
    mutation_operator: str = "one_bit_flip"
    chromosome_representation: str = "binary_bit_array"
    infeasible_fitness: float = 0.0
    library: str = "pyeasyga"
    library_version: str = PYEASYGA_VERSION

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        official = {
            "population_size": (self.population_size, 200),
            "tournament_size": (self.tournament_size, 20),
            "generations": (self.generations, 30),
            "crossover_probability": (self.crossover_probability, 0.8),
            "mutation_probability": (self.mutation_probability, 0.2),
            "elitism": (self.elitism, True),
            "maximise_fitness": (self.maximise_fitness, True),
            "selection_operator": (self.selection_operator, "tournament"),
            "crossover_operator": (self.crossover_operator, "one_point"),
            "mutation_operator": (self.mutation_operator, "one_bit_flip"),
            "chromosome_representation": (
                self.chromosome_representation,
                "binary_bit_array",
            ),
            "infeasible_fitness": (self.infeasible_fitness, 0.0),
            "library": (self.library, "pyeasyga"),
            "library_version": (self.library_version, PYEASYGA_VERSION),
        }
        for name, (actual, expected) in official.items():
            if actual != expected:
                raise ValueError(f"{name} must be {expected!r} for ASSUMP-041 KG Round 1")

    def as_metadata(self) -> dict[str, str]:
        """Return the complete recorded ASSUMP-041 configuration."""

        return {
            "ga.library": self.library,
            "ga.library_version": self.library_version,
            "ga.population_size": str(self.population_size),
            "ga.tournament_size": str(self.tournament_size),
            "ga.generations": str(self.generations),
            "ga.seed": str(self.seed),
            "ga.crossover_probability": str(self.crossover_probability),
            "ga.mutation_probability": str(self.mutation_probability),
            "ga.elitism": str(self.elitism).lower(),
            "ga.maximise_fitness": str(self.maximise_fitness).lower(),
            "ga.selection_operator": self.selection_operator,
            "ga.crossover_operator": self.crossover_operator,
            "ga.mutation_operator": self.mutation_operator,
            "ga.chromosome_representation": self.chromosome_representation,
            "ga.infeasible_fitness": str(self.infeasible_fitness),
            "ga.provenance": "pyeasyga_0.3.1_audit_and_ASSUMP-041",
        }


@dataclass(slots=True)
class PyeasygaUtilityKnapsackSelector:
    """Official stochastic utility-maximizing selector for Pipeline DK-R.

    The adapter executes the installed pyeasyga implementation rather than
    reproducing its operators locally. It temporarily transfers a private RNG
    state into Python's module-level ``random`` object because pyeasyga 0.3.1
    exposes no seed parameter. The caller's global RNG state is restored after
    every call, while this selector's private stream continues across R1, R2 and
    client tie decisions in one auction.
    """

    config: PyeasygaConfig | KGPyeasygaConfig
    _rng: random.Random = field(init=False, repr=False)
    _zero_fitness_feasibility_repairs: int = field(init=False, default=0, repr=False)
    _kg_client_equal_minimum_price_ties: int = field(init=False, default=0, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.config, (PyeasygaConfig, KGPyeasygaConfig)):
            raise TypeError("config must be a PyeasygaConfig or KGPyeasygaConfig")
        installed_version = version("pyeasyga")
        if installed_version != self.config.library_version:
            raise RuntimeError(
                f"pyeasyga version mismatch: expected {self.config.library_version}, "
                f"found {installed_version}"
            )
        self._rng = random.Random(self.config.seed)

    @property
    def zero_fitness_feasibility_repairs(self) -> int:
        """Return the cumulative ASSUMP-042 repair count for this RNG stream."""

        return self._zero_fitness_feasibility_repairs

    def runtime_metadata(self) -> dict[str, str]:
        """Return selector counters that are only known after execution."""

        return {
            "ga.zero_fitness_feasibility_repairs": str(
                self.zero_fitness_feasibility_repairs
            ),
            "ga.zero_fitness_feasibility_repair_semantics": (
                "ASSUMP-042_infeasible_zero_to_all_zero_feasible_same_fitness"
            ),
            "client.equal_minimum_price_ties": str(
                self._kg_client_equal_minimum_price_ties
            ),
            "client.equal_minimum_price_tie_semantics": (
                "ASSUMP-043_sorted_uniform_same_policy_rng_KG_only"
            ),
        }

    def choose_uniform(self, values: Sequence[str]) -> str:
        """Choose uniformly from a nonempty canonical sequence using the run RNG."""

        choices = tuple(values)
        if not choices:
            raise ValueError("values must not be empty")
        return self._rng.choice(choices)

    def choose_kg_equal_minimum_server(self, values: Sequence[str]) -> str:
        """Resolve one ASSUMP-043 KG client tie with this policy's RNG stream."""

        choices = tuple(values)
        if len(choices) < 2:
            raise ValueError("ASSUMP-043 requires at least two tied servers")
        if choices != tuple(sorted(choices)) or len(choices) != len(set(choices)):
            raise ValueError("tied server identifiers must be unique and sorted")
        self._kg_client_equal_minimum_price_ties += 1
        return self._rng.choice(choices)

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        """Run the audited GA and return one feasible utility-seeking subset."""

        if not isinstance(capacity, ResourceVector):
            raise TypeError("capacity must be a ResourceVector")
        raw_candidates = tuple(tasks)
        if any(not isinstance(task, Task) for task in raw_candidates):
            raise TypeError("tasks must contain only Task instances")
        candidates = tuple(sorted(raw_candidates, key=lambda task: task.task_id))
        task_ids = tuple(task.task_id for task in candidates)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("tasks must have unique identifiers")
        if not candidates:
            return ()
        if len(candidates) == 1:
            # pyeasyga 0.3.1's audited one-point crossover calls
            # randrange(1, 1) for one-gene chromosomes. This exact degenerate
            # objective has no stochastic choice unless utility is zero.
            candidate = candidates[0]
            if candidate.utility == 0.0 and candidate.demand.fits_within(capacity):
                raise StateValidationError(
                    "one-candidate zero-utility knapsack has an unresolved empty/subset tie"
                )
            if candidate.utility > 0.0 and candidate.demand.fits_within(capacity):
                return (candidate.task_id,)
            return ()
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

        def fitness(individual: list[int], data: list[Task]) -> float:
            demand = ResourceVector.zero()
            utility = 0.0
            for selected, task in zip(individual, data, strict=True):
                if selected:
                    demand = demand + task.demand
                    utility += task.utility
            if not demand.fits_within(capacity):
                return self.config.infeasible_fitness
            if not isfinite(utility):
                raise ValueError("knapsack utility must be finite")
            return float(utility)

        ga.fitness_function = fitness
        caller_state = random.getstate()
        random.setstate(self._rng.getstate())
        try:
            ga.run()
        finally:
            self._rng.setstate(random.getstate())
            random.setstate(caller_state)

        best_fitness, genes = ga.best_individual()
        if len(genes) != len(candidates) or any(gene not in (0, 1) for gene in genes):
            raise StateValidationError("pyeasyga returned an invalid binary chromosome")
        selected_tasks = tuple(
            task for selected, task in zip(genes, candidates, strict=True) if selected
        )
        selected_demand = ResourceVector.zero()
        for task in selected_tasks:
            selected_demand = selected_demand + task.demand
        if not selected_demand.fits_within(capacity):
            if best_fitness != self.config.infeasible_fitness:
                raise StateValidationError(
                    "pyeasyga returned an infeasible best chromosome with nonzero fitness"
                )
            self._zero_fitness_feasibility_repairs += 1
            return ()
        return tuple(task.task_id for task in selected_tasks)
