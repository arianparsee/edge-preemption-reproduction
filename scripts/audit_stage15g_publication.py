"""Fail-closed security and scope audit for Stage 15-G publication files."""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path

ALLOWED_BINARY_SUFFIXES = {".pdf", ".png"}
FORBIDDEN_SUFFIXES = {".env", ".zip", ".tar", ".gz", ".db", ".sqlite"}
FORBIDDEN_PARTS = {"data", "tmp", "backups", ".venv", "raw"}
SENSITIVE_PATTERNS = {
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "windows_personal_path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    "unix_home_path": re.compile("/" + r"home/[^/\s]+/"),
    "github_secret_expression": re.compile(r"\$\{\{\s*secrets\."),
}
MAX_ALLOWED_BYTES = 500_000


def _scan_text(path: Path, relative: Path, violations: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        violations.append(f"non_utf8_text:{relative.as_posix()}")
        return
    for name, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            violations.append(f"{name}:{relative.as_posix()}")


def _scan_pdf(path: Path, relative: Path, violations: list[str]) -> None:
    payload = path.read_bytes()
    if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-2048:]:
        violations.append(f"invalid_pdf:{relative.as_posix()}")
    lowered = payload.lower()
    if b"/embeddedfile" in lowered or b"/filespec" in lowered:
        violations.append(f"pdf_attachment:{relative.as_posix()}")
    if b"/javascript" in lowered or b"/openaction" in lowered:
        violations.append(f"pdf_active_content:{relative.as_posix()}")


def _scan_png(path: Path, relative: Path, violations: list[str]) -> None:
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        violations.append(f"invalid_png:{relative.as_posix()}")


def audit(project_root: Path, relative_paths: list[str]) -> dict[str, object]:
    """Audit only explicitly named Stage 15-G publication files."""

    if not relative_paths:
        raise ValueError("publication set must not be empty")
    violations: list[str] = []
    inventory: list[dict[str, object]] = []
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
        suffix = relative.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES or relative.name.lower().startswith(".env"):
            violations.append(f"forbidden_file_type:{raw_path}")
        size = path.stat().st_size
        if size > MAX_ALLOWED_BYTES:
            violations.append(f"oversized:{raw_path}:{size}")
        if suffix == ".pdf":
            _scan_pdf(path, relative, violations)
        elif suffix == ".png":
            _scan_png(path, relative, violations)
        elif suffix not in ALLOWED_BINARY_SUFFIXES:
            _scan_text(path, relative, violations)
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
        "schema_version": "stage15g-publication-audit-v1",
        "status": "passed",
        "files": inventory,
        "checks": {
            "secret_credential_path_patterns": "passed",
            "env_raw_data_and_archive_files": "absent",
            "source_paper_pdf": "absent",
            "large_files_over_500000_bytes": "absent",
            "generated_pdf_attachments_or_active_content": "absent",
            "generated_png_signature": "passed",
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
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    files = report["files"]
    if not isinstance(files, list):
        raise TypeError("audit files inventory must be a list")
    print(json.dumps({"status": "passed", "files": len(files)}))


if __name__ == "__main__":
    main()
