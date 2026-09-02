"""Non-interventional aggregate preemption diagnostics for Stage 15-K.2."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from math import isclose
from typing import Any

from edge_reproduction.models.enums import EventType
from edge_reproduction.simulation.state import SimulationState


class Stage15K2PreemptionObserver:
    """Observe DK-P atomic repacking without changing decisions or RNG calls."""

    def __init__(self, delegate: Any, *, tolerance: float = 1e-9) -> None:
        if not hasattr(delegate, "run") or not callable(delegate.run):
            raise TypeError("delegate must expose callable run")
        if tolerance != 1e-9:
            raise ValueError("Stage 15-K.2 tolerance must be 1e-9")
        self._delegate = delegate
        self._tolerance = tolerance
        self.name = str(delegate.name)
        self._counts: Counter[str] = Counter()
        self._accepted_utility = 0.0
        self._victim_utility = 0.0
        self._net_utility = 0.0
        self._finite_multipliers: list[float] = []

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> Any:
        result = self._delegate.run(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            epoch=epoch,
        )
        scores = getattr(result, "round_two_scores_by_server", None)
        if scores is None:
            return result

        accepted = set(result.accepted_task_ids)
        preempted = set(result.preempted_task_ids)
        self._counts["preempted_tasks"] += len(preempted)
        self._counts["accepted_tasks"] += len(accepted)
        self._accepted_utility += sum(state.tasks[item].utility for item in accepted)

        for entries in scores.values():
            incoming = [row for row in entries if not row.is_current and row.task_id in accepted]
            victims = [row for row in entries if row.is_current and row.task_id in preempted]
            if not victims:
                continue
            self._counts["preemption_batches"] += 1
            self._counts["accepted_in_preemption_batches"] += len(incoming)
            incoming_utility = sum(state.tasks[row.task_id].utility for row in incoming)
            victim_utility = sum(state.tasks[row.task_id].utility for row in victims)
            net = incoming_utility - victim_utility
            self._victim_utility += victim_utility
            self._net_utility += net
            if net > self._tolerance:
                self._counts["positive_net_batches"] += 1
            elif net < -self._tolerance:
                self._counts["negative_net_batches"] += 1
            else:
                self._counts["zero_net_batches"] += 1

            for new_row in incoming:
                for victim_row in victims:
                    self._counts["five_percent_pair_count"] += 1
                    victim_ratio = float(victim_row.utility_time_ratio)
                    new_ratio = float(new_row.utility_time_ratio)
                    if victim_ratio == 0.0:
                        self._counts["five_percent_zero_victim_ratio"] += 1
                        passed = new_ratio > 0.0
                    else:
                        multiplier = new_ratio / victim_ratio
                        self._finite_multipliers.append(multiplier)
                        passed = multiplier >= 1.05
                        if isclose(multiplier, 1.05, rel_tol=0.0, abs_tol=self._tolerance):
                            self._counts["five_percent_exact_boundary"] += 1
                    self._counts["five_percent_pass" if passed else "five_percent_fail"] += 1
        return result

    def summary(self) -> dict[str, object]:
        """Return aggregate-only diagnostics; never serialize task identifiers."""

        multipliers = self._finite_multipliers
        batches = self._counts["preemption_batches"]
        return {
            "label": "[آزمون کمکی] aggregate DK-P preemption observation",
            "semantic_unit": "atomic_server_epoch_repacking_batch",
            "five_percent_status": "counterfactual_diagnostic_not_a_DK_P_rule",
            "counts": dict(sorted(self._counts.items())),
            "accepted_new_utility": self._accepted_utility,
            "victim_utility": self._victim_utility,
            "net_utility": self._net_utility,
            "mean_net_utility_per_batch": self._net_utility / batches if batches else None,
            "finite_five_percent_multiplier": {
                "count": len(multipliers),
                "mean": sum(multipliers) / len(multipliers) if multipliers else None,
                "minimum": min(multipliers) if multipliers else None,
                "maximum": max(multipliers) if multipliers else None,
            },
            "task_identifiers_recorded": False,
            "random_draws_added": 0,
        }


def terminal_preemption_summary(events: Sequence[Any]) -> dict[str, object]:
    """Count admission-to-preemption outcomes transiently, without retaining IDs."""

    accepted = {event.task_id for event in events if event.event_type is EventType.ACCEPTED}
    preempted = {event.task_id for event in events if event.event_type is EventType.PREEMPTED}
    completed = {event.task_id for event in events if event.event_type is EventType.COMPLETED}
    return {
        "unique_admitted_tasks": len(accepted),
        "admissions_eventually_preempted": len(accepted & preempted),
        "completed_admissions": len(accepted & completed),
        "completion_per_admission": len(accepted & completed) / len(accepted) if accepted else 0.0,
        "task_identifiers_recorded": False,
    }
