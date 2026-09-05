"""Build the four-branch sanitized Oracle reuse package from private evidence."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY_SEED,
    assert_public_safe,
)
from run_stage15n1b1r_suffix_hash_coverage import file_sha256

from edge_reproduction.diagnostics.oracle_checkpoint import public_payload_is_sanitized


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def build_reuse(*, branch_root: Path, crosswalk_path: Path) -> dict[str, object]:
    crosswalk_payload = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    crosswalk = {
        int(row["transaction_locator"]["sequence"]): row
        for row in cast(list[dict[str, Any]], crosswalk_payload["rows"])
    }
    branches: list[dict[str, object]] = []
    for sequence in range(4):
        path = branch_root / f"transaction-{sequence:03d}.json"
        sidecar = branch_root / f"transaction-{sequence:03d}.sha256"
        digest = file_sha256(path)
        if sidecar.read_text(encoding="ascii").strip() != digest:
            raise ValueError("local Oracle branch checksum mismatch")
        private = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        if (
            private.get("schema_version") != "stage15n1b2-private-oracle-branch-v1"
            or int(private["sequence"]) != sequence
        ):
            raise ValueError("local Oracle branch identity mismatch")
        identity = cast(dict[str, Any], private["identity"])
        validation = cast(dict[str, Any], private["validation"])
        row = crosswalk[sequence]
        if (
            identity["transaction_locator"] != row["transaction_locator"]
            or identity["semantic_closure_sha256"]
            != row["canonical_semantic_closure_sha256"]
            or identity["workload_sha256"] != EXPECTED_WORKLOAD_SHA256
            or identity["config_sha256"] != EXPECTED_CONFIG_SHA256
            or identity["policy_seed"] != POLICY_SEED
            or not all(
                validation.get(key) is True
                for key in (
                    "factual_history_checkpoint_verified",
                    "intervention_exactly_once",
                    "replay_exact",
                    "rng_option_a",
                    "scientific_fingerprint_exact_between_replays",
                    "terminal_partition",
                )
            )
            or abs(float(validation["utility_conservation_residual"])) > 1e-9
        ):
            raise ValueError("local Oracle branch scientific gate mismatch")
        decision = {
            key: value
            for key, value in cast(dict[str, Any], private["decision_features"]).items()
            if key != "task_features"
        }
        terminal = {
            key: value
            for key, value in cast(dict[str, Any], private["terminal"]).items()
            if key not in {"incoming_outcomes", "victim_outcomes"}
        }
        branches.append(
            {
                "sequence": sequence,
                "epoch": int(identity["transaction_locator"]["epoch"]),
                "source_private_sha256": digest,
                "semantic_closure_sha256": row["canonical_semantic_closure_sha256"],
                "rng_state_sha256": row["rng_state_sha256"],
                "workload_sha256": EXPECTED_WORKLOAD_SHA256,
                "config_sha256": EXPECTED_CONFIG_SHA256,
                "policy_seed": str(POLICY_SEED),
                "decision_features": decision,
                "divergence": private["divergence"],
                "intervention": private["intervention"],
                "terminal": terminal,
                "validation": validation,
            }
        )
    payload: dict[str, object] = {
        "schema_version": "stage15n1b2g-reused-oracle-branches-v1",
        "scope": {
            "workload_seed": "541501192080118187",
            "policy": "DK-P",
            "variant": "ASSUMP-046",
            "sequences": [0, 1, 2, 3],
            "branch_count": 4,
            "recomputed": False,
        },
        "branches": branches,
        "publication": {
            "task_ids": False,
            "snapshots": False,
            "raw_rng_state": False,
            "candidate_pool": False,
            "victim_edges": False,
            "traces": False,
            "personal_paths": False,
        },
    }
    assert_public_safe(payload)
    public_payload_is_sanitized(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-root", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("reuse output already exists")
    payload = build_reuse(branch_root=args.branch_root, crosswalk_path=args.crosswalk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(payload)
    args.output.write_bytes(raw)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        sha256(raw).hexdigest() + "\n", encoding="ascii"
    )


if __name__ == "__main__":
    main()
