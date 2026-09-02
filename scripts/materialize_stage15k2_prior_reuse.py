"""Create sanitized reuse evidence from the validated Stage-15E stable archive."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

NEW_SEEDS = (
    2074092324964443463,
    2218754797665862270,
    2997476077322633071,
    3782887846963969634,
)
POLICIES = (
    "pipeline_double_knapsack_retention",
    "pipeline_double_knapsack_preemption",
)


def materialize(archive: Path) -> dict[str, object]:
    manifest_path = archive / "manifest_sha256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "validated_20_of_20":
        raise ValueError("Stage-15E archive is not the validated 20/20 package")
    listed = {row["path"]: row for row in manifest["files"]}
    pairs: list[dict[str, object]] = []
    for seed in NEW_SEEDS:
        for policy in POLICIES:
            pattern = (
                f"stage15e-{seed}-initial_population_repair-{policy}-*"
                f"/stage15e-{seed}-initial_population_repair-{policy}.json"
            )
            matches = list((archive / "artifacts").glob(pattern))
            if len(matches) != 1:
                raise ValueError(f"expected one validated prior artifact for {seed}:{policy}")
            path = matches[0]
            relative = path.relative_to(archive / "artifacts").as_posix()
            expected = listed.get(relative)
            actual_hash = sha256(path.read_bytes()).hexdigest()
            if expected is None or expected["sha256"] != actual_hash:
                raise ValueError(f"source checksum mismatch: {relative}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            replay = cast(dict[str, Any], payload["variant_replay"])
            pairs.append(
                {
                    "workload_seed": seed,
                    "policy_seed": payload["policy_seed"],
                    "policy": policy,
                    "variant": payload["variant"],
                    "replay_exact": payload["replay_exact"],
                    "rng_gate": payload["rng_gate"],
                    "scientific_fingerprint": replay["scientific_fingerprint"],
                    "selector_funnel": replay["selector_funnel"],
                    "auction_funnel": replay["auction_funnel"],
                    "lifecycle_funnel": replay["lifecycle_funnel"],
                    "counterfactual": replay["counterfactual"],
                    "outcome_delta_from_baseline": payload["outcome_delta_from_baseline"],
                    "source_run_id": 31729227438,
                    "source_artifact_sha256": actual_hash,
                }
            )
    return {
        "schema_version": "stage15k2-prior-initialization-repair-reuse-v1",
        "label": "[آزمون کمکی] sanitized reuse of validated Stage 15-E artifacts",
        "source_stage": "Stage 15-E",
        "source_run_id": 31729227438,
        "source_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "variant_recomputed": False,
        "pair_count": len(pairs),
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    args.output.write_text(
        json.dumps(materialize(args.archive), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
