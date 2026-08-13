"""Fail-closed security audit for the exact Stage 15-B publication file set."""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path

FORBIDDEN_SUFFIXES = {
    ".env",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip",
    ".tar",
    ".gz",
    ".db",
    ".sqlite",
}
FORBIDDEN_PARTS = {"data", "results", "figures", "tmp", "backups", ".venv"}
SENSITIVE_PATTERNS = {
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "windows_personal_path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    "unix_home_path": re.compile("/" + r"home/[^/\s]+/"),
    "github_secret_expression": re.compile(r"\$\{\{\s*secrets\."),
}


def audit(project_root: Path, relative_paths: list[str]) -> dict[str, object]:
    """Audit only the explicit publication set and return its hash inventory."""

    if not relative_paths:
        raise ValueError("publication set must not be empty")
    inventory: list[dict[str, object]] = []
    violations: list[str] = []
    for raw_path in sorted(set(relative_paths)):
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            violations.append(f"unsafe_path:{raw_path}")
            continue
        path = project_root / relative
        if not path.is_file():
            violations.append(f"missing:{raw_path}")
            continue
        lowered_parts = {part.lower() for part in relative.parts}
        if lowered_parts & FORBIDDEN_PARTS:
            violations.append(f"forbidden_directory:{raw_path}")
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES or relative.name.lower().startswith(
            ".env"
        ):
            violations.append(f"forbidden_file_type:{raw_path}")
        size = path.stat().st_size
        if size > 500_000:
            violations.append(f"oversized:{raw_path}:{size}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            violations.append(f"non_utf8_or_binary:{raw_path}")
            continue
        for name, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{name}:{raw_path}")
        inventory.append(
            {
                "path": relative.as_posix(),
                "bytes": size,
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
        )
    if violations:
        raise ValueError("publication audit failed: " + ", ".join(violations))
    return {
        "schema_version": "stage15b-publication-audit-v1",
        "status": "passed",
        "files": inventory,
        "checks": {
            "secret_or_token_patterns": "passed",
            "credential_and_private_key_patterns": "passed",
            "personal_absolute_paths": "passed",
            "env_files": "absent",
            "raw_data_directories": "absent",
            "pdf_or_image_files": "absent",
            "large_files_over_500000_bytes": "absent",
            "workflow_secret_references": "absent",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.project_root.resolve(), args.file)
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite audit report: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    files = report["files"]
    if not isinstance(files, list):
        raise TypeError("audit files inventory must be a list")
    print(json.dumps({"status": "passed", "files": len(files)}))


if __name__ == "__main__":
    main()
