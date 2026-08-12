"""Auxiliary statistical and visual checks for generated synthetic data."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from math import exp, pi, sqrt
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from edge_reproduction.datasets.synthetic import (
    ARRIVAL_SPEC,
    BIMODAL_JOB_SPECS,
    NORMAL_JOB_SPECS,
    SERVER_SPECS,
    NormalSpec,
    SyntheticDataset,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes


@dataclass(frozen=True, slots=True)
class DistributionCheck:
    """Observed moments and an explicit auxiliary acceptance rule."""

    field: str
    count: int
    target_mean: float
    target_standard_deviation: float
    observed_mean: float
    observed_standard_deviation: float
    mean_z_score: float
    standard_deviation_relative_error: float
    status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "count": self.count,
            "target_mean": self.target_mean,
            "target_standard_deviation": self.target_standard_deviation,
            "observed_mean": self.observed_mean,
            "observed_standard_deviation": self.observed_standard_deviation,
            "mean_z_score": self.mean_z_score,
            "standard_deviation_relative_error": self.standard_deviation_relative_error,
            "status": self.status,
        }


def distribution_check(
    field: str,
    values: npt.NDArray[np.float64],
    spec: NormalSpec,
    *,
    minimum_test_count: int = 30,
) -> DistributionCheck:
    """Check moments using four-standard-error auxiliary limits."""

    count = int(values.size)
    if count == 0:
        raise ValueError("distribution check requires at least one value")
    observed_mean = float(np.mean(values))
    observed_standard_deviation = float(np.std(values, ddof=0))
    mean_standard_error = spec.standard_deviation / sqrt(count)
    mean_z_score = abs(observed_mean - spec.mean) / mean_standard_error
    standard_deviation_relative_error = (
        abs(observed_standard_deviation - spec.standard_deviation) / spec.standard_deviation
    )
    if count < minimum_test_count:
        status = "informational_small_sample"
    else:
        std_limit = 4.0 / sqrt(2.0 * (count - 1))
        status = (
            "pass"
            if mean_z_score <= 4.0 and standard_deviation_relative_error <= std_limit
            else "fail"
        )
    return DistributionCheck(
        field,
        count,
        spec.mean,
        spec.standard_deviation,
        observed_mean,
        observed_standard_deviation,
        mean_z_score,
        standard_deviation_relative_error,
        status,
    )


def summarize_dataset(dataset: SyntheticDataset) -> dict[str, object]:
    """Return moment checks and exact mixture diagnostics."""

    server_arrays = {
        "server.storage": np.asarray(
            [item.storage_mb for item in dataset.servers], dtype=np.float64
        ),
        "server.computation": np.asarray(
            [item.computation_mflops_per_s for item in dataset.servers],
            dtype=np.float64,
        ),
        "server.upload": np.asarray(
            [item.upload_mb_per_s for item in dataset.servers], dtype=np.float64
        ),
        "server.download": np.asarray(
            [item.download_mb_per_s for item in dataset.servers], dtype=np.float64
        ),
    }
    checks = [
        distribution_check(name, values, SERVER_SPECS[name.split(".")[1]])
        for name, values in server_arrays.items()
    ]
    common_task_arrays = {
        "job.storage": np.asarray([item.storage_mb for item in dataset.tasks], dtype=np.float64),
        "job.computation": np.asarray(
            [item.computation_mflops for item in dataset.tasks], dtype=np.float64
        ),
        "job.upload": np.asarray(
            [item.upload_mb_per_s for item in dataset.tasks], dtype=np.float64
        ),
        "job.download": np.asarray(
            [item.download_mb_per_s for item in dataset.tasks], dtype=np.float64
        ),
        "job.deadline": np.asarray(
            [item.deadline_slots for item in dataset.tasks], dtype=np.float64
        ),
    }
    specs = NORMAL_JOB_SPECS if dataset.config.workload_kind == "normal" else BIMODAL_JOB_SPECS
    checks.extend(
        distribution_check(name, values, specs[name.split(".")[1]])
        for name, values in common_task_arrays.items()
    )
    mixture: dict[str, object] | None = None
    if dataset.config.workload_kind == "normal":
        checks.append(
            distribution_check(
                "job.utility",
                np.asarray([item.utility for item in dataset.tasks], dtype=np.float64),
                NORMAL_JOB_SPECS["utility"],
            )
        )
    else:
        low = np.asarray(
            [item.utility for item in dataset.tasks if item.utility_class == "low"],
            dtype=np.float64,
        )
        high = np.asarray(
            [item.utility for item in dataset.tasks if item.utility_class == "high"],
            dtype=np.float64,
        )
        checks.extend(
            (
                distribution_check("job.utility_low", low, BIMODAL_JOB_SPECS["utility_low"]),
                distribution_check("job.utility_high", high, BIMODAL_JOB_SPECS["utility_high"]),
            )
        )
        mixture = {
            "low_count": int(low.size),
            "high_count": int(high.size),
            "low_fraction": float(low.size / len(dataset.tasks)),
            "high_fraction": float(high.size / len(dataset.tasks)),
            "exact_90_10": bool(
                low.size * 10 == len(dataset.tasks) * 9 and high.size * 10 == len(dataset.tasks)
            ),
        }
    checks.append(
        distribution_check(
            "arrivals.count",
            np.asarray(dataset.arrival_counts, dtype=np.float64),
            ARRIVAL_SPEC,
        )
    )
    failed = [item.field for item in checks if item.status == "fail"]
    return {
        "label": "auxiliary_statistical_diagnostics_not_paper_result",
        "dataset_id": dataset.config.dataset_id,
        "workload_kind": dataset.config.workload_kind,
        "checks": [item.as_dict() for item in checks],
        "mixture": mixture,
        "failed_checks": failed,
        "all_eligible_checks_passed": not failed,
    }


def _normal_density(values: npt.NDArray[np.float64], spec: NormalSpec) -> npt.NDArray[np.float64]:
    coefficient = 1.0 / (spec.standard_deviation * sqrt(2.0 * pi))
    return np.asarray(
        [
            coefficient * exp(-0.5 * ((float(value) - spec.mean) / spec.standard_deviation) ** 2)
            for value in values
        ],
        dtype=np.float64,
    )


def _histogram_with_target(
    axis: Axes,
    values: npt.NDArray[np.float64],
    spec: NormalSpec,
    *,
    title: str,
    x_label: str,
) -> None:
    axis.hist(values, bins="auto", density=True, alpha=0.7, label="Generated")
    left = min(float(np.min(values)), spec.mean - 4.0 * spec.standard_deviation)
    right = max(float(np.max(values)), spec.mean + 4.0 * spec.standard_deviation)
    x_values = np.linspace(left, right, 300, dtype=np.float64)
    axis.plot(x_values, _normal_density(x_values, spec), linewidth=1.5, label="Target normal")
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel("Density")
    axis.grid(alpha=0.2)


def _save_figure(figure: object, base_path: Path) -> tuple[Path, Path]:
    from matplotlib.figure import Figure

    if not isinstance(figure, Figure):
        raise TypeError("figure must be a matplotlib Figure")
    png_path = base_path.with_suffix(".png")
    svg_path = base_path.with_suffix(".svg")
    figure.savefig(
        png_path,
        dpi=160,
        bbox_inches="tight",
        metadata={"Software": "edge-reproduction stage11b"},
    )
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "edge-reproduction stage11b"},
    )
    return png_path, svg_path


def write_diagnostic_figures(dataset: SyntheticDataset, output_directory: Path) -> tuple[Path, ...]:
    """Write PNG and SVG auxiliary distribution diagnostics."""

    output_directory.mkdir(parents=True, exist_ok=True)
    cache_directory = Path(tempfile.gettempdir()) / "edge-reproduction-matplotlib-cache"
    cache_directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_directory.resolve()))

    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "edge-reproduction-stage11b"
    from matplotlib import pyplot as plt

    specs = NORMAL_JOB_SPECS if dataset.config.workload_kind == "normal" else BIMODAL_JOB_SPECS
    task_values = {
        "storage": np.asarray([item.storage_mb for item in dataset.tasks], dtype=np.float64),
        "computation": np.asarray(
            [item.computation_mflops for item in dataset.tasks], dtype=np.float64
        ),
        "upload": np.asarray([item.upload_mb_per_s for item in dataset.tasks], dtype=np.float64),
        "download": np.asarray(
            [item.download_mb_per_s for item in dataset.tasks], dtype=np.float64
        ),
        "deadline": np.asarray([item.deadline_slots for item in dataset.tasks], dtype=np.float64),
    }
    figure, axes = plt.subplots(2, 3, figsize=(12, 7), constrained_layout=True)
    labels = {
        "storage": "Storage (MB)",
        "computation": "Computation (MFlops)",
        "upload": "Upload bandwidth (MB/s)",
        "download": "Download bandwidth (MB/s)",
        "deadline": "Deadline (slots)",
    }
    for axis, field in zip(axes.flat[:5], task_values, strict=True):
        _histogram_with_target(
            axis,
            task_values[field],
            specs[field],
            title=field.capitalize(),
            x_label=labels[field],
        )
    utility_axis = axes.flat[5]
    if dataset.config.workload_kind == "normal":
        _histogram_with_target(
            utility_axis,
            np.asarray([item.utility for item in dataset.tasks], dtype=np.float64),
            NORMAL_JOB_SPECS["utility"],
            title="Utility",
            x_label="Utility",
        )
    else:
        for class_name, spec_name in (("low", "utility_low"), ("high", "utility_high")):
            values = np.asarray(
                [item.utility for item in dataset.tasks if item.utility_class == class_name],
                dtype=np.float64,
            )
            utility_axis.hist(
                values,
                bins="auto",
                density=True,
                alpha=0.55,
                label=f"Generated {class_name}",
            )
            x_values = np.linspace(
                min(
                    float(np.min(values)),
                    specs[spec_name].mean - 4 * specs[spec_name].standard_deviation,
                ),
                max(
                    float(np.max(values)),
                    specs[spec_name].mean + 4 * specs[spec_name].standard_deviation,
                ),
                300,
                dtype=np.float64,
            )
            utility_axis.plot(
                x_values,
                _normal_density(x_values, specs[spec_name]),
                linewidth=1.5,
                label=f"Target {class_name}",
            )
        utility_axis.set_title("Utility mixture")
        utility_axis.set_xlabel("Utility")
        utility_axis.set_ylabel("Density")
        utility_axis.grid(alpha=0.2)
    handles, legend_labels = utility_axis.get_legend_handles_labels()
    if handles:
        utility_axis.legend(handles, legend_labels, fontsize="small")
    figure.suptitle(
        f"{dataset.config.workload_kind.title()} task distributions - auxiliary diagnostic"
    )
    task_paths = _save_figure(figure, output_directory / f"{dataset.config.dataset_id}_tasks")
    plt.close(figure)

    server_figure, server_axes = plt.subplots(2, 2, figsize=(9, 7), constrained_layout=True)
    server_values = {
        "storage": np.asarray([item.storage_mb for item in dataset.servers], dtype=np.float64),
        "computation": np.asarray(
            [item.computation_mflops_per_s for item in dataset.servers],
            dtype=np.float64,
        ),
        "upload": np.asarray([item.upload_mb_per_s for item in dataset.servers], dtype=np.float64),
        "download": np.asarray(
            [item.download_mb_per_s for item in dataset.servers], dtype=np.float64
        ),
    }
    server_labels = {
        "storage": "Storage (MB)",
        "computation": "Computation (MFlops/s)",
        "upload": "Upload bandwidth (MB/s)",
        "download": "Download bandwidth (MB/s)",
    }
    for axis, field in zip(server_axes.flat, server_values, strict=True):
        _histogram_with_target(
            axis,
            server_values[field],
            SERVER_SPECS[field],
            title=field.capitalize(),
            x_label=server_labels[field],
        )
    server_figure.suptitle("Server distributions (n=8) - informational diagnostic")
    server_paths = _save_figure(
        server_figure, output_directory / f"{dataset.config.dataset_id}_servers"
    )
    plt.close(server_figure)

    arrival_figure, arrival_axis = plt.subplots(1, 1, figsize=(7, 4.5), constrained_layout=True)
    _histogram_with_target(
        arrival_axis,
        np.asarray(dataset.arrival_counts, dtype=np.float64),
        ARRIVAL_SPEC,
        title="Arrival counts",
        x_label="Jobs per slot",
    )
    arrival_figure.suptitle("Arrival distribution - auxiliary diagnostic")
    arrival_paths = _save_figure(
        arrival_figure, output_directory / f"{dataset.config.dataset_id}_arrivals"
    )
    plt.close(arrival_figure)
    return task_paths + server_paths + arrival_paths
