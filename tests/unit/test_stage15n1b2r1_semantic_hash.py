from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from edge_reproduction.diagnostics.oracle_checkpoint import (
    SEMANTIC_SCHEMA_VERSION,
    canonical_semantic_bytes,
    canonical_semantic_sha256,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class LogicalState:
    count: int
    ratio: float
    labels: set[str]
    ordered: list[int]


def _state() -> LogicalState:
    return LogicalState(7, 0.1, {"beta", "alpha"}, [3, 2, 1])


def test_semantic_hash_is_insertion_order_independent() -> None:
    first = {"mapping": {"b": 2, "a": 1}, "set": {"z", "a"}}
    second = {"set": {"a", "z"}, "mapping": {"a": 1, "b": 2}}
    assert canonical_semantic_sha256(first) == canonical_semantic_sha256(second)


def test_list_and_tuple_order_remain_semantic() -> None:
    assert canonical_semantic_sha256([1, 2]) != canonical_semantic_sha256([2, 1])
    assert canonical_semantic_sha256((1, 2)) != canonical_semantic_sha256((2, 1))


def test_type_tags_and_scientific_fields_change_hash() -> None:
    assert canonical_semantic_sha256(1) != canonical_semantic_sha256("1")
    original = _state()
    changed = LogicalState(8, original.ratio, original.labels, original.ordered)
    assert canonical_semantic_sha256(original) != canonical_semantic_sha256(changed)


def test_float_contract_is_exact_and_rejects_nonfinite() -> None:
    value = json.loads(canonical_semantic_bytes(0.1))["value"]
    assert value == {"type": "float", "value": (0.1).hex()}
    with pytest.raises(ValueError, match="NaN and Infinity"):
        canonical_semantic_sha256(float("nan"))
    with pytest.raises(ValueError, match="NaN and Infinity"):
        canonical_semantic_sha256(float("inf"))


def test_canonicalization_does_not_mutate_or_draw_rng() -> None:
    import random

    rng = random.Random(42)
    before_rng = rng.getstate()
    state = _state()
    before = (state.count, state.ratio, set(state.labels), list(state.ordered))
    canonical_semantic_sha256({"state": state, "rng_state": before_rng})
    after = (state.count, state.ratio, set(state.labels), list(state.ordered))
    assert rng.getstate() == before_rng
    assert before == after


def test_semantic_hash_is_stable_across_process_and_pythonhashseed() -> None:
    code = (
        "from edge_reproduction.diagnostics.oracle_checkpoint import "
        "canonical_semantic_sha256; "
        "print(canonical_semantic_sha256({'m': {'b': 2, 'a': 1}, "
        "'s': {'gamma', 'alpha', 'beta'}, 'ordered': [3, 2, 1]}))"
    )
    results: list[str] = []
    for hash_seed in ("1", "777"):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = hash_seed
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
            cwd=ROOT,
        )
        results.append(completed.stdout.strip())
    assert len(set(results)) == 1


def test_schema_is_versioned_and_legacy_contract_is_not_reused() -> None:
    envelope = json.loads(canonical_semantic_bytes(_state()))
    assert envelope["schema_version"] == SEMANTIC_SCHEMA_VERSION
    source = (ROOT / "src/edge_reproduction/diagnostics/oracle_checkpoint.py").read_text(
        encoding="utf-8"
    )
    assert "legacy_raw_pickle_sha256" in source
    assert "semantic_closure_sha256" in source


def test_runner_is_suffix_only_and_has_no_oracle_execution() -> None:
    source = (ROOT / "scripts/run_stage15n1b2r1_semantic_materialization.py").read_text(
        encoding="utf-8"
    )
    assert "synthetic_normal_temporal_tasks" not in source
    assert "run_temporal_policy(" not in source
    assert "workflow_dispatch" not in source
    assert '"oracle_or_counterfactual_branches_executed": 0' in source
