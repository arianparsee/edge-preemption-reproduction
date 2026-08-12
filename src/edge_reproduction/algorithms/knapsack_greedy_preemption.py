"""KnapsackGreedy Preemption from arXiv v2 with ASSUMP-004..008 and 010."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from edge_reproduction.algorithms.feasibility import (
    can_preempt_single_victim,
    utility_time_ratio,
)
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.algorithms.knapsack_greedy_retention import (
    choose_servers_from_bids,
    reject_for_current_round,
    require_time_remaining,
    run_kg_retention_round_one_for_server,
    validate_task_ids,
)
from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.bid import AuctionRound
from edge_reproduction.models.enums import AuctionRoundNumber
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import (
    allocate_now,
    preempt_and_allocate_now,
)
from edge_reproduction.simulation.invariants import (
    has_sufficient_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class VictimSnapshotEntry:
    """One immutable ASSUMP-010 victim record captured at Round-2 start."""

    task_id: str
    utility_time_ratio: float
    time_remaining: float


@dataclass(frozen=True, slots=True)
class KGPreemptionRoundTwoResult:
    """Decisions and final state from one server's preemptive Round 2."""

    final_state: SimulationState
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    auto_fit_task_ids: tuple[str, ...]
    victim_snapshot_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KGPreemptionAuctionResult:
    """Complete two-round KG-P result for one auction epoch."""

    final_state: SimulationState
    round_one: AuctionRound
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    selected_server_by_task: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class KnapsackGreedyPreemptionPolicy:
    """Common-interface wrapper around the complete KG-P auction control flow."""

    selector: KnapsackSelector
    name: str = "knapsack_greedy_preemption"

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> KGPreemptionAuctionResult:
        choose_equal_server = getattr(self.selector, "choose_kg_equal_minimum_server", None)
        if choose_equal_server is not None and not callable(choose_equal_server):
            raise TypeError("KG selector tie resolver must be callable")
        return run_knapsack_greedy_preemption(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=self.selector,
            choose_equal_server=choose_equal_server,
            epoch=epoch,
        )


def capture_victim_snapshot(
    state: SimulationState,
    *,
    server_id: str,
    time_remaining_by_task: Mapping[str, float],
) -> tuple[VictimSnapshotEntry, ...]:
    """Capture and rank the fixed ASSUMP-010 victim pool before any admission."""

    captured: list[VictimSnapshotEntry] = []
    for allocation in state.active_allocations_for_server(server_id):
        frozen_time = require_time_remaining(allocation.task_id, time_remaining_by_task)
        captured.append(
            VictimSnapshotEntry(
                allocation.task_id,
                utility_time_ratio(state.tasks[allocation.task_id].utility, frozen_time),
                frozen_time,
            )
        )
    entries = tuple(captured)
    ratios = tuple(entry.utility_time_ratio for entry in entries)
    if len(ratios) != len(set(ratios)):
        raise UnresolvedDecisionError(
            "equal victim snapshot utility/time_remaining ratios require a tie-break"
        )
    return tuple(sorted(entries, key=lambda entry: entry.utility_time_ratio))


def _rank_returning_tasks(
    state: SimulationState,
    task_ids: tuple[str, ...],
    time_remaining_by_task: Mapping[str, float],
) -> tuple[str, ...]:
    ranked = tuple(
        (
            utility_time_ratio(
                state.tasks[task_id].utility,
                require_time_remaining(task_id, time_remaining_by_task),
            ),
            task_id,
        )
        for task_id in task_ids
    )
    ratios = tuple(ratio for ratio, _ in ranked)
    if len(ratios) != len(set(ratios)):
        raise UnresolvedDecisionError(
            "equal returning utility/time_remaining ratios require an unreported tie-break"
        )
    return tuple(task_id for _, task_id in sorted(ranked, reverse=True))


def _active_snapshot_victim(
    state: SimulationState, server_id: str, entry: VictimSnapshotEntry
) -> Task | None:
    allocation = state.allocations.get(entry.task_id)
    if allocation is None or not allocation.is_active:
        return None
    if allocation.server_id != server_id:
        raise StateValidationError("snapshot victim moved away from its captured server")
    return state.tasks[entry.task_id]


def run_kg_preemption_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    auto_fit_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
) -> KGPreemptionRoundTwoResult:
    """Execute Algorithm 2 using the fixed victim snapshot in ASSUMP-010."""

    returning = validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    auto_fit = validate_task_ids(state, auto_fit_task_ids, field_name="auto_fit_task_ids")
    if not set(auto_fit).issubset(returning):
        raise ValueError("auto_fit_task_ids must be a subset of returning_task_ids")

    # Both orders and all time values are frozen before the first admission.
    victim_snapshot = capture_victim_snapshot(
        state,
        server_id=server_id,
        time_remaining_by_task=time_remaining_by_task,
    )
    auto_fit_set = set(auto_fit)
    remaining = tuple(task_id for task_id in returning if task_id not in auto_fit_set)
    ordered_remaining = _rank_returning_tasks(state, remaining, time_remaining_by_task)

    updated = state.snapshot()
    accepted: list[str] = []
    rejected: list[str] = []
    preempted: list[str] = []
    for task_id in auto_fit:
        task = updated.tasks[task_id]
        if not has_sufficient_resources(updated, server_id, task.demand):
            raise StateValidationError("an autoFit task no longer fits the server residual")
        updated = allocate_now(updated, task_id=task_id, server_id=server_id)
        accepted.append(task_id)

    for task_id in ordered_remaining:
        incoming = updated.tasks[task_id]
        if has_sufficient_resources(updated, server_id, incoming.demand):
            updated = allocate_now(updated, task_id=task_id, server_id=server_id)
            accepted.append(task_id)
            continue

        selected_victim: VictimSnapshotEntry | None = None
        for entry in victim_snapshot:
            victim = _active_snapshot_victim(updated, server_id, entry)
            if victim is None:
                continue
            if can_preempt_single_victim(
                updated,
                incoming_task=incoming,
                victim_task=victim,
                server_id=server_id,
                incoming_time=incoming.deadline_slots,
                victim_time_remaining=entry.time_remaining,
            ):
                selected_victim = entry
                break

        if selected_victim is None:
            updated = reject_for_current_round(updated, task_id)
            rejected.append(task_id)
            continue

        updated = preempt_and_allocate_now(
            updated,
            incoming_task_id=task_id,
            server_id=server_id,
            victim_task_ids=(selected_victim.task_id,),
        )
        preempted.append(selected_victim.task_id)
        accepted.append(task_id)

    validate_state_invariants(updated)
    return KGPreemptionRoundTwoResult(
        updated,
        tuple(accepted),
        tuple(rejected),
        tuple(preempted),
        tuple(auto_fit),
        tuple(entry.task_id for entry in victim_snapshot),
    )


def run_knapsack_greedy_preemption(
    state: SimulationState,
    *,
    requesting_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    choose_equal_server: Callable[[Sequence[str]], str] | None = None,
    epoch: int = 0,
) -> KGPreemptionAuctionResult:
    """Execute the complete two-round KG-P control flow for one auction epoch."""

    task_ids = validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")
    bids = tuple(
        bid
        for server_id in state.servers
        for bid in run_kg_retention_round_one_for_server(
            state,
            server_id=server_id,
            requesting_task_ids=task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=selector,
        )
    )
    round_one = AuctionRound(AuctionRoundNumber.ROUND_ONE, epoch, task_ids, bids)
    selected_server_by_task, rejected_without_server = choose_servers_from_bids(
        state, task_ids, bids, choose_equal_server=choose_equal_server
    )

    updated = state.snapshot()
    rejected: list[str] = list(rejected_without_server)
    for task_id in rejected_without_server:
        updated = reject_for_current_round(updated, task_id)
    accepted: list[str] = []
    preempted: list[str] = []
    for server_id in state.servers:
        returning = tuple(
            task_id for task_id in task_ids if selected_server_by_task.get(task_id) == server_id
        )
        server_auto_fit = tuple(
            bid.task_id
            for bid in bids
            if bid.server_id == server_id and bid.task_id in returning and bid.auto_fit
        )
        result = run_kg_preemption_round_two_for_server(
            updated,
            server_id=server_id,
            returning_task_ids=returning,
            auto_fit_task_ids=server_auto_fit,
            time_remaining_by_task=time_remaining_by_task,
        )
        updated = result.final_state
        accepted.extend(result.accepted_task_ids)
        rejected.extend(result.rejected_task_ids)
        preempted.extend(result.preempted_task_ids)
    validate_state_invariants(updated)
    return KGPreemptionAuctionResult(
        updated,
        round_one,
        tuple(accepted),
        tuple(rejected),
        tuple(preempted),
        selected_server_by_task,
    )
