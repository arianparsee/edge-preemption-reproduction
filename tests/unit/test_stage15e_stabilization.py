from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path("scripts/stabilize_stage15e_artifacts.py")


def _load_script() -> object:
    sys.path.insert(0, str(SCRIPT.parent.resolve()))
    spec = importlib.util.spec_from_file_location("stabilize_stage15e", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage 15-E stabilizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stabilizer_requires_exactly_sixteen_new_pairs(tmp_path: Path) -> None:
    module = _load_script()
    output = tmp_path / "manifest.json"

    with pytest.raises(ValueError, match="expected 16 new pair JSON files"):
        module.stabilize(
            artifact_root=tmp_path,
            seed_one_fixture=Path("tests/fixtures/stage15e_seed_one_reuse.json"),
            baseline_fixture=Path("tests/fixtures/stage15e_reused_baselines.json"),
            run_id=1,
            output_manifest=output,
        )

    assert not output.exists()


def test_stabilizer_refuses_to_overwrite_manifest(tmp_path: Path) -> None:
    module = _load_script()
    output = tmp_path / "manifest.json"
    output.write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        module.stabilize(
            artifact_root=tmp_path,
            seed_one_fixture=Path("tests/fixtures/stage15e_seed_one_reuse.json"),
            baseline_fixture=Path("tests/fixtures/stage15e_reused_baselines.json"),
            run_id=1,
            output_manifest=output,
        )

    assert output.read_text(encoding="utf-8") == "preserve"
