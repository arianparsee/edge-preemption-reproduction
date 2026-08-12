"""Execute the bounded Stage-13D temporal smoke and preserve its raw JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.temporal_smoke import run_temporal_smoke


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {arguments.output}")
    result = run_temporal_smoke(arguments.config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "succeeded", "output": arguments.output.as_posix()}))


if __name__ == "__main__":
    main()
