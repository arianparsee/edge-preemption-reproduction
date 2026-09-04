"""Proposed DK-P method with permanent batch-derived preemption protection.

This module implements approved ASSUMP-054 only for the Stage 15-M auxiliary
research path.  It deliberately does not modify the official reproduction
policy in :mod:`edge_reproduction.algorithms.double_knapsack_preemption`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from math import isclose

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPScoreEntry,
    PipelineDKPAuctionResult,
    PipelineDKPConfig,
    _make_score_entries,
    _reject_returning,
    _validate_selection,
    _validate_task_ids,
)
from edge_reproduction.algorithms.double_knapsack_retention import (
    run_dkr_round_one_for_server,
)
from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.bid import AuctionRound
from edge_reproduction.models.enums import AuctionRoundNumber, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.accounting import allocate_now, release_now
from edge_reproduction.simulation.invariants import validate_state_invariants
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class GuardedRoundTwoResult:
    """One atomic server result plus private counterfactual guard evidence."""

    final_state: SimulationState
    score_entries: tuple[DKPScoreEntry, ...]
    knapsack_selected_task_ids: tuple[str, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    reference_preempted_task_ids: tuple[str, ...]
    reference_accepted_task_ids: tuple[str, ...]
    protected_task_ids: tuple[str, ...]
    final_residual: ResourceVector


@dataclass(frozen=True, slots=True)
class ProtectionBatch:
    """Private task-level record retained only in process memory."""

    epoch: int
    server_id: str
    incoming_task_ids: tuple[str, ...]
    victim_task_ids: tuple[str, ...]
    incoming_utility: float
    victim_utility: float


@dataclass(frozen=True, slots=True)
class ProtectionRecord:
    """Private lifecycle of a task protected by one committed batch."""

    protected_at_epoch: int
    server_id: str


def _plan_without_guard(
    state: SimulationState,
    entries: Sequence[DKPScoreEntry],
    capacity: ResourceVector,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Replay the already-computed official score plan without RNG or mutation."""

    residual = capacity
    accepted: list[str] = []
    preempted: list[str] = []
    for entry in entries:
        demand = state.tasks[entry.task_id].demand
        if demand.fits_within(residual):
            residual = residual.subtract(demand)
            if not entry.is_current:
                accepted.append(entry.task_id)
        elif entry.is_current:
            preempted.append(entry.task_id)
    return tuple(accepted), tuple(preempted)


def run_guarded_dkp_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    protected_task_ids: frozenset[str],
) -> GuardedRoundTwoResult:
    """Run unchanged GA/scoring, then pin protected allocations at commit time."""

    validate_state_invariants(state)
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    returning = _validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    active = state.active_allocations_for_server(server_id)
    current = tuple(allocation.task_id for allocation in active)
    if set(current) & set(returning):
        raise StateValidationError("current and returning task pools must be disjoint")
    active_set = set(current)
    protected = tuple(task_id for task_id in current if task_id in protected_task_ids)
    for task_id in protected_task_ids & active_set:
        allocation = state.allocations[task_id]
        if not allocation.is_active or allocation.server_id != server_id:
            raise StateValidationError("protected task must have an active server allocation")
    for allocation in active:
        if allocation.resources != state.tasks[allocation.task_id].demand:
            raise StateValidationError("guarded DK-P requires allocation resources equal demand")
    for task_id in returning:
        if task_id in state.allocations:
            raise StateValidationError("a returning task must not already have an allocation")

    pool_ids = current + returning
    pool_tasks = tuple(state.tasks[task_id] for task_id in pool_ids)
    capacity = state.servers[server_id].capacity
    selected = _validate_selection(
        selected_ids=selector.select(capacity=capacity, tasks=pool_tasks),
        tasks=pool_tasks,
        capacity=capacity,
    )
    entries = _make_score_entries(
        tasks=pool_tasks,
        current_task_ids=set(current),
        selected_task_ids=set(selected),
        time_remaining_by_task=time_remaining_by_task,
    )
    reference_accepted, reference_preempted = _plan_without_guard(state, entries, capacity)

    protected_demand = ResourceVector.zero()
    for task_id in protected:
        protected_demand = protected_demand + state.tasks[task_id].demand
    if not protected_demand.fits_within(capacity):
        raise StateValidationError("active protected allocations are not jointly feasible")
    residual = capacity.subtract(protected_demand)
    retained: list[str] = list(protected)
    preempted: list[str] = []
    accepted: list[str] = []
    rejected: list[str] = []
    protected_set = set(protected)
    for entry in entries:
        if entry.task_id in protected_set:
            continue
        task = state.tasks[entry.task_id]
        if task.demand.fits_within(residual):
            residual = residual.subtract(task.demand)
            (retained if entry.is_current else accepted).append(entry.task_id)
        else:
            (preempted if entry.is_current else rejected).append(entry.task_id)
    if protected_set & set(preempted):
        raise StateValidationError("ASSUMP-054 protected task entered actual victim set")

    updated = state.snapshot()
    for task_id in preempted:
        updated = release_now(updated, task_id=task_id, terminal_state=TaskState.PREEMPTED)
    for task_id in accepted:
        updated = allocate_now(updated, task_id=task_id, server_id=server_id)
    for task_id in rejected:
        updated = _reject_returning(updated, task_id)
    validate_state_invariants(updated)
    return GuardedRoundTwoResult(
        updated,
        entries,
        selected,
        tuple(retained),
        tuple(preempted),
        tuple(accepted),
        tuple(rejected),
        reference_preempted,
        reference_accepted,
        protected,
        residual,
    )


class NoCascadingDKPPolicy:
    """ASSUMP-046 + ASSUMP-054 proposed method; never the official DK-P policy."""

    name = "proposed_dkp_initial_repair_no_cascading"

    def __init__(self, config: PipelineDKPConfig, selector: KnapsackSelector | None = None) -> None:
        self.config = config
        self.selector = selector or PyeasygaUtilityKnapsackSelector(config.ga)
        self._active_protection: dict[str, ProtectionRecord] = {}
        self._all_protection: dict[str, ProtectionRecord] = {}
        self._batches: list[ProtectionBatch] = []
        self._counters: Counter[str] = Counter()

    @property
    def protected_task_ids(self) -> frozenset[str]:
        return frozenset(self._active_protection)

    def _reconcile_terminal(self, state: SimulationState, epoch: int) -> None:
        for task_id in tuple(self._active_protection):
            allocation = state.allocations.get(task_id)
            if allocation is None:
                raise StateValidationError("protected task lost its allocation record")
            if allocation.is_active:
                if state.task_states[task_id] in {
                    TaskState.COMPLETED,
                    TaskState.PREEMPTED,
                    TaskState.EXPIRED,
                }:
                    raise StateValidationError("terminal protected task has an active allocation")
                continue
            if state.task_states[task_id] is TaskState.PREEMPTED:
                raise StateValidationError("protected task was preempted")
            self._counters[f"protected_terminal_{state.task_states[task_id].value}"] += 1
            record = self._active_protection.pop(task_id)
            end_epoch = allocation.end_slot if allocation.end_slot is not None else epoch
            self._counters["protection_duration_slots"] += end_epoch - record.protected_at_epoch

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> PipelineDKPAuctionResult:
        """Run the proposed method while retaining private protection state."""

        self._reconcile_terminal(state, epoch)
        selector = self.selector
        choose_equal_server = getattr(selector, "choose_uniform", None)
        if not callable(choose_equal_server):
            raise TypeError("modified DK-P selector must expose callable choose_uniform")
        result = self._run_auction(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=selector,
            choose_equal_server=choose_equal_server,
            epoch=epoch,
        )
        return result

    def _run_auction(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        selector: KnapsackSelector,
        choose_equal_server: Callable[[Sequence[str]], str],
        epoch: int,
    ) -> PipelineDKPAuctionResult:
        validate_state_invariants(state)
        self.config.validate_workload(state)
        task_ids = _validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")
        round_one_by_server = {
            server_id: run_dkr_round_one_for_server(
                state,
                server_id=server_id,
                requesting_task_ids=task_ids,
                selector=selector,
                config=self.config.retention_base,
            )
            for server_id in state.servers
        }
        round_one_bids = tuple(
            bid for server_result in round_one_by_server.values() for bid in server_result.bids
        )
        round_one = AuctionRound(AuctionRoundNumber.ROUND_ONE, epoch, task_ids, round_one_bids)
        selected_server: dict[str, str] = {}
        rejected_without_server: list[str] = []
        for task_id in task_ids:
            bids = tuple(bid for bid in round_one_bids if bid.task_id == task_id)
            if len(bids) != len(state.servers):
                raise StateValidationError("each task must receive one bid from every server")
            minimum = min(bid.price for bid in bids)
            if minimum > state.tasks[task_id].utility:
                rejected_without_server.append(task_id)
                continue
            cheapest = tuple(sorted(bid.server_id for bid in bids if bid.price == minimum))
            chosen = choose_equal_server(cheapest)
            if chosen not in cheapest:
                raise StateValidationError("tie selector returned non-minimum server")
            selected_server[task_id] = chosen

        updated = state.snapshot()
        rejected = list(rejected_without_server)
        for task_id in rejected_without_server:
            updated = _reject_returning(updated, task_id)
        accepted: list[str] = []
        retained: list[str] = []
        preempted: list[str] = []
        round_two_task_ids: list[str] = []
        round_two_knapsack: dict[str, tuple[str, ...]] = {}
        round_two_scores: dict[str, tuple[DKPScoreEntry, ...]] = {}
        for server_id in state.servers:
            returning = tuple(
                task_id for task_id in task_ids if selected_server.get(task_id) == server_id
            )
            result = run_guarded_dkp_round_two_for_server(
                updated,
                server_id=server_id,
                returning_task_ids=returning,
                time_remaining_by_task=time_remaining_by_task,
                selector=selector,
                protected_task_ids=frozenset(self._active_protection),
            )
            self._counters["reference_preemptions"] += len(result.reference_preempted_task_ids)
            self._counters["actual_preemptions"] += len(result.preempted_task_ids)
            self._counters["protected_victim_attempts"] += len(
                set(result.reference_preempted_task_ids) & set(result.protected_task_ids)
            )
            self._counters["incoming_rejected_due_protection"] += len(
                set(result.reference_accepted_task_ids) - set(result.accepted_task_ids)
            )
            self._counters["incoming_accepted_due_protection"] += len(
                set(result.accepted_task_ids) - set(result.reference_accepted_task_ids)
            )
            updated = result.final_state
            if result.preempted_task_ids and result.accepted_task_ids:
                incoming_utility = float(
                    sum(updated.tasks[task_id].utility for task_id in result.accepted_task_ids)
                )
                victim_utility = float(
                    sum(updated.tasks[task_id].utility for task_id in result.preempted_task_ids)
                )
                self._batches.append(
                    ProtectionBatch(
                        epoch,
                        server_id,
                        result.accepted_task_ids,
                        result.preempted_task_ids,
                        incoming_utility,
                        victim_utility,
                    )
                )
                for task_id in result.accepted_task_ids:
                    if task_id in self._all_protection:
                        raise StateValidationError("protection event recorded more than once")
                    record = ProtectionRecord(epoch, server_id)
                    self._active_protection[task_id] = record
                    self._all_protection[task_id] = record
                    self._counters["protection_events"] += 1
            accepted.extend(result.accepted_task_ids)
            rejected.extend(result.rejected_task_ids)
            retained.extend(result.retained_task_ids)
            preempted.extend(result.preempted_task_ids)
            round_two_task_ids.extend(entry.task_id for entry in result.score_entries)
            round_two_knapsack[server_id] = result.knapsack_selected_task_ids
            round_two_scores[server_id] = result.score_entries

        if set(preempted) & set(self._all_protection):
            raise StateValidationError("protected task was preempted")
        validate_state_invariants(updated)
        metadata = self.config.as_metadata() | {
            "method": self.name,
            "scientific_status": "proposed_modified_method",
            "ga_repair": "ASSUMP-046_full_initial_population_only",
            "preemption_guard": "ASSUMP-054_permanent_batch_derived_no_cascading",
            "official_pipeline_changed": "false",
        }
        return PipelineDKPAuctionResult(
            updated,
            round_one,
            AuctionRound(AuctionRoundNumber.ROUND_TWO, epoch, tuple(round_two_task_ids), ()),
            tuple(accepted),
            tuple(rejected),
            tuple(retained),
            tuple(preempted),
            selected_server,
            {
                server_id: server_result.selected_task_ids
                for server_id, server_result in round_one_by_server.items()
            },
            round_two_knapsack,
            round_two_scores,
            metadata,
        )

    def public_summary(
        self, final_state: SimulationState, events: Sequence[object]
    ) -> dict[str, object]:
        """Return aggregate-only ASSUMP-054 evidence after the temporal run."""

        self._reconcile_terminal(final_state, final_state.current_slot)
        completed_ids = {
            task_id
            for task_id, status in final_state.task_states.items()
            if status is TaskState.COMPLETED
        }
        expired_ids = {
            task_id
            for task_id, status in final_state.task_states.items()
            if status is TaskState.EXPIRED
        }
        preempted_ids = {
            task_id
            for task_id, status in final_state.task_states.items()
            if status is TaskState.PREEMPTED
        }
        protected_ids = set(self._all_protection)
        if protected_ids & preempted_ids:
            raise StateValidationError("protected task reached PREEMPTED terminal state")
        batch_incoming = {task_id for batch in self._batches for task_id in batch.incoming_task_ids}
        batch_victims = {task_id for batch in self._batches for task_id in batch.victim_task_ids}
        terminal_incoming = float(
            sum(final_state.tasks[task_id].utility for task_id in batch_incoming & completed_ids)
        )
        terminal_victim = float(
            sum(final_state.tasks[task_id].utility for task_id in batch_victims & completed_ids)
        )
        local_positive_terminal_negative = 0
        local_signs: Counter[str] = Counter()
        terminal_signs: Counter[str] = Counter()
        for batch in self._batches:
            local = batch.incoming_utility - batch.victim_utility
            terminal = (
                sum(
                    final_state.tasks[task_id].utility
                    for task_id in batch.incoming_task_ids
                    if task_id in completed_ids
                )
                - batch.victim_utility
            )
            local_signs["positive" if local > 0.0 else "negative" if local < 0.0 else "zero"] += 1
            terminal_signs[
                "positive" if terminal > 0.0 else "negative" if terminal < 0.0 else "zero"
            ] += 1
            if local > 0.0 and terminal < 0.0:
                local_positive_terminal_negative += 1
        active_intervals = []
        durations = []
        for task_id, record in self._all_protection.items():
            allocation = final_state.allocations[task_id]
            end = allocation.end_slot
            if end is None:
                raise StateValidationError("protected allocation remained active after simulation")
            active_intervals.append((record.protected_at_epoch, end))
            durations.append(end - record.protected_at_epoch)
        waiting_expirations_during_protection = 0
        for event in events:
            event_type = getattr(getattr(event, "event_type", None), "value", None)
            reason = str(getattr(event, "reason", ""))
            epoch = int(getattr(event, "time", -1))
            if (
                event_type == "expired"
                and ("waiting" in reason or "post_rejection" in reason)
                and any(start <= epoch <= end for start, end in active_intervals)
            ):
                waiting_expirations_during_protection += 1
        epoch_resource_share: list[dict[str, float | int]] = []
        if active_intervals:
            first_epoch = min(start for start, _ in active_intervals)
            last_epoch = max(end for _, end in active_intervals)
            for epoch in range(first_epoch, last_epoch + 1):
                server_ratios: list[tuple[float, float, float, float]] = []
                protected_count = 0
                for server_id, server in final_state.servers.items():
                    demand = ResourceVector.zero()
                    for task_id, record in self._all_protection.items():
                        allocation = final_state.allocations[task_id]
                        end = allocation.end_slot
                        if (
                            record.server_id == server_id
                            and end is not None
                            and record.protected_at_epoch <= epoch <= end
                        ):
                            protected_count += 1
                            demand = demand + final_state.tasks[task_id].demand
                    capacity = server.capacity
                    server_ratios.append(
                        (
                            demand.storage / capacity.storage if capacity.storage else 0.0,
                            demand.computation / capacity.computation
                            if capacity.computation
                            else 0.0,
                            demand.upload / capacity.upload if capacity.upload else 0.0,
                            demand.download / capacity.download if capacity.download else 0.0,
                        )
                    )
                flattened = [value for ratios in server_ratios for value in ratios]
                epoch_resource_share.append(
                    {
                        "epoch": epoch,
                        "protected_server_task_count": protected_count,
                        "mean_dimension_share_across_servers": sum(flattened) / len(flattened),
                        "maximum_dimension_share": max(flattened, default=0.0),
                    }
                )
        sample_means = [
            float(row["mean_dimension_share_across_servers"]) for row in epoch_resource_share
        ]
        sample_maxima = [float(row["maximum_dimension_share"]) for row in epoch_resource_share]
        return {
            "label": "[روش اصلاح‌شده پیشنهادی] ASSUMP-046_plus_ASSUMP-054",
            "task_identifiers_recorded": False,
            "raw_edges_recorded": False,
            "raw_workload_recorded": False,
            "protection": {
                "created": len(protected_ids),
                "completed": len(protected_ids & completed_ids),
                "expired": len(protected_ids & expired_ids),
                "preempted": len(protected_ids & preempted_ids),
                "victim_attempts_blocked": self._counters["protected_victim_attempts"],
                "mean_duration_slots": sum(durations) / len(durations) if durations else 0.0,
                "maximum_duration_slots": max(durations, default=0),
            },
            "preemption": {
                "reference_without_guard": self._counters["reference_preemptions"],
                "actual_with_guard": self._counters["actual_preemptions"],
                "batch_count": len(self._batches),
                "incoming_count": sum(len(batch.incoming_task_ids) for batch in self._batches),
                "victim_count": sum(len(batch.victim_task_ids) for batch in self._batches),
                "incoming_utility": sum(batch.incoming_utility for batch in self._batches),
                "victim_utility": sum(batch.victim_utility for batch in self._batches),
                "local_net_utility": sum(
                    batch.incoming_utility - batch.victim_utility for batch in self._batches
                ),
                "terminal_incoming_completed_utility": terminal_incoming,
                "terminal_victim_completed_utility": terminal_victim,
                "terminal_net_after_victim_opportunity_cost": terminal_incoming
                - sum(batch.victim_utility for batch in self._batches),
                "local_positive_terminal_negative_batches": local_positive_terminal_negative,
                "local_effect_sign_counts": {
                    key: local_signs[key] for key in ("positive", "zero", "negative")
                },
                "terminal_effect_sign_counts": {
                    key: terminal_signs[key] for key in ("positive", "zero", "negative")
                },
                "direct_chain_maximum_depth": 1 if self._batches else 0,
            },
            "admission": {
                "rejected_due_protection": self._counters["incoming_rejected_due_protection"],
                "accepted_due_protection": self._counters["incoming_accepted_due_protection"],
            },
            "resource_share": {
                "sample_count": len(epoch_resource_share),
                "mean_of_dimension_means": (
                    sum(sample_means) / len(sample_means) if sample_means else 0.0
                ),
                "maximum_dimension_share": max(sample_maxima, default=0.0),
                "by_epoch": epoch_resource_share,
            },
            "starvation_proxy": {
                "waiting_expiration_events_during_any_protection": (
                    waiting_expirations_during_protection
                )
            },
        }


def assert_no_cascading_summary(summary: Mapping[str, object]) -> None:
    """Validate public guard invariants without accessing private task identifiers."""

    protection = summary.get("protection")
    preemption = summary.get("preemption")
    if not isinstance(protection, Mapping) or not isinstance(preemption, Mapping):
        raise TypeError("No-Cascading summary sections are missing")
    if int(protection["preempted"]) != 0:
        raise StateValidationError("protected tasks must never be preempted")
    if int(preemption["direct_chain_maximum_depth"]) > 1:
        raise StateValidationError("ASSUMP-054 direct preemption chain exceeds depth one")
    if not isclose(
        float(preemption["local_net_utility"]),
        float(preemption["incoming_utility"]) - float(preemption["victim_utility"]),
        abs_tol=1e-9,
    ):
        raise StateValidationError("local preemption Utility does not conserve")


def validate_utility_conservation(
    *, total: float, completed: float, rejected: float, tolerance: float = 1e-9
) -> float:
    """Return the residual or fail the Stage 15-M Utility invariant."""

    residual = float(total) - float(completed) - float(rejected)
    if abs(residual) > tolerance:
        raise StateValidationError("Stage 15-M Utility conservation failed")
    return residual
