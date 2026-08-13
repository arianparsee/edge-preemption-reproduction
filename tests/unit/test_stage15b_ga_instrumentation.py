from __future__ import annotations

import random

from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    InstrumentedKnapsackSelector,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def test_instrumentation_preserves_outputs_global_rng_and_private_rng_stream() -> None:
    capacity = ResourceVector(8.0, 8.0, 8.0, 8.0)
    tasks = (
        _task("a", 5.0, 20.0),
        _task("b", 3.0, 12.0),
        _task("c", 4.0, 11.0),
    )
    direct = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=91))
    delegated = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=91))
    instrumented = InstrumentedKnapsackSelector(delegated, server_count=1)
    random.seed(772)
    caller_state = random.getstate()

    direct_results = (
        direct.select(capacity=capacity, tasks=tasks),
        direct.select(capacity=capacity, tasks=tuple(reversed(tasks))),
    )
    instrumented_results = (
        instrumented.select(capacity=capacity, tasks=tasks),
        instrumented.select(capacity=capacity, tasks=tuple(reversed(tasks))),
    )

    assert instrumented_results == direct_results
    assert random.getstate() == caller_state
    assert delegated._rng.getstate() == direct._rng.getstate()  # noqa: SLF001
    summary = instrumented.summary()
    assert summary.total_calls == 2
    assert summary.auction_count == 1
    assert summary.by_round["round_1"]["ga_calls"] == 1
    assert summary.by_round["round_2"]["ga_calls"] == 1


def test_empty_and_single_candidate_observations_do_not_advance_rng() -> None:
    delegate = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=3))
    instrumented = InstrumentedKnapsackSelector(delegate, server_count=1)
    capacity = ResourceVector(2.0, 2.0, 2.0, 2.0)
    before = delegate._rng.getstate()  # noqa: SLF001

    assert instrumented.select(capacity=capacity, tasks=()) == ()
    assert instrumented.select(capacity=capacity, tasks=(_task("a", 1.0, 2.0),)) == ("a",)

    assert delegate._rng.getstate() == before  # noqa: SLF001
    summary = instrumented.summary()
    assert summary.by_round["round_1"]["empty_calls"] == 1
    assert summary.by_round["round_2"]["single_candidate_calls"] == 1


def test_instrumentation_runtime_metadata_preserves_delegate_counters() -> None:
    delegate = PyeasygaUtilityKnapsackSelector(PyeasygaConfig(seed=5))
    instrumented = InstrumentedKnapsackSelector(delegate, server_count=2)

    metadata = instrumented.runtime_metadata()

    assert metadata["ga.zero_fitness_feasibility_repairs"] == "0"
    assert metadata["client.equal_minimum_price_ties"] == "0"
    assert metadata["diagnostic.ga_instrumentation"] == "stage15b_non_interventional"
