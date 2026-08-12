import pytest

from edge_reproduction.models.schedule import TaskSchedule


def test_schedule_totals_and_one_based_cumulative_values() -> None:
    schedule = TaskSchedule((1.0, 2.0), (0.0, 3.0), (0.0, 1.0))

    assert schedule.horizon == 2
    assert schedule.total_upload() == 3.0
    assert schedule.total_computation() == 3.0
    assert schedule.total_download() == 1.0
    assert schedule.cumulative_through("upload", 1) == 1.0


def test_schedule_rejects_unequal_horizons() -> None:
    with pytest.raises(ValueError, match="share one horizon"):
        TaskSchedule((1.0,), (1.0, 2.0), (1.0,))


def test_schedule_rejects_negative_or_empty_series() -> None:
    with pytest.raises(ValueError):
        TaskSchedule((), (), ())
    with pytest.raises(ValueError, match="non-negative"):
        TaskSchedule((1.0,), (-1.0,), (1.0,))
