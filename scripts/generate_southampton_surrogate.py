"""Generate the approved qualitative-only Southampton histogram surrogate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from edge_reproduction.datasets.southampton_surrogate import (
    SouthamptonSurrogateConfig,
    generate_southampton_surrogate,
)
from edge_reproduction.datasets.southampton_surrogate_artifacts import (
    write_surrogate_artifacts,
)
from edge_reproduction.datasets.southampton_surrogate_diagnostics import (
    summarize_surrogate,
    write_diagnostic_summary,
    write_qualitative_figures,
)


def _load_config(path: Path) -> SouthamptonSurrogateConfig:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("Southampton surrogate config must be a JSON object")
    return SouthamptonSurrogateConfig.from_mapping(dict[str, Any](raw))


def run_generation(config_path: Path, *, project_root: Path = Path(".")) -> dict[str, object]:
    """Generate separated data, diagnostic summary and qualitative figures."""

    config = _load_config(config_path)
    dataset, supports = generate_southampton_surrogate(config, project_root=project_root)
    data_directory = project_root / "data" / "processed" / "surrogates" / config.dataset_id
    summary_path = (
        project_root
        / "results"
        / "aggregated"
        / "stage12c"
        / f"{config.dataset_id}_diagnostics.json"
    )
    figure_directory = project_root / "figures" / "diagnostics" / "stage12c"
    data_paths = write_surrogate_artifacts(dataset, data_directory)
    summary = summarize_surrogate(dataset, supports)
    write_diagnostic_summary(summary, summary_path)
    figure_paths = write_qualitative_figures(
        dataset,
        supports,
        published_figures_directory=project_root / config.published_figures_directory,
        output_directory=figure_directory,
    )
    if not bool(summary["all_checks_passed"]):
        raise RuntimeError(f"auxiliary Southampton checks failed: {summary['failed_checks']}")
    return {
        "dataset_id": config.dataset_id,
        "scientific_label": config.label,
        "record_count": len(dataset.records),
        "records_per_priority": config.records_per_priority,
        "seed": config.seed,
        "data_paths": [path.as_posix() for path in data_paths],
        "summary_path": summary_path.as_posix(),
        "figure_paths": [path.as_posix() for path in figure_paths],
        "all_auxiliary_checks_passed": True,
        "algorithm_input_compatible": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(run_generation(arguments.config), sort_keys=True))


if __name__ == "__main__":
    main()
