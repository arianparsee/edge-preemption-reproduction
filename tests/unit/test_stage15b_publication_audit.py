from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _script() -> ModuleType:
    path = ROOT / "scripts/audit_stage15b_publication.py"
    spec = importlib.util.spec_from_file_location("stage15b_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load publication audit")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_publication_audit_accepts_small_sanitized_source(tmp_path: Path) -> None:
    module = _script()
    source = tmp_path / "docs/report.md"
    source.parent.mkdir()
    source.write_text("sanitized auxiliary report\n", encoding="utf-8")

    report = module.audit(tmp_path, ["docs/report.md"])

    assert report["status"] == "passed"
    assert report["files"][0]["path"] == "docs/report.md"


@pytest.mark.parametrize(
    ("path", "content"),
    [
        ("results/raw.json", "{}"),
        ("docs/output.pdf", "not really a pdf"),
        ("docs/report.md", "github_" + "pat_" + "abcdefghijklmnopqrstuvwxyz123456"),
        ("docs/report.md", "C:" + "\\Users\\named-user\\private.txt"),
    ],
)
def test_publication_audit_rejects_forbidden_content(
    tmp_path: Path, path: str, content: str
) -> None:
    module = _script()
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="publication audit failed"):
        module.audit(tmp_path, [path])
