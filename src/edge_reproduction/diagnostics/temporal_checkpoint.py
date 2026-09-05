"""Private, non-interventional temporal checkpoints for Stage 15-N.1B.1.

This module mirrors the approved temporal engine without changing the official
engine.  It exists only to prove that a factual suffix can continue from a deep
checkpoint.  Checkpoints contain private task-level state and must never be
published.
"""

from __future__ import annotations

import copy
import pickle
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Any

from edge_reproduction.algorithms.base import AllocationPolicy
from edge_reproduction.evaluation.temporal_outcomes import aggregate_temporal_outcome
from edge_reproduction.exceptions import StateValidationError
from edge_reproduction.models.enums import EventType, TaskState
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import release_now
from edge_reproduction.simulation.events import SimulationEvent
from edge_reproduction.simulation.invariants import remaining_resources, validate_state_invariants
from edge_reproduction.simulation.pipeline import (
    PipelineProgress,
    advance_pipeline,
    canonicalize_admission,
    pipeline_complete,
)
from edge_reproduction.simulation.state import SimulationState
from edge_reproduction.simulation.temporal_engine import TemporalRun, TemporalRunConfig


def _event(
    events: list[SimulationEvent],
    *,
    epoch: int,
    event_type: EventType,
    task: Task,
    reason: str,
    server_id: str | None = None,
    resources_before: ResourceVector | None = None,
    resources_after: ResourceVector | None = None,
    earned_utility: float = 0.0,
    price: float | None = None,
) -> None:
    events.append(
        SimulationEvent(
            len(events), epoch, event_type, task.task_id, server_id,
            resources_before, resources_after, task.utility, earned_utility,
            price, reason,
        )
    )


def _accepted_price(result: object, task_id: str, server_id: str) -> float | None:
    final_prices = getattr(result, "final_price_by_task", None)
    if isinstance(final_prices, Mapping) and task_id in final_prices:
        value = float(final_prices[task_id])
        return value if isfinite(value) else None
    round_one = getattr(result, "round_one", None)
    bids = getattr(round_one, "bids", ())
    values = [bid.price for bid in bids if bid.task_id == task_id and bid.server_id == server_id]
    return float(values[0]) if len(values) == 1 and isfinite(values[0]) else None


def _pipeline_feasible(admission: Any, servers: Mapping[str, Server]) -> bool:
    return admission.pipeline_feasible and any(
        admission.reservation.fits_within(server.capacity) for server in servers.values()
    )


@dataclass(slots=True)
class TemporalCheckpoint:
    """Deep, private continuation checkpoint immediately before one policy call."""

    schema_version: str
    session: CheckpointableTemporalSession
    epoch: int
    requesting_task_ids: tuple[str, ...]
    time_remaining_by_task: dict[str, float]
    event_cursor: int

    def serialize(self) -> bytes:
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, payload: bytes) -> TemporalCheckpoint:
        value = pickle.loads(payload)  # noqa: S301 - trusted local checkpoint only
        if not isinstance(value, cls):
            raise TypeError("checkpoint payload has an unexpected type")
        if value.schema_version != "stage15n1b1-private-checkpoint-v1":
            raise ValueError("unsupported checkpoint schema")
        value.session.rebind_observation_sink()
        return value

    def digest(self) -> str:
        return sha256(self.serialize()).hexdigest()


@dataclass(frozen=True, slots=True)
class EpochObservation:
    """Private diagnostic evidence returned after one unchanged policy call."""

    epoch: int
    checkpoint: TemporalCheckpoint | None
    policy_result: Any | None
    selector_observation_start: int | None
    selector_observation_end: int | None


@dataclass(slots=True)
class CheckpointableTemporalSession:
    """State-machine mirror of ``run_temporal_policy`` for checkpoint validation."""

    original_tasks: tuple[Task, ...]
    servers_input: tuple[Server, ...]
    policy: AllocationPolicy
    config: TemporalRunConfig
    policy_metadata: dict[str, str]
    task_ids: tuple[str, ...]
    original: dict[str, Task]
    state: SimulationState
    configured_last_slot: int
    last_arrival_slot: int
    drain_slots: int
    events: list[SimulationEvent] = field(default_factory=list)
    progress: dict[str, PipelineProgress] = field(default_factory=dict)
    retry_count: dict[str, int] = field(default_factory=dict)
    rejection_reasons: dict[str, list[str]] = field(default_factory=dict)
    ever_preempted: set[str] = field(default_factory=set)
    raw_rejections: int = 0
    next_epoch: int = 0
    finished: bool = False
    transaction_records: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        original_tasks: tuple[Task, ...],
        servers: tuple[Server, ...],
        policy: AllocationPolicy,
        config: TemporalRunConfig,
        policy_metadata: Mapping[str, str] | None = None,
    ) -> CheckpointableTemporalSession:
        if not original_tasks or not servers:
            raise ValueError("temporal run requires nonempty tasks and servers")
        task_ids = tuple(task.task_id for task in original_tasks)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task identifiers must be unique")
        if any(task.output_size is None for task in original_tasks):
            raise ValueError("all temporal tasks require output_size")
        if any(task.arrival_slot >= config.arrival_slots for task in original_tasks):
            raise ValueError("task arrival lies outside configured arrival envelope")
        original = {task.task_id: task for task in original_tasks}
        configured_last_slot = max(task.absolute_deadline_slot for task in original_tasks)
        last_arrival_slot = config.arrival_slots - 1
        return cls(
            original_tasks=original_tasks,
            servers_input=servers,
            policy=policy,
            config=config,
            policy_metadata=dict(policy_metadata or {}),
            task_ids=task_ids,
            original=original,
            state=SimulationState(0, original, {server.server_id: server for server in servers}),
            configured_last_slot=configured_last_slot,
            last_arrival_slot=last_arrival_slot,
            drain_slots=configured_last_slot - last_arrival_slot,
            retry_count={task_id: 0 for task_id in task_ids},
            rejection_reasons={task_id: [] for task_id in task_ids},
        )

    def checkpoint(
        self,
        *,
        epoch: int,
        requesting_task_ids: Sequence[str],
        time_remaining_by_task: Mapping[str, float],
    ) -> TemporalCheckpoint:
        """Capture all mutable execution and RNG closure without consuming RNG."""

        cloned = copy.deepcopy(self)
        checkpoint = TemporalCheckpoint(
            "stage15n1b1-private-checkpoint-v1",
            cloned,
            epoch,
            tuple(requesting_task_ids),
            dict(time_remaining_by_task),
            len(self.events),
        )
        # Serialization is part of the validity gate, not the policy decision.
        return TemporalCheckpoint.deserialize(checkpoint.serialize())

    def rebind_observation_sink(self) -> None:
        """Reconnect the copied selector sink to its copied observation list."""

        selector = getattr(self.policy, "_selector", None)
        delegate = getattr(selector, "_delegate", None)
        observations = getattr(selector, "_selector_observations", None)
        if delegate is not None and isinstance(observations, list):
            delegate.observation_sink = observations.append

    def _prepare_epoch(self, epoch: int) -> tuple[tuple[str, ...], dict[str, float]]:
        self.state.current_slot = epoch
        active_at_start = tuple(
            task_id
            for task_id, allocation in self.state.allocations.items()
            if allocation.is_active and allocation.start_slot < epoch
        )
        for task_id in active_at_start:
            allocation = self.state.allocations[task_id]
            source = self.original[task_id]
            output_size = source.output_size
            if output_size is None:
                raise StateValidationError("active temporal task has no output_size")
            before = remaining_resources(self.state, allocation.server_id)
            current = self.progress.get(task_id, PipelineProgress())
            if current.active_slots == 0:
                self.state.task_states[task_id] = TaskState.PIPELINE_ACTIVE
                _event(
                    self.events, epoch=epoch, event_type=EventType.ACTIVATED, task=source,
                    server_id=allocation.server_id, resources_before=before,
                    resources_after=before, reason="accepted_previous_epoch_activation",
                )
            updated = advance_pipeline(
                current,
                input_size=source.demand.storage,
                total_computation=source.demand.computation,
                output_size=output_size,
                reservation=allocation.resources,
                tolerance=self.config.numerical_tolerance,
            )
            self.progress[task_id] = updated
            _event(
                self.events, epoch=epoch, event_type=EventType.PROGRESSED, task=source,
                server_id=allocation.server_id, resources_before=before,
                resources_after=before,
                reason=(f"pipeline_slot={updated.active_slots};uploaded={updated.uploaded};"
                        f"computed={updated.computed};downloaded={updated.downloaded}"),
            )
            if pipeline_complete(
                updated,
                input_size=source.demand.storage,
                total_computation=source.demand.computation,
                output_size=output_size,
                tolerance=self.config.numerical_tolerance,
            ):
                self.state = release_now(
                    self.state, task_id=task_id, terminal_state=TaskState.COMPLETED
                )
                after = remaining_resources(self.state, allocation.server_id)
                _event(
                    self.events, epoch=epoch, event_type=EventType.COMPLETED, task=source,
                    server_id=allocation.server_id, resources_before=before,
                    resources_after=after, earned_utility=source.utility,
                    reason="all_pipeline_activities_complete_by_inclusive_deadline",
                )

        for task_id in self.task_ids:
            if self.state.task_states[task_id] in {
                TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED
            }:
                continue
            source = self.original[task_id]
            if epoch < source.absolute_deadline_slot:
                continue
            expiring_allocation = self.state.allocations.get(task_id)
            if expiring_allocation is not None and expiring_allocation.is_active:
                before = remaining_resources(self.state, expiring_allocation.server_id)
                self.state = release_now(
                    self.state, task_id=task_id, terminal_state=TaskState.EXPIRED
                )
                after = remaining_resources(self.state, expiring_allocation.server_id)
                _event(
                    self.events, epoch=epoch, event_type=EventType.EXPIRED, task=source,
                    server_id=expiring_allocation.server_id, resources_before=before,
                    resources_after=after,
                    reason="active_pipeline_incomplete_after_inclusive_deadline_opportunity",
                )
            elif source.arrival_slot <= epoch:
                self.state.task_states[task_id] = TaskState.EXPIRED
                _event(
                    self.events, epoch=epoch, event_type=EventType.EXPIRED, task=source,
                    reason="waiting_task_no_remaining_completion_opportunity",
                )

        for task_id in self.task_ids:
            source = self.original[task_id]
            if source.arrival_slot == epoch:
                self.state.task_states[task_id] = TaskState.WAITING_FOR_BID
                _event(
                    self.events, epoch=epoch, event_type=EventType.ARRIVED, task=source,
                    reason="workload_arrival_registered",
                )

        eligible = tuple(
            task_id
            for task_id in self.task_ids
            if self.state.task_states[task_id]
            in {TaskState.WAITING_FOR_BID, TaskState.WAITING_RETRY}
            and self.original[task_id].arrival_slot < epoch
        )
        requesting: list[str] = []
        for task_id in eligible:
            if self.state.task_states[task_id] is TaskState.WAITING_RETRY:
                self.retry_count[task_id] += 1
            source = self.original[task_id]
            remaining_computation = source.demand.computation - self.progress.get(
                task_id, PipelineProgress()
            ).computed
            admission = canonicalize_admission(
                source,
                auction_epoch=epoch,
                remaining_computation=remaining_computation,
                tolerance=self.config.numerical_tolerance,
            )
            if not _pipeline_feasible(admission, self.state.servers):
                self.state.task_states[task_id] = TaskState.EXPIRED
                self.rejection_reasons[task_id].append(admission.reason)
                _event(
                    self.events, epoch=epoch, event_type=EventType.EXPIRED, task=source,
                    reason=f"canonical_admission_infeasible:{admission.reason}",
                )
                continue
            self.state.tasks[task_id] = admission.task
            requesting.append(task_id)
        time_remaining = {
            task_id: float(self.original[task_id].absolute_deadline_slot - epoch)
            for task_id in self.task_ids
            if self.original[task_id].absolute_deadline_slot - epoch > 0
        }
        return tuple(requesting), time_remaining

    def _apply_auction(
        self,
        *,
        epoch: int,
        requesting: tuple[str, ...],
        time_remaining: Mapping[str, float],
    ) -> object:
        before_auction = self.state.snapshot()
        result = self.policy.run(
            self.state,
            requesting_task_ids=requesting,
            time_remaining_by_task=time_remaining,
            epoch=epoch,
        )
        self.state = result.final_state
        preempted_ids = tuple(getattr(result, "preempted_task_ids", ()))
        for task_id in preempted_ids:
            self.ever_preempted.add(task_id)
            allocation = self.state.allocations[task_id]
            _event(
                self.events, epoch=epoch, event_type=EventType.PREEMPTED,
                task=self.original[task_id], server_id=allocation.server_id,
                resources_before=remaining_resources(before_auction, allocation.server_id),
                resources_after=remaining_resources(self.state, allocation.server_id),
                reason="policy_round_two_terminal_preemption",
            )
        selected_server_by_task = getattr(result, "selected_server_by_task", {})
        for task_id in result.accepted_task_ids:
            allocation = self.state.allocations[task_id]
            self.state.task_states[task_id] = TaskState.ACCEPTED
            _event(
                self.events, epoch=epoch, event_type=EventType.ACCEPTED,
                task=self.original[task_id], server_id=allocation.server_id,
                resources_before=remaining_resources(before_auction, allocation.server_id),
                resources_after=remaining_resources(self.state, allocation.server_id),
                price=_accepted_price(result, task_id, allocation.server_id),
                reason="atomic_round_two_admission_activation_next_epoch",
            )
        for task_id in result.rejected_task_ids:
            self.raw_rejections += 1
            self.rejection_reasons[task_id].append("policy_round_two_rejection")
            _event(
                self.events, epoch=epoch, event_type=EventType.REJECTED,
                task=self.original[task_id], server_id=selected_server_by_task.get(task_id),
                reason="policy_round_two_rejection_nonterminal",
            )
            source = self.original[task_id]
            next_epoch = epoch + 1
            next_admission = canonicalize_admission(
                source,
                auction_epoch=next_epoch,
                remaining_computation=source.demand.computation,
                tolerance=self.config.numerical_tolerance,
            )
            if _pipeline_feasible(next_admission, self.state.servers):
                self.state.task_states[task_id] = TaskState.WAITING_RETRY
                _event(
                    self.events, epoch=epoch, event_type=EventType.RETRY_SCHEDULED,
                    task=source,
                    reason=(f"completed_retry_attempts={self.retry_count[task_id]};"
                            f"next_epoch={next_epoch}"),
                )
            else:
                self.state.task_states[task_id] = TaskState.EXPIRED
                self.rejection_reasons[task_id].append(next_admission.reason)
                _event(
                    self.events, epoch=epoch, event_type=EventType.EXPIRED, task=source,
                    reason=f"post_rejection_next_epoch_infeasible:{next_admission.reason}",
                )
        return result

    def step(self, *, capture_checkpoint: bool = False) -> EpochObservation:
        if self.finished:
            raise RuntimeError("temporal session is already complete")
        epoch = self.next_epoch
        requesting, time_remaining = self._prepare_epoch(epoch)
        checkpoint = None
        result = None
        selector = getattr(self.policy, "_selector", None)
        start = getattr(selector, "observation_count", None)
        start_count = int(start) if isinstance(start, int) else None
        if requesting:
            before_state = self.state.snapshot()
            progress_before = self.progress.copy()
            retry_before = self.retry_count.copy()
            if capture_checkpoint:
                checkpoint = self.checkpoint(
                    epoch=epoch,
                    requesting_task_ids=requesting,
                    time_remaining_by_task=time_remaining,
                )
            result = self._apply_auction(
                epoch=epoch, requesting=requesting, time_remaining=time_remaining
            )
            end = getattr(selector, "observation_count", None)
            end_count = int(end) if isinstance(end, int) else None
            self._record_victim_transactions(
                epoch=epoch,
                before_state=before_state,
                progress_before=progress_before,
                retry_before=retry_before,
                result=result,
                selector_observation_start=start_count,
                selector_observation_end=end_count,
            )
        validate_state_invariants(self.state)
        terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
        all_terminal = all(status in terminal for status in self.state.task_states.values())
        self.next_epoch = epoch + 1
        if (epoch >= self.last_arrival_slot and all_terminal) or epoch >= self.configured_last_slot:
            self.finished = True
        end = getattr(selector, "observation_count", None)
        end_count = int(end) if isinstance(end, int) else None
        return EpochObservation(epoch, checkpoint, result, start_count, end_count)

    def _record_victim_transactions(
        self,
        *,
        epoch: int,
        before_state: SimulationState,
        progress_before: Mapping[str, PipelineProgress],
        retry_before: Mapping[str, int],
        result: Any,
        selector_observation_start: int | None,
        selector_observation_end: int | None,
    ) -> None:
        """Capture private post-decision evidence without changing the result."""

        score_map = getattr(result, "round_two_scores_by_server", {})
        selected_server = getattr(result, "selected_server_by_task", {})
        accepted_all = set(getattr(result, "accepted_task_ids", ()))
        rejected_all = set(getattr(result, "rejected_task_ids", ()))
        retained_all = set(getattr(result, "retained_task_ids", ()))
        preempted_all = set(getattr(result, "preempted_task_ids", ()))
        bids = getattr(getattr(result, "round_one", None), "bids", ())
        for server_ordinal, server_id in enumerate(before_state.servers):
            current = tuple(
                allocation.task_id
                for allocation in before_state.active_allocations_for_server(server_id)
            )
            victims = tuple(task_id for task_id in current if task_id in preempted_all)
            if not victims:
                continue
            returning = tuple(
                task_id
                for task_id in result.round_one.task_ids
                if selected_server.get(task_id) == server_id
            )
            scores = tuple(score_map[server_id])
            accepted = tuple(task_id for task_id in returning if task_id in accepted_all)
            rejected = tuple(task_id for task_id in returning if task_id in rejected_all)
            retained = tuple(task_id for task_id in current if task_id in retained_all)
            pool = current + returning
            task_features: dict[str, dict[str, object]] = {}
            for task_id in pool:
                task = before_state.tasks[task_id]
                source = self.original[task_id]
                pipeline = progress_before.get(task_id, PipelineProgress())
                task_features[task_id] = {
                    "role": "current" if task_id in current else "returning",
                    "utility": source.utility,
                    "absolute_deadline_slot": source.absolute_deadline_slot,
                    "slack": source.absolute_deadline_slot - epoch,
                    "remaining_computation": source.demand.computation - pipeline.computed,
                    "pipeline_progress": {
                        "uploaded": pipeline.uploaded,
                        "computed": pipeline.computed,
                        "downloaded": pipeline.downloaded,
                        "active_slots": pipeline.active_slots,
                    },
                    "demand": task.demand.as_dict(),
                    "retry_count": retry_before[task_id],
                    "price": next(
                        (
                            bid.price
                            for bid in bids
                            if bid.task_id == task_id and bid.server_id == server_id
                        ),
                        None,
                    ),
                }
            residual = before_state.servers[server_id].capacity
            for entry in scores:
                task = before_state.tasks[entry.task_id]
                if task.demand.fits_within(residual):
                    residual = residual.subtract(task.demand)
            self.transaction_records.append(
                {
                    "transaction_key": {
                        "epoch": epoch,
                        "server_id": server_id,
                        "server_ordinal": server_ordinal,
                        "sequence": len(self.transaction_records),
                    },
                    "current_task_ids": current,
                    "returning_task_ids": returning,
                    "candidate_pool_task_ids": pool,
                    "task_features": task_features,
                    "ga_membership_and_scores": tuple(
                        {
                            "task_id": entry.task_id,
                            "is_current": entry.is_current,
                            "in_knapsack": entry.in_knapsack,
                            "time_remaining": entry.time_remaining,
                            "utility_time_ratio": entry.utility_time_ratio,
                            "score": entry.score,
                        }
                        for entry in scores
                    ),
                    "planned": {
                        "retained": retained,
                        "preempted": victims,
                        "accepted": accepted,
                        "rejected": rejected,
                        "residual": residual.as_dict(),
                    },
                    "local_utility": {
                        "incoming": float(sum(self.original[item].utility for item in accepted)),
                        "victim": float(sum(self.original[item].utility for item in victims)),
                    },
                    "selector_observation_range": (
                        selector_observation_start,
                        selector_observation_end,
                    ),
                }
            )

    def run_to_completion(
        self, *, capture_until_victim: bool = False
    ) -> tuple[TemporalRun, TemporalCheckpoint | None]:
        canary: TemporalCheckpoint | None = None
        while not self.finished:
            observation = self.step(capture_checkpoint=capture_until_victim and canary is None)
            result = observation.policy_result
            if result is not None and bool(result.preempted_task_ids) and canary is None:
                if observation.checkpoint is None:
                    raise AssertionError("victim transaction lacks its pre-decision checkpoint")
                canary = observation.checkpoint
        return self.finalize(), canary

    def resume_checkpoint(
        self, checkpoint: TemporalCheckpoint
    ) -> tuple[TemporalRun, CheckpointableTemporalSession]:
        restored = TemporalCheckpoint.deserialize(checkpoint.serialize()).session
        if restored.next_epoch != checkpoint.epoch:
            raise ValueError("checkpoint epoch does not match continuation cursor")
        result = restored._apply_auction(
            epoch=checkpoint.epoch,
            requesting=checkpoint.requesting_task_ids,
            time_remaining=checkpoint.time_remaining_by_task,
        )
        if result is None:
            raise AssertionError("checkpoint continuation omitted the factual policy decision")
        validate_state_invariants(restored.state)
        restored.next_epoch = checkpoint.epoch + 1
        terminal = {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
        if checkpoint.epoch >= restored.last_arrival_slot and all(
            status in terminal for status in restored.state.task_states.values()
        ):
            restored.finished = True
        while not restored.finished:
            restored.step(capture_checkpoint=False)
        return restored.finalize(), restored

    def finalize(self) -> TemporalRun:
        if not self.finished:
            raise RuntimeError("cannot finalize an incomplete temporal session")
        nonterminal = {
            task_id
            for task_id, status in self.state.task_states.items()
            if status not in {TaskState.COMPLETED, TaskState.PREEMPTED, TaskState.EXPIRED}
        }
        if nonterminal:
            raise StateValidationError(
                "nonterminal tasks after configured_last_slot="
                f"{self.configured_last_slot}: {sorted(nonterminal)}"
            )
        outcome = aggregate_temporal_outcome(
            self.state,
            ever_preempted_task_ids=self.ever_preempted,
            raw_auction_rejection_count=self.raw_rejections,
        )
        metadata = {
            "baseline": "arXiv:2403.15665v2_2024",
            "scientific_label": "reproduction_under_ASSUMP-033_through_ASSUMP-043",
            "run_id": self.config.run_id,
            "policy": self.policy.name,
            "policy_seed": str(self.config.policy_seed),
            "arrival_slots": str(self.config.arrival_slots),
            "last_arrival_slot": str(self.last_arrival_slot),
            "configured_last_slot": str(self.configured_last_slot),
            "drain_slots": str(self.drain_slots),
            "drain_policy": self.config.drain_policy,
            "numerical_tolerance": repr(self.config.numerical_tolerance),
            "output_size_provenance": self.config.output_size_provenance,
            "capacity_slot_normalization": self.config.capacity_slot_normalization,
            "auction_time_advances_simulation": "false",
            "full_100_slot_30_repeat_run": "false",
        }
        metadata.update(self.policy_metadata)
        return TemporalRun(
            self.policy.name,
            self.state,
            outcome,
            tuple(self.events),
            self.progress,
            self.retry_count,
            {key: tuple(value) for key, value in self.rejection_reasons.items()},
            MappingProxyType(metadata),
        )


def checkpoint_alias_gate(checkpoint: TemporalCheckpoint) -> None:
    """Prove checkpoint and restore do not alias the captured live session."""

    restored = TemporalCheckpoint.deserialize(checkpoint.serialize())
    if restored.session is checkpoint.session:
        raise AssertionError("restored checkpoint aliases serialized checkpoint")
    if restored.session.state is checkpoint.session.state:
        raise AssertionError("restored SimulationState aliases checkpoint state")
    if restored.session.progress is checkpoint.session.progress:
        raise AssertionError("restored pipeline progress aliases checkpoint progress")
    if restored.session.policy is checkpoint.session.policy:
        raise AssertionError("restored policy aliases checkpoint policy")
