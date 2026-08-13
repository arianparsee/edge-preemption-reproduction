"""Non-interventional aggregate funnel observation for Pipeline DK auctions."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from edge_reproduction.diagnostics.ga_instrumentation import (
    GACallObservation,
    InstrumentedKnapsackSelector,
)
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class DKAuctionFunnelObservation:
    """Sanitized aggregate counts for one completed two-round auction."""

    epoch: int
    counts: Mapping[str, int]


def _sum(rows: Sequence[GACallObservation], attribute: str) -> int:
    return sum(int(getattr(row, attribute)) for row in rows)


class InstrumentedDKPolicy:
    """Delegate the official policy unchanged and observe its returned result.

    Task identifiers are used transiently only to count unique memberships. They
    are never retained by the wrapper or included in its serialized summary.
    """

    def __init__(self, delegate: Any, selector: InstrumentedKnapsackSelector) -> None:
        if not hasattr(delegate, "run") or not callable(delegate.run):
            raise TypeError("delegate must expose callable run")
        if not isinstance(selector, InstrumentedKnapsackSelector):
            raise TypeError("selector must be InstrumentedKnapsackSelector")
        self._delegate = delegate
        self._selector = selector
        self.name = str(delegate.name)
        self._observations: list[DKAuctionFunnelObservation] = []

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> Any:
        """Return the exact delegate result and retain only aggregate counters."""

        start = self._selector.observation_count
        result = self._delegate.run(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            epoch=epoch,
        )
        rows = self._selector.observations_since(start)
        round_one = tuple(row for row in rows if row.round_name == "round_1")
        round_two = tuple(row for row in rows if row.round_name == "round_2")
        server_count = len(state.servers)
        if len(round_one) != server_count or len(round_two) != server_count:
            raise ValueError("one DK auction must emit one selector call per server and round")

        round_one_selected = result.round_one_selected_by_server
        selected_server = result.selected_server_by_task
        selected_any_server = {
            task_id for selected_ids in round_one_selected.values() for task_id in selected_ids
        }
        round_two_knapsack = getattr(result, "round_two_knapsack_by_server", None)
        scores = getattr(result, "round_two_scores_by_server", None)
        if round_two_knapsack is None:
            round_two_knapsack_entries = len(result.accepted_task_ids)
            round_two_current_entries = 0
            round_two_returning_entries = len(selected_server)
            round_two_member_current = 0
            round_two_member_returning = len(result.accepted_task_ids)
        else:
            if scores is None:
                raise ValueError("DK-P round-two scores are missing")
            round_two_knapsack_entries = sum(len(values) for values in round_two_knapsack.values())
            score_entries = tuple(entry for values in scores.values() for entry in values)
            round_two_current_entries = sum(entry.is_current for entry in score_entries)
            round_two_returning_entries = sum(not entry.is_current for entry in score_entries)
            round_two_member_current = sum(
                entry.is_current and entry.in_knapsack for entry in score_entries
            )
            round_two_member_returning = sum(
                not entry.is_current and entry.in_knapsack for entry in score_entries
            )

        requesting_count = len(tuple(requesting_task_ids))
        counts = {
            "requesting_task_attempts": requesting_count,
            "round_1_selector_calls": len(round_one),
            "round_1_candidate_entries": _sum(round_one, "candidate_count"),
            "round_1_raw_best_selected_entries": _sum(round_one, "raw_selected_count"),
            "round_1_postrepair_selected_entries": _sum(round_one, "selected_count"),
            "round_1_repair_calls": _sum(round_one, "repair_delta"),
            "round_1_tasks_selected_on_any_server": len(selected_any_server),
            "round_1_server_assignments": len(selected_server),
            "round_1_no_server": requesting_count - len(selected_server),
            "round_2_selector_calls": len(round_two),
            "round_2_candidate_entries": _sum(round_two, "candidate_count"),
            "round_2_current_entries": round_two_current_entries,
            "round_2_returning_entries": round_two_returning_entries,
            "round_2_raw_best_selected_entries": _sum(round_two, "raw_selected_count"),
            "round_2_postrepair_selected_entries": _sum(round_two, "selected_count"),
            "round_2_repair_calls": _sum(round_two, "repair_delta"),
            "round_2_knapsack_member_entries": round_two_knapsack_entries,
            "round_2_knapsack_member_current": round_two_member_current,
            "round_2_knapsack_member_returning": round_two_member_returning,
            "round_2_accepted": len(result.accepted_task_ids),
            "round_2_rejected": len(result.rejected_task_ids),
            "round_2_retained": len(getattr(result, "retained_task_ids", ())),
            "round_2_preempted": len(getattr(result, "preempted_task_ids", ())),
        }
        if any(value < 0 for value in counts.values()):
            raise ValueError("funnel counters must be non-negative")
        self._observations.append(DKAuctionFunnelObservation(epoch, counts))
        return result

    def summary(self) -> dict[str, object]:
        """Return only totals and per-stage conversion fractions."""

        totals: Counter[str] = Counter()
        for observation in self._observations:
            totals.update(observation.counts)
        requesting = totals["requesting_task_attempts"]
        assigned = totals["round_1_server_assignments"]
        accepted = totals["round_2_accepted"]
        return {
            "label": "auxiliary_test_stage15c_non_interventional_DK_funnel",
            "auction_count": len(self._observations),
            "task_identifiers_recorded": False,
            "chromosome_bits_recorded": False,
            "totals": dict(sorted(totals.items())),
            "conversion_fractions": {
                "server_assignment_per_requesting_attempt": (
                    assigned / requesting if requesting else 0.0
                ),
                "acceptance_per_server_assignment": assigned and accepted / assigned or 0.0,
                "acceptance_per_requesting_attempt": (
                    accepted / requesting if requesting else 0.0
                ),
            },
        }


def lifecycle_funnel(events: Sequence[Any]) -> dict[str, int]:
    """Aggregate existing temporal events without retaining task identifiers."""

    counts: Counter[str] = Counter()
    for event in events:
        event_type = str(event.event_type.value)
        counts[event_type] += 1
        if event_type == "expired":
            reason = str(event.reason)
            if reason.startswith("post_rejection_next_epoch_infeasible"):
                counts["expired_after_round_2_rejection"] += 1
            elif reason.startswith("canonical_admission_infeasible"):
                counts["expired_during_canonicalization"] += 1
            elif reason == "waiting_task_no_remaining_completion_opportunity":
                counts["expired_waiting_at_deadline"] += 1
            elif reason == "active_pipeline_incomplete_after_inclusive_deadline_opportunity":
                counts["expired_active_at_deadline"] += 1
    return dict(sorted(counts.items()))
