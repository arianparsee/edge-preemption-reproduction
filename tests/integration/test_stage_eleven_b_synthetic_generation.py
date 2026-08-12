from hashlib import sha256
from pathlib import Path

from edge_reproduction.datasets.artifacts import write_dataset_artifacts
from edge_reproduction.datasets.diagnostics import (
    summarize_dataset,
    write_diagnostic_figures,
)
from edge_reproduction.datasets.synthetic import (
    SyntheticGenerationConfig,
    generate_synthetic,
)


def config(kind: str) -> SyntheticGenerationConfig:
    return SyntheticGenerationConfig(
        dataset_id=f"integration-{kind}",
        label="auxiliary_test",
        workload_kind=kind,  # type: ignore[arg-type]
        seed=20240811,
        arrival_slots=102,
        drain_slots=0,
    )


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_written_normal_artifacts_are_byte_reproducible(tmp_path: Path) -> None:
    dataset = generate_synthetic(config("normal"))

    first_paths = write_dataset_artifacts(dataset, tmp_path / "first")
    second_paths = write_dataset_artifacts(dataset, tmp_path / "second")

    assert [path.name for path in first_paths] == [path.name for path in second_paths]
    assert [file_hash(path) for path in first_paths] == [file_hash(path) for path in second_paths]
    assert first_paths[1].read_text(encoding="utf-8").count("\n") == 1411


def test_statistical_diagnostics_pass_and_bimodal_quota_is_exact() -> None:
    normal = summarize_dataset(generate_synthetic(config("normal")))
    bimodal = summarize_dataset(generate_synthetic(config("bimodal")))

    assert normal["all_eligible_checks_passed"] is True
    assert normal["failed_checks"] == []
    assert bimodal["all_eligible_checks_passed"] is True
    assert bimodal["mixture"] == {
        "low_count": 1269,
        "high_count": 141,
        "low_fraction": 0.9,
        "high_fraction": 0.1,
        "exact_90_10": True,
    }


def test_auxiliary_diagnostic_figures_are_written_in_png_and_svg(tmp_path: Path) -> None:
    paths = write_diagnostic_figures(generate_synthetic(config("normal")), tmp_path / "figures")

    assert len(paths) == 6
    assert {path.suffix for path in paths} == {".png", ".svg"}
    assert all(path.stat().st_size > 1_000 for path in paths)
