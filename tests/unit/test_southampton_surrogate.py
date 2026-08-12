import shutil
from pathlib import Path

import pytest

from edge_reproduction.datasets.southampton_surrogate import (
    RECORDS_PER_PRIORITY,
    SCIENTIFIC_LABEL,
    SouthamptonSurrogateConfig,
    generate_southampton_surrogate,
    load_visible_supports,
)
from edge_reproduction.datasets.southampton_surrogate_diagnostics import (
    summarize_surrogate,
)


def config(*, seed: int = 20240812) -> SouthamptonSurrogateConfig:
    return SouthamptonSurrogateConfig(
        dataset_id="unit-southampton-surrogate",
        label=SCIENTIFIC_LABEL,
        seed=seed,
        records_per_priority=RECORDS_PER_PRIORITY,
        digitized_components_path=(
            "data/interim/digitized/southampton_histograms_arxiv_v2/visible_components.csv"
        ),
        digitization_manifest_path=(
            "data/interim/digitized/southampton_histograms_arxiv_v2/digitization_manifest.json"
        ),
        published_figures_directory="data/raw/published_figures/arxiv_v2",
    )


def test_config_requires_approved_count_label_and_seed_type() -> None:
    with pytest.raises(ValueError, match="records_per_priority must be 10000"):
        SouthamptonSurrogateConfig(
            **(config().as_dict() | {"records_per_priority": 9999})  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="label must be"):
        SouthamptonSurrogateConfig(
            **(config().as_dict() | {"label": "real-trace"})  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="seed must be an integer"):
        SouthamptonSurrogateConfig(
            **(config().as_dict() | {"seed": True})  # type: ignore[arg-type]
        )


def test_visible_support_loader_omits_duplicated_computation() -> None:
    supports = load_visible_supports(
        Path("data/interim/digitized/southampton_histograms_arxiv_v2/visible_components.csv")
    )

    assert len(supports) == 23
    assert {item.resource for item in supports} == {"storage", "deadline"}
    assert all(item.pixel_count > 0 and item.lower <= item.upper for item in supports)


def test_changed_published_figure_fails_fast(tmp_path: Path) -> None:
    components = tmp_path / "visible_components.csv"
    manifest = tmp_path / "digitization_manifest.json"
    figures = tmp_path / "figures"
    figures.mkdir()
    shutil.copyfile(
        "data/interim/digitized/southampton_histograms_arxiv_v2/visible_components.csv",
        components,
    )
    shutil.copyfile(
        "data/interim/digitized/southampton_histograms_arxiv_v2/digitization_manifest.json",
        manifest,
    )
    source_figures = Path("data/raw/published_figures/arxiv_v2")
    for source in source_figures.glob("*.png"):
        shutil.copyfile(source, figures / source.name)
    (figures / "trace_storage_distribution.png").write_bytes(b"changed")
    changed_config = SouthamptonSurrogateConfig(
        dataset_id="changed-source",
        label=SCIENTIFIC_LABEL,
        seed=1,
        records_per_priority=RECORDS_PER_PRIORITY,
        digitized_components_path=components.name,
        digitization_manifest_path=manifest.name,
        published_figures_directory=figures.name,
    )

    with pytest.raises(ValueError, match="published figure hash mismatch"):
        generate_southampton_surrogate(changed_config, project_root=tmp_path)


def test_generation_is_seeded_balanced_limited_and_repeatable() -> None:
    first, _ = generate_southampton_surrogate(config())
    second, _ = generate_southampton_surrogate(config())

    assert first.records == second.records
    assert first.selection_counts == second.selection_counts
    assert len(first.records) == 30_000
    assert sum(item.priority == "low" for item in first.records) == 10_000
    assert sum(item.priority == "medium" for item in first.records) == 10_000
    assert sum(item.priority == "high" for item in first.records) == 10_000
    assert tuple(first.records[0].as_dict()) == (
        "surrogate_id",
        "priority",
        "storage_gb",
        "deadline_hours",
    )
    assert sum(first.selection_counts.values()) == 60_000
    metadata = first.metadata()
    assert metadata["algorithm_input_compatible"] is False
    assert metadata["parameter_tuning_performed"] is False
    assert metadata["omitted_fields"] == [
        "computation",
        "arrival",
        "utility",
        "upload",
        "download",
        "output_size",
    ]


def test_different_seed_changes_values_without_changing_schema() -> None:
    first, _ = generate_southampton_surrogate(config(seed=1))
    second, _ = generate_southampton_surrogate(config(seed=2))

    assert first.records != second.records
    assert tuple(first.records[0].as_dict()) == tuple(second.records[0].as_dict())


def test_auxiliary_visible_area_statistical_checks_pass_for_declared_seed() -> None:
    dataset, supports = generate_southampton_surrogate(config())
    summary = summarize_surrogate(dataset, supports)

    assert summary["all_checks_passed"] is True
    assert summary["failed_checks"] == []
    assert isinstance(summary["checks"], list)
    assert len(summary["checks"]) == 6
