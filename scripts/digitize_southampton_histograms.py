"""Digitize visible colored components from arXiv v2 Southampton histograms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.datasets.histogram_digitization import digitize_sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data/raw/published_figures/arxiv_v2"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/interim/digitized/southampton_histograms_arxiv_v2"),
    )
    parser.add_argument(
        "--diagnostics-dir",
        type=Path,
        default=Path("figures/diagnostics/stage12b"),
    )
    arguments = parser.parse_args()
    result = digitize_sources(
        arguments.source_dir,
        arguments.output_dir,
        arguments.diagnostics_dir,
    )
    serializable_result = dict(result)
    serializable_result["component_path"] = str(result["component_path"])
    serializable_result["manifest_path"] = str(result["manifest_path"])
    print(json.dumps(serializable_result, sort_keys=True))


if __name__ == "__main__":
    main()
