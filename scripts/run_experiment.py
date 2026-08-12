"""Run one resolved auxiliary experiment config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.orchestration import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    outcome = run_experiment(arguments.config, resume=arguments.resume)
    print(json.dumps(outcome.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
