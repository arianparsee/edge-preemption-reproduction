"""Observational GA instrumentation that delegates every scientific decision."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from edge_reproduction.algorithms.genetic_knapsack import (
    GASelectionObservation,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task


def _state_hash(state: object) -> str:
    """Hash a Python random state without advancing or replacing it."""

    encoded = json.dumps(state, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class GACallObservation:
    """Sanitized counts for one delegated selector call; no task identifiers."""

    auction_ordinal: int
    round_name: str
    server_ordinal: int
    candidate_count: int
    selected_count: int
    candidate_utility: float
    selected_utility: float
    repair_delta: int
    raw_selected_count: int
    raw_best_feasible: bool
    raw_best_fitness: float | None
    rng_state_before_sha256: str
    rng_state_after_sha256: str

    @property
    def call_kind(self) -> str:
        if self.candidate_count == 0:
            return "empty"
        if self.candidate_count == 1:
            return "single_candidate"
        return "ga"


@dataclass(frozen=True, slots=True)
class GAInstrumentationSummary:
    """Aggregate auxiliary counters split by inferred DK auction round."""

    server_count: int
    diagnostic_stage: str
    total_calls: int
    auction_count: int
    initial_rng_state_sha256: str
    final_rng_state_sha256: str
    by_round: dict[str, dict[str, int | float]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": (
                f"auxiliary_test_{self.diagnostic_stage}_non_interventional_GA_instrumentation"
            ),
            "server_count": self.server_count,
            "total_calls": self.total_calls,
            "auction_count": self.auction_count,
            "initial_rng_state_sha256": self.initial_rng_state_sha256,
            "final_rng_state_sha256": self.final_rng_state_sha256,
            "task_identifiers_recorded": False,
            "raw_workload_recorded": False,
            "by_round": self.by_round,
        }


class InstrumentedKnapsackSelector:
    """Delegate unchanged decisions while observing sanitized DK call counters.

    Pipeline DK calls the selector exactly once per server in Round 1 and once
    per server in Round 2. The wrapper uses only that existing call order. It
    does not alter candidate order, capacity, returned identifiers, GA config,
    or either the module-level or private random stream.
    """

    def __init__(
        self,
        delegate: PyeasygaUtilityKnapsackSelector,
        *,
        server_count: int,
        diagnostic_stage: str = "stage15b",
    ) -> None:
        if not isinstance(delegate, PyeasygaUtilityKnapsackSelector):
            raise TypeError("delegate must be PyeasygaUtilityKnapsackSelector")
        if isinstance(server_count, bool) or not isinstance(server_count, int):
            raise TypeError("server_count must be an integer")
        if server_count <= 0:
            raise ValueError("server_count must be positive")
        if diagnostic_stage not in {
            "stage15b",
            "stage15c",
            "stage15d",
            "stage15e",
            "stage15k1",
        }:
            raise ValueError(
                "diagnostic_stage must be stage15b, stage15c, stage15d, stage15e "
                "or stage15k1"
            )
        self._delegate = delegate
        self._server_count = server_count
        self._diagnostic_stage = diagnostic_stage
        self._observations: list[GACallObservation] = []
        self._selector_observations: list[GASelectionObservation] = []
        if delegate.observation_sink is not None:
            raise ValueError("delegate already has an observation sink")
        delegate.observation_sink = self._selector_observations.append
        self._initial_rng_state_sha256 = self._rng_state_sha256()

    def _rng_state_sha256(self) -> str:
        # Reading Random.getstate() is observational and consumes no random value.
        return _state_hash(self._delegate._rng.getstate())  # noqa: SLF001

    @property
    def zero_fitness_feasibility_repairs(self) -> int:
        return self._delegate.zero_fitness_feasibility_repairs

    def choose_uniform(self, values: Sequence[str]) -> str:
        return self._delegate.choose_uniform(values)

    def choose_kg_equal_minimum_server(self, values: Sequence[str]) -> str:
        return self._delegate.choose_kg_equal_minimum_server(values)

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        """Return the exact delegate output and append one observation afterward."""

        candidates = tuple(tasks)
        call_index = len(self._observations)
        position = call_index % (2 * self._server_count)
        round_name = "round_1" if position < self._server_count else "round_2"
        server_ordinal = position % self._server_count
        auction_ordinal = call_index // (2 * self._server_count)
        before_repairs = self._delegate.zero_fitness_feasibility_repairs
        before_selector_observations = len(self._selector_observations)
        before_rng = self._rng_state_sha256()
        set_round = getattr(self._delegate, "set_diagnostic_round", None)
        if callable(set_round):
            set_round(round_name)
        selected = self._delegate.select(capacity=capacity, tasks=candidates)
        if len(self._selector_observations) != before_selector_observations + 1:
            raise ValueError("selector must emit exactly one aggregate observation per call")
        selector_observation = self._selector_observations[-1]
        if selector_observation.candidate_count != len(candidates):
            raise ValueError("selector observation candidate count changed")
        if selector_observation.final_selected_count != len(selected):
            raise ValueError("selector observation final count changed")
        repair_delta = self._delegate.zero_fitness_feasibility_repairs - before_repairs
        if repair_delta != int(selector_observation.repair_applied):
            raise ValueError("selector observation repair count changed")
        after_rng = self._rng_state_sha256()
        selected_set = set(selected)
        self._observations.append(
            GACallObservation(
                auction_ordinal=auction_ordinal,
                round_name=round_name,
                server_ordinal=server_ordinal,
                candidate_count=len(candidates),
                selected_count=len(selected),
                candidate_utility=float(sum(task.utility for task in candidates)),
                selected_utility=float(
                    sum(task.utility for task in candidates if task.task_id in selected_set)
                ),
                repair_delta=repair_delta,
                raw_selected_count=selector_observation.raw_selected_count,
                raw_best_feasible=selector_observation.raw_best_feasible,
                raw_best_fitness=selector_observation.raw_best_fitness,
                rng_state_before_sha256=before_rng,
                rng_state_after_sha256=after_rng,
            )
        )
        return selected

    @property
    def observation_count(self) -> int:
        """Return the number of completed selector calls without exposing task data."""

        return len(self._observations)

    def observations_since(self, start: int) -> tuple[GACallObservation, ...]:
        """Return sanitized call aggregates created after ``start``."""

        if isinstance(start, bool) or not isinstance(start, int):
            raise TypeError("start must be an integer")
        if start < 0 or start > len(self._observations):
            raise ValueError("start is outside the observation sequence")
        return tuple(self._observations[start:])

    def runtime_metadata(self) -> dict[str, str]:
        """Preserve original scientific metadata and add explicit auxiliary flags."""

        return self._delegate.runtime_metadata() | {
            "diagnostic.ga_instrumentation": f"{self._diagnostic_stage}_non_interventional",
            "diagnostic.ga_instrumentation_task_ids_recorded": "false",
        }

    def summary(self) -> GAInstrumentationSummary:
        """Aggregate observations without exposing per-call or task-level detail."""

        if len(self._observations) % (2 * self._server_count) != 0:
            raise ValueError("incomplete DK Round-1/Round-2 call group")
        grouped: dict[str, list[GACallObservation]] = defaultdict(list)
        for observation in self._observations:
            grouped[observation.round_name].append(observation)
        by_round: dict[str, dict[str, int | float]] = {}
        for round_name in ("round_1", "round_2"):
            rows = grouped[round_name]
            kind_counts: defaultdict[str, int] = defaultdict(int)
            for row in rows:
                kind_counts[row.call_kind] += 1
            candidates = sum(row.candidate_count for row in rows)
            selected = sum(row.selected_count for row in rows)
            by_round[round_name] = {
                "selector_calls": len(rows),
                "empty_calls": kind_counts["empty"],
                "single_candidate_calls": kind_counts["single_candidate"],
                "ga_calls": kind_counts["ga"],
                "candidate_entries": candidates,
                "selected_entries": selected,
                "selection_fraction": (selected / candidates if candidates else 0.0),
                "repair_count": sum(row.repair_delta for row in rows),
                "raw_best_selected_entries": sum(row.raw_selected_count for row in rows),
                "postrepair_removed_entries": sum(
                    row.raw_selected_count - row.selected_count for row in rows
                ),
                "raw_best_feasible_ga_calls": sum(
                    row.call_kind == "ga" and row.raw_best_feasible for row in rows
                ),
                "raw_best_infeasible_ga_calls": sum(
                    row.call_kind == "ga" and not row.raw_best_feasible for row in rows
                ),
                "raw_best_empty_ga_calls": sum(
                    row.call_kind == "ga" and row.raw_selected_count == 0 for row in rows
                ),
                "candidate_utility_sum": float(sum(row.candidate_utility for row in rows)),
                "selected_utility_sum": float(sum(row.selected_utility for row in rows)),
            }
        summary = GAInstrumentationSummary(
            server_count=self._server_count,
            diagnostic_stage=self._diagnostic_stage,
            total_calls=len(self._observations),
            auction_count=len(self._observations) // (2 * self._server_count),
            initial_rng_state_sha256=self._initial_rng_state_sha256,
            final_rng_state_sha256=self._rng_state_sha256(),
            by_round=by_round,
        )
        return summary
