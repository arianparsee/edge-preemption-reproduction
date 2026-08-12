"""Generate one explicitly configured synthetic allocation-layer dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from edge_reproduction.datasets.artifacts import write_dataset_artifacts
from edge_reproduction.datasets.diagnostics import (
    summarize_dataset,
    write_diagnostic_figures,
)
from edge_reproduction.datasets.synthetic import (
    SyntheticGenerationConfig,
    generate_synthetic,
)


def _load_config(path: Path) -> SyntheticGenerationConfig:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("synthetic generation config must be a JSON object")
    return SyntheticGenerationConfig.from_mapping(dict[str, Any](raw))


def run_generation(config_path: Path, *, project_root: Path = Path(".")) -> dict[str, object]:
    """Generate data, statistical summary and auxiliary figures."""

    config = _load_config(config_path)
    dataset = generate_synthetic(config)
    data_directory = project_root / "data" / "processed" / "synthetic" / config.dataset_id
    summary_directory = project_root / "results" / "aggregated" / "stage11b"
    figure_directory = project_root / "figures" / "diagnostics" / "stage11b"
    data_paths = write_dataset_artifacts(dataset, data_directory)
    summary = summarize_dataset(dataset)
    summary_directory.mkdir(parents=True, exist_ok=True)
    summary_path = summary_directory / f"{config.dataset_id}_diagnostics.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    figure_paths = write_diagnostic_figures(dataset, figure_directory)
    if not bool(summary["all_eligible_checks_passed"]):
        raise RuntimeError(f"auxiliary statistical checks failed: {summary['failed_checks']}")
    return {
        "dataset_id": config.dataset_id,
        "workload_kind": config.workload_kind,
        "server_count": len(dataset.servers),
        "task_count": len(dataset.tasks),
        "seed": config.seed,
        "data_paths": [path.as_posix() for path in data_paths],
        "summary_path": summary_path.as_posix(),
        "figure_paths": [path.as_posix() for path in figure_paths],
        "all_eligible_checks_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="JSON config with explicit seed and workload envelope",
    )
    arguments = parser.parse_args()
    result = run_generation(arguments.config)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
