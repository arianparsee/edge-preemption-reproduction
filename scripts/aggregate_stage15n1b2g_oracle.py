"""Validate and aggregate 4 reused plus 24 cloud Oracle branches."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, cast

from run_stage15n1b1_checkpoint_audit import (
    EXPECTED_CONFIG_SHA256,
    EXPECTED_WORKLOAD_SHA256,
    POLICY_SEED,
    assert_public_safe,
)
from run_stage15n1b1r_suffix_hash_coverage import file_sha256

from edge_reproduction.diagnostics.oracle_checkpoint import public_payload_is_sanitized

EXPECTED_REUSE_SHA256 = "7f497cc1d20ba3b1047902ebb717f42d720982e427eaea070dcb29676b5bbbda"
TOLERANCE = 1e-9


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _branch_gate(row: dict[str, Any]) -> None:
    if (
        int(row["sequence"]) not in range(28)
        or row["workload_sha256"] != EXPECTED_WORKLOAD_SHA256
        or row["config_sha256"] != EXPECTED_CONFIG_SHA256
        or str(row["policy_seed"]) != str(POLICY_SEED)
    ):
        raise ValueError("Oracle branch identity mismatch")
    validation = cast(dict[str, Any], row["validation"])
    required = (
        "factual_history_checkpoint_verified",
        "intervention_exactly_once",
        "replay_exact",
        "rng_option_a",
        "scientific_fingerprint_exact_between_replays",
        "terminal_partition",
    )
    if not all(validation.get(key) is True for key in required):
        raise ValueError("Oracle branch validation gate failed")
    if abs(float(validation["utility_conservation_residual"])) > TOLERANCE:
        raise ValueError("Oracle branch utility conservation failed")
    assert_public_safe(row)
    public_payload_is_sanitized(row)


def _load_reuse(path: Path) -> list[dict[str, Any]]:
    if file_sha256(path) != EXPECTED_REUSE_SHA256:
        raise ValueError("local reuse package checksum mismatch")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if sidecar.read_text(encoding="ascii").strip() != EXPECTED_REUSE_SHA256:
        raise ValueError("local reuse sidecar mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "stage15n1b2g-reused-oracle-branches-v1":
        raise ValueError("local reuse schema mismatch")
    rows = cast(list[dict[str, Any]], payload["branches"])
    if [int(row["sequence"]) for row in rows] != [0, 1, 2, 3]:
        raise ValueError("local reuse scope mismatch")
    for row in rows:
        _branch_gate(row)
    return rows


def _load_cloud(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("oracle_branch.json")):
        manifest_path = path.parent / "sha256_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = cast(list[dict[str, Any]], manifest["files"])
        expected = next((row for row in files if row["name"] == path.name), None)
        if expected is None or file_sha256(path) != expected["sha256"]:
            raise ValueError("cloud Oracle branch checksum mismatch")
        row = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        if row.get("schema_version") != "stage15n1b2g-public-oracle-branch-v1":
            raise ValueError("cloud Oracle branch schema mismatch")
        _branch_gate(row)
        rows.append(row)
    return rows


def _load_bootstrap(path: Path) -> dict[str, Any]:
    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    coverage = cast(dict[str, Any], payload["coverage"])
    validation = cast(dict[str, Any], payload["validation"])
    if (
        coverage.get("checkpoints") != "28/28"
        or coverage.get("duplicate") != 0
        or coverage.get("missing") != 0
        or coverage.get("orphan") != 0
        or not all(value is True for value in validation.values())
    ):
        raise ValueError("factual bootstrap validation failed")
    return payload


def _confusion(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        local = float(row["decision_features"]["local_net_utility"])
        label = str(row["terminal"]["oracle_label"])
        predicted_veto = local <= TOLERANCE
        if label == "HARMFUL":
            counts["true_veto"] += int(predicted_veto)
            counts["missed_veto"] += int(not predicted_veto)
        elif label == "BENEFICIAL":
            counts["false_veto"] += int(predicted_veto)
            counts["true_commit"] += int(not predicted_veto)
        else:
            counts["neutral"] += 1
    return dict(sorted(counts.items()))


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, object]:
    labels = Counter(str(row["terminal"]["oracle_label"]) for row in rows)
    deltas = [float(row["terminal"]["oracle_delta"]) for row in rows]
    local_positive_terminal_negative = sum(
        float(row["decision_features"]["local_net_utility"]) > TOLERANCE
        and row["terminal"]["oracle_label"] == "HARMFUL"
        for row in rows
    )
    divergence = Counter(str(row["divergence"]["kind"]) for row in rows)
    return {
        "label_counts": dict(sorted(labels.items())),
        "oracle_delta": {
            "minimum": min(deltas),
            "maximum": max(deltas),
            "mean": mean(deltas),
            "median": median(deltas),
            "sum_nonadditive_diagnostic_only": sum(deltas),
        },
        "local_positive_terminal_negative_count": local_positive_terminal_negative,
        "local_guard_confusion": _confusion(rows),
        "divergence_kind_counts": dict(sorted(divergence.items())),
        "direct_involved_delta_sum_nonadditive": sum(
            float(row["terminal"]["direct_involved_delta"]) for row in rows
        ),
        "downstream_path_delta_sum_nonadditive": sum(
            float(row["terminal"]["downstream_path_delta"]) for row in rows
        ),
        "effects_are_independent_and_nonadditive": True,
        "feature_separability_is_descriptive_only": True,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "sequence",
        "epoch",
        "incoming_count",
        "victim_count",
        "local_net_utility",
        "oracle_delta",
        "oracle_label",
        "direct_involved_delta",
        "downstream_path_delta",
        "completed_jobs_delta",
        "preempted_jobs_delta",
        "retry_delta",
        "expiration_delta",
        "never_admitted_expired_delta",
        "factual_chain_depth",
        "retain_chain_depth",
        "divergence_kind",
        "divergence_call_index",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            terminal = row["terminal"]
            factual = terminal["factual_metrics"]
            retain = terminal["retain_metrics"]
            writer.writerow(
                {
                    "sequence": row["sequence"],
                    "epoch": row["epoch"],
                    "incoming_count": row["decision_features"]["incoming_count"],
                    "victim_count": row["decision_features"]["victim_count"],
                    "local_net_utility": row["decision_features"]["local_net_utility"],
                    "oracle_delta": terminal["oracle_delta"],
                    "oracle_label": terminal["oracle_label"],
                    "direct_involved_delta": terminal["direct_involved_delta"],
                    "downstream_path_delta": terminal["downstream_path_delta"],
                    "completed_jobs_delta": retain["completed_jobs"] - factual["completed_jobs"],
                    "preempted_jobs_delta": retain["preempted_jobs"] - factual["preempted_jobs"],
                    "retry_delta": retain["retry_scheduled"] - factual["retry_scheduled"],
                    "expiration_delta": retain["expired"] - factual["expired"],
                    "never_admitted_expired_delta": (
                        retain["never_admitted_expired"]
                        - factual["never_admitted_expired"]
                    ),
                    "factual_chain_depth": terminal["chain_depth_factual"],
                    "retain_chain_depth": terminal["chain_depth_retain"],
                    "divergence_kind": row["divergence"]["kind"],
                    "divergence_call_index": row["divergence"]["call_index"],
                }
            )


def aggregate(
    *, reuse_path: Path, cloud_root: Path, bootstrap_path: Path, output_root: Path
) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("aggregate output root already exists")
    bootstrap = _load_bootstrap(bootstrap_path)
    inventory = {
        int(row["sequence"]): row
        for row in cast(list[dict[str, Any]], bootstrap["inventory"])
    }
    rows = _load_reuse(reuse_path) + _load_cloud(cloud_root)
    sequences = [int(row["sequence"]) for row in rows]
    duplicates = len(sequences) - len(set(sequences))
    missing = sorted(set(range(28)) - set(sequences))
    orphan = sorted(set(sequences) - set(range(28)))
    for row in rows:
        expected = inventory[int(row["sequence"])]
        if (
            row["semantic_closure_sha256"] != expected["semantic_closure_sha256"]
            or row["rng_state_sha256"] != expected["rng_state_sha256"]
            or int(row["epoch"]) != int(expected["epoch"])
        ):
            raise ValueError("Oracle branch/bootstrap identity mismatch")
    complete = len(rows) == 28 and not duplicates and not missing and not orphan
    output_root.mkdir(parents=True, exist_ok=False)
    completeness: dict[str, object] = {
        "schema_version": "stage15n1b2g-completeness-v1",
        "status": "complete" if complete else "incomplete",
        "expected": 28,
        "observed": len(rows),
        "reused": 4,
        "new": len([value for value in sequences if value >= 4]),
        "duplicate": duplicates,
        "missing": missing,
        "orphan": orphan,
        "scientific_result_emitted": complete,
    }
    (output_root / "completeness_report.json").write_bytes(_json_bytes(completeness))
    if complete:
        ordered = sorted(rows, key=lambda row: int(row["sequence"]))
        summary: dict[str, object] = {
            "schema_version": "stage15n1b2g-oracle-summary-v1",
            "label": "[پیشنهاد فنی تشخیصی] Oracle retain-branch یک-seed",
            "scope": {
                "workload_seed": "541501192080118187",
                "policy": "DK-P",
                "variant": "ASSUMP-046",
                "logical_branches": 28,
                "reused_branches": 4,
                "new_branches": 24,
                "replays_per_new_branch": 2,
            },
            "validation": {
                "bootstrap_28_of_28": True,
                "all_branch_replays_exact": True,
                "rng_option_a": True,
                "all_invariants": True,
                "completeness_28_of_28": True,
            },
            "aggregate": _aggregate(ordered),
            "interpretation": {
                "single_seed_only": True,
                "branch_effects_nonadditive": True,
                "classifier_or_threshold_trained": False,
                "official_pipeline_changed": False,
                "figure_6_status": "بازتولید نشد",
            },
        }
        assert_public_safe(summary)
        public_payload_is_sanitized(summary)
        (output_root / "oracle_summary.json").write_bytes(_json_bytes(summary))
        _write_csv(output_root / "oracle_effects_by_transaction.csv", ordered)
        report = (
            "# Stage 15-N.1B.2-G-R — Oracle retain branches\n\n"
            "Status: complete (28/28).\n\n"
            "This is a single-seed diagnostic technical proposal. Branch effects are "
            "independent and non-additive. The official pipeline is unchanged and "
            "Figure 6 remains not reproduced.\n"
        )
        (output_root / "stage15n1b2g_report.md").write_text(report, encoding="utf-8")
    manifest = [
        {
            "logical_name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in sorted(output_root.iterdir())
        if path.is_file() and path.name != "checksum_manifest.json"
    ]
    (output_root / "checksum_manifest.json").write_bytes(_json_bytes(manifest))
    return completeness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", type=Path, required=True)
    parser.add_argument("--cloud-root", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = aggregate(
        reuse_path=args.reuse,
        cloud_root=args.cloud_root,
        bootstrap_path=args.bootstrap,
        output_root=args.output_root,
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
