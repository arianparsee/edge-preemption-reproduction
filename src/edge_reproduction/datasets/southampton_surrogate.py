"""Approximate Southampton raster surrogate under approved ASSUMP-028..032.

This module samples only visible storage/deadline color geometry. Its output is
not raw trace data and is not an executable workload for the paper algorithms.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Literal

import numpy as np

Priority = Literal["low", "medium", "high"]
Resource = Literal["storage", "deadline"]

PRIORITIES: tuple[Priority, ...] = ("low", "medium", "high")
RESOURCES: tuple[Resource, ...] = ("storage", "deadline")
RECORDS_PER_PRIORITY = 10_000
SCIENTIFIC_LABEL = (
    "auxiliary_visible_histogram_surrogate_not_real_trace_not_paper_numerical_reproduction"
)
STREAM_NAMES = tuple(
    f"{resource}_{priority}_{operation}"
    for resource in RESOURCES
    for priority in PRIORITIES
    for operation in ("component_selection", "within_component")
)


def _required_int(name: str, value: object, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class SouthamptonSurrogateConfig:
    """Fully explicit auxiliary configuration; no paper seed is implied."""

    dataset_id: str
    label: str
    seed: int
    records_per_priority: int
    digitized_components_path: str
    digitization_manifest_path: str
    published_figures_directory: str

    def __post_init__(self) -> None:
        if not self.dataset_id:
            raise ValueError("dataset_id must not be empty")
        if self.label != SCIENTIFIC_LABEL:
            raise ValueError(f"label must be {SCIENTIFIC_LABEL!r}")
        _required_int("seed", self.seed, minimum=0)
        _required_int("records_per_priority", self.records_per_priority, minimum=1)
        if self.records_per_priority != RECORDS_PER_PRIORITY:
            raise ValueError(
                f"records_per_priority must be {RECORDS_PER_PRIORITY} under ASSUMP-029"
            )
        for name, value in (
            ("digitized_components_path", self.digitized_components_path),
            ("digitization_manifest_path", self.digitization_manifest_path),
            ("published_figures_directory", self.published_figures_directory),
        ):
            if not value:
                raise ValueError(f"{name} must not be empty")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> SouthamptonSurrogateConfig:
        required = {
            "dataset_id",
            "label",
            "seed",
            "records_per_priority",
            "digitized_components_path",
            "digitization_manifest_path",
            "published_figures_directory",
        }
        missing = required - set(raw)
        extra = set(raw) - required
        if missing:
            raise ValueError(f"missing Southampton surrogate config keys: {sorted(missing)}")
        if extra:
            raise ValueError(f"unknown Southampton surrogate config keys: {sorted(extra)}")
        return cls(
            dataset_id=str(raw["dataset_id"]),
            label=str(raw["label"]),
            seed=_required_int("seed", raw["seed"], minimum=0),
            records_per_priority=_required_int(
                "records_per_priority", raw["records_per_priority"], minimum=1
            ),
            digitized_components_path=str(raw["digitized_components_path"]),
            digitization_manifest_path=str(raw["digitization_manifest_path"]),
            published_figures_directory=str(raw["published_figures_directory"]),
        )

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VisibleSupport:
    """One approved sampling support derived from a visible raster component."""

    component_id: str
    resource: Resource
    priority: Priority
    pixel_count: int
    lower: float
    upper: float
    unit: str

    def __post_init__(self) -> None:
        if self.pixel_count <= 0:
            raise ValueError("pixel_count must be positive")
        if not isfinite(self.lower) or not isfinite(self.upper):
            raise ValueError("support bounds must be finite")
        if self.lower > self.upper:
            raise ValueError("support lower bound must not exceed upper bound")


@dataclass(frozen=True, slots=True)
class SouthamptonSurrogateRecord:
    """Limited ASSUMP-031 schema; intentionally not convertible to ``Task``."""

    surrogate_id: str
    priority: Priority
    storage_gb: float
    deadline_hours: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SouthamptonSurrogateDataset:
    config: SouthamptonSurrogateConfig
    records: tuple[SouthamptonSurrogateRecord, ...]
    selection_counts: Mapping[str, int]
    source_component_sha256: str
    source_manifest_sha256: str
    source_figure_hashes: Mapping[str, str]
    stream_spawn_keys: Mapping[str, tuple[int, ...]]

    def metadata(self) -> dict[str, object]:
        return {
            "scientific_label": SCIENTIFIC_LABEL,
            "warning": (
                "Approximate technical surrogate from visible raster geometry; "
                "not Southampton raw trace and not a numerical paper reproduction."
            ),
            "baseline": "arXiv:2403.15665v2_2024",
            "approved_assumptions": [
                "ASSUMP-028",
                "ASSUMP-029",
                "ASSUMP-030",
                "ASSUMP-031",
                "ASSUMP-032",
            ],
            "config": self.config.as_dict(),
            "record_count": len(self.records),
            "priority_order": list(PRIORITIES),
            "record_schema": [
                "surrogate_id",
                "priority",
                "storage_gb",
                "deadline_hours",
            ],
            "sampling": {
                "component_weight": "normalized_visible_pixel_count",
                "within_component": "continuous_uniform_on_visible_x_bounds",
                "joint_dependence": "storage_and_deadline_independent_conditional_on_priority",
                "selection_counts": dict(sorted(self.selection_counts.items())),
            },
            "rng": {
                "library": "numpy",
                "numpy_version": np.__version__,
                "bit_generator": "PCG64",
                "root_seed": self.config.seed,
                "stream_order": list(STREAM_NAMES),
                "stream_spawn_keys": {
                    name: list(self.stream_spawn_keys[name]) for name in STREAM_NAMES
                },
                "seed_selection_rule": "explicit_auxiliary_config_not_visual_tuning",
            },
            "provenance": {
                "digitized_components_sha256": self.source_component_sha256,
                "digitization_manifest_sha256": self.source_manifest_sha256,
                "published_figure_hashes_sha256": dict(self.source_figure_hashes),
            },
            "omitted_fields": [
                "computation",
                "arrival",
                "utility",
                "upload",
                "download",
                "output_size",
            ],
            "algorithm_input_compatible": False,
            "parameter_tuning_performed": False,
        }


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _parse_priority(value: str) -> Priority:
    if value not in PRIORITIES:
        raise ValueError(f"unknown priority in digitized components: {value!r}")
    return value


def _parse_resource(value: str) -> Resource | None:
    if value == "computation":
        return None
    if value not in RESOURCES:
        raise ValueError(f"unknown resource in digitized components: {value!r}")
    return value


def load_visible_supports(path: Path) -> tuple[VisibleSupport, ...]:
    """Load only storage/deadline supports, explicitly omitting computation."""

    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = tuple(csv.DictReader(stream))
    supports: list[VisibleSupport] = []
    for row in rows:
        resource = _parse_resource(row["resource"])
        if resource is None:
            continue
        if row["scientific_label"] != "visible_color_component_not_underlying_histogram_bin":
            raise ValueError("unexpected digitized component scientific label")
        unit = row["x_unit_as_published"]
        expected_unit = "Gigabytes" if resource == "storage" else "Hours"
        if unit != expected_unit:
            raise ValueError(f"unexpected {resource} unit: {unit!r}")
        supports.append(
            VisibleSupport(
                component_id=row["component_id"],
                resource=resource,
                priority=_parse_priority(row["priority"]),
                pixel_count=int(row["pixel_count"]),
                lower=float(row["x_visible_left_approx"]),
                upper=float(row["x_visible_right_approx"]),
                unit=unit,
            )
        )
    for resource in RESOURCES:
        for priority in PRIORITIES:
            if not any(
                support.resource == resource and support.priority == priority
                for support in supports
            ):
                raise ValueError(f"missing visible supports for {resource}/{priority}")
    return tuple(supports)


def _validated_manifest(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("digitization manifest must be a JSON object")
    manifest = dict[str, object](raw)
    if manifest.get("baseline") != "arXiv:2403.15665v2_2024":
        raise ValueError("unexpected digitization baseline")
    if manifest.get("storage_computation_identical_below_title_pixel_row_58") is not True:
        raise ValueError("digitization manifest must record storage/computation duplication")
    hashes = manifest.get("source_hashes_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("digitization manifest must contain source figure hashes")
    return manifest


def _validated_published_figure_hashes(
    manifest: Mapping[str, object], published_directory: Path
) -> dict[str, str]:
    raw_hashes = manifest["source_hashes_sha256"]
    if not isinstance(raw_hashes, dict):
        raise TypeError("source_hashes_sha256 must be a mapping")
    hashes = {str(key): str(value) for key, value in raw_hashes.items()}
    for filename, expected_hash in hashes.items():
        source_path = published_directory / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        actual_hash = file_sha256(source_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"published figure hash mismatch for {filename}: "
                f"expected {expected_hash}, observed {actual_hash}"
            )
    return hashes


def _sample_resource(
    supports: tuple[VisibleSupport, ...],
    *,
    count: int,
    selection_rng: np.random.Generator,
    within_rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, int]]:
    weights = np.asarray([support.pixel_count for support in supports], dtype=np.float64)
    probabilities = weights / float(np.sum(weights))
    selected = selection_rng.choice(len(supports), size=count, p=probabilities)
    fractions = within_rng.random(count)
    lower = np.asarray([support.lower for support in supports], dtype=np.float64)[selected]
    upper = np.asarray([support.upper for support in supports], dtype=np.float64)[selected]
    values = lower + fractions * (upper - lower)
    observed = np.bincount(selected, minlength=len(supports))
    return values, {
        support.component_id: int(observed[index]) for index, support in enumerate(supports)
    }


def generate_southampton_surrogate(
    config: SouthamptonSurrogateConfig,
    *,
    project_root: Path = Path("."),
) -> tuple[SouthamptonSurrogateDataset, tuple[VisibleSupport, ...]]:
    """Generate the approved limited surrogate with independent named streams."""

    component_path = project_root / config.digitized_components_path
    manifest_path = project_root / config.digitization_manifest_path
    published_directory = project_root / config.published_figures_directory
    supports = load_visible_supports(component_path)
    manifest = _validated_manifest(manifest_path)
    source_hashes = _validated_published_figure_hashes(manifest, published_directory)

    seed_sequence = np.random.SeedSequence(config.seed)
    children = seed_sequence.spawn(len(STREAM_NAMES))
    generators = {
        name: np.random.Generator(np.random.PCG64(child))
        for name, child in zip(STREAM_NAMES, children, strict=True)
    }
    spawn_keys = {
        name: tuple(int(item) for item in child.spawn_key)
        for name, child in zip(STREAM_NAMES, children, strict=True)
    }

    values: dict[tuple[Resource, Priority], np.ndarray] = {}
    selection_counts: dict[str, int] = {}
    for resource in RESOURCES:
        for priority in PRIORITIES:
            group = tuple(
                support
                for support in supports
                if support.resource == resource and support.priority == priority
            )
            sampled, counts = _sample_resource(
                group,
                count=config.records_per_priority,
                selection_rng=generators[f"{resource}_{priority}_component_selection"],
                within_rng=generators[f"{resource}_{priority}_within_component"],
            )
            values[(resource, priority)] = sampled
            selection_counts.update(counts)

    width = len(str(config.records_per_priority))
    records: list[SouthamptonSurrogateRecord] = []
    for priority in PRIORITIES:
        for index in range(config.records_per_priority):
            records.append(
                SouthamptonSurrogateRecord(
                    surrogate_id=f"{config.dataset_id}-{priority}-{index + 1:0{width}d}",
                    priority=priority,
                    storage_gb=float(values[("storage", priority)][index]),
                    deadline_hours=float(values[("deadline", priority)][index]),
                )
            )

    return (
        SouthamptonSurrogateDataset(
            config=config,
            records=tuple(records),
            selection_counts=selection_counts,
            source_component_sha256=file_sha256(component_path),
            source_manifest_sha256=file_sha256(manifest_path),
            source_figure_hashes=source_hashes,
            stream_spawn_keys=spawn_keys,
        ),
        supports,
    )
