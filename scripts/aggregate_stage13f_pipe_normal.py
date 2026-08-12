"""Aggregate Stage-13F only when all 120 raw results are present."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.pipe_normal_full import aggregate_complete_full_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(aggregate_complete_full_run(args.config), indent=2, sort_keys=True))
