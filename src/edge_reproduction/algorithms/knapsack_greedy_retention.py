"""KnapsackGreedy Retention reconstructed from arXiv v2 and ASSUMP-007..009."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from edge_reproduction.algorithms.feasibility import utility_time_ratio
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.algorithms.pricing import (
    algorithm_one_congestion,
    fit_price,
    impossible_price,
    preemption_price,
    utility_time_percentile,
)
from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.bid import AuctionRound, Bid
from edge_reproduction.models.enums import AuctionRoundNumber, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import (
    has_sufficient_resources,
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


@dataclass(frozen=True, slots=True)
class KGRetentionRoundTwoResult:
    """Final state and decisions from one server's non-preemptive Round 2."""

    final_state: SimulationState
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    auto_fit_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KGRetentionAuctionResult:
    """Complete two-round KG-R result for one auction epoch."""

    final_state: SimulationState
    round_one: AuctionRound
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    selected_server_by_task: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class KnapsackGreedyRetentionPolicy:
    """Common-interface wrapper around the complete KG-R auction control flow."""

    selector: KnapsackSelector
    name: str = "knapsack_greedy_retention"

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> KGRetentionAuctionResult:
        choose_equal_server = getattr(self.selector, "choose_kg_equal_minimum_server", None)
        if choose_equal_server is not None and not callable(choose_equal_server):
            raise TypeError("KG selector tie resolver must be callable")
        return run_knapsack_greedy_retention(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=self.selector,
            choose_equal_server=choose_equal_server,
            epoch=epoch,
        )


def validate_task_ids(
    state: SimulationState, task_ids: Sequence[str], *, field_name: str
) -> tuple[str, ...]:
    normalized = tuple(task_ids)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    for task_id in normalized:
        if task_id not in state.tasks:
            raise KeyError(f"unknown task_id: {task_id}")
    return normalized


def require_time_remaining(task_id: str, time_remaining_by_task: Mapping[str, float]) -> float:
    try:
        value = time_remaining_by_task[task_id]
    except KeyError as error:
        raise KeyError(f"missing time remaining for task: {task_id}") from error
    # Reuse the paper-aligned ratio validator for type, finiteness and positivity.
    utility_time_ratio(0.0, value)
    return float(value)


def _selected_subset_demand(tasks: Sequence[Task], selected: set[str]) -> ResourceVector:
    total = ResourceVector.zero()
    for task in tasks:
        if task.task_id in selected:
            total = total + task.demand
    return total


def run_kg_retention_round_one_for_server(
    state: SimulationState,
    *,
    server_id: str,
    requesting_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
) -> tuple[Bid, ...]:
    """Run Algorithm 1 for one server without mutating simulation state."""

    task_ids = validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    if any(
        (allocation := state.allocations.get(task_id)) is not None and allocation.is_active
        for task_id in task_ids
    ):
        raise StateValidationError("a currently active task cannot request Round 1 again")
    server = state.servers[server_id]
    residual = remaining_resources(state, server_id)
    requesting_tasks = tuple(state.tasks[task_id] for task_id in task_ids)
    selected_ids = tuple(selector.select(capacity=residual, tasks=requesting_tasks))
    if len(selected_ids) != len(set(selected_ids)):
        raise StateValidationError("knapsack selector returned duplicate task identifiers")
    selected = set(selected_ids)
    if not selected.issubset(task_ids):
        raise StateValidationError("knapsack selector returned a task outside the request pool")
    if not _selected_subset_demand(requesting_tasks, selected).fits_within(residual):
        raise StateValidationError("knapsack selector returned a jointly infeasible subset")

    current_tasks = tuple(
        state.tasks[allocation.task_id]
        for allocation in state.active_allocations_for_server(server_id)
    )
    current_pairs = tuple(
        (task.utility, require_time_remaining(task.task_id, time_remaining_by_task))
        for task in current_tasks
    )

    bids: list[Bid] = []
    for task in requesting_tasks:
        congestion = algorithm_one_congestion(task.demand, residual, server.capacity)
        if congestion is None:
            bids.append(
                Bid(
                    task.task_id,
                    server_id,
                    AuctionRoundNumber.ROUND_ONE,
                    impossible_price(task.utility),
                    feasible=False,
                )
            )
            continue
        if task.task_id in selected:
            bids.append(
                Bid(
                    task.task_id,
                    server_id,
                    AuctionRoundNumber.ROUND_ONE,
                    fit_price(task.utility),
                    feasible=True,
                    auto_fit=True,
                    marked_task_ids=(task.task_id,),
                )
            )
            continue
        percentile = utility_time_percentile(
            new_utility=task.utility,
            new_time_remaining=require_time_remaining(task.task_id, time_remaining_by_task),
            current_utility_time_pairs=current_pairs,
        )
        bids.append(
            Bid(
                task.task_id,
                server_id,
                AuctionRoundNumber.ROUND_ONE,
                preemption_price(
                    task.utility,
                    percentile=percentile,
                    congestion=congestion,
                ),
            )
        )
    return tuple(bids)


def reject_for_current_round(state: SimulationState, task_id: str) -> SimulationState:
    if task_id in state.allocations:
        raise StateValidationError("a task with an allocation cannot be rejected")
    updated = state.snapshot()
    updated.task_states[task_id] = TaskState.REJECTED
    validate_state_invariants(updated)
    return updated


def run_kg_retention_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    auto_fit_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
) -> KGRetentionRoundTwoResult:
    """Run the ASSUMP-009 fit-only Round 2 for one server."""

    returning = validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    auto_fit = validate_task_ids(state, auto_fit_task_ids, field_name="auto_fit_task_ids")
    if not set(auto_fit).issubset(returning):
        raise ValueError("auto_fit_task_ids must be a subset of returning_task_ids")

    remaining = tuple(task_id for task_id in returning if task_id not in set(auto_fit))
    ranked = tuple(
        (
            utility_time_ratio(
                state.tasks[task_id].utility,
                require_time_remaining(task_id, time_remaining_by_task),
            ),
            task_id,
        )
        for task_id in remaining
    )
    ratios = tuple(ratio for ratio, _ in ranked)
    if len(ratios) != len(set(ratios)):
        raise UnresolvedDecisionError(
            "equal returning utility/time_remaining ratios require an unreported tie-break"
        )
    ordered_remaining = tuple(task_id for _, task_id in sorted(ranked, reverse=True))

    updated = state.snapshot()
    accepted: list[str] = []
    rejected: list[str] = []
    for task_id in auto_fit:
        if not has_sufficient_resources(updated, server_id, updated.tasks[task_id].demand):
            raise StateValidationError("an autoFit task no longer fits the server residual")
        updated = allocate_now(updated, task_id=task_id, server_id=server_id)
        accepted.append(task_id)
    for task_id in ordered_remaining:
        task = updated.tasks[task_id]
        if has_sufficient_resources(updated, server_id, task.demand):
            updated = allocate_now(updated, task_id=task_id, server_id=server_id)
            accepted.append(task_id)
        else:
            updated = reject_for_current_round(updated, task_id)
            rejected.append(task_id)
    validate_state_invariants(updated)
    return KGRetentionRoundTwoResult(updated, tuple(accepted), tuple(rejected), tuple(auto_fit))


def choose_servers_from_bids(
    state: SimulationState,
    task_ids: tuple[str, ...],
    bids: tuple[Bid, ...],
    *,
    choose_equal_server: Callable[[Sequence[str]], str] | None = None,
) -> tuple[dict[str, str], tuple[str, ...]]:
    selected: dict[str, str] = {}
    rejected: list[str] = []
    for task_id in task_ids:
        task_bids = tuple(bid for bid in bids if bid.task_id == task_id)
        if len(task_bids) != len(state.servers):
            raise StateValidationError("each task must receive a bid from every server")
        minimum = min(bid.price for bid in task_bids)
        if minimum > state.tasks[task_id].utility:
            rejected.append(task_id)
            continue
        cheapest_server_ids = tuple(
            sorted(bid.server_id for bid in task_bids if bid.price == minimum)
        )
        if len(cheapest_server_ids) == 1:
            selected[task_id] = cheapest_server_ids[0]
            continue
        if choose_equal_server is None:
            raise UnresolvedDecisionError(
                "equal minimum server prices require an unreported client tie-break"
            )
        chosen_server_id = choose_equal_server(cheapest_server_ids)
        if chosen_server_id not in cheapest_server_ids:
            raise StateValidationError("KG tie selector returned a non-minimum-price server")
        selected[task_id] = chosen_server_id
    return selected, tuple(rejected)


def run_knapsack_greedy_retention(
    state: SimulationState,
    *,
    requesting_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    choose_equal_server: Callable[[Sequence[str]], str] | None = None,
    epoch: int = 0,
) -> KGRetentionAuctionResult:
    """Execute the complete two-round KG-R control flow for one auction epoch."""

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
    for server_id in state.servers:
        returning = tuple(
            task_id for task_id in task_ids if selected_server_by_task.get(task_id) == server_id
        )
        server_auto_fit = tuple(
            bid.task_id
            for bid in bids
            if bid.server_id == server_id and bid.task_id in returning and bid.auto_fit
        )
        result = run_kg_retention_round_two_for_server(
            updated,
            server_id=server_id,
            returning_task_ids=returning,
            auto_fit_task_ids=server_auto_fit,
            time_remaining_by_task=time_remaining_by_task,
        )
        updated = result.final_state
        accepted.extend(result.accepted_task_ids)
        rejected.extend(result.rejected_task_ids)
    validate_state_invariants(updated)
    return KGRetentionAuctionResult(
        updated,
        round_one,
        tuple(accepted),
        tuple(rejected),
        selected_server_by_task,
    )
