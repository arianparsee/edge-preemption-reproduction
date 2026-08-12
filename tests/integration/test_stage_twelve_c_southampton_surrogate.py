import csv
from hashlib import sha256
from pathlib import Path

from edge_reproduction.datasets.southampton_surrogate import (
    RECORDS_PER_PRIORITY,
    SCIENTIFIC_LABEL,
    SouthamptonSurrogateConfig,
    generate_southampton_surrogate,
)
from edge_reproduction.datasets.southampton_surrogate_artifacts import (
    write_surrogate_artifacts,
)
from edge_reproduction.datasets.southampton_surrogate_diagnostics import (
    summarize_surrogate,
    write_qualitative_figures,
)


def config() -> SouthamptonSurrogateConfig:
    return SouthamptonSurrogateConfig(
        dataset_id="integration-southampton-surrogate",
        label=SCIENTIFIC_LABEL,
        seed=20240812,
        records_per_priority=RECORDS_PER_PRIORITY,
        digitized_components_path=(
            "data/interim/digitized/southampton_histograms_arxiv_v2/visible_components.csv"
        ),
        digitization_manifest_path=(
            "data/interim/digitized/southampton_histograms_arxiv_v2/digitization_manifest.json"
        ),
        published_figures_directory="data/raw/published_figures/arxiv_v2",
    )


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_stage_twelve_c_artifacts_are_separated_and_byte_reproducible(
    tmp_path: Path,
) -> None:
    dataset, supports = generate_southampton_surrogate(config())
    first_paths = write_surrogate_artifacts(dataset, tmp_path / "generated-first")
    second_paths = write_surrogate_artifacts(dataset, tmp_path / "generated-second")

    assert [file_hash(path) for path in first_paths] == [file_hash(path) for path in second_paths]
    with first_paths[0].open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == [
            "surrogate_id",
            "priority",
            "storage_gb",
            "deadline_hours",
        ]
        assert sum(1 for _ in reader) == 30_000
    summary = summarize_surrogate(dataset, supports)
    assert summary["all_checks_passed"] is True


def test_stage_twelve_c_writes_two_png_and_two_svg_qualitative_figures(
    tmp_path: Path,
) -> None:
    dataset, supports = generate_southampton_surrogate(config())
    paths = write_qualitative_figures(
        dataset,
        supports,
        published_figures_directory=Path("data/raw/published_figures/arxiv_v2"),
        output_directory=tmp_path / "qualitative-figures",
    )

    assert len(paths) == 4
    assert {path.suffix for path in paths} == {".png", ".svg"}
    assert all(path.stat().st_size > 10_000 for path in paths)
