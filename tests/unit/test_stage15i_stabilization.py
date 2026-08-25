from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from stabilize_stage15i_artifact import (
    _validate_delivery,
    _validate_download_report,
    _validate_inner_manifest,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stage15i_delivery_and_inner_checksum_validation(tmp_path: Path) -> None:
    payload = tmp_path / "payload.csv"
    payload.write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "checksum_manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "name": payload.name,
                        "bytes": payload.stat().st_size,
                        "sha256": _hash(payload),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    delivery_files = (payload, tmp_path / "checksum_manifest.json")
    (tmp_path / "stage15i_delivery.sha256").write_text(
        "".join(f"{_hash(path)}  stage15h-final/{path.name}\n" for path in delivery_files),
        encoding="utf-8",
    )
    assert _validate_inner_manifest(tmp_path) == 1
    assert _validate_delivery(tmp_path) == 2

    payload.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        _validate_delivery(tmp_path)


def test_stage15i_download_report_requires_github_digest(tmp_path: Path) -> None:
    report = tmp_path / "download.json"
    document = {
        "run_id": 10,
        "artifact_count": 1,
        "token_recorded": False,
        "pinned_archive_sha256_enforced": True,
        "artifacts": [{"github_digest_checked": True}],
    }
    report.write_text(json.dumps(document), encoding="utf-8")
    assert _validate_download_report(report, run_id=10, artifact_count=1, pinned=True)

    document["artifacts"][0]["github_digest_checked"] = False
    report.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        _validate_download_report(report, run_id=10, artifact_count=1, pinned=True)
