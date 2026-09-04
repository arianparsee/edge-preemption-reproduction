"""Validate the sanitized public Stage 15-M.1B pilot artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_PUBLIC_KEYS = {
    "task_id",
    "task_ids",
    "incoming_task_ids",
    "victim_task_ids",
    "chromosome",
    "raw_trace",
}


def _assert_no_private_payload(value: object) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_PUBLIC_KEYS & set(value)
        if forbidden:
            raise ValueError(f"private public-artifact keys found: {sorted(forbidden)}")
        if value.get("raw_edges") is not None and value.get("raw_edges") is not False:
            raise ValueError("public artifact contains raw edges")
        for child in value.values():
            _assert_no_private_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_private_payload(child)


def validate(payload: dict[str, Any]) -> dict[str, object]:
    if payload.get("schema_version") != "stage15m1b-one-auction-cooldown-pilot-v1":
        raise ValueError("invalid Stage 15-M.1B schema")
    _assert_no_private_payload(payload)
    if payload.get("logical_pairs") != 1 or payload.get("replay_count") != 2:
        raise ValueError("Stage 15-M.1B must contain one logical pair and two replays")
    if payload.get("replay_exact") is not True:
        raise ValueError("Stage 15-M.1B replay equality failed")
    for key in ("baseline_recomputed", "repair_only_recomputed", "permanent_guard_recomputed"):
        if payload.get(key) is not False:
            raise ValueError(f"reuse-only contract failed: {key}")
    if payload.get("workload_seed") != 541501192080118187:
        raise ValueError("unexpected workload seed")
    if payload.get("policy") != "pipeline_double_knapsack_preemption":
        raise ValueError("unexpected policy")
    if payload.get("variant") != "initial_population_repair_plus_one_auction_cooldown":
        raise ValueError("unexpected Stage 15-M.1B variant")
    rng = payload.get("rng_gate")
    if not isinstance(rng, dict) or any(
        rng.get(key) is not True
        for key in (
            "initial_state_matches_policy_seed",
            "same_variant_replays_exact",
            "call_shape_differences_explain_later_rng_divergence",
        )
    ):
        raise ValueError("RNG Option-A validation failed")
    if rng.get("direct_random_draws_added_by_guard") is not False:
        raise ValueError("cooldown guard added a direct random draw")
    publication = payload.get("publication")
    if not isinstance(publication, dict):
        raise TypeError("publication section is missing")
    for key in ("task_identifiers", "raw_edges", "chromosomes", "raw_workload"):
        if publication.get(key) is not False:
            raise ValueError(f"public artifact contains forbidden material: {key}")
    if publication.get("official_pipeline_changed") is not False:
        raise ValueError("official pipeline changed")
    if publication.get("figure_6_status") != "بازتولید نشد":
        raise ValueError("Figure 6 status changed")
    modified = payload.get("modified")
    if not isinstance(modified, dict):
        raise TypeError("modified result is missing")
    invariant = modified.get("invariant_gate")
    if not isinstance(invariant, dict) or any(
        invariant.get(key) is not True
        for key in (
            "capacity_and_state",
            "terminal_partition",
            "preempted_subset_of_rejected",
            "utility_conservation",
        )
    ):
        raise ValueError("scientific invariant gate failed")
    guard = modified.get("cooldown_guard")
    if not isinstance(guard, dict):
        raise TypeError("cooldown guard summary is missing")
    public_flags = ("task_identifiers_recorded", "raw_edges_recorded", "raw_workload_recorded")
    if any(guard.get(key) is not False for key in public_flags):
        raise ValueError("cooldown summary is not sanitized")
    criteria = payload.get("success_criteria")
    if not isinstance(criteria, dict) or payload.get("pilot_success") is not all(
        value is True for value in criteria.values()
    ):
        raise ValueError("pilot success flag does not match its criteria")
    return {
        "schema_version": "stage15m1b-public-validation-v1",
        "valid": True,
        "pilot_success": bool(payload["pilot_success"]),
        "logical_pairs": 1,
        "replay_count": 2,
        "sanitized": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Stage 15-M.1B artifact must be an object")
    report = validate(payload)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
