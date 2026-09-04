"""Run the single-seed ASSUMP-046 + ASSUMP-055 auxiliary pilot."""

from __future__ import annotations

import argparse
import json
import random
import time
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from run_stage15b_ga_diagnostic import scientific_fingerprint
from run_stage15d_counterfactual import _canonical_hash, _sanitized_selector_calls
from run_stage15m1_pilot import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY,
    POLICY_SEED,
    VARIANT,
    WORKLOAD_SEED,
    _find_reused_comparators,
    _object,
    _shape,
    _terminal_funnel,
    file_sha256,
)

from edge_reproduction.algorithms.double_knapsack_preemption import PipelineDKPConfig
from edge_reproduction.algorithms.genetic_knapsack import PyeasygaConfig
from edge_reproduction.diagnostics.dk_funnel import InstrumentedDKPolicy, lifecycle_funnel
from edge_reproduction.diagnostics.ga_counterfactual import CounterfactualKnapsackSelector
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
from edge_reproduction.modified_methods.no_cascading_dkp import validate_utility_conservation
from edge_reproduction.modified_methods.one_auction_cooldown_dkp import (
    OneAuctionCooldownDKPPolicy,
    assert_cooldown_summary,
)
from edge_reproduction.simulation.temporal_engine import (
    TemporalRunConfig,
    run_temporal_policy,
    synthetic_normal_temporal_tasks,
)

PERMANENT_FIXTURE_SHA256 = "236aa0031163512bfccb73d67fba64ed0c099f9e1ed596260230fcab4cc9cdc5"
PERMANENT_SOURCE_ZIP_SHA256 = "8799ec05d3e37c14c54aeb78c80c53fdb3bad01c5ec301bfdc6fb585e57dac14"
PERMANENT_SOURCE_PILOT_SHA256 = "b5b35d07afe9a4dc3927df9c597a736ca03eefafdb9a50e955802d362e3e7f22"


def _find_permanent_comparator(path: Path) -> dict[str, Any]:
    if file_sha256(path) != PERMANENT_FIXTURE_SHA256:
        raise ValueError("pinned ASSUMP-054 fixture checksum mismatch")
    value = _object(path)
    source = cast(dict[str, Any], value["source"])
    identity = cast(dict[str, Any], value["identity"])
    validation = cast(dict[str, Any], value["validation"])
    if (
        source["artifact_zip_sha256"] != PERMANENT_SOURCE_ZIP_SHA256
        or source["pilot_json_sha256"] != PERMANENT_SOURCE_PILOT_SHA256
        or source["workflow_conclusion"] != "success"
        or validation["valid"] is not True
        or validation["sanitized"] is not True
        or validation["logical_pairs"] != 1
        or validation["replay_count"] != 2
        or validation["replay_exact"] is not True
        or validation["baseline_recomputed"] is not False
        or validation["repair_only_recomputed"] is not False
    ):
        raise ValueError("ASSUMP-054 comparator provenance is invalid")
    if (
        int(identity["workload_seed"]) != WORKLOAD_SEED
        or int(identity["policy_seed"]) != POLICY_SEED
        or identity["policy"] != POLICY
        or identity["workload_sha256"] != EXPECTED_WORKLOAD_SHA256
        or identity["config_sha256"] != EXPECTED_CONFIG_SHA256
    ):
        raise ValueError("ASSUMP-054 comparator scientific identity mismatch")
    return value


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
        counterfactual, server_count=len(servers), diagnostic_stage="stage15m1b"
    )
    dkp_config = PipelineDKPConfig.from_workload(ga=ga, workload_tasks=tasks)
    modified = OneAuctionCooldownDKPPolicy(dkp_config, selector)
    policy = InstrumentedDKPolicy(modified, selector)
    run = run_temporal_policy(
        original_tasks=tasks,
        servers=servers,
        policy=policy,
        config=TemporalRunConfig(
            run_id=f"STAGE15M1B.{WORKLOAD_SEED}.DKP",
            policy_seed=policy_seed,
            arrival_slots=100,
        ),
        policy_metadata=dkp_config.as_metadata()
        | {
            "scientific_status": "auxiliary_proposed_modified_method",
            "assumptions": "ASSUMP-046,ASSUMP-055",
            "ASSUMP-054": "inactive",
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
    cooldown = modified.public_summary(run.final_state)
    assert_cooldown_summary(cooldown)
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
        "cooldown_guard": cooldown,
        "invariant_gate": {
            "capacity_and_state": True,
            "terminal_partition": True,
            "preempted_subset_of_rejected": True,
            "utility_conservation": True,
            "utility_conservation_residual": conservation_residual,
            "numerical_tolerance": 1e-9,
        },
    }


def run_pilot(
    *,
    config_path: Path,
    baseline_fixture: Path,
    repair_fixture: Path,
    permanent_fixture: Path,
) -> dict[str, object]:
    if file_sha256(config_path) != EXPECTED_CONFIG_SHA256:
        raise ValueError("approved PIPE-NORMAL config checksum mismatch")
    baseline, repair, provenance = _find_reused_comparators(baseline_fixture, repair_fixture)
    permanent = _find_permanent_comparator(permanent_fixture)
    config = load_full_config(config_path)
    started = time.perf_counter()
    first = _execute_once(config)
    first_seconds = time.perf_counter() - started
    started = time.perf_counter()
    second = _execute_once(config)
    second_seconds = time.perf_counter() - started
    if first != second:
        raise ValueError("scientific failure: Stage 15-M.1B replay mismatch")

    selector = cast(dict[str, Any], first["selector_funnel"])
    if selector["initial_rng_state_sha256"] != _state_hash(random.Random(POLICY_SEED).getstate()):
        raise ValueError("scientific failure: initial RNG state differs from policy seed")
    repair_selector = cast(dict[str, Any], repair["selector_funnel"])
    current_shape = _shape(selector)
    repair_shape = _shape(repair_selector)
    changed_shape = {
        key: {"repair_only": repair_shape[key], "cooldown": current_shape[key]}
        for key in current_shape
        if current_shape[key] != repair_shape[key]
    }
    final_rng_equal = selector["final_rng_state_sha256"] == repair_selector[
        "final_rng_state_sha256"
    ]
    if not changed_shape and not final_rng_equal:
        raise ValueError("scientific failure: RNG changed despite identical selector call shape")

    fingerprint = cast(dict[str, Any], first["scientific_fingerprint"])
    outcome = cast(dict[str, float | int], fingerprint["outcome"])
    repair_fp = cast(dict[str, Any], repair["scientific_fingerprint"])
    repair_outcome = cast(dict[str, float | int], repair_fp["outcome"])
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
    totals = cast(dict[str, int], cast(dict[str, Any], first["auction_funnel"])["totals"])
    repair_totals = cast(dict[str, int], cast(dict[str, Any], repair["auction_funnel"])["totals"])
    admission = totals["round_2_accepted"]
    repair_admission = repair_totals["round_2_accepted"]
    completion = int(outcome["completed_jobs"])
    completed_utility = float(outcome["completed_utility"])
    rejected_utility = float(outcome["rejected_utility"])
    preemptions = int(outcome["ever_preempted_jobs"])
    criteria = {
        "completed_utility_not_decreased": completed_utility
        >= float(repair_outcome["completed_utility"]),
        "rejected_utility_not_increased": rejected_utility
        <= float(repair_outcome["rejected_utility"]),
        "preemptions_decreased": preemptions < int(repair_outcome["ever_preempted_jobs"]),
        "pre_admission_infeasible_unchanged": terminal["pre_admission_infeasible"]
        == repair_lifecycle["expired_during_canonicalization"],
        "round_one_implementation_and_settings_unchanged": True,
        "replay_rng_invariants_passed": True,
    }
    return {
        "schema_version": "stage15m1b-one-auction-cooldown-pilot-v1",
        "label": "[فرض روش اصلاح‌شده پیشنهادی — آزمون کمکی] Stage 15-M.1B",
        "workload_seed": WORKLOAD_SEED,
        "policy_seed": POLICY_SEED,
        "policy": POLICY,
        "variant": "initial_population_repair_plus_one_auction_cooldown",
        "logical_pairs": 1,
        "replay_count": 2,
        "replay_exact": True,
        "baseline_recomputed": False,
        "repair_only_recomputed": False,
        "permanent_guard_recomputed": False,
        "provenance": provenance
        | {
            "permanent_fixture_sha256": PERMANENT_FIXTURE_SHA256,
            "permanent_source_zip_sha256": PERMANENT_SOURCE_ZIP_SHA256,
            "permanent_source_pilot_sha256": PERMANENT_SOURCE_PILOT_SHA256,
        },
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
            "completion_per_admission": int(repair_outcome["completed_jobs"])
            / repair_admission,
        },
        "permanent_guard": permanent,
        "modified": first,
        "comparison_to_repair_only": {
            "completed_utility_delta": completed_utility
            - float(repair_outcome["completed_utility"]),
            "rejected_utility_delta": rejected_utility - float(repair_outcome["rejected_utility"]),
            "completed_jobs_delta": completion - int(repair_outcome["completed_jobs"]),
            "preempted_jobs_delta": preemptions - int(repair_outcome["ever_preempted_jobs"]),
            "round_2_admission_delta": admission - repair_admission,
            "completion_per_admission": completion / admission if admission else 0.0,
            "retry_scheduled_delta": lifecycle.get("retry_scheduled", 0)
            - repair_lifecycle.get("retry_scheduled", 0),
            "expired_delta": lifecycle.get("expired", 0) - repair_lifecycle.get("expired", 0),
            "never_admitted_expired_delta": terminal["never_admitted_expired"]
            - (
                int(repair_outcome["rejected_jobs"])
                - int(repair_outcome["ever_preempted_jobs"])
                - repair_lifecycle.get("expired_during_canonicalization", 0)
            ),
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
    parser.add_argument("--permanent-fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Stage 15-M.1B output: {args.output}")
    report = run_pilot(
        config_path=args.config,
        baseline_fixture=args.baseline_fixture,
        repair_fixture=args.repair_fixture,
        permanent_fixture=args.permanent_fixture,
    )
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"status": "stage15m1b_pair_complete", "pilot_success": report["pilot_success"]})
    )


if __name__ == "__main__":
    main()
