import json
from pathlib import Path
from typing import Any

SPEC_DIRECTORY = Path("configs/experiments")
SCHEMA_VERSION = "stage13a-experiment-spec-v1"
SCIENTIFIC_LABELS = {
    "non_executable_specification_with_unresolved_decisions",
    "official_path_blocked_auxiliary_visible_raster_surrogate_available",
}


def load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return dict[str, Any](raw)


def specifications() -> tuple[dict[str, Any], ...]:
    registry = load_json(SPEC_DIRECTORY / "registry_arxiv_v2.json")
    return tuple(
        load_json(SPEC_DIRECTORY / str(entry["file"])) for entry in registry["specifications"]
    )


def test_registry_has_one_independent_specification_per_experiment_family() -> None:
    registry = load_json(SPEC_DIRECTORY / "registry_arxiv_v2.json")
    entries = registry["specifications"]
    expected_ids = {
        "OPT-25",
        "OPT-18",
        "OPT-10",
        "R1-DIAG",
        "PIPE-NORMAL",
        "PIPE-NORMAL-TIME",
        "BATCH-NORMAL",
        "BATCH-NORMAL-TIME",
        "BATCH-BIMODAL",
        "TRACE-DIAG",
        "TRACE-BASE",
        "TRACE-CAP-2H",
    }

    assert registry["schema_version"] == SCHEMA_VERSION
    assert {entry["experiment_id"] for entry in entries} == expected_ids
    assert len({entry["file"] for entry in entries}) == len(entries) == 12
    assert all((SPEC_DIRECTORY / entry["file"]).is_file() for entry in entries)
    for entry in entries:
        specification = load_json(SPEC_DIRECTORY / entry["file"])
        assert specification["experiment_id"] == entry["experiment_id"]
        assert specification["execution_status"] == entry["execution_status"]


def test_specs_preserve_unresolved_run_control_without_hidden_defaults() -> None:
    required_keys = {
        "schema_version",
        "experiment_id",
        "scientific_label",
        "baseline",
        "source_location",
        "processing_mode",
        "workload",
        "methods",
        "target_figures",
        "metrics",
        "paper_explicit",
        "run_control",
        "unresolved_decisions",
        "implementation_gaps",
        "execution_status",
        "auxiliary_capability",
    }
    required_run_control = {
        "seed",
        "repeats",
        "horizon_slots",
        "drain_policy",
        "aggregation",
    }

    for spec in specifications():
        assert required_keys <= set(spec)
        assert spec["schema_version"] == SCHEMA_VERSION
        assert spec["scientific_label"] in SCIENTIFIC_LABELS
        assert spec["baseline"] == "arXiv:2403.15665v2_2024"
        assert set(spec["run_control"]) == required_run_control
        assert spec["run_control"]["seed"] is None
        assert spec["unresolved_decisions"]
        assert spec["implementation_gaps"]
        assert spec["execution_status"] in {"blocked", "auxiliary_only_official_blocked"}


def test_experiment_specs_cover_every_evaluation_figure_exactly_once() -> None:
    target_figures = [figure for spec in specifications() for figure in spec["target_figures"]]

    assert sorted(target_figures) == list(range(3, 21))
    assert len(target_figures) == len(set(target_figures))


def test_southampton_auxiliary_path_cannot_be_mistaken_for_official_execution() -> None:
    by_id = {spec["experiment_id"]: spec for spec in specifications()}
    trace_diagnostic = by_id["TRACE-DIAG"]

    assert trace_diagnostic["execution_status"] == "auxiliary_only_official_blocked"
    assert "not_numerical_reproduction" in trace_diagnostic["auxiliary_capability"]
    assert by_id["TRACE-BASE"]["execution_status"] == "blocked"
    assert by_id["TRACE-CAP-2H"]["execution_status"] == "blocked"
    assert "histogram_surrogate_is_not_algorithm_input" in {
        by_id["TRACE-BASE"]["auxiliary_capability"],
        by_id["TRACE-CAP-2H"]["auxiliary_capability"],
    }


def test_pipeline_and_batch_specs_record_current_implementation_boundaries() -> None:
    by_id = {spec["experiment_id"]: spec for spec in specifications()}

    assert (
        "POLICY_INTEGRATED_TEMPORAL_SIMULATOR_MISSING"
        in by_id["PIPE-NORMAL"]["implementation_gaps"]
    )
    assert "OUTPUT_SIZE" in by_id["PIPE-NORMAL"]["unresolved_decisions"]
    for experiment_id in ("BATCH-NORMAL", "BATCH-NORMAL-TIME", "BATCH-BIMODAL"):
        assert "BATCH_DKR_BLOCKED" in by_id[experiment_id]["implementation_gaps"]
