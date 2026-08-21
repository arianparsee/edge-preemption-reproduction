from __future__ import annotations

import json
import urllib.parse
import zipfile
from pathlib import Path

import download_github_run_artifacts
import pytest
from download_github_run_artifacts import (
    _download_selected,
    _list_run_artifacts,
    _safe_extract,
    _select_artifacts,
)


def test_pinned_archive_digest_is_checked_before_extraction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_request(
        url: str, token: str, *, allow_retry: bool = True
    ) -> tuple[bytes, int]:
        assert url.startswith("https://api.github.com/")
        assert token == "masked-token"
        assert allow_retry is True
        return b"not-the-pinned-archive", 0

    monkeypatch.setattr(download_github_run_artifacts, "_request_bytes", fake_request)
    selected = [
        {
            "id": 7,
            "name": "pinned-reuse",
            "archive_download_url": "https://api.github.com/repos/o/r/actions/artifacts/7/zip",
            "digest": None,
        }
    ]

    with pytest.raises(ValueError, match="pinned artifact digest mismatch"):
        _download_selected(
            selected=selected,
            output=tmp_path / "output",
            token="masked-token",
            retry_available=True,
            expected_archive_sha256="0" * 64,
        )

    assert not (tmp_path / "output" / "pinned-reuse").exists()


def test_list_run_artifacts_fetches_the_second_page(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(url: str, token: str, *, allow_retry: bool = True) -> tuple[bytes, int]:
        calls.append(url)
        assert token == "masked-token"
        assert allow_retry is True
        page = int(urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["page"][0])
        start = 0 if page == 1 else 100
        count = 100 if page == 1 else 8
        payload = {
            "artifacts": [
                {"id": index, "name": f"artifact-{index}", "expired": False}
                for index in range(start, start + count)
            ]
        }
        return json.dumps(payload).encode(), 0

    monkeypatch.setattr(download_github_run_artifacts, "_request_bytes", fake_request)

    artifacts, retries = _list_run_artifacts(
        repository="owner/repository",
        run_id=42,
        token="masked-token",
    )

    assert len(artifacts) == 108
    assert retries == 0
    assert len(calls) == 2


def test_select_artifact_can_find_an_exact_name_after_the_first_hundred() -> None:
    artifacts = [
        {"id": index, "name": f"artifact-{index}", "expired": False}
        for index in range(108)
    ]
    selected = _select_artifacts(
        artifacts,
        exact_name="artifact-107",
        name_prefix=None,
        name_suffix="",
    )
    assert [row["id"] for row in selected] == [107]


def test_select_artifacts_uses_fixed_prefix_and_suffix() -> None:
    artifacts = [
        {"id": 1, "name": "stage15h-pair-a-42", "expired": False},
        {"id": 2, "name": "stage15h-pair-b-42", "expired": False},
        {"id": 3, "name": "stage15h-pair-c-41", "expired": False},
    ]
    selected = _select_artifacts(
        artifacts,
        exact_name=None,
        name_prefix="stage15h-pair-",
        name_suffix="-42",
    )
    assert [row["id"] for row in selected] == [1, 2]


def test_safe_extract_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "forbidden")
    with pytest.raises(ValueError, match="unsafe"):
        _safe_extract(archive, tmp_path / "output")
