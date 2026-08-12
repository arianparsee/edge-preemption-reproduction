"""Pipeline Double Knapsack Retention reconstructed from v2, [1], [4] and assumptions."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from math import isclose, isfinite
from statistics import fmean, pstdev
from types import MappingProxyType

from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.algorithms.pricing import (
    double_knapsack_round_one_price,
    double_knapsack_round_two_price,
    double_knapsack_violation,
)
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.bid import AuctionRound, Bid
from edge_reproduction.models.enums import AuctionRoundNumber, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.invariants import (
    remaining_resources,
    validate_state_invariants,
)
from edge_reproduction.simulation.state import SimulationState


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _validate_task_ids(
    state: SimulationState, task_ids: Sequence[str], *, field_name: str
) -> tuple[str, ...]:
    normalized = tuple(task_ids)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    for task_id in normalized:
        if task_id not in state.tasks:
            raise KeyError(f"unknown task_id: {task_id}")
    return normalized


def _subset_demand(tasks: Sequence[Task], selected_ids: set[str]) -> ResourceVector:
    demand = ResourceVector.zero()
    for task in tasks:
        if task.task_id in selected_ids:
            demand = demand + task.demand
    return demand


def _validate_selector_result(
    *,
    selected_ids: Sequence[str],
    tasks: Sequence[Task],
    capacity: ResourceVector,
) -> tuple[str, ...]:
    selected = tuple(selected_ids)
    if len(selected) != len(set(selected)):
        raise StateValidationError("knapsack selector returned duplicate task identifiers")
    pool_ids = {task.task_id for task in tasks}
    if not set(selected).issubset(pool_ids):
        raise StateValidationError("knapsack selector returned a task outside its pool")
    if not _subset_demand(tasks, set(selected)).fits_within(capacity):
        raise StateValidationError("knapsack selector returned a jointly infeasible subset")
    return selected


@dataclass(frozen=True, slots=True)
class PipelineDKRConfig:
    """One complete official Pipeline DK-R configuration and workload-level ``f``."""

    ga: PyeasygaConfig
    workload_task_ids: tuple[str, ...]
    workload_utility_mean: float
    workload_utility_std: float
    scaling_factor_f: float
    scaling_scope: str = "complete_workload_before_auction"
    standard_deviation_semantics: str = "population_ddof_0"
    alpha: float = 0.1

    def __post_init__(self) -> None:
        if not isinstance(self.ga, PyeasygaConfig):
            raise TypeError("ga must be a PyeasygaConfig")
        task_ids = tuple(self.workload_task_ids)
        if not task_ids or len(task_ids) != len(set(task_ids)):
            raise ValueError("workload_task_ids must be nonempty and unique")
        object.__setattr__(self, "workload_task_ids", task_ids)
        for name in ("workload_utility_mean", "workload_utility_std", "scaling_factor_f"):
            _finite(name, getattr(self, name))
        if self.workload_utility_std < 0.0:
            raise ValueError("workload_utility_std must be non-negative")
        if self.scaling_factor_f <= 0.0:
            raise ValueError("scaling_factor_f must be positive")
        if self.scaling_scope != "complete_workload_before_auction":
            raise ValueError("scaling_scope must preserve ASSUMP-012 workload scope")
        if self.standard_deviation_semantics != "population_ddof_0":
            raise ValueError("official Pipeline DK-R uses full-workload population deviation")
        if self.alpha != 0.1:
            raise ValueError("alpha must be 0.1 under ASSUMP-011")

    @classmethod
    def from_workload(
        cls, *, ga: PyeasygaConfig, workload_tasks: Sequence[Task]
    ) -> PipelineDKRConfig:
        """Compute ASSUMP-012 statistics once over the complete workload."""

        raw_tasks = tuple(workload_tasks)
        if not raw_tasks or any(not isinstance(task, Task) for task in raw_tasks):
            raise ValueError("workload_tasks must contain at least one Task")
        tasks = tuple(sorted(raw_tasks, key=lambda task: task.task_id))
        task_ids = tuple(task.task_id for task in tasks)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("workload_tasks must have unique identifiers")
        utilities = tuple(float(task.utility) for task in tasks)
        utility_mean = float(fmean(utilities))
        utility_std = float(pstdev(utilities))
        scaling_factor = utility_mean - 1.1 * utility_std
        if not isfinite(scaling_factor) or scaling_factor <= 0.0:
            raise ValueError("ASSUMP-012 scaling factor must be finite and positive")
        return cls(ga, task_ids, utility_mean, utility_std, float(scaling_factor))

    def validate_workload(self, state: SimulationState) -> None:
        """Fail if config statistics do not describe the state's complete workload."""

        if tuple(sorted(state.tasks)) != self.workload_task_ids:
            raise StateValidationError(
                "PipelineDKRConfig does not cover the complete state workload"
            )
        utilities = tuple(state.tasks[task_id].utility for task_id in self.workload_task_ids)
        observed_mean = float(fmean(utilities))
        observed_std = float(pstdev(utilities))
        observed_f = observed_mean - 1.1 * observed_std
        if not (
            isclose(observed_mean, self.workload_utility_mean, rel_tol=0.0, abs_tol=1e-12)
            and isclose(observed_std, self.workload_utility_std, rel_tol=0.0, abs_tol=1e-12)
            and isclose(observed_f, self.scaling_factor_f, rel_tol=0.0, abs_tol=1e-12)
        ):
            raise StateValidationError("PipelineDKRConfig workload statistics are stale")

    def as_metadata(self) -> dict[str, str]:
        """Serialize GA and workload-level pricing settings for each run."""

        metadata = self.ga.as_metadata()
        metadata.update(
            {
                "method": "pipeline_double_knapsack_retention",
                "processing_mode": "pipeline",
                "workload.task_count": str(len(self.workload_task_ids)),
                "workload.task_ids": ",".join(self.workload_task_ids),
                "pricing.utility_mean": repr(self.workload_utility_mean),
                "pricing.utility_std": repr(self.workload_utility_std),
                "pricing.standard_deviation_semantics": self.standard_deviation_semantics,
                "pricing.scaling_factor_f": repr(self.scaling_factor_f),
                "pricing.scaling_scope": self.scaling_scope,
                "pricing.alpha": repr(self.alpha),
                "pricing.violation_dimensions": "storage,computation,upload,download",
                "assumptions": "ASSUMP-011,ASSUMP-012,ASSUMP-013,ASSUMP-014,ASSUMP-015",
                "exact_solver_role": "auxiliary_tests_only_not_official_path",
                "batch_dkr_status": "blocked_missing_success_count_pricing",
            }
        )
        return metadata


@dataclass(frozen=True, slots=True)
class DKRoundOneServerResult:
    """One server's R1 membership, subset demand and offered prices."""

    bids: tuple[Bid, ...]
    selected_task_ids: tuple[str, ...]
    selected_subset_demand: ResourceVector


@dataclass(frozen=True, slots=True)
class DKRoundTwoServerResult:
    """One server's retention-only final placement and accepted prices."""

    final_state: SimulationState
    bids: tuple[Bid, ...]
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PipelineDKRAuctionResult:
    """Complete official two-round Pipeline DK-R result."""

    final_state: SimulationState
    round_one: AuctionRound
    round_two: AuctionRound
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    selected_server_by_task: Mapping[str, str]
    round_one_selected_by_server: Mapping[str, tuple[str, ...]]
    final_price_by_task: Mapping[str, float]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "selected_server_by_task", MappingProxyType(dict(self.selected_server_by_task))
        )
        object.__setattr__(
            self,
            "round_one_selected_by_server",
            MappingProxyType(dict(self.round_one_selected_by_server)),
        )
        object.__setattr__(
            self, "final_price_by_task", MappingProxyType(dict(self.final_price_by_task))
        )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class PipelineDoubleKnapsackRetentionPolicy:
    """Official pyeasyga-backed Pipeline DK-R policy."""

    config: PipelineDKRConfig
    selector: KnapsackSelector | None = None
    name: str = "pipeline_double_knapsack_retention"

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> PipelineDKRAuctionResult:
        del time_remaining_by_task
        selector = self.selector or PyeasygaUtilityKnapsackSelector(self.config.ga)
        choose_equal_server = getattr(selector, "choose_uniform", None)
        if not callable(choose_equal_server):
            raise TypeError("Pipeline DK-R selector must expose callable choose_uniform")
        return run_pipeline_double_knapsack_retention(
            state,
            requesting_task_ids=requesting_task_ids,
            selector=selector,
            choose_equal_server=choose_equal_server,
            config=self.config,
            epoch=epoch,
        )


def run_dkr_round_one_for_server(
    state: SimulationState,
    *,
    server_id: str,
    requesting_task_ids: Sequence[str],
    selector: KnapsackSelector,
    config: PipelineDKRConfig,
) -> DKRoundOneServerResult:
    """Run the reference-[4] Case-3 R1 knapsack and approved pricing."""

    task_ids = _validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")
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
    selected_ids = _validate_selector_result(
        selected_ids=selector.select(capacity=residual, tasks=requesting_tasks),
        tasks=requesting_tasks,
        capacity=residual,
    )
    selected = set(selected_ids)
    selected_demand = _subset_demand(requesting_tasks, selected)

    bids: list[Bid] = []
    for task in requesting_tasks:
        individually_feasible = task.demand.fits_within(server.capacity)
        violation = None
        if individually_feasible and task.task_id not in selected:
            violation = double_knapsack_violation(
                task.demand,
                selected_demand,
                server.capacity,
                scaling_factor=config.scaling_factor_f,
            )
        bids.append(
            Bid(
                task.task_id,
                server_id,
                AuctionRoundNumber.ROUND_ONE,
                double_knapsack_round_one_price(
                    task.utility,
                    selected=task.task_id in selected,
                    individually_feasible=individually_feasible,
                    violation=violation,
                    alpha=config.alpha,
                ),
                feasible=individually_feasible,
            )
        )
    return DKRoundOneServerResult(tuple(bids), selected_ids, selected_demand)


def _reject_for_round(state: SimulationState, task_id: str) -> SimulationState:
    if task_id in state.allocations:
        raise StateValidationError("a task with an allocation cannot be rejected")
    updated = state.snapshot()
    updated.task_states[task_id] = TaskState.REJECTED
    validate_state_invariants(updated)
    return updated


def run_dkr_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    selector: KnapsackSelector,
    config: PipelineDKRConfig,
) -> DKRoundTwoServerResult:
    """Run the second knapsack on residual capacity without preemption."""

    returning = _validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    residual = remaining_resources(state, server_id)
    tasks = tuple(state.tasks[task_id] for task_id in returning)
    selected_ids = _validate_selector_result(
        selected_ids=selector.select(capacity=residual, tasks=tasks),
        tasks=tasks,
        capacity=residual,
    )
    selected = set(selected_ids)
    selected_demand = _subset_demand(tasks, selected)

    updated = state.snapshot()
    accepted: list[str] = []
    rejected: list[str] = []
    bids: list[Bid] = []
    for task_id in returning:
        task = updated.tasks[task_id]
        if task_id not in selected:
            updated = _reject_for_round(updated, task_id)
            rejected.append(task_id)
            continue
        violation = double_knapsack_violation(
            task.demand,
            selected_demand,
            updated.servers[server_id].capacity,
            scaling_factor=config.scaling_factor_f,
        )
        price = double_knapsack_round_two_price(task.utility, violation=violation)
        updated = allocate_now(updated, task_id=task_id, server_id=server_id)
        accepted.append(task_id)
        bids.append(
            Bid(
                task_id,
                server_id,
                AuctionRoundNumber.ROUND_TWO,
                price,
                feasible=True,
            )
        )
    validate_state_invariants(updated)
    return DKRoundTwoServerResult(updated, tuple(bids), tuple(accepted), tuple(rejected))


def run_pipeline_double_knapsack_retention(
    state: SimulationState,
    *,
    requesting_task_ids: Sequence[str],
    selector: KnapsackSelector,
    choose_equal_server: Callable[[Sequence[str]], str],
    config: PipelineDKRConfig,
    epoch: int = 0,
) -> PipelineDKRAuctionResult:
    """Execute both official Pipeline DK-R auction rounds without preemption."""

    if not callable(choose_equal_server):
        raise TypeError("choose_equal_server must be callable")
    validate_state_invariants(state)
    config.validate_workload(state)
    task_ids = _validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")

    round_one_by_server = {
        server_id: run_dkr_round_one_for_server(
            state,
            server_id=server_id,
            requesting_task_ids=task_ids,
            selector=selector,
            config=config,
        )
        for server_id in state.servers
    }
    round_one_bids = tuple(bid for result in round_one_by_server.values() for bid in result.bids)
    round_one = AuctionRound(AuctionRoundNumber.ROUND_ONE, epoch, task_ids, round_one_bids)

    selected_server_by_task: dict[str, str] = {}
    rejected_without_server: list[str] = []
    for task_id in task_ids:
        task_bids = tuple(bid for bid in round_one_bids if bid.task_id == task_id)
        if len(task_bids) != len(state.servers):
            raise StateValidationError("each task must receive a bid from every server")
        minimum = min(bid.price for bid in task_bids)
        if minimum > state.tasks[task_id].utility:
            rejected_without_server.append(task_id)
            continue
        cheapest_server_ids = tuple(
            sorted(bid.server_id for bid in task_bids if bid.price == minimum)
        )
        chosen_server_id = choose_equal_server(cheapest_server_ids)
        if chosen_server_id not in cheapest_server_ids:
            raise StateValidationError("tie selector returned a non-minimum-price server")
        selected_server_by_task[task_id] = chosen_server_id

    updated = state.snapshot()
    rejected: list[str] = list(rejected_without_server)
    for task_id in rejected_without_server:
        updated = _reject_for_round(updated, task_id)

    accepted: list[str] = []
    round_two_bids: list[Bid] = []
    round_two_task_ids: list[str] = []
    final_prices: dict[str, float] = {}
    for server_id in state.servers:
        returning = tuple(
            task_id for task_id in task_ids if selected_server_by_task.get(task_id) == server_id
        )
        round_two_task_ids.extend(returning)
        result = run_dkr_round_two_for_server(
            updated,
            server_id=server_id,
            returning_task_ids=returning,
            selector=selector,
            config=config,
        )
        updated = result.final_state
        accepted.extend(result.accepted_task_ids)
        rejected.extend(result.rejected_task_ids)
        round_two_bids.extend(result.bids)
        final_prices.update({bid.task_id: bid.price for bid in result.bids})
    round_two = AuctionRound(
        AuctionRoundNumber.ROUND_TWO,
        epoch,
        tuple(round_two_task_ids),
        tuple(round_two_bids),
    )
    validate_state_invariants(updated)
    return PipelineDKRAuctionResult(
        updated,
        round_one,
        round_two,
        tuple(accepted),
        tuple(rejected),
        selected_server_by_task,
        {server_id: result.selected_task_ids for server_id, result in round_one_by_server.items()},
        final_prices,
        config.as_metadata(),
    )
