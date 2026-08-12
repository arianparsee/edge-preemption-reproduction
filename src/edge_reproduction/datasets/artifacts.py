"""Deterministic CSV and JSON serialization for synthetic datasets."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from edge_reproduction.datasets.synthetic import SyntheticDataset


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_dataset_artifacts(dataset: SyntheticDataset, output_directory: Path) -> tuple[Path, ...]:
    """Write stable table-faithful dataset artifacts."""

    output_directory.mkdir(parents=True, exist_ok=True)
    server_path = output_directory / "servers.csv"
    task_path = output_directory / "tasks.csv"
    arrivals_path = output_directory / "arrival_counts.csv"
    metadata_path = output_directory / "metadata.json"

    server_rows = [item.as_dict() for item in dataset.servers]
    task_rows = [item.as_dict() for item in dataset.tasks]
    arrival_rows = [
        {
            "arrival_slot": slot,
            "raw_draw": dataset.arrival_raw_draws[slot],
            "job_count": dataset.arrival_counts[slot],
        }
        for slot in range(dataset.config.arrival_slots)
    ]
    _write_csv(server_path, server_rows, tuple(server_rows[0]))
    _write_csv(task_path, task_rows, tuple(task_rows[0]))
    _write_csv(
        arrivals_path,
        arrival_rows,
        ("arrival_slot", "raw_draw", "job_count"),
    )
    metadata_path.write_text(
        json.dumps(dataset.metadata(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return server_path, task_path, arrivals_path, metadata_path
