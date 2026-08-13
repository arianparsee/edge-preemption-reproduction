"""Create sanitized Stage-15E baseline and seed-one reuse fixtures.

This script reads only already-validated artifacts. It never invokes a policy,
simulator, GA or workload generator and refuses to overwrite its outputs.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from run_stage15b_ga_diagnostic import DK_POLICIES, scientific_fingerprint

from edge_reproduction.experiments.pipe_normal_full import load_full_config

FIRST_FIVE_SEEDS = (
    541501192080118187,
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)
VARIANTS = ("initial_population_repair", "offspring_repair")


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _lifecycle(events: object) -> dict[str, int]:
    if not isinstance(events, list):
        raise TypeError("baseline events must be a list")
    counts: Counter[str] = Counter()
    for raw in events:
        if not isinstance(raw, dict):
            raise TypeError("baseline event must be an object")
        event_type = str(raw["event_type"])
        counts[event_type] += 1
        if event_type == "expired":
            reason = str(raw["reason"])
            if reason.startswith("post_rejection_next_epoch_infeasible"):
                counts["expired_after_round_2_rejection"] += 1
            elif reason.startswith("canonical_admission_infeasible"):
                counts["expired_during_canonicalization"] += 1
            elif reason == "waiting_task_no_remaining_completion_opportunity":
                counts["expired_waiting_at_deadline"] += 1
            elif reason == "active_pipeline_incomplete_after_inclusive_deadline_opportunity":
                counts["expired_active_at_deadline"] += 1
    return dict(sorted(counts.items()))


def build_baselines(
    *, config_path: Path, result_paths: list[Path], rng_guard_path: Path
) -> dict[str, object]:
    config = load_full_config(config_path)
    runs = cast(list[dict[str, Any]], config["runs"])
    expected_seeds = tuple(int(run["workload_seed"]) for run in runs[:5])
    if expected_seeds != FIRST_FIVE_SEEDS:
        raise ValueError("first five materialized ASSUMP-033 seeds changed")
    expected = {
        (int(run["workload_seed"]), policy): int(run["policy_seeds"][policy])
        for run in runs[:5]
        for policy in DK_POLICIES
    }
    if len(result_paths) != 10:
        raise ValueError("Stage 15-E baseline fixture requires exactly ten result files")
    guard = _load(rng_guard_path)
    if guard.get("baseline_recomputed") is not False:
        raise ValueError("seed-one RNG guard must be reuse-only")
    records: dict[str, dict[str, object]] = {}
    seen: set[tuple[int, str]] = set()
    for path in result_paths:
        payload = _load(path)
        seed = int(payload["workload_seed"])
        policy = str(payload["policy"])
        key = (seed, policy)
        if key not in expected or key in seen:
            raise ValueError("unexpected or duplicate baseline result")
        if int(payload["policy_seed"]) != expected[key]:
            raise ValueError("baseline policy seed differs from materialized config")
        run = cast(dict[str, Any], payload["run"])
        fingerprint = scientific_fingerprint(cast(dict[str, object], payload))
        rng = None
        rng_status = "unavailable_not_recorded"
        if seed == FIRST_FIVE_SEEDS[0]:
            rng = guard["policies"].get(policy)
            if rng is None:
                raise ValueError("seed-one policy missing from Stage-15C RNG guard")
            rng_status = "available_reused_stage15c"
        records[f"{seed}:{policy}"] = {
            "workload_seed": seed,
            "policy_seed": expected[key],
            "policy": policy,
            "source_result_sha256": _hash(path),
            "source_stage": "Stage 13-H" if seed == FIRST_FIVE_SEEDS[0] else "Stage 13-I",
            "scientific_fingerprint": fingerprint,
            "lifecycle_funnel": _lifecycle(run["events"]),
            "baseline_rng_status": rng_status,
            "baseline_rng": rng,
        }
        seen.add(key)
    if seen != set(expected):
        raise ValueError("baseline result matrix is incomplete")
    return {
        "schema_version": "stage15e-reused-baselines-v1",
        "label": "[آزمون کمکی] reusable baseline evidence; no baseline recomputation",
        "baseline_recomputed": False,
        "first_five_materialized_seeds": list(FIRST_FIVE_SEEDS),
        "record_count": 10,
        "records": dict(sorted(records.items())),
    }


def build_seed_one_reuse(pair_paths: list[Path]) -> dict[str, object]:
    if len(pair_paths) != 4:
        raise ValueError("seed-one reuse requires exactly four Stage-15D pair artifacts")
    pairs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for path in pair_paths:
        payload = _load(path)
        key = (str(payload["policy"]), str(payload["variant"]))
        if (
            payload.get("schema_version") != "stage15d-counterfactual-pair-v1"
            or payload.get("workload_seed") != FIRST_FIVE_SEEDS[0]
            or key[0] not in DK_POLICIES
            or key[1] not in VARIANTS
            or key in seen
            or payload.get("baseline_recomputed") is not False
            or payload.get("replay_exact") is not True
            or cast(dict[str, object], payload["rng_gate"]).get("passed") is not True
        ):
            raise ValueError("invalid Stage-15D seed-one reuse artifact")
        replay = cast(dict[str, object], payload["variant_replay"])
        pairs.append(
            {
                "source_artifact_sha256": _hash(path),
                "workload_seed": payload["workload_seed"],
                "policy_seed": payload["policy_seed"],
                "policy": payload["policy"],
                "variant": payload["variant"],
                "replay_count": payload["replay_count"],
                "replay_exact": payload["replay_exact"],
                "rng_gate": payload["rng_gate"],
                "scientific_fingerprint": replay["scientific_fingerprint"],
                "selector_funnel": replay["selector_funnel"],
                "auction_funnel": replay["auction_funnel"],
                "lifecycle_funnel": replay["lifecycle_funnel"],
                "counterfactual": replay["counterfactual"],
                "outcome_delta_from_baseline": payload["outcome_delta_from_baseline"],
            }
        )
        seen.add(key)
    expected = {(policy, variant) for policy in DK_POLICIES for variant in VARIANTS}
    if seen != expected:
        raise ValueError("seed-one Stage-15D reuse matrix is incomplete")
    return {
        "schema_version": "stage15e-seed-one-reuse-v1",
        "label": "[آزمون کمکی] reused Stage 15-D.1 pairs",
        "source_stage": "Stage 15-D.1",
        "baseline_recomputed": False,
        "variant_recomputed": False,
        "pair_count": 4,
        "pairs": sorted(pairs, key=lambda row: (str(row["policy"]), str(row["variant"]))),
    }


def _write(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite fixture: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline-result", action="append", type=Path, required=True)
    parser.add_argument("--rng-guard", type=Path, required=True)
    parser.add_argument("--seed-one-pair", action="append", type=Path, required=True)
    parser.add_argument("--baseline-output", type=Path, required=True)
    parser.add_argument("--seed-one-output", type=Path, required=True)
    args = parser.parse_args()
    _write(
        args.baseline_output,
        build_baselines(
            config_path=args.config,
            result_paths=args.baseline_result,
            rng_guard_path=args.rng_guard,
        ),
    )
    _write(args.seed_one_output, build_seed_one_reuse(args.seed_one_pair))
    print(json.dumps({"status": "materialized_reuse_only", "baselines": 10, "pairs": 4}))


if __name__ == "__main__":
    main()
