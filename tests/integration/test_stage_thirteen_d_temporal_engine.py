from pathlib import Path

from edge_reproduction.experiments.temporal_smoke import run_temporal_smoke

CONFIG = Path("configs/stage13d_temporal_smoke.json")


def _by_policy(result: dict[str, object]) -> dict[str, dict[str, object]]:
    raw_runs = result["runs"]
    assert isinstance(raw_runs, list)
    runs = [item for item in raw_runs if isinstance(item, dict)]
    assert len(runs) == 4
    return {str(item["policy"]): item for item in runs}


def test_four_policy_temporal_smoke_matches_manual_outcomes() -> None:
    result = run_temporal_smoke(CONFIG)
    runs = _by_policy(result)
    assert result["full_100_slot_30_repeat_run"] is False
    assert result["figure_6_reproduced"] is False

    for name in ("knapsack_greedy_retention", "pipeline_double_knapsack_retention"):
        outcome = runs[name]["outcome"]
        assert isinstance(outcome, dict)
        assert outcome["completed_task_ids"] == ["task-current"]
        assert outcome["rejected_task_ids"] == ["task-incoming"]
        assert outcome["ever_preempted_task_ids"] == []
        assert outcome["completed_utility"] == 10.0
        assert outcome["rejected_utility"] == 12.0
        assert outcome["raw_auction_rejection_count"] == 2

    for name in ("knapsack_greedy_preemption", "pipeline_double_knapsack_preemption"):
        outcome = runs[name]["outcome"]
        assert isinstance(outcome, dict)
        assert outcome["completed_task_ids"] == ["task-incoming"]
        assert outcome["rejected_task_ids"] == ["task-current"]
        assert outcome["ever_preempted_task_ids"] == ["task-current"]
        assert outcome["completed_utility"] == 12.0
        assert outcome["rejected_utility"] == 10.0
        assert outcome["ever_preempted_utility"] == 10.0


def test_temporal_smoke_is_reproducible_and_records_policy_streams() -> None:
    first = run_temporal_smoke(CONFIG)
    second = run_temporal_smoke(CONFIG)
    assert first == second
    seeds = first["policy_seeds"]
    assert isinstance(seeds, dict)
    assert len(set(seeds.values())) == 4
    for run in _by_policy(first).values():
        metadata = run["metadata"]
        assert isinstance(metadata, dict)
        assert metadata["numerical_tolerance"] == "1e-09"
        assert metadata["full_100_slot_30_repeat_run"] == "false"
        assert metadata["output_size_provenance"] == (
            "reproduction_assumption_input_equals_output"
        )
        assert str(metadata["rng.stream_name"]).startswith("policy.")
        assert metadata["ga.zero_fitness_feasibility_repairs"] == "0"
        assert metadata["ga.zero_fitness_feasibility_repair_semantics"] == (
            "ASSUMP-042_infeasible_zero_to_all_zero_feasible_same_fitness"
        )
        assert metadata["client.equal_minimum_price_ties"] == "0"
        assert metadata["client.equal_minimum_price_tie_semantics"] == (
            "ASSUMP-043_sorted_uniform_same_policy_rng_KG_only"
        )


def test_event_order_and_retry_are_logged() -> None:
    runs = _by_policy(run_temporal_smoke(CONFIG))
    retention = runs["knapsack_greedy_retention"]
    events = retention["events"]
    assert isinstance(events, list)
    epoch_two = [event for event in events if event["time"] == 2]
    assert [event["event_type"] for event in epoch_two] == [
        "activated",
        "progressed",
        "rejected",
        "retry_scheduled",
    ]
    assert retention["retry_count_by_task"] == {
        "task-current": 0,
        "task-incoming": 1,
    }


def test_preemption_is_terminal_and_never_retried() -> None:
    runs = _by_policy(run_temporal_smoke(CONFIG))
    preemptive = runs["knapsack_greedy_preemption"]
    assert preemptive["final_task_states"] == {
        "task-current": "preempted",
        "task-incoming": "completed",
    }
    assert preemptive["retry_count_by_task"] == {
        "task-current": 0,
        "task-incoming": 0,
    }
