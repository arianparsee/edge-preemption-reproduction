"""Always write a batch inventory, then validate a complete Stage-13J batch."""

from __future__ import annotations

import argparse
import csv
import json
from hashlib import sha256
from pathlib import Path

from record_stage13j_batch import record_batch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--batch-plan", type=Path, required=True)
    parser.add_argument("--batch", type=int, choices=range(1, 6), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(path for path in args.root.rglob("*") if path.is_file())
    args.inventory.parent.mkdir(parents=True, exist_ok=True)
    if args.inventory.exists() or args.output.exists():
        raise FileExistsError("batch validation outputs already exist")
    with args.inventory.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("path", "bytes", "sha256"))
        writer.writeheader()
        for path in files:
            writer.writerow(
                {
                    "path": path.relative_to(args.root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                }
            )
    try:
        result = record_batch(
            root=args.root, config_path=args.config, plan_path=args.batch_plan, batch=args.batch
        )
    except Exception as error:
        retry_metadata = []
        for path in sorted(args.root.glob("**/*retry*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            retry_metadata.append(value)
        failed_metadata = [value for value in retry_metadata if value.get("status") != "succeeded"]
        scientific_failure = any(
            not bool(value.get("attempts"))
            or bool(value["attempts"][-1].get("scientific_stop_match"))
            or not bool(value["attempts"][-1].get("transient_allowlist_match"))
            for value in failed_metadata
        )
        complete_result_count = len(list(args.root.glob("**/result.json")))
        technical_only = (
            complete_result_count < 20 and bool(failed_metadata) and not scientific_failure
        )
        result = {
            "schema_version": "stage13j-batch-validation-failure-v1",
            "status": (
                "incomplete_transient_technical_failure"
                if technical_only
                else "invalid_or_incomplete"
            ),
            "technical_failure_only": technical_only,
            "batch": args.batch,
            "error_type": type(error).__name__,
            "error": str(error),
            "inventory_file_count": len(files),
            "retry_metadata": retry_metadata,
        }
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if technical_only:
            print(json.dumps({"status": result["status"], "batch": args.batch}))
            return
        raise
    result["status"] = "validated"
    result["inventory_file_count"] = len(files)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "validated", "batch": args.batch, "pairs": 20}))


if __name__ == "__main__":
    main()
