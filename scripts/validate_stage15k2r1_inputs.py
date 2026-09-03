"""Validate immutable Stage-15K.1/K.2 pair artifacts before aggregation."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from finalize_stage15k2 import POLICIES, SEEDS, _exact_decimal_seed
from validate_stage15k1_public_pair import validate_pair as validate_k1_pair
from validate_stage15k2_pair import validate as validate_k2_pair

K1_RUN_ID = "33663692202"
K2_RUN_ID = "33688857517"
K2_SOURCE_HEAD_SHA = "95dd0910b0ce4f46595ddce2eaed0d3e87954e2c"
CONFIG_SHA256_LF_NORMALIZED = (
    "b0ae2597119fb5ee3a27b2998d27e252b5d66e67356408abb7315238056f1963"
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _lf_sha256(path: Path) -> str:
    return sha256(path.read_text(encoding="utf-8").replace("\r\n", "\n").encode()).hexdigest()


def _validate_internal_checksum(pair_path: Path) -> int:
    checksum_path = pair_path.with_name(f"{pair_path.stem}-checksum.json")
    manifest = _load(checksum_path)
    if manifest.get("schema_version") not in {
        "stage15k1-pair-checksum-v1",
        "stage15k2-pair-checksum-v1",
    }:
        raise ValueError(f"unexpected checksum schema: {checksum_path}")
    entries = cast(list[dict[str, Any]], manifest.get("files"))
    if len(entries) != 2:
        raise ValueError(f"checksum manifest must cover pair and validation files: {checksum_path}")
    for entry in entries:
        target = pair_path.with_name(str(entry["name"]))
        if not target.is_file():
            raise FileNotFoundError(target)
        if target.stat().st_size != int(entry["bytes"]):
            raise ValueError(f"byte-size mismatch: {target}")
        if sha256(target.read_bytes()).hexdigest() != str(entry["sha256"]):
            raise ValueError(f"SHA-256 mismatch: {target}")
    return len(entries)


def _fingerprints(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = [
        cast(dict[str, Any], payload["baseline"]),
        cast(dict[str, Any], payload["round_two_only_repair"]),
        cast(dict[str, Any], payload["prior_all_round_initialization_repair"]),
        cast(dict[str, Any], payload["variant_replay"]),
    ]
    return [cast(dict[str, Any], record["scientific_fingerprint"]) for record in records]


def validate_inputs(input_dir: Path, config_path: Path) -> dict[str, object]:
    if _lf_sha256(config_path) != CONFIG_SHA256_LF_NORMALIZED:
        raise ValueError("pinned scientific config checksum mismatch")
    pair_paths: list[Path] = []
    for path in input_dir.rglob("*.json"):
        try:
            schema = _load(path).get("schema_version")
        except (json.JSONDecodeError, TypeError):
            continue
        if schema in {
            "stage15k1-r2-initialization-repair-pilot-v1",
            "stage15k2-r2-initialization-repair-pair-v1",
        }:
            pair_paths.append(path)

    expected = {(seed, policy) for seed in SEEDS for policy in POLICIES}
    observed: set[tuple[int, str]] = set()
    records: list[dict[str, object]] = []
    for pair_path in pair_paths:
        payload = _load(pair_path)
        seed = _exact_decimal_seed(payload["workload_seed"])
        policy = str(payload["policy"])
        key = (seed, policy)
        if key in observed:
            raise ValueError(f"duplicate logical pair: {key}")
        observed.add(key)
        source_run_id = K1_RUN_ID if seed == SEEDS[0] else K2_RUN_ID
        if not any(source_run_id in part for part in pair_path.parts):
            raise ValueError(f"pair is outside its pinned source artifact: {pair_path}")

        checksum_files = _validate_internal_checksum(pair_path)
        if seed == SEEDS[0]:
            public = validate_k1_pair(pair_path)
            if payload.get("config_sha256_lf_normalized") != CONFIG_SHA256_LF_NORMALIZED:
                raise ValueError("Stage 15-K.1 config identity mismatch")
        else:
            public = validate_k2_pair(payload)
        validation_path = pair_path.with_name(f"{pair_path.stem}-validation.json")
        if _load(validation_path).get("status") not in {"valid", "passed"}:
            raise ValueError(f"published validation did not pass: {validation_path}")

        fingerprints = _fingerprints(payload)
        policy_seeds = {int(item["policy_seed"]) for item in fingerprints}
        workload_hashes = {str(item["workload_sha256"]) for item in fingerprints}
        if any(_exact_decimal_seed(item["workload_seed"]) != seed for item in fingerprints):
            raise ValueError(f"workload seed identity mismatch: {key}")
        if any(str(item["policy"]) != policy for item in fingerprints):
            raise ValueError(f"policy identity mismatch: {key}")
        if policy_seeds != {int(payload["policy_seed"])} or len(workload_hashes) != 1:
            raise ValueError(f"policy seed or workload hash mismatch: {key}")

        records.append(
            {
                "workload_seed": str(seed),
                "policy": policy,
                "source_run_id": source_run_id,
                "source_pair_sha256": sha256(pair_path.read_bytes()).hexdigest(),
                "internal_checksum_files_validated": checksum_files,
                "workload_sha256": next(iter(workload_hashes)),
                "policy_seed": next(iter(policy_seeds)),
                "replay_exact": payload["replay_exact"],
                "rng_gate": "passed",
                "invariant_gate": "passed",
                "public_validation_status": public["status"],
                "config_identity": (
                    "explicit_pair_digest" if seed == SEEDS[0] else "pinned_source_commit_and_path"
                ),
            }
        )

    if len(pair_paths) != 10 or observed != expected:
        raise ValueError("pre-aggregation completeness failed: expected 10/10 logical pairs")
    records.sort(key=lambda row: (_exact_decimal_seed(row["workload_seed"]), str(row["policy"])))
    return {
        "schema_version": "stage15k2r1-input-validation-v1",
        "status": "passed",
        "aggregation_only": True,
        "scientific_executions": 0,
        "logical_pairs_validated": 10,
        "reused_k1_pairs": 2,
        "reused_k2_pairs": 8,
        "internal_files_checksum_validated": 20,
        "approved_seed_strings": [str(seed) for seed in SEEDS],
        "config_sha256_lf_normalized": CONFIG_SHA256_LF_NORMALIZED,
        "k2_source_head_sha": K2_SOURCE_HEAD_SHA,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    report = validate_inputs(args.input_dir, args.config)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
