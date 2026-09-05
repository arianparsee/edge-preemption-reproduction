"""Private restorable transaction checkpoints for diagnostic Oracle work.

Payloads produced by this module contain task-level state and must remain in a
trusted, gitignored location.  Hashes bind a full pre-auction checkpoint to one
natural-order transaction locator and its immutable pre-commit context.
"""

from __future__ import annotations

import json
import os
import pickle
from base64 import b64encode
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
from math import isfinite
from pathlib import Path
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, MethodType
from typing import Any, cast

from edge_reproduction.algorithms.double_knapsack_preemption import DKPPreCommitContext
from edge_reproduction.diagnostics.temporal_checkpoint import TemporalCheckpoint

SCHEMA_VERSION = "stage15n1b2r-private-restorable-transaction-v1"
SEMANTIC_SCHEMA_VERSION = "stage15n1b2_semantic_closure_v1"
SEMANTIC_PAYLOAD_SCHEMA_VERSION = "stage15n1b2r1-private-restorable-transaction-v1"
CLOSURE_DOMAIN = b"stage15n1b1r-closure-v1\0"


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def closure_digest(checkpoint_payload: bytes, transaction_locator: object) -> str:
    digest = sha256()
    digest.update(CLOSURE_DOMAIN)
    digest.update(checkpoint_payload)
    digest.update(b"\0")
    digest.update(_canonical_json(transaction_locator))
    return digest.hexdigest()


def context_digest(context: DKPPreCommitContext) -> str:
    return sha256(_canonical_json(asdict(context))).hexdigest()


def _type_name(value: object) -> str:
    kind = type(value)
    return f"{kind.__module__}.{kind.__qualname__}"


def canonical_semantic_value(
    value: object, *, _active: frozenset[int] = frozenset()
) -> object:
    """Build a process-independent, type-tagged representation without mutation."""

    if value is None:
        return {"type": "none"}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": str(value)}
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("semantic closure rejects NaN and Infinity")
        return {"type": "float", "value": value.hex()}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    if isinstance(value, bytes):
        return {
            "type": "bytes",
            "encoding": "base64",
            "value": b64encode(value).decode(),
        }
    if isinstance(value, Enum):
        return {
            "type": "enum",
            "enum_type": _type_name(value),
            "member": value.name,
        }
    if isinstance(value, type):
        return {
            "type": "python_type",
            "value": f"{value.__module__}.{value.__qualname__}",
        }
    if isinstance(value, (FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType)):
        owner = getattr(value, "__self__", None)
        return {
            "type": "callable",
            "module": getattr(value, "__module__", None),
            "qualname": getattr(value, "__qualname__", getattr(value, "__name__", None)),
            "bound_owner_type": None if owner is None else _type_name(owner),
        }

    identity = id(value)
    if identity in _active:
        return {"type": "cycle", "value_type": _type_name(value)}
    active = _active | {identity}
    if isinstance(value, Mapping):
        items = [
            (
                canonical_semantic_value(key, _active=active),
                canonical_semantic_value(child, _active=active),
            )
            for key, child in value.items()
        ]
        items.sort(key=lambda item: _canonical_json(item[0]))
        return {
            "type": "mapping",
            "mapping_type": _type_name(value),
            "items": [[key, child] for key, child in items],
        }
    if isinstance(value, (set, frozenset)):
        members = [canonical_semantic_value(child, _active=active) for child in value]
        members.sort(key=_canonical_json)
        return {
            "type": "frozenset" if isinstance(value, frozenset) else "set",
            "items": members,
        }
    if isinstance(value, (list, tuple)):
        return {
            "type": "tuple" if isinstance(value, tuple) else "list",
            "items": [canonical_semantic_value(child, _active=active) for child in value],
        }

    attributes: dict[str, object] = {}
    if hasattr(value, "__dict__"):
        attributes.update(vars(value))
    for kind in type(value).__mro__:
        slots = getattr(kind, "__slots__", ())
        if isinstance(slots, str):
            slots = (slots,)
        for name in slots:
            if name not in {"__dict__", "__weakref__"} and hasattr(value, name):
                attributes.setdefault(name, getattr(value, name))
    if attributes:
        return {
            "type": "object",
            "object_type": _type_name(value),
            "fields": {
                name: canonical_semantic_value(attributes[name], _active=active)
                for name in sorted(attributes)
            },
        }
    raise TypeError(f"unsupported semantic closure type: {_type_name(value)}")


def canonical_semantic_bytes(value: object) -> bytes:
    envelope = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "value": canonical_semantic_value(value),
    }
    return _canonical_json(envelope)


def canonical_semantic_sha256(value: object) -> str:
    return sha256(canonical_semantic_bytes(value)).hexdigest()


def semantic_closure_sha256(
    *,
    checkpoint: TemporalCheckpoint,
    transaction_locator: Mapping[str, object],
    precommit_context: DKPPreCommitContext,
) -> str:
    return canonical_semantic_sha256(
        {
            "checkpoint": checkpoint,
            "transaction_locator": dict(transaction_locator),
            "precommit_context": precommit_context,
        }
    )


@dataclass(frozen=True, slots=True)
class RestorableTransactionCheckpoint:
    """One pre-auction checkpoint plus exact post-selection target identity."""

    schema_version: str
    checkpoint_payload: bytes
    transaction_locator: dict[str, object]
    precommit_context: DKPPreCommitContext
    expected_closure_sha256: str
    expected_context_sha256: str
    workload_sha256: str
    config_sha256: str
    policy_seed: int

    @classmethod
    def create(
        cls,
        *,
        checkpoint_payload: bytes,
        transaction_locator: dict[str, object],
        precommit_context: DKPPreCommitContext,
        expected_closure_sha256: str,
        workload_sha256: str,
        config_sha256: str,
        policy_seed: int,
    ) -> RestorableTransactionCheckpoint:
        value = cls(
            SCHEMA_VERSION,
            checkpoint_payload,
            dict(transaction_locator),
            precommit_context,
            expected_closure_sha256,
            context_digest(precommit_context),
            workload_sha256,
            config_sha256,
            policy_seed,
        )
        value.validate()
        return value

    def serialize(self) -> bytes:
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, payload: bytes) -> RestorableTransactionCheckpoint:
        value = pickle.loads(payload)  # noqa: S301 - trusted local diagnostic payload
        if not isinstance(value, cls):
            raise TypeError("restorable payload has an unexpected type")
        value.validate()
        return value

    def restore(self) -> TemporalCheckpoint:
        checkpoint = TemporalCheckpoint.deserialize(self.checkpoint_payload)
        self.validate()
        return checkpoint

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported restorable checkpoint schema")
        if closure_digest(self.checkpoint_payload, self.transaction_locator) != (
            self.expected_closure_sha256
        ):
            raise ValueError("restored closure hash differs from approved closure")
        if context_digest(self.precommit_context) != self.expected_context_sha256:
            raise ValueError("pre-commit context checksum mismatch")
        checkpoint = TemporalCheckpoint.deserialize(self.checkpoint_payload)
        if checkpoint.epoch != int(
            cast(int | str, self.transaction_locator["epoch"])
        ):
            raise ValueError("checkpoint epoch differs from transaction locator")
        if checkpoint.session.config.policy_seed != self.policy_seed:
            raise ValueError("checkpoint policy seed differs from payload identity")


@dataclass(frozen=True, slots=True)
class SemanticRestorableTransactionCheckpoint:
    """Versioned semantic checkpoint retaining legacy raw-pickle provenance."""

    schema_version: str
    semantic_schema_version: str
    checkpoint_payload: bytes
    transaction_locator: dict[str, object]
    precommit_context: DKPPreCommitContext
    semantic_closure_sha256: str
    legacy_raw_pickle_sha256: str
    legacy_raw_checkpoint_sha256: str
    rng_state_sha256: str
    workload_sha256: str
    config_sha256: str
    policy_seed: int

    @classmethod
    def create(
        cls,
        *,
        checkpoint_payload: bytes,
        transaction_locator: dict[str, object],
        precommit_context: DKPPreCommitContext,
        legacy_raw_pickle_sha256: str,
        legacy_raw_checkpoint_sha256: str,
        rng_state_sha256: str,
        workload_sha256: str,
        config_sha256: str,
        policy_seed: int,
    ) -> SemanticRestorableTransactionCheckpoint:
        checkpoint = TemporalCheckpoint.deserialize(checkpoint_payload)
        semantic = semantic_closure_sha256(
            checkpoint=checkpoint,
            transaction_locator=transaction_locator,
            precommit_context=precommit_context,
        )
        value = cls(
            SEMANTIC_PAYLOAD_SCHEMA_VERSION,
            SEMANTIC_SCHEMA_VERSION,
            checkpoint_payload,
            dict(transaction_locator),
            precommit_context,
            semantic,
            legacy_raw_pickle_sha256,
            legacy_raw_checkpoint_sha256,
            rng_state_sha256,
            workload_sha256,
            config_sha256,
            policy_seed,
        )
        value.validate()
        return value

    def serialize(self) -> bytes:
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, payload: bytes) -> SemanticRestorableTransactionCheckpoint:
        value = pickle.loads(payload)  # noqa: S301 - trusted local diagnostic payload
        if not isinstance(value, cls):
            raise TypeError("semantic restorable payload has an unexpected type")
        value.validate()
        return value

    def restore(self) -> TemporalCheckpoint:
        checkpoint = TemporalCheckpoint.deserialize(self.checkpoint_payload)
        self.validate(checkpoint=checkpoint)
        return checkpoint

    def validate(self, *, checkpoint: TemporalCheckpoint | None = None) -> None:
        if self.schema_version != SEMANTIC_PAYLOAD_SCHEMA_VERSION:
            raise ValueError("unsupported semantic restorable payload schema")
        if self.semantic_schema_version != SEMANTIC_SCHEMA_VERSION:
            raise ValueError("unsupported semantic closure schema")
        restored = checkpoint or TemporalCheckpoint.deserialize(self.checkpoint_payload)
        semantic = semantic_closure_sha256(
            checkpoint=restored,
            transaction_locator=self.transaction_locator,
            precommit_context=self.precommit_context,
        )
        if semantic != self.semantic_closure_sha256:
            raise ValueError("semantic closure hash mismatch after restore")
        if restored.epoch != int(cast(int | str, self.transaction_locator["epoch"])):
            raise ValueError("semantic payload checkpoint epoch mismatch")
        if restored.session.config.policy_seed != self.policy_seed:
            raise ValueError("semantic payload policy seed mismatch")


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_atomic_new(path: Path, payload: bytes) -> bool:
    """Atomically create a payload, or validate an identical resume artifact."""

    expected = sha256(payload).hexdigest()
    if path.exists():
        if file_sha256(path) != expected:
            raise FileExistsError(f"existing checkpoint differs: {path.name}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise FileExistsError(f"stale atomic-write temporary exists: {temporary.name}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise
    if file_sha256(path) != expected:
        raise ValueError("atomic checkpoint write checksum mismatch")
    return True


def validate_payload_inventory(
    payloads: list[RestorableTransactionCheckpoint],
    expected_locators: list[dict[str, object]],
) -> dict[str, int]:
    actual = [_canonical_json(item.transaction_locator) for item in payloads]
    expected = [_canonical_json(item) for item in expected_locators]
    duplicate_count = len(actual) - len(set(actual))
    missing_count = len(set(expected) - set(actual))
    orphan_count = len(set(actual) - set(expected))
    if duplicate_count or missing_count or orphan_count:
        raise ValueError(
            "restorable checkpoint inventory mismatch: "
            f"duplicate={duplicate_count}, missing={missing_count}, orphan={orphan_count}"
        )
    if actual != expected:
        raise ValueError("restorable checkpoint order mismatch")
    return {
        "duplicate_count": duplicate_count,
        "missing_count": missing_count,
        "orphan_count": orphan_count,
    }


def public_payload_is_sanitized(value: object) -> None:
    private_keys = {
        "task_id",
        "task_ids",
        "transaction_locator",
        "precommit_context",
        "checkpoint_payload",
        "raw_rng_state",
        "candidate_pool",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if (
                str(key).lower() in private_keys
                and child is not False
                and child is not None
                and child != 0
            ):
                raise ValueError(f"private value in public payload: {key}")
            public_payload_is_sanitized(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            public_payload_is_sanitized(child)
    elif isinstance(value, str) and ("C:/Users/" in value or "C:\\Users\\" in value):
        raise ValueError("personal path in public payload")


def checkpoint_identity_summary(value: RestorableTransactionCheckpoint) -> dict[str, Any]:
    """Return private diagnostics without serializing the underlying engine state."""

    checkpoint = value.restore()
    return {
        "epoch": checkpoint.epoch,
        "event_cursor": checkpoint.event_cursor,
        "closure_sha256": value.expected_closure_sha256,
        "context_sha256": value.expected_context_sha256,
        "checkpoint_sha256": sha256(value.checkpoint_payload).hexdigest(),
    }
