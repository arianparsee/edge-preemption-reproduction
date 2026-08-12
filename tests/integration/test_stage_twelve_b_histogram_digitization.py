from hashlib import sha256
from pathlib import Path

from edge_reproduction.datasets.histogram_digitization import digitize_sources


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_digitization_artifacts_are_reproducible_and_source_specific(tmp_path: Path) -> None:
    source = Path("data/raw/published_figures/arxiv_v2")
    first = digitize_sources(source, tmp_path / "first-data", tmp_path / "first-figures")
    second = digitize_sources(source, tmp_path / "second-data", tmp_path / "second-figures")

    assert first["component_count"] == second["component_count"]
    assert first["component_counts_by_figure"] == second["component_counts_by_figure"]
    assert first["storage_computation_identical_below_title"] is True
    assert hash_file(tmp_path / "first-data" / "visible_components.csv") == hash_file(
        tmp_path / "second-data" / "visible_components.csv"
    )
    assert hash_file(tmp_path / "first-data" / "digitization_manifest.json") == hash_file(
        tmp_path / "second-data" / "digitization_manifest.json"
    )
    assert len(tuple((tmp_path / "first-figures").glob("*.png"))) == 3
