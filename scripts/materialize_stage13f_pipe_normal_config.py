"""Materialize the complete Stage-13F seed matrix before execution."""

from __future__ import annotations

from pathlib import Path

from edge_reproduction.experiments.pipe_normal_full import write_materialized_config

if __name__ == "__main__":
    write_materialized_config(Path("configs/experiments/pipe_normal_full_stage13f.json"))
