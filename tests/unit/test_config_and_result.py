import math

import pytest

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.models.config import ExperimentConfig
from edge_reproduction.models.enums import ProcessingMode, ResultStatus
from edge_reproduction.models.result import ExperimentResult


def test_resolved_config_passes_execution_gate() -> None:
    config = ExperimentConfig(
        experiment_id="smoke",
        method="kg-r",
        processing_mode=ProcessingMode.PIPELINE,
        horizon_slots=5,
        random_seed=123,
        parameters={"server_count": 2},
        provenance={"server_count": "technical"},
    )

    config.ensure_resolved()
    assert config.auction_rounds == 2


def test_unresolved_scientific_decision_blocks_execution() -> None:
    config = ExperimentConfig(
        experiment_id="paper-normal",
        method="kg-p",
        processing_mode=ProcessingMode.PIPELINE,
        horizon_slots=5,
        unresolved_decisions=("DEC-DEADLINE-BOUNDARY",),
    )

    with pytest.raises(UnresolvedDecisionError, match="DEC-DEADLINE-BOUNDARY"):
        config.ensure_resolved()


def test_config_rejects_non_paper_auction_round_count() -> None:
    with pytest.raises(ValueError, match="exactly two"):
        ExperimentConfig(
            experiment_id="smoke",
            method="kg-r",
            processing_mode=ProcessingMode.BATCH,
            horizon_slots=1,
            auction_rounds=1,
        )


def test_config_copies_and_freezes_nested_mappings() -> None:
    parameters: dict[str, object] = {"server_count": 2}
    config = ExperimentConfig(
        experiment_id="smoke",
        method="kg-r",
        processing_mode=ProcessingMode.BATCH,
        horizon_slots=1,
        parameters=parameters,
    )
    parameters["server_count"] = 99

    assert config.parameters["server_count"] == 2
    with pytest.raises(TypeError):
        config.parameters["server_count"] = 3  # type: ignore[index]


def test_result_allows_ever_preempted_overlap_with_final_outcome() -> None:
    result = ExperimentResult(
        run_id="run-1",
        experiment_id="smoke",
        method="kg-p",
        random_seed=123,
        completed_task_ids=("job-1",),
        rejected_task_ids=("job-2",),
        ever_preempted_task_ids=("job-1", "job-2"),
        completed_utility=10.0,
        rejected_utility=5.0,
        preempted_utility=15.0,
        event_count=8,
    )

    assert result.status is ResultStatus.SUCCEEDED
    assert result.ever_preempted_task_ids == ("job-1", "job-2")


def test_result_rejects_duplicate_ids_within_one_metric_category() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        ExperimentResult(
            run_id="run-1",
            experiment_id="smoke",
            method="kg-p",
            random_seed=None,
            completed_task_ids=("job-1", "job-1"),
        )


@pytest.mark.parametrize("utility", [math.inf, -math.inf, math.nan])
def test_result_rejects_non_finite_metric_utility(utility: float) -> None:
    with pytest.raises(ValueError):
        ExperimentResult(
            run_id="run-1",
            experiment_id="smoke",
            method="kg-p",
            random_seed=None,
            completed_utility=utility,
        )
