"""Pixel-traceable digitization of the published Southampton histograms.

The output describes visible solid-color components only. It does not infer
occluded bins, raw trace rows, sample counts, or cross-field dependence.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PIL import Image, ImageDraw

RGB = tuple[int, int, int]

SERIES_COLORS: dict[str, RGB] = {
    "low": (44, 160, 44),
    "medium": (255, 127, 14),
    "high": (214, 39, 40),
}

EXPECTED_SOURCE_HASHES = {
    "trace_storage_distribution.png": (
        "52de43f031e04d9214a2f2117ced71c04a9ba0aa0148334e725fb299f076c6e6"
    ),
    "trace_computation_distribution.png": (
        "951b74d895c5cc8a495b99b13de41d66532d03ad54e68e7b178882aaedf38187"
    ),
    "trace_deadline_distribution.png": (
        "8139f3c85a631cc9e8571e884e80b16e152002fcb87f813caafd37ede5372355"
    ),
}


@dataclass(frozen=True, slots=True)
class AxisCalibration:
    """Two-point linear pixel-to-data calibration for one plot."""

    x_pixel_0: int
    x_value_0: float
    x_pixel_1: int
    x_value_1: float
    y_pixel_0: int
    y_value_0: float
    y_pixel_1: int
    y_value_1: float

    def __post_init__(self) -> None:
        if self.x_pixel_0 == self.x_pixel_1 or self.y_pixel_0 == self.y_pixel_1:
            raise ValueError("calibration pixel pairs must be distinct")

    def x_value(self, pixel: float) -> float:
        return self.x_value_0 + (pixel - self.x_pixel_0) * (
            (self.x_value_1 - self.x_value_0) / (self.x_pixel_1 - self.x_pixel_0)
        )

    def y_value(self, pixel: float) -> float:
        return self.y_value_0 + (pixel - self.y_pixel_0) * (
            (self.y_value_1 - self.y_value_0) / (self.y_pixel_1 - self.y_pixel_0)
        )


@dataclass(frozen=True, slots=True)
class FigureSpec:
    filename: str
    resource: str
    x_unit_as_published: str
    calibration: AxisCalibration


COMMON_RESOURCE_CALIBRATION = AxisCalibration(
    x_pixel_0=103,
    x_value_0=0.0,
    x_pixel_1=518,
    x_value_1=2500.0,
    y_pixel_0=427,
    y_value_0=0.0,
    y_pixel_1=78,
    y_value_1=0.010,
)
DEADLINE_CALIBRATION = AxisCalibration(
    x_pixel_0=99,
    x_value_0=0.0,
    x_pixel_1=553,
    x_value_1=120.0,
    y_pixel_0=427,
    y_value_0=0.0,
    y_pixel_1=96,
    y_value_1=0.12,
)
FIGURE_SPECS = (
    FigureSpec(
        "trace_storage_distribution.png",
        "storage",
        "Gigabytes",
        COMMON_RESOURCE_CALIBRATION,
    ),
    FigureSpec(
        "trace_computation_distribution.png",
        "computation",
        "Gigabytes",
        COMMON_RESOURCE_CALIBRATION,
    ),
    FigureSpec(
        "trace_deadline_distribution.png",
        "deadline",
        "Hours",
        DEADLINE_CALIBRATION,
    ),
)


@dataclass(frozen=True, slots=True)
class VisibleComponent:
    """One connected region of a visible series fill color."""

    figure: str
    resource: str
    priority: str
    component_id: str
    pixel_count: int
    pixel_left: int
    pixel_right: int
    pixel_top: int
    pixel_bottom: int
    x_visible_left_approx: float
    x_visible_right_approx: float
    x_visible_midpoint_approx: float
    probability_top_approx: float
    probability_bottom_approx: float
    x_unit_as_published: str
    scientific_label: str = "visible_color_component_not_underlying_histogram_bin"


def file_sha256(path: Path) -> str:
    """Return lowercase SHA-256 for a source artifact."""

    return sha256(path.read_bytes()).hexdigest()


def validate_source(path: Path, expected_hash: str) -> None:
    """Fail fast when a published source image is absent or has changed."""

    if not path.is_file():
        raise FileNotFoundError(path)
    actual_hash = file_sha256(path)
    if actual_hash != expected_hash:
        message = (
            f"source hash mismatch for {path.name}: "
            f"expected {expected_hash}, observed {actual_hash}"
        )
        raise ValueError(message)
    with Image.open(path) as image:
        if image.size != (640, 480):
            raise ValueError(f"unexpected source image size for {path.name}: {image.size}")


def _component_pixels(mask: npt.NDArray[np.bool_]) -> Iterable[list[tuple[int, int]]]:
    """Yield four-connected components as ``(y, x)`` pixel lists."""

    seen = np.zeros(mask.shape, dtype=np.bool_)
    for raw_y, raw_x in np.argwhere(mask):
        y = int(raw_y)
        x = int(raw_x)
        if bool(seen[y, x]):
            continue
        stack = [(y, x)]
        seen[y, x] = True
        component: list[tuple[int, int]] = []
        while stack:
            current_y, current_x = stack.pop()
            component.append((current_y, current_x))
            for delta_y, delta_x in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor_y = current_y + delta_y
                neighbor_x = current_x + delta_x
                if (
                    0 <= neighbor_y < mask.shape[0]
                    and 0 <= neighbor_x < mask.shape[1]
                    and bool(mask[neighbor_y, neighbor_x])
                    and not bool(seen[neighbor_y, neighbor_x])
                ):
                    seen[neighbor_y, neighbor_x] = True
                    stack.append((neighbor_y, neighbor_x))
        yield component


def digitize_figure(path: Path, spec: FigureSpec) -> tuple[VisibleComponent, ...]:
    """Extract visible solid-color components using source-specific calibration."""

    validate_source(path, EXPECTED_SOURCE_HASHES[spec.filename])
    with Image.open(path) as image:
        pixels: npt.NDArray[np.uint8] = np.asarray(image.convert("RGB"), dtype=np.uint8)

    records: list[VisibleComponent] = []
    for priority, color in SERIES_COLORS.items():
        mask = np.asarray(
            np.all(pixels == np.asarray(color, dtype=np.uint8), axis=2),
            dtype=np.bool_,
        )
        # Published plot interior. Pixels outside it are labels/titles.
        mask[:58, :] = False
        mask[427:, :] = False
        mask[:, :80] = False
        mask[:, 577:] = False
        # Legend swatches are inside the axes and must not become data.
        mask[65:131, 480:540] = False

        components = []
        for component in _component_pixels(mask):
            if len(component) < 8:
                continue
            ys = [item[0] for item in component]
            xs = [item[1] for item in component]
            components.append((min(xs), max(xs), min(ys), max(ys), len(component)))
        components.sort(key=lambda item: (item[0], item[2], item[1], item[3]))
        for index, (left, right, top, bottom, count) in enumerate(components, start=1):
            calibration = spec.calibration
            records.append(
                VisibleComponent(
                    figure=spec.filename,
                    resource=spec.resource,
                    priority=priority,
                    component_id=f"{spec.resource}-{priority}-{index:02d}",
                    pixel_count=count,
                    pixel_left=left,
                    pixel_right=right,
                    pixel_top=top,
                    pixel_bottom=bottom,
                    x_visible_left_approx=calibration.x_value(left),
                    x_visible_right_approx=calibration.x_value(right),
                    x_visible_midpoint_approx=calibration.x_value((left + right) / 2.0),
                    probability_top_approx=max(0.0, calibration.y_value(top)),
                    probability_bottom_approx=max(0.0, calibration.y_value(bottom)),
                    x_unit_as_published=spec.x_unit_as_published,
                )
            )
    return tuple(records)


def _write_components(path: Path, records: tuple[VisibleComponent, ...]) -> None:
    rows = [asdict(record) for record in records]
    if not rows:
        raise ValueError("digitization produced no visible components")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_overlay(
    source_path: Path,
    output_path: Path,
    records: tuple[VisibleComponent, ...],
) -> None:
    with Image.open(source_path) as source:
        rendered = source.convert("RGB")
    draw = ImageDraw.Draw(rendered)
    for record in records:
        color = SERIES_COLORS[record.priority]
        draw.rectangle(
            (
                record.pixel_left - 1,
                record.pixel_top - 1,
                record.pixel_right + 1,
                record.pixel_bottom + 1,
            ),
            outline=color,
            width=2,
        )
        draw.text(
            (record.pixel_left, max(132, record.pixel_top - 11)),
            record.component_id.rsplit("-", maxsplit=1)[-1],
            fill=(0, 0, 0),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered.save(output_path, format="PNG", optimize=False)


def digitize_sources(
    source_directory: Path,
    output_directory: Path,
    diagnostics_directory: Path,
) -> dict[str, object]:
    """Digitize all three v2 histograms and write deterministic artifacts."""

    all_records: list[VisibleComponent] = []
    per_figure_counts: dict[str, int] = {}
    source_hashes: dict[str, str] = {}
    for spec in FIGURE_SPECS:
        source_path = source_directory / spec.filename
        records = digitize_figure(source_path, spec)
        all_records.extend(records)
        per_figure_counts[spec.filename] = len(records)
        source_hashes[spec.filename] = file_sha256(source_path)
        _write_overlay(
            source_path,
            diagnostics_directory / f"{source_path.stem}_visible_components.png",
            records,
        )

    storage_pixels = np.asarray(
        Image.open(source_directory / "trace_storage_distribution.png").convert("RGBA"),
        dtype=np.uint8,
    )
    computation_pixels = np.asarray(
        Image.open(source_directory / "trace_computation_distribution.png").convert("RGBA"),
        dtype=np.uint8,
    )
    identical_below_title = bool(np.array_equal(storage_pixels[58:], computation_pixels[58:]))
    if not identical_below_title:
        raise ValueError("expected storage/computation source duplication was not reproduced")

    records_tuple = tuple(all_records)
    component_path = output_directory / "visible_components.csv"
    _write_components(component_path, records_tuple)
    manifest = {
        "baseline": "arXiv:2403.15665v2_2024",
        "label": "approximate_visible_pixel_digitization_not_raw_trace_not_histogram_bins",
        "source_directory": source_directory.as_posix(),
        "source_hashes_sha256": source_hashes,
        "series_colors_rgb": {name: list(color) for name, color in SERIES_COLORS.items()},
        "axis_calibrations": {
            spec.filename: asdict(spec.calibration)
            | {"x_unit_as_published": spec.x_unit_as_published}
            for spec in FIGURE_SPECS
        },
        "component_count": len(records_tuple),
        "component_counts_by_figure": per_figure_counts,
        "storage_computation_identical_below_title_pixel_row_58": identical_below_title,
        "limitations": [
            "visible exact fill-color components only",
            "connected components are not asserted to be histogram bins",
            "occluded bars and hidden bin heights are not reconstructed",
            "probability normalization and original sample counts are unknown",
            "no raw rows, timestamps, dependence, or surrogate samples are produced",
            "computation x-axis is Gigabytes as published and is not converted to MFlops",
        ],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = output_directory / "digitization_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "component_path": component_path,
        "manifest_path": manifest_path,
        "component_count": len(records_tuple),
        "component_counts_by_figure": per_figure_counts,
        "storage_computation_identical_below_title": identical_below_title,
    }
