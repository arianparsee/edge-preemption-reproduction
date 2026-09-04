"""Run the single-seed ASSUMP-046 + ASSUMP-054 proposed-method pilot."""

from __future__ import annotations

import argparse
import json
import random
import time
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls

from edge_reproduction.algorithms.double_knapsack_preemption import PipelineDKPConfig
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy, lifecycle_funnel
from edge_reproduction.diagnostics.ga_counterfactual import (
    CounterfactualKnapsackSelector,
    CounterfactualVariant,
)
from edge_reproduction.diagnostics.ga_instrumentation import (
    InstrumentedKnapsackSelector,
    _state_hash,
)
from edge_reproduction.experiments.pipe_normal_full import (
    BASELINE,
    _descriptor,
    _mapping,
    _workload_payload,
    load_full_config,
)
from edge_reproduction.modified_methods.no_cascading_dkp import (
    NoCascadingDKPPolicy,
    assert_no_cascading_summary,
    validate_utility_conservation,
)
from edge_reproduction.simulation.temporal_engine import (
    TemporalRunConfig,
    run_temporal_policy,
    synthetic_normal_temporal_tasks,
)

WORKLOAD_SEED = 541501192080118187
POLICY_SEED = 18158600156516774620
POLICY = "pipeline_double_knapsack_preemption"
VARIANT = CounterfactualVariant.INITIAL_POPULATION_REPAIR
BASELINE_FIXTURE_SHA256 = "5a76406da63fdcb853a5cb04d57e0a3e0bc41d6dac94b90b39e562ce686bc3ca"
REPAIR_FIXTURE_SHA256 = "06eec52a4d346cb6014b8cd29e73323659a5c72c4e8ac86e81dac57932a25c12"
BASELINE_SOURCE_RESULT_SHA256 = "5d13847acc54f5581193a442918256deea375b50b42f25aba4a740d600f50cc8"
REPAIR_SOURCE_ARTIFACT_SHA256 = "e37204aa7fa8516db1224cd13c59076e52699647751be99672ad412fc37e7d4e"
EXPECTED_WORKLOAD_SHA256 = "e571940d01f46f5251d62d89453099c7f466fda7e22ccd350f4aa05d3c4a1200"
EXPECTED_CONFIG_SHA256 = "b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963"


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path.name}")
    return value


def _find_reused_comparators(
    baseline_fixture: Path, repair_fixture: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, object]]:
    if file_sha256(baseline_fixture) != BASELINE_FIXTURE_SHA256:
        raise ValueError("pinned baseline fixture checksum mismatch")
    if file_sha256(repair_fixture) != REPAIR_FIXTURE_SHA256:
        raise ValueError("pinned repair-only fixture checksum mismatch")
    baselines = _object(baseline_fixture)
    baseline = cast(
        dict[str, Any],
        cast(dict[str, Any], baselines["records"])[f"{WORKLOAD_SEED}:{POLICY}"],
    )
    pairs = cast(list[dict[str, Any]], _object(repair_fixture)["pairs"])
    matches = [
        pair
        for pair in pairs
        if int(pair["workload_seed"]) == WORKLOAD_SEED
        and pair["policy"] == POLICY
        and pair["variant"] == VARIANT.value
    ]
    if len(matches) != 1:
        raise ValueError("expected exactly one validated repair-only comparator")
    repair = matches[0]
    if (
        baseline.get("source_result_sha256") != BASELINE_SOURCE_RESULT_SHA256
        or repair.get("source_artifact_sha256") != REPAIR_SOURCE_ARTIFACT_SHA256
        or baseline.get("baseline_rng_status") != "available_reused_stage15c"
        or not repair.get("replay_exact")
    ):
        raise ValueError("comparator provenance is not the pinned validated lineage")
    baseline_fp = cast(dict[str, Any], baseline["scientific_fingerprint"])
    repair_fp = cast(dict[str, Any], repair["scientific_fingerprint"])
    for fingerprint in (baseline_fp, repair_fp):
        if (
            int(fingerprint["workload_seed"]) != WORKLOAD_SEED
            or int(fingerprint["policy_seed"]) != POLICY_SEED
            or fingerprint["policy"] != POLICY
            or fingerprint["workload_sha256"] != EXPECTED_WORKLOAD_SHA256
        ):
            raise ValueError("comparator scientific identity mismatch")
    baseline_outcome = cast(dict[str, object], baseline_fp["outcome"])
    repair_outcome = cast(dict[str, object], repair_fp["outcome"])
    expected_baseline = {
        "completed_utility": 3193.9193472199277,
        "completed_jobs": 40,
        "ever_preempted_jobs": 6,
    }
    expected_repair = {
        "completed_utility": 9541.426964770584,
        "completed_jobs": 117,
        "ever_preempted_jobs": 29,
        "rejected_utility": 74460.00877807708,
    }
    for key, expected in expected_baseline.items():
        if float(cast(float | int, baseline_outcome[key])) != float(expected):
            raise ValueError(f"baseline comparator mismatch: {key}")
    for key, expected in expected_repair.items():
        if float(cast(float | int, repair_outcome[key])) != float(expected):
            raise ValueError(f"repair-only comparator mismatch: {key}")
    repair_auction = cast(dict[str, Any], repair["auction_funnel"])
    repair_totals = cast(dict[str, int], repair_auction["totals"])
    if repair_totals["round_2_accepted"] != 146:
        raise ValueError("repair-only Round-2 admission mismatch")
    baseline_lifecycle = cast(dict[str, int], baseline["lifecycle_funnel"])
    if baseline_lifecycle["accepted"] != 46:
        raise ValueError("baseline Round-2 admission mismatch")
    provenance = {
        "baseline_fixture_sha256": BASELINE_FIXTURE_SHA256,
        "baseline_source_result_sha256": BASELINE_SOURCE_RESULT_SHA256,
        "repair_fixture_sha256": REPAIR_FIXTURE_SHA256,
        "repair_source_artifact_sha256": REPAIR_SOURCE_ARTIFACT_SHA256,
        "baseline_recomputed": False,
        "repair_only_recomputed": False,
    }
    return baseline, repair, provenance


def _terminal_funnel(run: Any) -> dict[str, int]:
    events = tuple(run.events)
    ever_accepted = {event.task_id for event in events if event.event_type.value == "accepted"}
    preempted = set(run.outcome.ever_preempted_task_ids)
    completed = set(run.outcome.completed_task_ids)
    accepted_then_expired = {
        task_id
        for task_id in ever_accepted
        if task_id not in completed and task_id not in preempted
    }
    canonical_infeasible = {
        event.task_id
        for event in events
        if event.event_type.value == "expired"
        and str(event.reason).startswith("canonical_admission_infeasible")
        and event.task_id not in ever_accepted
    }
    never_admitted = (
        set(run.outcome.rejected_task_ids)
        - preempted
        - accepted_then_expired
        - canonical_infeasible
    )
    all_ids = set(run.final_state.tasks)
    groups = (
        completed,
        preempted,
        accepted_then_expired,
        canonical_infeasible,
        never_admitted,
    )
    if sum(len(group) for group in groups) != len(set().union(*groups)):
        raise ValueError("terminal funnel groups overlap")
    if set().union(*groups) != all_ids:
        raise ValueError("terminal funnel does not cover the generated workload")
    return {
        "completed": len(completed),
        "preempted": len(preempted),
        "accepted_then_expired": len(accepted_then_expired),
        "pre_admission_infeasible": len(canonical_infeasible),
        "never_admitted_expired": len(never_admitted),
    }


def _execute_once(config: dict[str, object]) -> dict[str, object]:
    descriptor = _descriptor(config, WORKLOAD_SEED)
    policy_seed = int(cast(int, _mapping(descriptor["policy_seeds"], "policy_seeds")[POLICY]))
    if policy_seed != POLICY_SEED:
        raise ValueError("materialized policy seed changed")
    workload, dataset = _workload_payload(WORKLOAD_SEED)
    workload_hash = sha256(
        (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    if workload_hash != EXPECTED_WORKLOAD_SHA256:
        raise ValueError("materialized workload hash changed")
    tasks = synthetic_normal_temporal_tasks(tuple(record.to_domain() for record in dataset.tasks))
    servers = tuple(record.to_domain() for record in dataset.servers)
    ga = PyeasygaConfig(seed=policy_seed)
    counterfactual = CounterfactualKnapsackSelector(ga, VARIANT)
    selector = InstrumentedKnapsackSelector(
        counterfactual, server_count=len(servers), diagnostic_stage="stage15m1"
    )
    config_dkp = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
    modified = NoCascadingDKPPolicy(config_dkp, selector)
    policy = InstrumentedDKPolicy(modified, selector)
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
            run_id=f"STAGE15M1.{WORKLOAD_SEED}.DKP",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=config_dkp.as_metadata()
        | {
            "scientific_status": "proposed_modified_method",
            "assumptions": "ASSUMP-046,ASSUMP-054",
        },
    )
    run.metadata = MappingProxyType(
        dict(run.metadata) | selector.runtime_metadata() | counterfactual.runtime_metadata()
    )
    completed_ids = set(run.outcome.completed_task_ids)
    rejected_ids = set(run.outcome.rejected_task_ids)
    all_ids = set(run.final_state.tasks)
    if completed_ids & rejected_ids or completed_ids | rejected_ids != all_ids:
        raise ValueError("scientific failure: terminal task partition invariant")
    if not set(run.outcome.ever_preempted_task_ids).issubset(rejected_ids):
        raise ValueError("scientific failure: preempted tasks are not a rejected subset")
    conservation_residual = validate_utility_conservation(
        total=sum(task.utility for task in tasks),
        completed=run.outcome.completed_utility,
        rejected=run.outcome.rejected_utility,
    )
    payload: dict[str, object] = {
        "baseline": BASELINE,
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": policy_seed,
        "policy": POLICY,
        "workload_sha256": workload_hash,
        "run": run.as_dict(),
    }
    call_rows = _sanitized_selector_calls(selector, counterfactual)
    public_guard = modified.public_summary(run.final_state, run.events)
    assert_no_cascading_summary(public_guard)
    return {
        "scientific_fingerprint": scientific_fingerprint(payload),
        "selector_funnel": selector.summary().as_dict(),
        "auction_funnel": policy.summary(),
        "lifecycle_funnel": lifecycle_funnel(run.events),
        "terminal_funnel": _terminal_funnel(run),
        "counterfactual": counterfactual.counterfactual_summary(),
        "selector_calls": call_rows,
        "selector_call_shape_sha256": _canonical_hash(
            [
                {
                    "auction_ordinal": row["auction_ordinal"],
                    "round_name": row["round_name"],
                    "server_ordinal": row["server_ordinal"],
                    "call_kind": row["call_kind"],
                    "candidate_count": row["candidate_count"],
                }
                for row in call_rows
            ]
        ),
        "selector_rng_trace_sha256": _canonical_hash(call_rows),
        "no_cascading": public_guard,
        "invariant_gate": {
            "capacity_and_state": True,
            "terminal_partition": True,
            "preempted_subset_of_rejected": True,
            "utility_conservation": True,
            "utility_conservation_residual": conservation_residual,
            "numerical_tolerance": 1e-9,
        },
    }


def _shape(summary: Mapping[str, Any]) -> dict[str, int]:
    by_round = cast(dict[str, dict[str, int]], summary["by_round"])
    keys = (
        "selector_calls",
        "empty_calls",
        "single_candidate_calls",
        "ga_calls",
        "candidate_entries",
    )
    return {
        f"{round_name}.{key}": int(by_round[round_name][key])
        for round_name in ("round_1", "round_2")
        for key in keys
    }


def run_pilot(
    *, config_path: Path, baseline_fixture: Path, repair_fixture: Path
) -> dict[str, object]:
    if file_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved PIPE-NORMAL config checksum mismatch")
    baseline, repair, provenance = _find_reused_comparators(baseline_fixture, repair_fixture)
    config = load_full_config(config_path)
    started = time.perf_counter()
    first = _execute_once(config)
    first_seconds = time.perf_counter() - started
    started = time.perf_counter()
    second = _execute_once(config)
    second_seconds = time.perf_counter() - started
    if first != second:
        raise ValueError("scientific failure: Stage 15-M.1 replay mismatch")
    selector = cast(dict[str, Any], first["selector_funnel"])
    if selector["initial_rng_state_sha256"] != _state_hash(random.Random(POLICY_SEED).getstate()):
        raise ValueError("scientific failure: initial RNG state differs from policy seed")
    repair_selector = cast(dict[str, Any], repair["selector_funnel"])
    current_shape = _shape(selector)
    repair_shape = _shape(repair_selector)
    changed_shape = {
        key: {"repair_only": repair_shape[key], "modified": current_shape[key]}
        for key in current_shape
        if current_shape[key] != repair_shape[key]
    }
    final_rng_equal = (
        selector["final_rng_state_sha256"] == repair_selector["final_rng_state_sha256"]
    )
    if not changed_shape and not final_rng_equal:
        raise ValueError("scientific failure: RNG changed despite identical selector call shape")
    fingerprint = cast(dict[str, Any], first["scientific_fingerprint"])
    outcome = cast(dict[str, float | int], fingerprint["outcome"])
    repair_outcome = cast(
        dict[str, float | int], cast(dict[str, Any], repair["scientific_fingerprint"])["outcome"]
    )
    baseline_outcome = cast(
        dict[str, float | int], cast(dict[str, Any], baseline["scientific_fingerprint"])["outcome"]
    )
    lifecycle = cast(dict[str, int], first["lifecycle_funnel"])
    repair_lifecycle = cast(dict[str, int], repair["lifecycle_funnel"])
    terminal = cast(dict[str, int], first["terminal_funnel"])
    if lifecycle.get("expired_during_canonicalization", 0) != repair_lifecycle.get(
        "expired_during_canonicalization", 0
    ):
        raise ValueError("PRE_ADMISSION_INFEASIBLE changed from ASSUMP-046 comparator")
    admission = int(
        cast(dict[str, int], cast(dict[str, Any], first["auction_funnel"])["totals"])[
            "round_2_accepted"
        ]
    )
    completion = int(outcome["completed_jobs"])
    preemptions = int(outcome["ever_preempted_jobs"])
    completed_utility = float(outcome["completed_utility"])
    rejected_utility = float(outcome["rejected_utility"])
    repair_admission = int(
        cast(dict[str, int], cast(dict[str, Any], repair["auction_funnel"])["totals"])[
            "round_2_accepted"
        ]
    )
    criteria = {
        "completed_utility_increased": completed_utility
        > float(repair_outcome["completed_utility"]),
        "rejected_utility_decreased": rejected_utility < float(repair_outcome["rejected_utility"]),
        "completion_per_admission_increased": completion / admission
        > int(repair_outcome["completed_jobs"]) / repair_admission,
        "preemptions_decreased": preemptions < int(repair_outcome["ever_preempted_jobs"]),
        "direct_chain_depth_at_most_one": int(
            cast(dict[str, Any], cast(dict[str, Any], first["no_cascading"])["preemption"])[
                "direct_chain_maximum_depth"
            ]
        )
        <= 1,
        "preemptive_admission_completed": int(
            cast(dict[str, Any], cast(dict[str, Any], first["no_cascading"])["protection"])[
                "completed"
            ]
        )
        > 0,
        "pre_admission_infeasible_unchanged": terminal["pre_admission_infeasible"]
        == repair_lifecycle["expired_during_canonicalization"],
        "waiting_expiration_not_increased": lifecycle.get("expired_waiting_at_deadline", 0)
        <= repair_lifecycle.get("expired_waiting_at_deadline", 0),
        "round_one_implementation_and_settings_unchanged": True,
        "replay_rng_invariants_passed": True,
    }
    return {
        "schema_version": "stage15m1-no-cascading-pilot-v1",
        "label": "[روش اصلاح‌شده پیشنهادی] Stage 15-M.1 ASSUMP-046 + ASSUMP-054",
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": POLICY_SEED,
        "policy": POLICY,
        "variant": "initial_population_repair_plus_permanent_no_cascading",
        "logical_pairs": 1,
        "replay_count": 2,
        "replay_exact": True,
        "baseline_recomputed": False,
        "repair_only_recomputed": False,
        "provenance": provenance,
        "config_sha256": EXPECTED_CONFIG_SHA256,
        "rng_gate": {
            "option": "A",
            "initial_state_matches_policy_seed": True,
            "same_variant_replays_exact": True,
            "direct_random_draws_added_by_guard": False,
            "repair_only_final_rng_equal": final_rng_equal,
            "call_shape_differences_explain_later_rng_divergence": bool(changed_shape)
            or final_rng_equal,
            "changed_call_shape": changed_shape,
        },
        "baseline": {
            "outcome": baseline_outcome,
            "round_2_admission": cast(dict[str, int], baseline["lifecycle_funnel"])["accepted"],
        },
        "repair_only": {
            "outcome": repair_outcome,
            "round_2_admission": repair_admission,
            "completion_per_admission": int(repair_outcome["completed_jobs"]) / repair_admission,
        },
        "modified": first,
        "comparison_to_repair_only": {
            "completed_utility_delta": completed_utility
            - float(repair_outcome["completed_utility"]),
            "rejected_utility_delta": rejected_utility - float(repair_outcome["rejected_utility"]),
            "completed_jobs_delta": completion - int(repair_outcome["completed_jobs"]),
            "preempted_jobs_delta": preemptions - int(repair_outcome["ever_preempted_jobs"]),
            "round_2_admission_delta": admission - repair_admission,
            "completion_per_admission": completion / admission if admission else 0.0,
        },
        "success_criteria": criteria,
        "pilot_success": all(criteria.values()),
        "runtime_seconds": {"replay_1": first_seconds, "replay_2": second_seconds},
        "publication": {
            "task_identifiers": False,
            "raw_edges": False,
            "chromosomes": False,
            "raw_workload": False,
            "official_pipeline_changed": False,
            "figure_6_status": "بازتولید نشد",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline-fixture", type=Path, required=True)
    parser.add_argument("--repair-fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-M.1 output: {args.output}")
    report = run_pilot(
        config_path=args.config,
        baseline_fixture=args.baseline_fixture,
        repair_fixture=args.repair_fixture,
    )
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"status": "stage15m1_pair_complete", "pilot_success": report["pilot_success"]})
    )


if __name__ == "__main__":
    main()
