import json
from pathlib import Path

import pytest

from edge_reproduction.exceptions import UnresolvedDecisionError
from edge_reproduction.experiments.orchestration import (
    AUXILIARY_LABEL,
    AuxiliaryExecutionConfig,
    load_execution_config,
)


def valid_mapping() -> dict[str, object]:
    return {
        "schema_version": "stage13b-execution-config-v1",
        "run_id": "seed-1",
        "experiment_id": "auxiliary-smoke",
        "scientific_label": AUXILIARY_LABEL,
        "baseline": "arXiv:2403.15665v2_2024",
        "runner": "four_policy_single_auction",
        "seed": 1,
        "input_config_path": "configs/scenario.json",
        "unresolved_decisions": [],
    }


def test_execution_config_rejects_hidden_or_mislabeled_inputs() -> None:
    with pytest.raises(ValueError, match="scientific_label must be"):
        AuxiliaryExecutionConfig.from_mapping(
            valid_mapping() | {"scientific_label": "paper_result"}
        )
    with pytest.raises(ValueError, match="unknown execution config keys"):
        AuxiliaryExecutionConfig.from_mapping(valid_mapping() | {"horizon": 100})
    with pytest.raises(TypeError, match="seed must be an integer"):
        AuxiliaryExecutionConfig.from_mapping(valid_mapping() | {"seed": True})


def test_unresolved_execution_config_is_blocked() -> None:
    config = AuxiliaryExecutionConfig.from_mapping(
        valid_mapping() | {"unresolved_decisions": ["MISSING_SCIENTIFIC_DECISION"]}
    )

    with pytest.raises(UnresolvedDecisionError, match="MISSING_SCIENTIFIC_DECISION"):
        config.ensure_resolved()


def test_stage_thirteen_a_paper_spec_cannot_be_loaded_for_execution(
    tmp_path: Path,
) -> None:
    path = tmp_path / "paper-spec.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "stage13a-experiment-spec-v1",
                "experiment_id": "PIPE-NORMAL",
                "unresolved_decisions": ["EXPERIMENT_SEEDS", "SYNTHETIC_HORIZON"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(UnresolvedDecisionError, match="paper experiment.*non-executable"):
        load_execution_config(path)
