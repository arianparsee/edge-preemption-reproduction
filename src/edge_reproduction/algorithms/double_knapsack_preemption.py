"""Pipeline Double Knapsack Preemption under approved ASSUMP-016..019."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType

from edge_reproduction.algorithms.double_knapsack_retention import (
    PipelineDKRConfig,
    run_dkr_round_one_for_server,
)
from edge_reproduction.algorithms.feasibility import utility_time_ratio
from edge_reproduction.algorithms.genetic_knapsack import (
    PyeasygaConfig,
    PyeasygaUtilityKnapsackSelector,
)
from edge_reproduction.algorithms.knapsack import KnapsackSelector
from edge_reproduction.exceptions import StateValidationError, UnresolvedDecisionError
from edge_reproduction.models.bid import AuctionRound
from edge_reproduction.models.enums import AuctionRoundNumber, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now, release_now
from edge_reproduction.simulation.invariants import validate_state_invariants
from edge_reproduction.simulation.state import SimulationState


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
    total = ResourceVector.zero()
    for task in tasks:
        if task.task_id in selected_ids:
            total = total + task.demand
    return total


def _validate_selection(
    *, selected_ids: Sequence[str], tasks: Sequence[Task], capacity: ResourceVector
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


def _reject_returning(state: SimulationState, task_id: str) -> SimulationState:
    if task_id in state.allocations:
        raise StateValidationError("a returning task with an allocation cannot be rejected")
    updated = state.snapshot()
    updated.task_states[task_id] = TaskState.REJECTED
    validate_state_invariants(updated)
    return updated


@dataclass(frozen=True, slots=True)
class PipelineDKPConfig:
    """Official DK-P configuration extending the approved DK-R GA configuration."""

    retention_base: PipelineDKRConfig

    def __post_init__(self) -> None:
        if not isinstance(self.retention_base, PipelineDKRConfig):
            raise TypeError("retention_base must be a PipelineDKRConfig")

    @classmethod
    def from_workload(
        cls, *, ga: PyeasygaConfig, workload_tasks: Sequence[Task]
    ) -> PipelineDKPConfig:
        """Build the shared R1 pricing and ASSUMP-018 GA configuration."""

        return cls(PipelineDKRConfig.from_workload(ga=ga, workload_tasks=workload_tasks))

    @property
    def ga(self) -> PyeasygaConfig:
        """Expose the one mandatory-seed GA configuration used by both rounds."""

        return self.retention_base.ga

    def validate_workload(self, state: SimulationState) -> None:
        """Validate the inherited complete-workload pricing statistics."""

        self.retention_base.validate_workload(state)

    def as_metadata(self) -> dict[str, str]:
        """Serialize all shared settings and the approved DK-P semantics."""

        metadata = self.retention_base.as_metadata()
        metadata.update(
            {
                "method": "pipeline_double_knapsack_preemption",
                "round_two.capacity_scope": "total_server_capacity",
                "round_two.pool": "current_plus_returning",
                "round_two.repacking": "atomic_from_empty_total_capacity",
                "round_two.time_remaining": "frozen_at_round_start",
                "round_two.member_score_base": "1000.0",
                "round_two.nonmember_score_base": "1.0",
                "round_two.tie_behavior": "fail_fast",
                "round_two.cross_tier_conflict": "fail_fast",
                "round_two.price_status": "absent_no_source_formula_ASSUMP-019",
                "round_two.maximum_preemptions": "unbounded_by_algorithm",
                "current_allocation_requirement": "allocation_resources_equal_task_demand",
                "assumptions": (
                    "ASSUMP-011,ASSUMP-012,ASSUMP-013,ASSUMP-014,ASSUMP-015,"
                    "ASSUMP-016,ASSUMP-017,ASSUMP-018,ASSUMP-019"
                ),
            }
        )
        return metadata


@dataclass(frozen=True, slots=True)
class DKPScoreEntry:
    """One frozen Round-2 membership, ratio and literal score decision input."""

    task_id: str
    is_current: bool
    in_knapsack: bool
    time_remaining: float
    utility_time_ratio: float
    score: float


class DKPPreCommitAction(Enum):
    """Diagnostic-only disposition selected after planning and before commit."""

    COMMIT = "commit"
    RETAIN_CURRENT_REJECT_RETURNING = "retain_current_reject_returning"


@dataclass(frozen=True, slots=True)
class DKPPreCommitContext:
    """Immutable diagnostic view of one fully selected, not-yet-committed transaction."""

    epoch: int
    server_id: str
    current_task_ids: tuple[str, ...]
    returning_task_ids: tuple[str, ...]
    knapsack_selected_task_ids: tuple[str, ...]
    score_entries: tuple[DKPScoreEntry, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    planned_residual: ResourceVector


type DKPPreCommitDiagnosticHook = Callable[
    [DKPPreCommitContext], DKPPreCommitAction | None
]

_DKP_PRE_COMMIT_DIAGNOSTIC_HOOK: ContextVar[DKPPreCommitDiagnosticHook | None] = (
    ContextVar("dkp_pre_commit_diagnostic_hook", default=None)
)


@contextmanager
def dkp_pre_commit_diagnostic_hook(
    hook: DKPPreCommitDiagnosticHook,
) -> Iterator[None]:
    """Install a process-local diagnostic hook; disabled unless explicitly scoped."""

    token = _DKP_PRE_COMMIT_DIAGNOSTIC_HOOK.set(hook)
    try:
        yield
    finally:
        _DKP_PRE_COMMIT_DIAGNOSTIC_HOOK.reset(token)


@dataclass(frozen=True, slots=True)
class DKPRoundTwoServerResult:
    """One server's atomic combined-pool repacking outcome."""

    final_state: SimulationState
    score_entries: tuple[DKPScoreEntry, ...]
    knapsack_selected_task_ids: tuple[str, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    final_residual: ResourceVector


@dataclass(frozen=True, slots=True)
class PipelineDKPAuctionResult:
    """Complete two-round DK-P result with no fabricated Round-2 price field."""

    final_state: SimulationState
    round_one: AuctionRound
    round_two: AuctionRound
    accepted_task_ids: tuple[str, ...]
    rejected_task_ids: tuple[str, ...]
    retained_task_ids: tuple[str, ...]
    preempted_task_ids: tuple[str, ...]
    selected_server_by_task: Mapping[str, str]
    round_one_selected_by_server: Mapping[str, tuple[str, ...]]
    round_two_knapsack_by_server: Mapping[str, tuple[str, ...]]
    round_two_scores_by_server: Mapping[str, tuple[DKPScoreEntry, ...]]
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
            self,
            "round_two_knapsack_by_server",
            MappingProxyType(dict(self.round_two_knapsack_by_server)),
        )
        object.__setattr__(
            self,
            "round_two_scores_by_server",
            MappingProxyType(dict(self.round_two_scores_by_server)),
        )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _make_score_entries(
    *,
    tasks: Sequence[Task],
    current_task_ids: set[str],
    selected_task_ids: set[str],
    time_remaining_by_task: Mapping[str, float],
) -> tuple[DKPScoreEntry, ...]:
    entries: list[DKPScoreEntry] = []
    for task in tasks:
        if task.task_id not in time_remaining_by_task:
            raise KeyError(f"missing time_remaining for task_id: {task.task_id}")
        time_remaining = time_remaining_by_task[task.task_id]
        ratio = utility_time_ratio(task.utility, time_remaining)
        in_knapsack = task.task_id in selected_task_ids
        score = (1000.0 if in_knapsack else 1.0) + ratio
        if not isfinite(score):
            raise ValueError("DK-P score must be finite")
        entries.append(
            DKPScoreEntry(
                task.task_id,
                task.task_id in current_task_ids,
                in_knapsack,
                float(time_remaining),
                ratio,
                float(score),
            )
        )

    ordered = tuple(sorted(entries, key=lambda entry: entry.score, reverse=True))
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.score == right.score:
            raise UnresolvedDecisionError(
                "equal DK-P Round-2 scores require an unreported tie-break"
            )
    members = tuple(entry for entry in ordered if entry.in_knapsack)
    nonmembers = tuple(entry for entry in ordered if not entry.in_knapsack)
    if (
        members
        and nonmembers
        and max(entry.score for entry in nonmembers) >= min(entry.score for entry in members)
    ):
        raise UnresolvedDecisionError(
            "literal DK-P scores contradict the paper's knapsack-first priority"
        )
    return ordered


def run_dkp_round_two_for_server(
    state: SimulationState,
    *,
    server_id: str,
    returning_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    epoch: int = 0,
) -> DKPRoundTwoServerResult:
    """Plan and atomically commit ASSUMP-016 combined-pool repacking."""

    validate_state_invariants(state)
    if server_id not in state.servers:
        raise KeyError(f"unknown server_id: {server_id}")
    returning = _validate_task_ids(state, returning_task_ids, field_name="returning_task_ids")
    active_allocations = state.active_allocations_for_server(server_id)
    current = tuple(allocation.task_id for allocation in active_allocations)
    if set(current) & set(returning):
        raise StateValidationError("current and returning task pools must be disjoint")
    for allocation in active_allocations:
        if allocation.resources != state.tasks[allocation.task_id].demand:
            raise StateValidationError(
                "DK-P repacking requires active allocation resources to equal task demand"
            )
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

    planned_residual = capacity
    retained: list[str] = []
    preempted: list[str] = []
    accepted: list[str] = []
    rejected: list[str] = []
    for entry in entries:
        task = state.tasks[entry.task_id]
        if task.demand.fits_within(planned_residual):
            planned_residual = planned_residual.subtract(task.demand)
            (retained if entry.is_current else accepted).append(entry.task_id)
        else:
            (preempted if entry.is_current else rejected).append(entry.task_id)

    action = DKPPreCommitAction.COMMIT
    hook = _DKP_PRE_COMMIT_DIAGNOSTIC_HOOK.get()
    if hook is not None:
        requested_action = hook(
            DKPPreCommitContext(
                epoch=epoch,
                server_id=server_id,
                current_task_ids=current,
                returning_task_ids=returning,
                knapsack_selected_task_ids=selected,
                score_entries=entries,
                retained_task_ids=tuple(retained),
                preempted_task_ids=tuple(preempted),
                accepted_task_ids=tuple(accepted),
                rejected_task_ids=tuple(rejected),
                planned_residual=planned_residual,
            )
        )
        if requested_action is not None:
            if not isinstance(requested_action, DKPPreCommitAction):
                raise TypeError("diagnostic pre-commit hook returned an invalid action")
            action = requested_action

    if action is DKPPreCommitAction.RETAIN_CURRENT_REJECT_RETURNING:
        planned_residual = capacity
        retained = list(current)
        preempted = []
        accepted = []
        rejected = list(returning)
        for task_id in current:
            planned_residual = planned_residual.subtract(state.tasks[task_id].demand)

    updated = state.snapshot()
    for task_id in preempted:
        updated = release_now(updated, task_id=task_id, terminal_state=TaskState.PREEMPTED)
    for task_id in accepted:
        updated = allocate_now(updated, task_id=task_id, server_id=server_id)
    for task_id in rejected:
        updated = _reject_returning(updated, task_id)
    validate_state_invariants(updated)

    return DKPRoundTwoServerResult(
        updated,
        entries,
        selected,
        tuple(retained),
        tuple(preempted),
        tuple(accepted),
        tuple(rejected),
        planned_residual,
    )


@dataclass(frozen=True, slots=True)
class PipelineDoubleKnapsackPreemptionPolicy:
    """Official pyeasyga-backed Pipeline DK-P policy."""

    config: PipelineDKPConfig
    selector: KnapsackSelector | None = None
    name: str = "pipeline_double_knapsack_preemption"

    def run(
        self,
        state: SimulationState,
        *,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
        epoch: int = 0,
    ) -> PipelineDKPAuctionResult:
        selector = self.selector or PyeasygaUtilityKnapsackSelector(self.config.ga)
        choose_equal_server = getattr(selector, "choose_uniform", None)
        if not callable(choose_equal_server):
            raise TypeError("Pipeline DK-P selector must expose callable choose_uniform")
        return run_pipeline_double_knapsack_preemption(
            state,
            requesting_task_ids=requesting_task_ids,
            time_remaining_by_task=time_remaining_by_task,
            selector=selector,
            choose_equal_server=choose_equal_server,
            config=self.config,
            epoch=epoch,
        )


def run_pipeline_double_knapsack_preemption(
    state: SimulationState,
    *,
    requesting_task_ids: Sequence[str],
    time_remaining_by_task: Mapping[str, float],
    selector: KnapsackSelector,
    choose_equal_server: Callable[[Sequence[str]], str],
    config: PipelineDKPConfig,
    epoch: int = 0,
) -> PipelineDKPAuctionResult:
    """Execute unchanged DK Round 1 then approved preemptive Round 2."""

    if not callable(choose_equal_server):
        raise TypeError("choose_equal_server must be callable")
    validate_state_invariants(state)
    config.validate_workload(state)
    task_ids = _validate_task_ids(state, requesting_task_ids, field_name="requesting_task_ids")
    if not state.servers:
        raise StateValidationError("Pipeline DK-P requires at least one server")

    round_one_by_server = {
        server_id: run_dkr_round_one_for_server(
            state,
            server_id=server_id,
            requesting_task_ids=task_ids,
            selector=selector,
            config=config.retention_base,
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
        updated = _reject_returning(updated, task_id)

    accepted: list[str] = []
    retained: list[str] = []
    preempted: list[str] = []
    round_two_task_ids: list[str] = []
    round_two_knapsack: dict[str, tuple[str, ...]] = {}
    round_two_scores: dict[str, tuple[DKPScoreEntry, ...]] = {}
    for server_id in state.servers:
        returning = tuple(
            task_id for task_id in task_ids if selected_server_by_task.get(task_id) == server_id
        )
        result = run_dkp_round_two_for_server(
            updated,
            server_id=server_id,
            returning_task_ids=returning,
            time_remaining_by_task=time_remaining_by_task,
            selector=selector,
            epoch=epoch,
        )
        updated = result.final_state
        accepted.extend(result.accepted_task_ids)
        rejected.extend(result.rejected_task_ids)
        retained.extend(result.retained_task_ids)
        preempted.extend(result.preempted_task_ids)
        round_two_task_ids.extend(entry.task_id for entry in result.score_entries)
        round_two_knapsack[server_id] = result.knapsack_selected_task_ids
        round_two_scores[server_id] = result.score_entries

    round_two = AuctionRound(
        AuctionRoundNumber.ROUND_TWO,
        epoch,
        tuple(round_two_task_ids),
        (),
    )
    validate_state_invariants(updated)
    return PipelineDKPAuctionResult(
        updated,
        round_one,
        round_two,
        tuple(accepted),
        tuple(rejected),
        tuple(retained),
        tuple(preempted),
        selected_server_by_task,
        {server_id: result.selected_task_ids for server_id, result in round_one_by_server.items()},
        round_two_knapsack,
        round_two_scores,
        config.as_metadata(),
    )
