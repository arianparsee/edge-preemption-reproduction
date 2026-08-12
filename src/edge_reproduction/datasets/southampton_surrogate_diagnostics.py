"""Qualitative-only diagnostics for the Southampton visible-raster surrogate."""

from __future__ import annotations

import json
import os
import tempfile
from math import sqrt
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from edge_reproduction.datasets.southampton_surrogate import (
    PRIORITIES,
    RESOURCES,
    SouthamptonSurrogateDataset,
    VisibleSupport,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

DIAGNOSTIC_BIN_COUNT = 60
SERIES_COLORS = {"low": "#2ca02c", "medium": "#ff7f0e", "high": "#d62728"}


def _expected_moments(supports: tuple[VisibleSupport, ...]) -> tuple[float, float]:
    weights = np.asarray([support.pixel_count for support in supports], dtype=np.float64)
    probabilities = weights / float(np.sum(weights))
    means = np.asarray([(item.lower + item.upper) / 2.0 for item in supports])
    second_moments = np.asarray(
        [(item.lower**2 + item.lower * item.upper + item.upper**2) / 3.0 for item in supports]
    )
    expected_mean = float(np.sum(probabilities * means))
    expected_variance = float(np.sum(probabilities * second_moments) - expected_mean**2)
    return expected_mean, max(0.0, expected_variance)


def summarize_surrogate(
    dataset: SouthamptonSurrogateDataset,
    supports: tuple[VisibleSupport, ...],
) -> dict[str, object]:
    """Compare generated values with the approved visible-area sampling law."""

    checks: list[dict[str, object]] = []
    for resource in RESOURCES:
        for priority in PRIORITIES:
            group = tuple(
                item for item in supports if item.resource == resource and item.priority == priority
            )
            records = tuple(item for item in dataset.records if item.priority == priority)
            values = np.asarray(
                [
                    item.storage_gb if resource == "storage" else item.deadline_hours
                    for item in records
                ],
                dtype=np.float64,
            )
            expected_mean, expected_variance = _expected_moments(group)
            mean_standard_error = sqrt(expected_variance / values.size)
            mean_z_score = (
                abs(float(np.mean(values)) - expected_mean) / mean_standard_error
                if mean_standard_error > 0.0
                else 0.0
            )
            total_pixels = sum(item.pixel_count for item in group)
            component_z_scores: list[float] = []
            for support in group:
                probability = support.pixel_count / total_pixels
                expected_count = values.size * probability
                binomial_std = sqrt(values.size * probability * (1.0 - probability))
                difference = abs(dataset.selection_counts[support.component_id] - expected_count)
                component_z_scores.append(difference / binomial_std if binomial_std else 0.0)
            within_bounds = bool(
                np.all(values >= min(item.lower for item in group))
                and np.all(values <= max(item.upper for item in group))
            )
            max_component_z_score = max(component_z_scores)
            status = (
                "pass"
                if mean_z_score <= 5.0 and max_component_z_score <= 5.0 and within_bounds
                else "fail"
            )
            checks.append(
                {
                    "resource": resource,
                    "priority": priority,
                    "count": int(values.size),
                    "expected_mean_visible_area_law": expected_mean,
                    "observed_mean": float(np.mean(values)),
                    "mean_z_score": mean_z_score,
                    "max_component_frequency_z_score": max_component_z_score,
                    "all_values_within_union_envelope": within_bounds,
                    "acceptance_rule": "mean_z<=5 and max_component_frequency_z<=5",
                    "status": status,
                }
            )
    failed = [
        f"{item['resource']}/{item['priority']}" for item in checks if item["status"] == "fail"
    ]
    return {
        "scientific_label": ("auxiliary_qualitative_visible_raster_diagnostic_not_paper_result"),
        "dataset_id": dataset.config.dataset_id,
        "diagnostic_bin_count": DIAGNOSTIC_BIN_COUNT,
        "checks": checks,
        "failed_checks": failed,
        "all_checks_passed": not failed,
        "limitations": [
            "checks target the approved visible-pixel surrogate law, not the raw trace",
            "no numerical agreement with the paper is claimed",
            "no hidden or occluded histogram mass is reconstructed",
        ],
    }


def _save_figure(figure: Figure, base_path: Path) -> tuple[Path, Path]:
    png_path = base_path.with_suffix(".png")
    svg_path = base_path.with_suffix(".svg")
    figure.savefig(
        png_path,
        dpi=160,
        bbox_inches="tight",
        metadata={"Software": "edge-reproduction stage12c qualitative diagnostic"},
    )
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "edge-reproduction stage12c"},
    )
    return png_path, svg_path


def write_qualitative_figures(
    dataset: SouthamptonSurrogateDataset,
    supports: tuple[VisibleSupport, ...],
    *,
    published_figures_directory: Path,
    output_directory: Path,
) -> tuple[Path, ...]:
    """Place source raster beside generated marginal without numeric-fit claims."""

    output_directory.mkdir(parents=True, exist_ok=True)
    cache_directory = Path(tempfile.gettempdir()) / "edge-reproduction-matplotlib-cache"
    cache_directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_directory.resolve()))

    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "edge-reproduction-stage12c"
    from matplotlib import pyplot as plt

    output_paths: list[Path] = []
    for resource, source_filename, x_label in (
        ("storage", "trace_storage_distribution.png", "Storage (GB)"),
        ("deadline", "trace_deadline_distribution.png", "Deadline (hours)"),
    ):
        source_path = published_figures_directory / source_filename
        source_image = plt.imread(source_path)
        figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
        axes[0].imshow(source_image)
        axes[0].axis("off")
        axes[0].set_title("Published arXiv v2 raster")
        group_supports = tuple(item for item in supports if item.resource == resource)
        left = min(item.lower for item in group_supports)
        right = max(item.upper for item in group_supports)
        for priority in PRIORITIES:
            records = tuple(item for item in dataset.records if item.priority == priority)
            values = [
                item.storage_gb if resource == "storage" else item.deadline_hours
                for item in records
            ]
            axes[1].hist(
                values,
                bins=DIAGNOSTIC_BIN_COUNT,
                range=(left, right),
                density=True,
                histtype="step",
                linewidth=1.5,
                color=SERIES_COLORS[priority],
                label=priority.title(),
            )
        axes[1].set_title("Generated visible-area surrogate")
        axes[1].set_xlabel(x_label)
        axes[1].set_ylabel("Density (not paper probability scale)")
        axes[1].grid(alpha=0.2)
        axes[1].legend()
        figure.suptitle(f"{resource.title()} — qualitative auxiliary comparison; not raw trace")
        output_paths.extend(
            _save_figure(figure, output_directory / f"{dataset.config.dataset_id}_{resource}")
        )
        plt.close(figure)
    return tuple(output_paths)


def write_diagnostic_summary(summary: dict[str, object], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
