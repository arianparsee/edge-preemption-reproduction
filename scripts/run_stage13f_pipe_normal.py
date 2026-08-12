"""Run one isolated policy/workload pair from the materialized full matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from edge_reproduction.experiments.pipe_normal_full import POLICY_NAMES, run_full_pair

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--workload-seed", type=int, required=True)
    parser.add_argument("--policy", choices=POLICY_NAMES, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    outcome = run_full_pair(
        args.config,
        workload_seed=args.workload_seed,
        policy_name=args.policy,
        resume=args.resume,
    )
    print(json.dumps({"status": outcome.status, "result": outcome.result_path.as_posix()}))
