"""Register the validated Figure 6 aggregate as the formal Stage 14-A artifact set.

This script copies only small, derived artifacts from the stable Stage 13-J/K
archive. It never reads or publishes the raw per-pair result directories and it
never executes a policy, simulator, or workload generator.
"""

# ruff: noqa: E501 - Persian report prose is intentionally stored as readable Markdown.

from __future__ import annotations

import argparse
import csv
import json
import shutil
from hashlib import sha256
from pathlib import Path
from typing import Final

EXPECTED: Final[dict[str, str]] = {
    "results/aggregated/stage13j/figure6_reproduced_data.csv": (
        "b36a1da84be5cef44d8ea5e3c2496e30fec5b60defb80b015366daa2f2c30e44"
    ),
    "results/aggregated/stage13j/raw_run_metrics.csv": (
        "4413f2cfa0a87d267d4cf855f66db87eb422140906d81a028cf5592585013e67"
    ),
    "figures/stage13j/figure6_reproduced.pdf": (
        "6a418a7a935e2bc09cbd4c0687502eaf225da99c0ea4aa6bf3e9d1765abe30ff"
    ),
    "figures/stage13j/figure6_reproduced.png": (
        "b1f98b44de78202eb2e78129c1bb6b62793bc0e8c5d5965b786fe48c9983708b"
    ),
}

POLICY_LABELS: Final[dict[str, str]] = {
    "knapsack_greedy_retention": "KG-R",
    "knapsack_greedy_preemption": "KG-P",
    "pipeline_double_knapsack_retention": "DK-R",
    "pipeline_double_knapsack_preemption": "DK-P",
}


def file_sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one file."""

    return sha256(path.read_bytes()).hexdigest()


def _require_new(paths: list[Path]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite Stage 14-A artifacts: {existing}")


def _copy_or_verify(source: Path, target: Path) -> None:
    """Resume safely when an earlier attempt already copied the exact source."""

    if target.exists():
        if file_sha256(target) != file_sha256(source):
            raise FileExistsError(f"existing target differs from verified source: {target}")
        return
    shutil.copyfile(source, target)


def _load_figure_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if {row["policy"] for row in rows} != set(POLICY_LABELS):
        raise ValueError("Figure 6 CSV must contain exactly the four approved policies")
    return rows


def _completed_utility_by_label(rows: list[dict[str, str]]) -> dict[str, float]:
    completed = {
        POLICY_LABELS[row["policy"]]: float(row["arithmetic_mean"])
        for row in rows
        if row["metric"] == "completed_utility"
    }
    if set(completed) != set(POLICY_LABELS.values()):
        raise ValueError("Figure 6 CSV lacks one completed-utility policy row")
    return completed


def register(source_root: Path, project_root: Path) -> dict[str, object]:
    """Verify and copy the final aggregate without touching raw artifacts."""

    for relative, expected_hash in EXPECTED.items():
        source = source_root / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        if file_sha256(source) != expected_hash:
            raise ValueError(f"stable source hash mismatch: {relative}")

    source_report = source_root / "results/aggregated/stage13j/finalization_report.json"
    finalization = json.loads(source_report.read_text(encoding="utf-8"))
    if finalization.get("status") != "complete":
        raise ValueError("Stage 13-J finalization status is not complete")
    if finalization.get("validated_pairs") != 120:
        raise ValueError("Stage 14-A requires 120 validated pairs")
    if finalization.get("validated_workloads") != 30:
        raise ValueError("Stage 14-A requires 30 validated workloads")

    aggregate_dir = project_root / "results/aggregated/stage14a"
    figure_dir = project_root / "figures/stage14a"
    report_path = project_root / "docs/stage14a_figure6.md"
    targets = {
        "figure_data": aggregate_dir / "figure6_reproduced_data.csv",
        "raw_metrics": aggregate_dir / "raw_run_metrics.csv",
        "comparison": aggregate_dir / "figure6_comparison.csv",
        "manifest": aggregate_dir / "stage14a_manifest.json",
        "pdf": figure_dir / "figure6_reproduced.pdf",
        "png": figure_dir / "figure6_reproduced.png",
        "report": report_path,
    }
    _require_new([targets["comparison"], targets["manifest"], targets["report"]])
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    _copy_or_verify(
        source_root / "results/aggregated/stage13j/figure6_reproduced_data.csv",
        targets["figure_data"],
    )
    _copy_or_verify(
        source_root / "results/aggregated/stage13j/raw_run_metrics.csv",
        targets["raw_metrics"],
    )
    _copy_or_verify(
        source_root / "figures/stage13j/figure6_reproduced.pdf", targets["pdf"]
    )
    _copy_or_verify(
        source_root / "figures/stage13j/figure6_reproduced.png", targets["png"]
    )

    figure_rows = _load_figure_rows(targets["figure_data"])
    completed = _completed_utility_by_label(figure_rows)
    reproduced_order = sorted(completed, key=completed.__getitem__, reverse=True)
    best = max(completed.values())
    worst = min(completed.values())
    reproduced_spread = 100.0 * (best - worst) / best
    comparison_rows = [
        {
            "comparison": "completed_utility_order",
            "paper": "DK-P > KG-P > DK-R > KG-R",
            "reproduction": " > ".join(reproduced_order),
            "absolute_difference": "not_applicable",
            "relative_difference_percent": "not_applicable",
            "status": "not_reproduced",
            "basis": "paper qualitative statement; 30-workload arithmetic mean",
        },
        {
            "comparison": "best_to_worst_completed_utility_spread",
            "paper": "approximately_at_most_5_percent",
            "reproduction": f"{reproduced_spread:.12f}_percent",
            "absolute_difference": "not_computable_without_paper_numeric_table",
            "relative_difference_percent": "not_computable_without_paper_numeric_table",
            "status": "not_reproduced",
            "basis": "paper does not publish numeric bars",
        },
    ]
    with targets["comparison"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison_rows[0]))
        writer.writeheader()
        writer.writerows(comparison_rows)

    report = f"""# Stage 14-A - ثبت رسمی بازتولید Figure 6

## منبع و دامنه

- [صریح در مقاله] مبنا: arXiv:2403.15665v2 (2024)، شکل 6، آزمایش PIPE-NORMAL.
- [فرض بازتولید] مقادیر بازتولیدشده میانگین حسابی 30 workload مشترک مطابق ASSUMP-033 تا ASSUMP-043 هستند.
- هیچ داده خام، policy، شبیه‌ساز یا workload در این مرحله اجرا یا بازتولید نشده است.

## نتیجه

ترتیب گزارش‌شده مقاله `DK-P > KG-P > DK-R > KG-R` است. ترتیب بازتولیدشده
`{" > ".join(reproduced_order)}` و فاصله بهترین تا ضعیف‌ترین روش `{reproduced_spread:.6f}%`
است. چون ترتیب کیفی منطبق نیست و فاصله با ادعای تقریبی حداکثر 5 درصد سازگار نیست،
وضعیت رسمی Figure 6 **بازتولید نشد** است.

مقاله جدول عددی پشت شکل، seedها، repeat count و روش aggregation را منتشر نکرده است؛
بنابراین اختلاف عددی نقطه‌به‌نقطه قابل محاسبه نیست و هیچ ارتفاعی از تصویر مقاله با
نتایج محاسباتی مخلوط نشده است.

## Artifactهای رسمی

- `results/aggregated/stage14a/figure6_reproduced_data.csv`: جدول داده شکل.
- `results/aggregated/stage14a/raw_run_metrics.csv`: 120 سطر مشتق‌شده از pairهای معتبر.
- `results/aggregated/stage14a/figure6_comparison.csv`: جدول مقایسه با مقاله.
- `figures/stage14a/figure6_reproduced.png` و `.pdf`: نمودارهای نهایی.
- `results/aggregated/stage14a/stage14a_manifest.json`: منشأ و SHA-256 artifactها.
"""
    targets["report"].write_text(report, encoding="utf-8")

    inventory = []
    for name in ("figure_data", "raw_metrics", "comparison", "pdf", "png", "report"):
        path = targets[name]
        inventory.append(
            {
                "path": path.relative_to(project_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    manifest: dict[str, object] = {
        "schema_version": "stage14a-figure6-registration-v1",
        "baseline": "arXiv:2403.15665v2_2024",
        "source_run_id": 31644121025,
        "validated_pairs": 120,
        "validated_workloads": 30,
        "aggregation": "ASSUMP-033_arithmetic_mean",
        "reproduction_status": "not_reproduced",
        "paper_order": ["DK-P", "KG-P", "DK-R", "KG-R"],
        "reproduced_order": reproduced_order,
        "reproduced_spread_percent": reproduced_spread,
        "raw_data_committed": False,
        "policy_or_workload_reexecution": False,
        "inventory": inventory,
    }
    targets["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = register(args.source_root.resolve(), args.project_root.resolve())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
