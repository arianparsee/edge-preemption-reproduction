"""Run the Stage-10J common auxiliary four-policy regression."""

from __future__ import annotations

import json
from pathlib import Path

from edge_reproduction.experiments.four_policy_smoke import run_four_policy_smoke

CONFIG_PATH = Path("configs/stage10j_four_policy_regression.json")
OUTPUT_PATH = Path("results/raw/stage10j/four_policy_regression.json")


def run_regression(config_path: Path = CONFIG_PATH) -> dict[str, object]:
    """Run all four policies independently on one unchanged state."""

    raw: object = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("regression config must be a JSON object")
    smoke = run_four_policy_smoke(config_path, expected_seed=int(raw["seed"]))
    return {
        "label": smoke["scenario_label"],
        "baseline": smoke["baseline"],
        "config_path": config_path.as_posix(),
        "seed": smoke["seed"],
        "requesting_task_ids": smoke["requesting_task_ids"],
        "initial_active_task_ids": smoke["initial_active_task_ids"],
        "metric_warning": smoke["metric_warning"],
        "records": smoke["records"],
    }


def main() -> None:
    result = run_regression()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"output_path={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
