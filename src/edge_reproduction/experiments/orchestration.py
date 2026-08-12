"""Deterministic auxiliary experiment orchestration and resume validation."""

from __future__ import annotations

import json
import platform
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.experiments.four_policy_smoke import run_four_policy_smoke

EXECUTION_SCHEMA = "stage13b-execution-config-v1"
REGISTRY_SCHEMA = "stage13b-execution-registry-v1"
AUXILIARY_LABEL = "auxiliary_single_auction_smoke_not_paper_experiment"
RunnerName = Literal["four_policy_single_auction"]


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _identifier(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{name} must be a non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} contains unsupported characters")
    return value


def _integer(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


@dataclass(frozen=True, slots=True)
class AuxiliaryExecutionConfig:
    """One explicitly auxiliary run with no unresolved scientific decisions."""

    run_id: str
    experiment_id: str
    scientific_label: str
    baseline: str
    runner: RunnerName
    seed: int
    input_config_path: str
    unresolved_decisions: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier("run_id", self.run_id)
        _identifier("experiment_id", self.experiment_id)
        if self.scientific_label != AUXILIARY_LABEL:
            raise ValueError(f"scientific_label must be {AUXILIARY_LABEL!r}")
        if self.baseline != "arXiv:2403.15665v2_2024":
            raise ValueError("unexpected baseline")
        if self.runner != "four_policy_single_auction":
            raise ValueError("unsupported auxiliary runner")
        _integer("seed", self.seed)
        if not self.input_config_path:
            raise ValueError("input_config_path must not be empty")
        for decision in self.unresolved_decisions:
            _identifier("unresolved decision", decision)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> AuxiliaryExecutionConfig:
        required = {
            "schema_version",
            "run_id",
            "experiment_id",
            "scientific_label",
            "baseline",
            "runner",
            "seed",
            "input_config_path",
            "unresolved_decisions",
        }
        missing = required - set(raw)
        extra = set(raw) - required
        if missing:
            raise ValueError(f"missing execution config keys: {sorted(missing)}")
        if extra:
            raise ValueError(f"unknown execution config keys: {sorted(extra)}")
        if raw["schema_version"] != EXECUTION_SCHEMA:
            raise ValueError("unexpected execution config schema_version")
        decisions = raw["unresolved_decisions"]
        if not isinstance(decisions, list) or not all(isinstance(item, str) for item in decisions):
            raise TypeError("unresolved_decisions must be a list of strings")
        runner = raw["runner"]
        if runner != "four_policy_single_auction":
            raise ValueError("unsupported auxiliary runner")
        return cls(
            run_id=_identifier("run_id", raw["run_id"]),
            experiment_id=_identifier("experiment_id", raw["experiment_id"]),
            scientific_label=str(raw["scientific_label"]),
            baseline=str(raw["baseline"]),
            runner=runner,
            seed=_integer("seed", raw["seed"]),
            input_config_path=str(raw["input_config_path"]),
            unresolved_decisions=tuple(decisions),
        )

    def ensure_resolved(self) -> None:
        if self.unresolved_decisions:
            joined = ", ".join(self.unresolved_decisions)
            raise UnresolvedDecisionError(f"unresolved reproduction decisions: {joined}")

    def as_dict(self) -> dict[str, object]:
        return {"schema_version": EXECUTION_SCHEMA} | asdict(self)


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    run_id: str
    experiment_id: str
    status: Literal["succeeded", "skipped_existing_verified"]
    output_directory: Path
    result_path: Path
    manifest_path: Path

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "status": self.status,
            "output_directory": self.output_directory.as_posix(),
            "result_path": self.result_path.as_posix(),
            "manifest_path": self.manifest_path.as_posix(),
        }


def _load_json(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return dict[str, object](raw)


def load_execution_config(path: Path) -> AuxiliaryExecutionConfig:
    """Load only executable auxiliary configs and reject paper specifications."""

    raw = _load_json(path)
    if raw.get("schema_version") == "stage13a-experiment-spec-v1":
        decisions = raw.get("unresolved_decisions")
        joined = ", ".join(str(item) for item in decisions) if isinstance(decisions, list) else ""
        raise UnresolvedDecisionError(
            "paper experiment specifications are non-executable"
            + (f"; unresolved: {joined}" if joined else "")
        )
    config = AuxiliaryExecutionConfig.from_mapping(raw)
    config.ensure_resolved()
    return config


def _environment_metadata() -> dict[str, object]:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "byteorder": sys.byteorder,
        "dependencies": {
            package: version(package) for package in ("edge-reproduction", "numpy", "pyeasyga")
        },
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verified_existing(
    config: AuxiliaryExecutionConfig,
    *,
    config_path: Path,
    result_path: Path,
    manifest_path: Path,
) -> ExecutionOutcome:
    if not result_path.is_file() or not manifest_path.is_file():
        raise FileExistsError("incomplete existing run directory; refusing to overwrite")
    manifest = _load_json(manifest_path)
    expected = {
        "run_id": config.run_id,
        "experiment_id": config.experiment_id,
        "execution_config_sha256": file_sha256(config_path),
        "result_sha256": file_sha256(result_path),
    }
    observed = {key: manifest.get(key) for key in expected}
    if observed != expected:
        raise ValueError(
            f"existing run provenance mismatch: expected {expected}, observed {observed}"
        )
    return ExecutionOutcome(
        config.run_id,
        config.experiment_id,
        "skipped_existing_verified",
        result_path.parent,
        result_path,
        manifest_path,
    )


def run_experiment(
    config_path: Path,
    *,
    project_root: Path = Path("."),
    resume: bool = False,
) -> ExecutionOutcome:
    """Run one supported auxiliary experiment without overwriting prior results."""

    resolved_config_path = project_root / config_path
    config = load_execution_config(resolved_config_path)
    output_directory = (
        project_root / "results" / "raw" / "stage13b" / config.experiment_id / config.run_id
    )
    result_path = output_directory / "result.json"
    manifest_path = output_directory / "manifest.json"
    if output_directory.exists():
        if not resume:
            raise FileExistsError(
                f"run output already exists: {output_directory}; use resume to verify and skip"
            )
        return _verified_existing(
            config,
            config_path=resolved_config_path,
            result_path=result_path,
            manifest_path=manifest_path,
        )

    input_path = project_root / config.input_config_path
    result = run_four_policy_smoke(input_path, expected_seed=config.seed)
    result["scenario_config_path"] = config.input_config_path
    result = {
        "schema_version": "stage13b-raw-result-v1",
        "run_id": config.run_id,
        "experiment_id": config.experiment_id,
        "execution_status": "succeeded",
        "scientific_label": config.scientific_label,
        "warnings": [
            "auxiliary single-auction smoke; not an arXiv v2 paper experiment",
            "active utility after auction is not completed paper utility",
        ],
        "payload": result,
    }
    output_directory.mkdir(parents=True, exist_ok=False)
    _write_json(result_path, result)
    manifest = {
        "schema_version": "stage13b-run-manifest-v1",
        "run_id": config.run_id,
        "experiment_id": config.experiment_id,
        "scientific_label": config.scientific_label,
        "baseline": config.baseline,
        "runner": config.runner,
        "seed": config.seed,
        "execution_status": "succeeded",
        "execution_config_path": config_path.as_posix(),
        "execution_config_sha256": file_sha256(resolved_config_path),
        "input_config_path": config.input_config_path,
        "input_config_sha256": file_sha256(input_path),
        "result_sha256": file_sha256(result_path),
        "environment": _environment_metadata(),
        "unresolved_decisions": [],
        "paper_experiment_claimed": False,
        "runtime_measurement_recorded": False,
        "runtime_note": "wall time omitted to keep scientific artifacts deterministic",
    }
    _write_json(manifest_path, manifest)
    return ExecutionOutcome(
        config.run_id,
        config.experiment_id,
        "succeeded",
        output_directory,
        result_path,
        manifest_path,
    )


def run_registry(
    registry_path: Path,
    *,
    project_root: Path = Path("."),
    resume: bool = False,
) -> dict[str, object]:
    """Run a bounded explicit registry sequentially and write an aggregate index."""

    resolved_registry = project_root / registry_path
    raw = _load_json(resolved_registry)
    if raw.get("schema_version") != REGISTRY_SCHEMA:
        raise ValueError("unexpected execution registry schema_version")
    configs = raw.get("execution_configs")
    if (
        not isinstance(configs, list)
        or not configs
        or not all(isinstance(item, str) for item in configs)
    ):
        raise TypeError("execution_configs must be a non-empty list of paths")
    if len(configs) != len(set(configs)):
        raise ValueError("execution registry config paths must be unique")
    outcomes = tuple(
        run_experiment(Path(path), project_root=project_root, resume=resume) for path in configs
    )
    summary = {
        "schema_version": "stage13b-run-registry-summary-v1",
        "scientific_label": AUXILIARY_LABEL,
        "registry_path": registry_path.as_posix(),
        "registry_sha256": file_sha256(resolved_registry),
        "run_count": len(outcomes),
        "succeeded_count": sum(item.status == "succeeded" for item in outcomes),
        "verified_skip_count": sum(item.status == "skipped_existing_verified" for item in outcomes),
        "paper_experiment_claimed": False,
        "runs": [item.as_dict() for item in outcomes],
    }
    summary_path = project_root / "results" / "aggregated" / "stage13b" / "run_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(summary_path, summary)
    return summary | {"summary_path": summary_path.as_posix()}
