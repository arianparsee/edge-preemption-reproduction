"""Run the bounded Stage-13B auxiliary execution registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.orchestration import run_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_registry(arguments.registry, resume=arguments.resume),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
