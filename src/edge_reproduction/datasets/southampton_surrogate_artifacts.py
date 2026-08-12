"""Deterministic artifacts for the approximate Southampton surrogate."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from edge_reproduction.datasets.southampton_surrogate import SouthamptonSurrogateDataset


def write_surrogate_artifacts(
    dataset: SouthamptonSurrogateDataset, output_directory: Path
) -> tuple[Path, Path]:
    """Write the four-column surrogate and complete provenance metadata."""

    output_directory.mkdir(parents=True, exist_ok=True)
    records_path = output_directory / "surrogate_records.csv"
    metadata_path = output_directory / "metadata.json"
    with records_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("surrogate_id", "priority", "storage_gb", "deadline_hours"),
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(record.as_dict() for record in dataset.records)
    metadata_path.write_text(
        json.dumps(dataset.metadata(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return records_path, metadata_path
