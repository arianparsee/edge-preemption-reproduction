"""Run a command with at most one allow-listed transient technical retry."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TRANSIENT = (
    "connection reset",
    "temporarily unavailable",
    "temporary failure",
    "tls handshake timeout",
    "http 502",
    "http 503",
    "service unavailable",
)
SCIENTIFIC = (
    "invariant",
    "config mismatch",
    "workload hash mismatch",
    "result hash mismatch",
    "invalid result",
    "assertionerror",
    "valueerror",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("command is required")
    attempts: list[dict[str, object]] = []
    for index in range(2):
        process = subprocess.run(
            command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
        sys.stdout.write(process.stdout)
        lower = process.stdout.lower()
        transient = any(token in lower for token in TRANSIENT)
        scientific = any(token in lower for token in SCIENTIFIC)
        attempts.append(
            {
                "attempt": index + 1,
                "returncode": process.returncode,
                "transient_allowlist_match": transient,
                "scientific_stop_match": scientific,
            }
        )
        if process.returncode == 0:
            status = "succeeded"
            break
        if index == 0 and transient and not scientific:
            continue
        status = "failed_without_retry" if index == 0 else "failed_after_one_retry"
        break
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(
        json.dumps(
            {
                "schema_version": "technical-retry-v1",
                "status": status,
                "maximum_retries": 1,
                "attempts": attempts,
                "command": command,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if status != "succeeded":
        # 75 is a temporary technical failure after its single allowed retry.
        # 65 is a permanent/scientific/config/unknown failure: never retry it.
        raise SystemExit(
            75
            if attempts[-1]["transient_allowlist_match"]
            and not attempts[-1]["scientific_stop_match"]
            else 65
        )


if __name__ == "__main__":
    main()
