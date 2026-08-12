"""Validate 120 PIPE-NORMAL pairs, aggregate ASSUMP-033, and create Fig. 6."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from edge_reproduction.experiments.pipe_normal_full import (
    POLICY_NAMES,
    aggregate_complete_full_run,
    load_full_config,
)

LABELS = {
    "pipeline_double_knapsack_preemption": "Double Knapsack - Preemption",
    "pipeline_double_knapsack_retention": "Double Knapsack - Retention",
    "knapsack_greedy_preemption": "KnapsackGreedy - Preemption",
    "knapsack_greedy_retention": "KnapsackGreedy - Retention",
}
METRICS = ("completed_utility", "rejected_utility", "ever_preempted_utility")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object: {path}")
    return value


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return value


def finalize(root: Path, config_path: Path, output: Path, figure_dir: Path) -> dict[str, Any]:
    config = load_full_config(config_path)
    expected_config_hash = _hash(config_path)
    rows: list[dict[str, Any]] = []
    for raw_descriptor in _mapping(config, "config")["runs"]:
        descriptor = _mapping(raw_descriptor, "run descriptor")
        seed = int(descriptor["workload_seed"])
        workload_hashes: set[str] = set()
        for policy in POLICY_NAMES:
            pair = root / "results/raw/stage13f/PIPE-NORMAL" / f"seed-{seed}" / policy
            result_path, workload_path, manifest_path = (
                pair / name for name in ("result.json", "workload.json", "manifest.json")
            )
            for path in (result_path, workload_path, manifest_path):
                if not path.is_file():
                    raise FileNotFoundError(path)
            result, manifest = _load(result_path), _load(manifest_path)
            workload_hash = _hash(workload_path)
            if manifest["config_sha256"] != expected_config_hash:
                raise ValueError(f"config mismatch: {seed}/{policy}")
            if manifest["result_sha256"] != _hash(result_path):
                raise ValueError(f"result hash mismatch: {seed}/{policy}")
            if manifest["workload_sha256"] != workload_hash:
                raise ValueError(f"workload hash mismatch: {seed}/{policy}")
            if result["workload_seed"] != seed or result["policy"] != policy:
                raise ValueError(f"identity mismatch: {seed}/{policy}")
            if result["workload_sha256"] != workload_hash:
                raise ValueError(f"result workload hash mismatch: {seed}/{policy}")
            expected_policy_seed = _mapping(descriptor["policy_seeds"], "policy seeds")[policy]
            if result["policy_seed"] != expected_policy_seed:
                raise ValueError(f"policy seed mismatch: {seed}/{policy}")
            outcome = result["run"]["outcome"]
            completed, rejected = (
                set(outcome["completed_task_ids"]),
                set(outcome["rejected_task_ids"]),
            )
            preempted, all_ids = (
                set(outcome["ever_preempted_task_ids"]),
                set(result["run"]["final_task_states"]),
            )
            if completed & rejected or completed | rejected != all_ids or not preempted <= rejected:
                raise ValueError(f"outcome invariant failed: {seed}/{policy}")
            workload_hashes.add(workload_hash)
            rows.append(
                {"workload_seed": seed, "policy": policy, **{m: outcome[m] for m in METRICS}}
            )
        if len(workload_hashes) != 1:
            raise ValueError(f"policies do not share workload: {seed}")
    if len(rows) != 120:
        raise ValueError(f"expected 120 pairs, found {len(rows)}")
    output.mkdir(parents=True, exist_ok=False)
    figure_dir.mkdir(parents=True, exist_ok=True)
    aggregate = aggregate_complete_full_run(config_path.relative_to(root), project_root=root)
    aggregate.update(
        {
            "stage": "13-J",
            "validation": "120_of_120_pairs",
            "official_under_assumptions": True,
            "paper_exact_values_available": False,
        }
    )
    (output / "assump033_aggregate.json").write_text(
        json.dumps(aggregate, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "raw_run_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    figure_rows = []
    for policy in (
        "pipeline_double_knapsack_preemption",
        "pipeline_double_knapsack_retention",
        "knapsack_greedy_preemption",
        "knapsack_greedy_retention",
    ):
        for metric in METRICS:
            figure_rows.append(
                {
                    "policy": policy,
                    "paper_legend": LABELS[policy],
                    "metric": metric,
                    "arithmetic_mean": _mapping(
                        _mapping(aggregate["policies"], "aggregate policies")[policy],
                        "policy aggregate",
                    )[metric],
                    "repeat_count": 30,
                }
            )
    with (output / "figure6_reproduced_data.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=figure_rows[0])
        writer.writeheader()
        writer.writerows(figure_rows)

    import matplotlib
    import numpy as np

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    policies = [row for row in LABELS]
    x = np.arange(3)
    width = 0.19
    colors = ("#4472C4", "#ED7D31", "#A5A5A5", "#FFC000")
    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    for i, policy in enumerate(policies):
        policy_aggregate = _mapping(
            _mapping(aggregate["policies"], "aggregate policies")[policy],
            "policy aggregate",
        )
        vals = [policy_aggregate[metric] for metric in METRICS]
        ax.bar(x + (i - 1.5) * width, vals, width, label=LABELS[policy], color=colors[i])
    ax.set_title(
        "Normal Distribution Workload (Pipeline Paradigm)\nReproduction under ASSUMP-033-043"
    )
    ax.set_ylabel("Mean Utility across 30 paired workloads")
    ax.set_xticks(x, ("Completed", "Rejected", "Preempted"))
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(figure_dir / "figure6_reproduced.png", dpi=200)
    fig.savefig(figure_dir / "figure6_reproduced.pdf")
    plt.close(fig)
    report = "# Stage 13-J - Figure 6 comparison\n\n"
    report += "**Baseline:** arXiv:2403.15665v2 (2024), Fig. 6.\n\n"
    report += (
        "The reproduced bars are arithmetic means over 30 validated paired "
        "workloads under ASSUMP-033-043. The paper does not publish the underlying "
        "numeric table, seeds, repeat count, or aggregation details. Therefore its "
        "raster bar heights are not mixed with computed results and no exact "
        "numerical-equality claim is made.\n\n"
    )
    report += (
        "The paper reports the qualitative completed-utility ordering DK-P > KG-P "
        "> DK-R > KG-R and an overall difference of at most approximately 5%. The "
        "final aggregate JSON and CSV are the authoritative reproduced values; "
        "this report is a transparent comparison, not parameter fitting.\n"
    )
    completed_means = {
        policy: float(
            _mapping(
                _mapping(aggregate["policies"], "aggregate policies")[policy],
                "policy aggregate",
            )["completed_utility"]
        )
        for policy in LABELS
    }
    reproduced_order = sorted(
        completed_means, key=lambda policy: completed_means[policy], reverse=True
    )
    spread = (
        (max(completed_means.values()) - min(completed_means.values()))
        / max(completed_means.values())
        * 100.0
    )
    paper_order = [
        "pipeline_double_knapsack_preemption",
        "knapsack_greedy_preemption",
        "pipeline_double_knapsack_retention",
        "knapsack_greedy_retention",
    ]
    report += "\n## Computed comparison\n\n"
    report += "- Paper qualitative order: " + " > ".join(LABELS[p] for p in paper_order) + ".\n"
    report += (
        "- Reproduced completed-utility order: "
        + " > ".join(LABELS[p] for p in reproduced_order)
        + ".\n"
    )
    report += f"- Reproduced relative completed-utility spread: {spread:.6f}%.\n"
    report += (
        "- Qualitative-order match: " + ("yes" if reproduced_order == paper_order else "no") + ".\n"
    )
    (output / "figure6_comparison.md").write_text(report, encoding="utf-8")
    inventory = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            inventory.append(
                {
                    "path": path.relative_to(output).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": _hash(path),
                }
            )
    for path in sorted(figure_dir.glob("figure6_reproduced.*")):
        inventory.append(
            {"path": "figures/" + path.name, "bytes": path.stat().st_size, "sha256": _hash(path)}
        )
    final = {
        "status": "complete",
        "validated_pairs": 120,
        "validated_workloads": 30,
        "aggregation": "ASSUMP-033 arithmetic mean",
        "inventory": inventory,
    }
    (output / "finalization_report.json").write_text(
        json.dumps(final, indent=2) + "\n", encoding="utf-8"
    )
    return final


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--figures", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(finalize(args.root, args.config, args.output, args.figures), indent=2))


if __name__ == "__main__":
    main()
