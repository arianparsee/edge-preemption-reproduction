import numpy as np
import pytest

from edge_reproduction.datasets.synthetic import (
    ARRIVAL_SPEC,
    BIMODAL_JOB_SPECS,
    NORMAL_JOB_SPECS,
    SERVER_SPECS,
    NormalSpec,
    SyntheticGenerationConfig,
    _positive_normal,
    _round_half_up,
    generate_synthetic,
)


def config(kind: str, *, arrival_slots: int = 102) -> SyntheticGenerationConfig:
    return SyntheticGenerationConfig.from_mapping(
        {
            "dataset_id": f"test-{kind}",
            "label": "auxiliary_test",
            "workload_kind": kind,
            "seed": 20240811,
            "arrival_slots": arrival_slots,
            "drain_slots": 0,
            "server_count": 8,
        }
    )


def test_arxiv_v2_table_parameters_are_literal() -> None:
    assert SERVER_SPECS["storage"] == NormalSpec(540.0, 30.0, "MB")
    assert SERVER_SPECS["computation"] == NormalSpec(80.0, 20.0, "MFlops/s")
    assert NORMAL_JOB_SPECS["storage"] == NormalSpec(200.0, 20.0, "MB")
    assert NORMAL_JOB_SPECS["utility"] == NormalSpec(60.0, 20.0, "utility")
    assert BIMODAL_JOB_SPECS["utility_low"] == NormalSpec(40.0, 10.0, "utility")
    assert BIMODAL_JOB_SPECS["utility_high"] == NormalSpec(160.0, 20.0, "utility")
    assert ARRIVAL_SPEC.mean == 14.0
    assert ARRIVAL_SPEC.standard_deviation == 4.0
    assert ARRIVAL_SPEC.unit == "jobs/slot"


def test_config_requires_every_paper_missing_envelope_field() -> None:
    with pytest.raises(ValueError, match="missing generation config keys"):
        SyntheticGenerationConfig.from_mapping(
            {
                "dataset_id": "missing",
                "label": "test",
                "workload_kind": "normal",
                "server_count": 8,
            }
        )


def test_config_rejects_nonpaper_server_count_and_boolean_seed() -> None:
    raw: dict[str, object] = {
        "dataset_id": "invalid",
        "label": "test",
        "workload_kind": "normal",
        "seed": 1,
        "arrival_slots": 10,
        "drain_slots": 0,
        "server_count": 7,
    }
    with pytest.raises(ValueError, match="server_count must be 8"):
        SyntheticGenerationConfig.from_mapping(raw)
    raw["server_count"] = 8
    raw["seed"] = True
    with pytest.raises(TypeError, match="seed must be an integer"):
        SyntheticGenerationConfig.from_mapping(raw)


def test_assump_022_rounds_half_up_and_rejects_nonpositive_continuous_draws() -> None:
    rounded = _round_half_up(np.asarray([0.49, 0.5, 1.49, 1.5], dtype=np.float64))
    values, resamples = _positive_normal(
        np.random.Generator(np.random.PCG64(4)),
        NormalSpec(0.0, 1.0, "test"),
        500,
    )

    assert rounded.tolist() == [0, 1, 1, 2]
    assert bool(np.all(values > 0.0))
    assert resamples > 0


def test_normal_generation_is_repeatable_positive_and_allocation_only() -> None:
    first = generate_synthetic(config("normal"))
    second = generate_synthetic(config("normal"))

    assert first == second
    assert len(first.servers) == 8
    assert len(first.tasks) == sum(first.arrival_counts) == 1410
    assert first.tasks[0].task_id == "job-000001"
    assert first.servers[0].server_id == "server-001"
    assert all(item.utility_class is None for item in first.tasks)
    assert all(item.deadline_slots >= 1 for item in first.tasks)
    assert all(item.utility > 0.0 and item.storage_mb > 0.0 for item in first.tasks)
    metadata = first.metadata()
    assert metadata["scientific_status"] == ("allocation_layer_only_not_full_pipeline_ASSUMP-026")
    assert metadata["rng"] == second.metadata()["rng"]
    assert first.tasks[0].as_dict()["output_size_status"] == ("unavailable_not_reported_ASSUMP-026")


def test_bimodal_generation_has_exact_seeded_90_10_quota() -> None:
    dataset = generate_synthetic(config("bimodal"))
    low = [item for item in dataset.tasks if item.utility_class == "low"]
    high = [item for item in dataset.tasks if item.utility_class == "high"]

    assert len(dataset.tasks) == 1410
    assert len(low) == 1269
    assert len(high) == 141
    assert {item.utility_class for item in dataset.tasks[:50]} == {"low", "high"}
    assert dataset.tasks[0].to_domain().task_id == "job-000001"
    assert dataset.servers[0].to_domain().server_id == "server-001"


def test_bimodal_generation_fails_when_total_is_not_divisible_by_ten() -> None:
    with pytest.raises(ValueError, match="ASSUMP-025"):
        generate_synthetic(config("bimodal", arrival_slots=100))
