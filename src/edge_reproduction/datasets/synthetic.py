"""Source-traceable synthetic workloads from arXiv v2 Tables I and II."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Literal

import numpy as np
import numpy.typing as npt

from edge_reproduction.models.resources import ResourceVector
from edge_reproduction.models.server import Server
from edge_reproduction.models.task import Task

WorkloadKind = Literal["normal", "bimodal"]
UtilityClass = Literal["low", "high"]

STREAM_NAMES = (
    "server_storage",
    "server_computation",
    "server_upload",
    "server_download",
    "arrivals",
    "job_storage",
    "job_computation",
    "job_upload",
    "job_download",
    "job_deadline",
    "normal_utility",
    "bimodal_low_utility",
    "bimodal_high_utility",
    "mixture_labels",
)


@dataclass(frozen=True, slots=True)
class NormalSpec:
    """One paper-reported ``N(mean, standard_deviation)`` marginal."""

    mean: float
    standard_deviation: float
    unit: str

    def __post_init__(self) -> None:
        if not isfinite(self.mean) or not isfinite(self.standard_deviation):
            raise ValueError("normal parameters must be finite")
        if self.standard_deviation <= 0.0:
            raise ValueError("standard_deviation must be positive")
        if not self.unit:
            raise ValueError("unit must not be empty")

    def as_dict(self) -> dict[str, float | str]:
        return {
            "mean": self.mean,
            "standard_deviation": self.standard_deviation,
            "unit": self.unit,
        }


SERVER_SPECS: Mapping[str, NormalSpec] = MappingProxyType(
    {
        "storage": NormalSpec(540.0, 30.0, "MB"),
        "computation": NormalSpec(80.0, 20.0, "MFlops/s"),
        "upload": NormalSpec(120.0, 30.0, "MB/s"),
        "download": NormalSpec(120.0, 30.0, "MB/s"),
    }
)
NORMAL_JOB_SPECS: Mapping[str, NormalSpec] = MappingProxyType(
    {
        "storage": NormalSpec(200.0, 20.0, "MB"),
        "computation": NormalSpec(100.0, 20.0, "MFlops"),
        "upload": NormalSpec(80.0, 10.0, "MB/s"),
        "download": NormalSpec(80.0, 10.0, "MB/s"),
        "deadline": NormalSpec(10.0, 3.0, "slot"),
        "utility": NormalSpec(60.0, 20.0, "utility"),
    }
)
BIMODAL_JOB_SPECS: Mapping[str, NormalSpec] = MappingProxyType(
    {
        "storage": NormalSpec(160.0, 10.0, "MB"),
        "computation": NormalSpec(80.0, 20.0, "MFlops"),
        "upload": NormalSpec(70.0, 10.0, "MB/s"),
        "download": NormalSpec(70.0, 10.0, "MB/s"),
        "deadline": NormalSpec(10.0, 3.0, "slot"),
        "utility_low": NormalSpec(40.0, 10.0, "utility"),
        "utility_high": NormalSpec(160.0, 20.0, "utility"),
    }
)
ARRIVAL_SPEC = NormalSpec(14.0, 4.0, "jobs/slot")


def _ensure_int(name: str, value: object, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class SyntheticGenerationConfig:
    """Explicit generation envelope; paper-missing values have no defaults."""

    dataset_id: str
    label: str
    workload_kind: WorkloadKind
    seed: int
    arrival_slots: int
    drain_slots: int
    server_count: int = 8

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.label:
            raise ValueError("dataset_id and label must not be empty")
        if self.workload_kind not in ("normal", "bimodal"):
            raise ValueError("workload_kind must be normal or bimodal")
        _ensure_int("seed", self.seed, minimum=0)
        _ensure_int("arrival_slots", self.arrival_slots, minimum=1)
        _ensure_int("drain_slots", self.drain_slots, minimum=0)
        _ensure_int("server_count", self.server_count, minimum=1)
        if self.server_count != 8:
            raise ValueError("server_count must be 8 as stated in arXiv v2 Section VI-A2")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> SyntheticGenerationConfig:
        """Parse a JSON-compatible mapping without hidden scientific defaults."""

        required = {
            "dataset_id",
            "label",
            "workload_kind",
            "seed",
            "arrival_slots",
            "drain_slots",
            "server_count",
        }
        missing = required - set(raw)
        extra = set(raw) - required
        if missing:
            raise ValueError(f"missing generation config keys: {sorted(missing)}")
        if extra:
            raise ValueError(f"unknown generation config keys: {sorted(extra)}")
        kind = raw["workload_kind"]
        if kind not in ("normal", "bimodal"):
            raise ValueError("workload_kind must be normal or bimodal")
        return cls(
            dataset_id=str(raw["dataset_id"]),
            label=str(raw["label"]),
            workload_kind=kind,
            seed=_ensure_int("seed", raw["seed"], minimum=0),
            arrival_slots=_ensure_int("arrival_slots", raw["arrival_slots"], minimum=1),
            drain_slots=_ensure_int("drain_slots", raw["drain_slots"], minimum=0),
            server_count=_ensure_int("server_count", raw["server_count"], minimum=1),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "label": self.label,
            "workload_kind": self.workload_kind,
            "seed": self.seed,
            "arrival_slots": self.arrival_slots,
            "drain_slots": self.drain_slots,
            "server_count": self.server_count,
        }


@dataclass(frozen=True, slots=True)
class SyntheticServerRecord:
    server_id: str
    storage_mb: float
    computation_mflops_per_s: float
    upload_mb_per_s: float
    download_mb_per_s: float

    def to_domain(self) -> Server:
        """Convert the table record to the allocation-layer server model."""

        return Server(
            self.server_id,
            ResourceVector(
                self.storage_mb,
                self.computation_mflops_per_s,
                self.upload_mb_per_s,
                self.download_mb_per_s,
            ),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "server_id": self.server_id,
            "storage_mb": self.storage_mb,
            "computation_mflops_per_s": self.computation_mflops_per_s,
            "upload_mb_per_s": self.upload_mb_per_s,
            "download_mb_per_s": self.download_mb_per_s,
        }


@dataclass(frozen=True, slots=True)
class SyntheticTaskRecord:
    task_id: str
    arrival_slot: int
    deadline_slots: int
    deadline_raw: float
    utility: float
    utility_class: UtilityClass | None
    storage_mb: float
    computation_mflops: float
    upload_mb_per_s: float
    download_mb_per_s: float

    def to_domain(self) -> Task:
        """Convert to the allocation-layer model; output size remains unavailable."""

        return Task(
            self.task_id,
            self.arrival_slot,
            self.deadline_slots,
            self.utility,
            ResourceVector(
                self.storage_mb,
                self.computation_mflops,
                self.upload_mb_per_s,
                self.download_mb_per_s,
            ),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "arrival_slot": self.arrival_slot,
            "deadline_slots": self.deadline_slots,
            "deadline_raw": self.deadline_raw,
            "utility": self.utility,
            "utility_class": self.utility_class or "",
            "storage_mb": self.storage_mb,
            "computation_mflops": self.computation_mflops,
            "upload_mb_per_s": self.upload_mb_per_s,
            "download_mb_per_s": self.download_mb_per_s,
            "output_size_status": "unavailable_not_reported_ASSUMP-026",
        }


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    """Generated allocation-layer dataset plus complete reproducibility metadata."""

    config: SyntheticGenerationConfig
    servers: tuple[SyntheticServerRecord, ...]
    tasks: tuple[SyntheticTaskRecord, ...]
    arrival_raw_draws: tuple[float, ...]
    arrival_counts: tuple[int, ...]
    resample_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "resample_counts", MappingProxyType(dict(self.resample_counts)))
        if len(self.servers) != self.config.server_count:
            raise ValueError("server record count must equal config.server_count")
        if len(self.arrival_counts) != self.config.arrival_slots:
            raise ValueError("arrival count length must equal config.arrival_slots")
        if len(self.arrival_raw_draws) != self.config.arrival_slots:
            raise ValueError("arrival raw-draw length must equal config.arrival_slots")
        if sum(self.arrival_counts) != len(self.tasks):
            raise ValueError("arrival counts must sum to generated task count")

    def metadata(self) -> dict[str, object]:
        """Return JSON-compatible provenance and scientific settings."""

        specs = NORMAL_JOB_SPECS if self.config.workload_kind == "normal" else BIMODAL_JOB_SPECS
        return {
            "baseline": "arXiv:2403.15665v2_2024",
            "scientific_status": "allocation_layer_only_not_full_pipeline_ASSUMP-026",
            "config": self.config.as_dict(),
            "assumptions": [
                "ASSUMP-020",
                "ASSUMP-021",
                "ASSUMP-022",
                "ASSUMP-023",
                "ASSUMP-024",
                "ASSUMP-025",
                "ASSUMP-026",
                "ASSUMP-027",
            ],
            "rng": {
                "library": "numpy",
                "version": np.__version__,
                "bit_generator": "PCG64",
                "root_seed": self.config.seed,
                "stream_spawn_order": list(STREAM_NAMES),
            },
            "rounding": {
                "deadline": "floor(raw+0.5), resample until >=1",
                "arrival_count": "floor(raw+0.5), resample until >=0",
                "continuous_fields": "none",
            },
            "sampling": {
                "dependence": "independent_marginals_ASSUMP-021",
                "positive_continuous": "rejection_sampling_ASSUMP-022",
                "resample_counts": dict(self.resample_counts),
            },
            "units": "literal_arxiv_v2_tables_I_II_ASSUMP-023",
            "server_distributions": {name: spec.as_dict() for name, spec in SERVER_SPECS.items()},
            "job_distributions": {name: spec.as_dict() for name, spec in specs.items()},
            "arrival_distribution": ARRIVAL_SPEC.as_dict(),
            "bimodal_mixture": (
                {
                    "low_fraction": 0.9,
                    "high_fraction": 0.1,
                    "assignment": "exact_quota_then_seeded_shuffle_ASSUMP-025",
                }
                if self.config.workload_kind == "bimodal"
                else None
            ),
            "record_counts": {
                "servers": len(self.servers),
                "tasks": len(self.tasks),
            },
            "missing_fields": {
                "output_size_s_prime_j": "not_reported_not_generated_ASSUMP-026",
                "normal_high_low_label": (
                    "not_reported_not_generated_ASSUMP-026"
                    if self.config.workload_kind == "normal"
                    else "not_applicable"
                ),
            },
        }


def _spawn_generators(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAM_NAMES))
    return {
        name: np.random.Generator(np.random.PCG64(child))
        for name, child in zip(STREAM_NAMES, children, strict=True)
    }


def _positive_normal(
    rng: np.random.Generator, spec: NormalSpec, count: int
) -> tuple[npt.NDArray[np.float64], int]:
    values = np.asarray(rng.normal(spec.mean, spec.standard_deviation, count), dtype=np.float64)
    invalid = ~np.isfinite(values) | (values <= 0.0)
    resamples = 0
    while bool(np.any(invalid)):
        invalid_count = int(np.count_nonzero(invalid))
        resamples += invalid_count
        values[invalid] = rng.normal(spec.mean, spec.standard_deviation, invalid_count)
        invalid = ~np.isfinite(values) | (values <= 0.0)
    return values, resamples


def _round_half_up(values: npt.NDArray[np.float64]) -> npt.NDArray[np.int64]:
    """Round non-negative-domain candidates using ASSUMP-022 semantics."""

    return np.floor(values + 0.5).astype(np.int64)


def _rounded_normal(
    rng: np.random.Generator,
    spec: NormalSpec,
    count: int,
    *,
    minimum: int,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.int64], int]:
    raw = np.asarray(rng.normal(spec.mean, spec.standard_deviation, count), dtype=np.float64)
    rounded = _round_half_up(raw)
    invalid = ~np.isfinite(raw) | (rounded < minimum)
    resamples = 0
    while bool(np.any(invalid)):
        invalid_count = int(np.count_nonzero(invalid))
        resamples += invalid_count
        raw[invalid] = rng.normal(spec.mean, spec.standard_deviation, invalid_count)
        rounded[invalid] = _round_half_up(raw[invalid])
        invalid = ~np.isfinite(raw) | (rounded < minimum)
    return raw, rounded, resamples


def _sample_fields(
    streams: Mapping[str, np.random.Generator],
    specs: Mapping[str, NormalSpec],
    *,
    prefix: str,
    count: int,
) -> tuple[dict[str, npt.NDArray[np.float64]], dict[str, int]]:
    values: dict[str, npt.NDArray[np.float64]] = {}
    resamples: dict[str, int] = {}
    for field_name, spec in specs.items():
        stream_name = f"{prefix}_{field_name}"
        sampled, rejected = _positive_normal(streams[stream_name], spec, count)
        values[field_name] = sampled
        resamples[stream_name] = rejected
    return values, resamples


def generate_synthetic(config: SyntheticGenerationConfig) -> SyntheticDataset:
    """Generate one deterministic, allocation-layer synthetic dataset."""

    streams = _spawn_generators(config.seed)
    server_values, resamples = _sample_fields(
        streams, SERVER_SPECS, prefix="server", count=config.server_count
    )
    arrival_raw, arrival_counts_array, arrival_resamples = _rounded_normal(
        streams["arrivals"],
        ARRIVAL_SPEC,
        config.arrival_slots,
        minimum=0,
    )
    resamples["arrivals"] = arrival_resamples
    total_tasks = int(arrival_counts_array.sum())
    if config.workload_kind == "bimodal" and total_tasks % 10 != 0:
        raise ValueError(
            "ASSUMP-025 requires a Bimodal total task count divisible by 10; "
            f"observed {total_tasks}"
        )

    common_names = ("storage", "computation", "upload", "download")
    job_specs = NORMAL_JOB_SPECS if config.workload_kind == "normal" else BIMODAL_JOB_SPECS
    job_values, job_resamples = _sample_fields(
        streams,
        {name: job_specs[name] for name in common_names},
        prefix="job",
        count=total_tasks,
    )
    resamples.update(job_resamples)
    deadline_raw, deadline_values, deadline_resamples = _rounded_normal(
        streams["job_deadline"],
        job_specs["deadline"],
        total_tasks,
        minimum=1,
    )
    resamples["job_deadline"] = deadline_resamples

    utility_classes: list[UtilityClass | None] = []
    if config.workload_kind == "normal":
        utilities, utility_resamples = _positive_normal(
            streams["normal_utility"], NORMAL_JOB_SPECS["utility"], total_tasks
        )
        resamples["normal_utility"] = utility_resamples
        utility_classes.extend(None for _ in range(total_tasks))
    else:
        high_count = total_tasks // 10
        low_count = total_tasks - high_count
        low_values, low_resamples = _positive_normal(
            streams["bimodal_low_utility"],
            BIMODAL_JOB_SPECS["utility_low"],
            low_count,
        )
        high_values, high_resamples = _positive_normal(
            streams["bimodal_high_utility"],
            BIMODAL_JOB_SPECS["utility_high"],
            high_count,
        )
        resamples["bimodal_low_utility"] = low_resamples
        resamples["bimodal_high_utility"] = high_resamples
        for _ in range(low_count):
            utility_classes.append("low")
        for _ in range(high_count):
            utility_classes.append("high")
        streams["mixture_labels"].shuffle(utility_classes)
        low_iterator = iter(low_values.tolist())
        high_iterator = iter(high_values.tolist())
        utilities = np.asarray(
            [
                next(low_iterator) if label == "low" else next(high_iterator)
                for label in utility_classes
            ],
            dtype=np.float64,
        )

    servers = tuple(
        SyntheticServerRecord(
            f"server-{index + 1:03d}",
            float(server_values["storage"][index]),
            float(server_values["computation"][index]),
            float(server_values["upload"][index]),
            float(server_values["download"][index]),
        )
        for index in range(config.server_count)
    )
    arrival_slots = tuple(
        slot for slot, count in enumerate(arrival_counts_array.tolist()) for _ in range(int(count))
    )
    tasks = tuple(
        SyntheticTaskRecord(
            f"job-{index + 1:06d}",
            arrival_slots[index],
            int(deadline_values[index]),
            float(deadline_raw[index]),
            float(utilities[index]),
            utility_classes[index],
            float(job_values["storage"][index]),
            float(job_values["computation"][index]),
            float(job_values["upload"][index]),
            float(job_values["download"][index]),
        )
        for index in range(total_tasks)
    )
    return SyntheticDataset(
        config,
        servers,
        tasks,
        tuple(float(item) for item in arrival_raw.tolist()),
        tuple(int(item) for item in arrival_counts_array.tolist()),
        resamples,
    )
