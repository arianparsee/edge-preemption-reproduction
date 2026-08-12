from pathlib import Path

import pytest

from edge_reproduction.datasets.histogram_digitization import (
    COMMON_RESOURCE_CALIBRATION,
    DEADLINE_CALIBRATION,
    EXPECTED_SOURCE_HASHES,
    FIGURE_SPECS,
    digitize_figure,
    validate_source,
)


def test_axis_calibrations_reproduce_published_tick_endpoints() -> None:
    assert COMMON_RESOURCE_CALIBRATION.x_value(103) == pytest.approx(0.0)
    assert COMMON_RESOURCE_CALIBRATION.x_value(518) == pytest.approx(2500.0)
    assert COMMON_RESOURCE_CALIBRATION.y_value(427) == pytest.approx(0.0)
    assert COMMON_RESOURCE_CALIBRATION.y_value(78) == pytest.approx(0.010)
    assert DEADLINE_CALIBRATION.x_value(99) == pytest.approx(0.0)
    assert DEADLINE_CALIBRATION.x_value(553) == pytest.approx(120.0)
    assert DEADLINE_CALIBRATION.y_value(96) == pytest.approx(0.12)


def test_source_hash_mismatch_fails_fast(tmp_path: Path) -> None:
    path = tmp_path / "source.png"
    path.write_bytes(b"not a source image")

    with pytest.raises(ValueError, match="source hash mismatch"):
        validate_source(path, "0" * 64)


def test_visible_components_keep_published_units_and_labels() -> None:
    source_directory = Path("data/raw/published_figures/arxiv_v2")
    records = digitize_figure(source_directory / FIGURE_SPECS[0].filename, FIGURE_SPECS[0])

    assert records
    assert {record.priority for record in records} == {"low", "medium", "high"}
    assert {record.x_unit_as_published for record in records} == {"Gigabytes"}
    assert all(record.probability_top_approx >= 0.0 for record in records)
    assert EXPECTED_SOURCE_HASHES[FIGURE_SPECS[0].filename]
