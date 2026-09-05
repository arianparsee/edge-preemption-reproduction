from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from edge_reproduction.algorithms.double_knapsack_preemption import (
    DKPPreCommitAction,
    DKPPreCommitContext,
    dkp_pre_commit_diagnostic_hook,
    run_dkp_round_two_for_server,
)
from edge_reproduction.diagnostics.oracle_checkpoint import (
    RestorableTransactionCheckpoint,
    closure_digest,
    file_sha256,
    public_payload_is_sanitized,
    validate_payload_inventory,
    write_atomic_new,
)
from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task
from edge_reproduction.simulation.accounting import allocate_now
from edge_reproduction.simulation.state import SimulationState

ROOT = Path(__file__).resolve().parents[2]


class SelectOnly:
    def __init__(self, *task_ids: str) -> None:
        self.task_ids = task_ids

    def select(self, *, capacity: ResourceVector, tasks: Sequence[Task]) -> tuple[str, ...]:
        del capacity, tasks
        return self.task_ids


def _task(task_id: str, demand: float, utility: float) -> Task:
    return Task(task_id, 0, 8, utility, ResourceVector(demand, demand, demand, demand))


def _preemptive_input() -> tuple[SimulationState, Task, Task]:
    current = _task("current", 8.0, 8.0)
    incoming = _task("incoming", 8.0, 20.0)
    server = Server("server", ResourceVector(10.0, 10.0, 10.0, 10.0))
    state = SimulationState(
        3,
        {current.task_id: current, incoming.task_id: incoming},
        {server.server_id: server},
    )
    state = allocate_now(state, task_id=current.task_id, server_id=server.server_id)
    return state, current, incoming


def _load_stage15n1b1_fixture() -> Any:
    path = ROOT / "tests" / "unit" / "test_stage15n1b1_checkpoint_audit.py"
    spec = importlib.util.spec_from_file_location("stage15n1b1_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    old = sys.path.copy()
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module


def _fixture_checkpoint_and_context() -> tuple[Any, DKPPreCommitContext]:
    fixture = _load_stage15n1b1_fixture()
    session, _, _ = fixture._session()  # noqa: SLF001
    _, checkpoint = session.run_to_completion(capture_until_victim=True)
    assert checkpoint is not None
    contexts: list[DKPPreCommitContext] = []
    state, current, incoming = _preemptive_input()
    with dkp_pre_commit_diagnostic_hook(
        lambda context: contexts.append(context) or DKPPreCommitAction.COMMIT
    ):
        run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(incoming.task_id,),
            time_remaining_by_task={current.task_id: 4.0, incoming.task_id: 4.0},
            selector=SelectOnly(incoming.task_id),
            epoch=3,
        )
    assert len(contexts) == 1
    return checkpoint, contexts[0]


def test_hook_runs_after_selection_and_before_commit() -> None:
    state, current, incoming = _preemptive_input()
    before = state.snapshot()
    contexts: list[DKPPreCommitContext] = []

    class BoundaryReached(Exception):
        pass

    def stop(context: DKPPreCommitContext) -> DKPPreCommitAction:
        contexts.append(context)
        raise BoundaryReached

    with pytest.raises(BoundaryReached), dkp_pre_commit_diagnostic_hook(stop):
        run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(incoming.task_id,),
            time_remaining_by_task={current.task_id: 4.0, incoming.task_id: 4.0},
            selector=SelectOnly(incoming.task_id),
            epoch=3,
        )
    assert state == before
    assert contexts[0].knapsack_selected_task_ids == (incoming.task_id,)
    assert contexts[0].preempted_task_ids == (current.task_id,)
    assert contexts[0].accepted_task_ids == (incoming.task_id,)


def test_hook_context_is_immutable() -> None:
    _, context = _fixture_checkpoint_and_context()
    with pytest.raises(FrozenInstanceError):
        context.epoch = 99  # type: ignore[misc]


def test_disabled_and_noop_hook_are_scientifically_and_rng_identical() -> None:
    fixture = _load_stage15n1b1_fixture()
    first, selector1, delegate1 = fixture._session()  # noqa: SLF001
    run1, _ = first.run_to_completion(capture_until_victim=True)
    run1.metadata = MappingProxyType(
        dict(run1.metadata) | selector1.runtime_metadata() | delegate1.runtime_metadata()
    )
    state1 = delegate1._counting_rng.getstate()  # noqa: SLF001

    second, selector2, delegate2 = fixture._session()  # noqa: SLF001
    observed: list[DKPPreCommitContext] = []
    with dkp_pre_commit_diagnostic_hook(
        lambda context: observed.append(context) or DKPPreCommitAction.COMMIT
    ):
        run2, _ = second.run_to_completion(capture_until_victim=True)
    run2.metadata = MappingProxyType(
        dict(run2.metadata) | selector2.runtime_metadata() | delegate2.runtime_metadata()
    )
    assert observed
    assert run1.as_dict() == run2.as_dict()
    assert state1 == delegate2._counting_rng.getstate()  # noqa: SLF001


def test_hook_preserves_current_returning_and_score_order() -> None:
    state, current, incoming = _preemptive_input()
    contexts: list[DKPPreCommitContext] = []
    with dkp_pre_commit_diagnostic_hook(
        lambda context: contexts.append(context) or DKPPreCommitAction.COMMIT
    ):
        result = run_dkp_round_two_for_server(
            state,
            server_id="server",
            returning_task_ids=(incoming.task_id,),
            time_remaining_by_task={current.task_id: 4.0, incoming.task_id: 4.0},
            selector=SelectOnly(incoming.task_id),
            epoch=3,
        )
    context = contexts[0]
    assert context.current_task_ids == (current.task_id,)
    assert context.returning_task_ids == (incoming.task_id,)
    assert context.score_entries == result.score_entries


def test_restorable_payload_round_trip_is_deep_and_hash_bound() -> None:
    checkpoint, context = _fixture_checkpoint_and_context()
    raw = checkpoint.serialize()
    locator = {
        "epoch": checkpoint.epoch,
        "server_id": context.server_id,
        "server_ordinal": 0,
        "sequence": 0,
    }
    approved = closure_digest(raw, locator)
    package = RestorableTransactionCheckpoint.create(
        checkpoint_payload=raw,
        transaction_locator=locator,
        precommit_context=context,
        expected_closure_sha256=approved,
        workload_sha256="a" * 64,
        config_sha256="b" * 64,
        policy_seed=checkpoint.session.config.policy_seed,
    )
    restored = RestorableTransactionCheckpoint.deserialize(package.serialize())
    first = restored.restore()
    second = restored.restore()
    assert first.session is not second.session
    assert first.session.state is not second.session.state
    assert first.serialize() == raw
    changed = dict(locator) | {"sequence": 1}
    assert closure_digest(raw, changed) != approved


def test_atomic_write_is_resume_safe(tmp_path: Path) -> None:
    path = tmp_path / "payload.pkl"
    assert write_atomic_new(path, b"payload") is True
    assert write_atomic_new(path, b"payload") is False
    assert file_sha256(path)
    with pytest.raises(FileExistsError, match="differs"):
        write_atomic_new(path, b"different")
    assert not path.with_name(f".{path.name}.tmp").exists()


def test_inventory_detects_duplicate_missing_and_orphan() -> None:
    checkpoint, context = _fixture_checkpoint_and_context()
    raw = checkpoint.serialize()

    def package(sequence: int) -> RestorableTransactionCheckpoint:
        locator = {
            "epoch": checkpoint.epoch,
            "server_id": context.server_id,
            "server_ordinal": 0,
            "sequence": sequence,
        }
        return RestorableTransactionCheckpoint.create(
            checkpoint_payload=raw,
            transaction_locator=locator,
            precommit_context=context,
            expected_closure_sha256=closure_digest(raw, locator),
            workload_sha256="a" * 64,
            config_sha256="b" * 64,
            policy_seed=checkpoint.session.config.policy_seed,
        )

    first = package(0)
    second = package(1)
    expected = [first.transaction_locator, second.transaction_locator]
    assert validate_payload_inventory([first, second], expected) == {
        "duplicate_count": 0,
        "missing_count": 0,
        "orphan_count": 0,
    }
    with pytest.raises(ValueError, match="inventory mismatch"):
        validate_payload_inventory([first, first], expected)
    with pytest.raises(ValueError, match="inventory mismatch"):
        validate_payload_inventory([first], expected)
    with pytest.raises(ValueError, match="inventory mismatch"):
        validate_payload_inventory([first, package(9)], expected)


def test_publication_sanitization() -> None:
    public_payload_is_sanitized(
        {"task_ids": False, "checkpoint_payload": False, "coverage": "28/28"}
    )
    with pytest.raises(ValueError, match="private value"):
        public_payload_is_sanitized({"task_ids": ["private"]})
    with pytest.raises(ValueError, match="personal path"):
        public_payload_is_sanitized({"path": "C:" + "/Users/example/private"})


def test_utility_conservation_positive_and_negative() -> None:
    fixture = _load_stage15n1b1_fixture()
    runner = fixture._load_runner()  # noqa: SLF001
    assert runner.validate_utility_conservation(
        total=10.0, completed=4.0, rejected=6.0
    ) == 0.0
    with pytest.raises(ValueError, match="conservation"):
        runner.validate_utility_conservation(total=10.0, completed=4.0, rejected=5.0)


def test_materializer_script_is_suffix_only_and_has_no_oracle_execution() -> None:
    source = (ROOT / "scripts/run_stage15n1b2r_materialize_checkpoints.py").read_text(
        encoding="utf-8"
    )
    assert "synthetic_normal_temporal_tasks" not in source
    assert "run_temporal_policy(" not in source
    assert "workflow_dispatch" not in source
    assert '"oracle_branches_executed": 0' in source
