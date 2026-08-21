"""Download GitHub Actions artifacts with explicit pagination and safe extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

TRANSIENT_HTTP_STATUS = {408, 429, 500, 502, 503, 504}


def _request_bytes(url: str, token: str, *, allow_retry: bool = True) -> tuple[bytes, int]:
    """Fetch one URL, retrying a transient transport failure exactly once."""

    attempts = 2 if allow_retry else 1
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "edge-reproduction-stage15h",
            },
        )
        # Do not forward the bearer token to the signed storage redirect target.
        request.add_unredirected_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
                return response.read(), attempt
        except urllib.error.HTTPError as exc:
            if exc.code not in TRANSIENT_HTTP_STATUS or attempt == attempts - 1:
                raise
        except urllib.error.URLError:
            if attempt == attempts - 1:
                raise
        time.sleep(2)
    raise AssertionError("unreachable retry state")


def _list_run_artifacts(
    *, repository: str, run_id: int, token: str
) -> tuple[list[dict[str, Any]], int]:
    """Return every artifact from every REST page for one immutable run ID."""

    artifacts: list[dict[str, Any]] = []
    retries = 0
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/artifacts"
            f"?per_page=100&page={page}"
        )
        payload, page_retries = _request_bytes(url, token, allow_retry=retries == 0)
        retries += page_retries
        document = json.loads(payload)
        rows = document.get("artifacts")
        if not isinstance(rows, list):
            raise ValueError("GitHub artifact response has no artifact list")
        artifacts.extend(rows)
        if len(rows) < 100:
            break
        page += 1
    return artifacts, retries


def _select_artifacts(
    artifacts: list[dict[str, Any]],
    *,
    exact_name: str | None,
    name_prefix: str | None,
    name_suffix: str,
) -> list[dict[str, Any]]:
    """Select either one exact artifact or all artifacts matching fixed affixes."""

    if (exact_name is None) == (name_prefix is None):
        raise ValueError("provide exactly one of exact_name or name_prefix")
    selected = []
    for artifact in artifacts:
        name = artifact.get("name")
        if not isinstance(name, str):
            continue
        matches = name == exact_name if exact_name is not None else (
            name.startswith(str(name_prefix)) and name.endswith(name_suffix)
        )
        if matches:
            if artifact.get("expired") is True:
                raise ValueError(f"required artifact is expired: {name}")
            selected.append(artifact)
    names = [str(item["name"]) for item in selected]
    if len(names) != len(set(names)):
        raise ValueError("duplicate artifact name in selected run")
    return sorted(selected, key=lambda item: str(item["name"]))


def _safe_extract(archive: Path, destination: Path) -> None:
    """Extract a ZIP while rejecting traversal, links, and duplicate members."""

    destination.mkdir(parents=True, exist_ok=False)
    root = destination.resolve()
    seen: set[str] = set()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            pure = PurePosixPath(member.filename)
            if pure.is_absolute() or ".." in pure.parts or member.filename in seen:
                raise ValueError("unsafe or duplicate artifact ZIP member")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("symbolic links are forbidden in artifact ZIPs")
            target = (destination / Path(*pure.parts)).resolve()
            if root != target and root not in target.parents:
                raise ValueError("artifact ZIP member escapes destination")
            seen.add(member.filename)
        bundle.extractall(destination)


def _download_selected(
    *,
    selected: list[dict[str, Any]],
    output: Path,
    token: str,
    retry_available: bool,
    expected_archive_sha256: str | None = None,
) -> tuple[list[dict[str, object]], int]:
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    retries = 0
    for artifact in selected:
        artifact_id = int(artifact["id"])
        name = str(artifact["name"])
        url = str(artifact["archive_download_url"])
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise ValueError("unexpected artifact download host")
        payload, download_retries = _request_bytes(
            url,
            token,
            allow_retry=retry_available and retries == 0,
        )
        retries += download_retries
        digest = hashlib.sha256(payload).hexdigest()
        if expected_archive_sha256 is not None and digest != expected_archive_sha256:
            raise ValueError(f"pinned artifact digest mismatch: {name}")
        expected_digest = artifact.get("digest")
        if expected_digest is not None and expected_digest != f"sha256:{digest}":
            raise ValueError(f"artifact digest mismatch: {name}")
        archive = output / f".{artifact_id}.zip"
        archive.write_bytes(payload)
        try:
            _safe_extract(archive, output / name)
        finally:
            archive.unlink(missing_ok=True)
        records.append(
            {
                "artifact_id": artifact_id,
                "name": name,
                "archive_sha256": digest,
                "github_digest_checked": expected_digest is not None,
                "size_bytes": len(payload),
            }
        )
    return records, retries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--exact-name")
    selector.add_argument("--name-prefix")
    parser.add_argument("--name-suffix", default="")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--expected-archive-sha256")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if len(args.repository.split("/")) != 2 or any(
        not part.replace("-", "").replace("_", "").replace(".", "").isalnum()
        for part in args.repository.split("/")
    ):
        raise ValueError("repository must be an owner/name pair")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is required")
    if args.expected_archive_sha256 is not None:
        if args.exact_name is None:
            raise ValueError("a pinned archive digest requires exact-name selection")
        if len(args.expected_archive_sha256) != 64 or any(
            character not in "0123456789abcdef"
            for character in args.expected_archive_sha256
        ):
            raise ValueError("expected archive SHA-256 must be 64 lowercase hex characters")
    artifacts, listing_retries = _list_run_artifacts(
        repository=args.repository, run_id=args.run_id, token=token
    )
    selected = _select_artifacts(
        artifacts,
        exact_name=args.exact_name,
        name_prefix=args.name_prefix,
        name_suffix=args.name_suffix,
    )
    if args.exact_name is not None and len(selected) != 1:
        raise ValueError("exactly one matching artifact is required")
    if not selected and not args.allow_empty:
        raise ValueError("no matching artifact found")
    records, download_retries = _download_selected(
        selected=selected,
        output=args.output,
        token=token,
        retry_available=listing_retries == 0,
        expected_archive_sha256=args.expected_archive_sha256,
    )
    report = {
        "schema_version": "github-paginated-artifact-download-v1",
        "repository": args.repository,
        "run_id": args.run_id,
        "artifact_count": len(records),
        "technical_retry_count": listing_retries + download_retries,
        "pinned_archive_sha256_enforced": args.expected_archive_sha256 is not None,
        "artifacts": records,
        "token_recorded": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "validated", "artifact_count": len(records)}))


if __name__ == "__main__":
    main()
