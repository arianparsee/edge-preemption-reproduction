"""ASSUMP-055 one-auction cooldown for the proposed modified DK-P path.

The guard is evaluated only after the unchanged ASSUMP-046 selector and score
plan have completed.  It never modifies the official DK-P implementation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

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
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaUtilityKnapsackSelector
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.bid import AuctionRound
from edge_reproduction.models.enums import AuctionRoundNumber, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.simulation.accounting import allocate_now, release_now
from edge_reproduction.simulation.invariants import validate_state_invariants
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class CooldownRecord:
    """Private lifecycle of one cooldown created by a committed batch."""

    created_epoch: int
    server_id: str


@dataclass(frozen=True, slots=True)
class PreemptionBatch:
    """Private task-level preemption batch retained only in process memory."""

    epoch: int
    server_id: str
    incoming_task_ids: tuple[str, ...]
    victim_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AbortedTransaction:
    """Private task-level evidence for one post-selection server abort."""

    epoch: int
    server_id: str
    protected_planned_victim_ids: tuple[str, ...]
    unprotected_planned_victim_ids: tuple[str, ...]
    returning_task_ids: tuple[str, ...]
    suppressed_planned_acceptance_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CooldownRoundTwoResult:
    """One server plan and atomic result under ASSUMP-055."""

    final_state: SimulationState
    score_entries: tuple[DKPScoreEntry, ...]
    knapsack_selected_task_ids: tuple[str, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    planned_retained_task_ids: tuple[str, ...]
    planned_preempted_task_ids: tuple[str, ...]
    planned_accepted_task_ids: tuple[str, ...]
    planned_rejected_task_ids: tuple[str, ...]
    cooldown_task_ids: tuple[str, ...]
    threatened_cooldown_task_ids: tuple[str, ...]
    transaction_aborted: bool
    final_residual: ResourceVector


def _plan_entries(
    state: SimulationState,
    entries: Sequence[DKPScoreEntry],
    capacity: ResourceVector,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    ResourceVector,
]:
    """Apply the official deterministic score-entry traversal without commit."""

    residual = capacity
    retained: list[str] = []
    preempted: list[str] = []
    accepted: list[str] = []
    rejected: list[str] = []
    for entry in entries:
        demand = state.tasks[entry.task_id].demand
        if demand.fits_within(residual):
            residual = residual.subtract(demand)
            (retained if entry.is_current else accepted).append(entry.task_id)
        else:
            (preempted if entry.is_current else rejected).append(entry.task_id)
    return tuple(retained), tuple(preempted), tuple(accepted), tuple(rejected), residual


def run_cooldown_dkp_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    cooldown_task_ids: Sequence[str],
) -> CooldownRoundTwoResult:
    """Run unchanged selection, then atomically abort only a threatened transaction."""

    validate_state_invariants(state)
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    returning = _validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    active = state.active_allocations_for_server(server_id)
    current = tuple(allocation.task_id for allocation in active)
    current_set = set(current)
    cooldown_input = tuple(cooldown_task_ids)
    if len(cooldown_input) != len(set(cooldown_input)):
        raise ValueError("cooldown_task_ids must not contain duplicates")
    cooldown_input_set = set(cooldown_input)
    cooldown = tuple(task_id for task_id in current if task_id in cooldown_input_set)
    if len(cooldown) != len(cooldown_input_set):
        raise StateValidationError("every cooldown task must be active on the selected server")
    if current_set & set(returning):
        raise StateValidationError("current and returning task pools must be disjoint")
    for allocation in active:
        if allocation.resources != state.tasks[allocation.task_id].demand:
            raise StateValidationError("cooldown DK-P requires allocation resources equal demand")
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
        current_task_ids=current_set,
        selected_task_ids=set(selected),
        time_remaining_by_task=time_remaining_by_task,
    )
    planned_retained, planned_preempted, planned_accepted, planned_rejected, residual = (
        _plan_entries(state, entries, capacity)
    )
    cooldown_set = set(cooldown)
    threatened = tuple(task_id for task_id in planned_preempted if task_id in cooldown_set)

    if threatened:
        updated = state.snapshot()
        for task_id in returning:
            updated = _reject_returning(updated, task_id)
        retained = current
        preempted: tuple[str, ...] = ()
        accepted: tuple[str, ...] = ()
        rejected = returning
        retained_demand = ResourceVector.zero()
        for task_id in retained:
            retained_demand = retained_demand + state.tasks[task_id].demand
        if not retained_demand.fits_within(capacity):
            raise StateValidationError("pre-abort current allocations are not jointly feasible")
        final_residual = capacity.subtract(retained_demand)
        aborted = True
    else:
        updated = state.snapshot()
        for task_id in planned_preempted:
            updated = release_now(updated, task_id=task_id, terminal_state=TaskState.PREEMPTED)
        for task_id in planned_accepted:
            updated = allocate_now(updated, task_id=task_id, server_id=server_id)
        for task_id in planned_rejected:
            updated = _reject_returning(updated, task_id)
        retained = planned_retained
        preempted = planned_preempted
        accepted = planned_accepted
        rejected = planned_rejected
        final_residual = residual
        aborted = False

    if cooldown_set & set(preempted):
        raise StateValidationError("ASSUMP-055 cooldown task entered actual victim set")
    validate_state_invariants(updated)
    return CooldownRoundTwoResult(
        updated,
        entries,
        selected,
        retained,
        preempted,
        accepted,
        rejected,
        planned_retained,
        planned_preempted,
        planned_accepted,
        planned_rejected,
        cooldown,
        threatened,
        aborted,
        final_residual,
    )


def _maximum_chain_depth(batches: Sequence[PreemptionBatch]) -> int:
    """Return the maximum incoming-to-victim path length using private IDs."""

    edges: dict[str, set[str]] = {}
    for batch in batches:
        for incoming in batch.incoming_task_ids:
            edges.setdefault(incoming, set()).update(batch.victim_task_ids)

    memo: dict[str, int] = {}

    def depth(task_id: str, visiting: frozenset[str]) -> int:
        if task_id in memo:
            return memo[task_id]
        if task_id in visiting:
            raise StateValidationError("preemption chain contains a cycle")
        children = edges.get(task_id, set())
        result = (
            0
            if not children
            else 1 + max(depth(child, visiting | {task_id}) for child in children)
        )
        memo[task_id] = result
        return result

    return max((depth(task_id, frozenset()) for task_id in edges), default=0)


class OneAuctionCooldownDKPPolicy:
    """ASSUMP-046 + ASSUMP-055 proposed method; never the official DK-P policy."""

    name = "proposed_dkp_initial_repair_one_auction_cooldown"

    def __init__(self, config: PipelineDKPConfig, selector: KnapsackSelector | None = None) -> None:
        self.config = config
        self.selector = selector or PyeasygaUtilityKnapsackSelector(config.ga)
        self._active_cooldowns: dict[str, CooldownRecord] = {}
        self._all_cooldowns: dict[str, CooldownRecord] = {}
        self._batches: list[PreemptionBatch] = []
        self._aborts: list[AbortedTransaction] = []
        self._counters: Counter[str] = Counter()

    @property
    def cooldown_task_ids(self) -> frozenset[str]:
        return frozenset(self._active_cooldowns)

    def _reconcile_terminal(self, state: SimulationState) -> None:
        for task_id in tuple(self._active_cooldowns):
            allocation = state.allocations.get(task_id)
            if allocation is None:
                raise StateValidationError("cooldown task lost its allocation record")
            if allocation.is_active:
                continue
            terminal = state.task_states[task_id]
            if terminal is TaskState.PREEMPTED:
                raise StateValidationError("task was preempted before its cooldown evaluation")
            self._active_cooldowns.pop(task_id)
            self._counters["cooldown_expired_without_evaluation"] += 1
            self._counters[f"cooldown_terminal_before_evaluation_{terminal.value}"] += 1

    def _eligible_for_server(
        self, state: SimulationState, *, server_id: str, epoch: int
    ) -> tuple[str, ...]:
        eligible: list[str] = []
        for allocation in state.active_allocations_for_server(server_id):
            record = self._active_cooldowns.get(allocation.task_id)
            if record is None:
                continue
            if record.server_id != server_id:
                raise StateValidationError("cooldown server identity changed")
            if allocation.start_slot < epoch:
                eligible.append(allocation.task_id)
        return tuple(eligible)

    def _consume(
        self,
        task_ids: Sequence[str],
        *,
        threatened_task_ids: Sequence[str],
        epoch: int,
    ) -> None:
        threatened = set(threatened_task_ids)
        for task_id in task_ids:
            record = self._active_cooldowns.pop(task_id)
            self._counters["cooldown_consumed"] += 1
            self._counters["cooldown_wait_epochs"] += epoch - record.created_epoch
            self._counters[
                "cooldown_consumed_with_abort"
                if task_id in threatened
                else "cooldown_consumed_without_intervention"
            ] += 1

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> PipelineDKPAuctionResult:
        """Run unchanged two-round selection and apply ASSUMP-055 after each plan."""

        self._reconcile_terminal(state)
        selector = self.selector
        choose_equal_server = getattr(selector, "choose_uniform", None)
        if not callable(choose_equal_server):
            raise TypeError("modified DK-P selector must expose callable choose_uniform")
        return self._run_auction(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=selector,
            choose_equal_server=choose_equal_server,
            epoch=epoch,
        )

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
        bids = tuple(bid for server in round_one_by_server.values() for bid in server.bids)
        round_one = AuctionRound(AuctionRoundNumber.ROUND_ONE, epoch, task_ids, bids)
        selected_server: dict[str, str] = {}
        rejected_without_server: list[str] = []
        for task_id in task_ids:
            task_bids = tuple(bid for bid in bids if bid.task_id == task_id)
            if len(task_bids) != len(state.servers):
                raise StateValidationError("each task must receive one bid from every server")
            minimum = min(bid.price for bid in task_bids)
            if minimum > state.tasks[task_id].utility:
                rejected_without_server.append(task_id)
                continue
            cheapest = tuple(sorted(bid.server_id for bid in task_bids if bid.price == minimum))
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
            cooldown = self._eligible_for_server(updated, server_id=server_id, epoch=epoch)
            result = run_cooldown_dkp_round_two_for_server(
                updated,
                server_id=server_id,
                returning_task_ids=returning,
                time_remaining_by_task=time_remaining_by_task,
                selector=selector,
                cooldown_task_ids=cooldown,
            )
            self._counters["reference_preemptions"] += len(result.planned_preempted_task_ids)
            self._counters["actual_preemptions"] += len(result.preempted_task_ids)
            if result.transaction_aborted:
                protected_victims = result.threatened_cooldown_task_ids
                protected_set = set(protected_victims)
                unprotected_victims = tuple(
                    task_id
                    for task_id in result.planned_preempted_task_ids
                    if task_id not in protected_set
                )
                self._aborts.append(
                    AbortedTransaction(
                        epoch,
                        server_id,
                        protected_victims,
                        unprotected_victims,
                        returning,
                        result.planned_accepted_task_ids,
                    )
                )
                self._counters["aborted_transactions"] += 1
            self._consume(
                result.cooldown_task_ids,
                threatened_task_ids=result.threatened_cooldown_task_ids,
                epoch=epoch,
            )
            updated = result.final_state
            if result.preempted_task_ids and result.accepted_task_ids:
                self._batches.append(
                    PreemptionBatch(
                        epoch,
                        server_id,
                        result.accepted_task_ids,
                        result.preempted_task_ids,
                    )
                )
                for task_id in result.accepted_task_ids:
                    if task_id in self._all_cooldowns:
                        raise StateValidationError("cooldown event recorded more than once")
                    record = CooldownRecord(epoch, server_id)
                    self._active_cooldowns[task_id] = record
                    self._all_cooldowns[task_id] = record
                    self._counters["cooldown_created"] += 1
            accepted.extend(result.accepted_task_ids)
            rejected.extend(result.rejected_task_ids)
            retained.extend(result.retained_task_ids)
            preempted.extend(result.preempted_task_ids)
            round_two_task_ids.extend(entry.task_id for entry in result.score_entries)
            round_two_knapsack[server_id] = result.knapsack_selected_task_ids
            round_two_scores[server_id] = result.score_entries

        validate_state_invariants(updated)
        metadata = self.config.as_metadata() | {
            "method": self.name,
            "scientific_status": "auxiliary_proposed_modified_method",
            "ga_repair": "ASSUMP-046_full_initial_population_only",
            "preemption_guard": "ASSUMP-055_minimum_one_auction_cooldown",
            "ASSUMP-054": "inactive_rejected_after_single_seed_pilot",
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

    def public_summary(self, final_state: SimulationState) -> dict[str, object]:
        """Return aggregate-only cooldown evidence after the temporal run."""

        self._reconcile_terminal(final_state)
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
        all_cooldown = set(self._all_cooldowns)
        aborted_returning = [
            task_id for abort in self._aborts for task_id in abort.returning_task_ids
        ]
        suppressed = [
            task_id for abort in self._aborts for task_id in abort.suppressed_planned_acceptance_ids
        ]
        protected_victims = [
            task_id for abort in self._aborts for task_id in abort.protected_planned_victim_ids
        ]
        unrelated_victims = [
            task_id for abort in self._aborts for task_id in abort.unprotected_planned_victim_ids
        ]
        unique_aborted_returning = set(aborted_returning)
        unique_suppressed = set(suppressed)
        return {
            "label": "[فرض روش اصلاح‌شده پیشنهادی — آزمون کمکی] ASSUMP-046_plus_ASSUMP-055",
            "task_identifiers_recorded": False,
            "raw_edges_recorded": False,
            "raw_workload_recorded": False,
            "cooldown": {
                "created": len(all_cooldown),
                "consumed": self._counters["cooldown_consumed"],
                "consumed_with_abort": self._counters["cooldown_consumed_with_abort"],
                "consumed_without_intervention": self._counters[
                    "cooldown_consumed_without_intervention"
                ],
                "expired_without_evaluation": self._counters[
                    "cooldown_expired_without_evaluation"
                ],
                "terminal_completed": len(all_cooldown & completed_ids),
                "terminal_expired": len(all_cooldown & expired_ids),
                "terminal_preempted": len(all_cooldown & preempted_ids),
                "mean_wait_epochs": (
                    self._counters["cooldown_wait_epochs"] / self._counters["cooldown_consumed"]
                    if self._counters["cooldown_consumed"]
                    else 0.0
                ),
            },
            "transactions": {
                "aborted": len(self._aborts),
                "returning_rejected_event_count": len(aborted_returning),
                "returning_rejected_unique_task_count": len(unique_aborted_returning),
                "returning_rejected_unique_utility": float(
                    sum(final_state.tasks[task_id].utility for task_id in unique_aborted_returning)
                ),
                "suppressed_planned_admission_event_count": len(suppressed),
                "suppressed_planned_admission_unique_task_count": len(unique_suppressed),
                "suppressed_planned_admission_unique_utility": float(
                    sum(final_state.tasks[task_id].utility for task_id in unique_suppressed)
                ),
                "protected_planned_victim_count": len(protected_victims),
                "protected_planned_victim_utility": float(
                    sum(final_state.tasks[task_id].utility for task_id in protected_victims)
                ),
                "unrelated_planned_victim_spared_count": len(unrelated_victims),
                "unrelated_planned_victim_spared_utility": float(
                    sum(final_state.tasks[task_id].utility for task_id in unrelated_victims)
                ),
            },
            "preemption": {
                "reference_before_guard": self._counters["reference_preemptions"],
                "actual_after_guard": self._counters["actual_preemptions"],
                "committed_preemptive_batches": len(self._batches),
                "chain_maximum_depth": _maximum_chain_depth(self._batches),
            },
        }


def assert_cooldown_summary(summary: Mapping[str, object]) -> None:
    """Validate aggregate ASSUMP-055 accounting without private identifiers."""

    cooldown = summary.get("cooldown")
    transactions = summary.get("transactions")
    if not isinstance(cooldown, Mapping) or not isinstance(transactions, Mapping):
        raise TypeError("cooldown summary sections are missing")
    created = int(cooldown["created"])
    consumed = int(cooldown["consumed"])
    expired = int(cooldown["expired_without_evaluation"])
    if created != consumed + expired:
        raise StateValidationError("every cooldown must be consumed or expire before evaluation")
    if int(cooldown["consumed_with_abort"]) > consumed:
        raise StateValidationError("aborted cooldown count exceeds consumed cooldowns")
    if int(transactions["suppressed_planned_admission_event_count"]) > int(
        transactions["returning_rejected_event_count"]
    ):
        raise StateValidationError("suppressed admissions exceed aborted returning tasks")
