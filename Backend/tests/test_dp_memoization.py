import pytest
from Backend.algorithms.dp.scheduling import SchedulingDP


def test_memoization_consistency():
    """Calling DP twice with the same input must return identical results."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "06:30", "passengers": 100},
        {"bus_id": "B1", "start_time": "06:30", "end_time": "07:00", "passengers": 120},
    ]

    result1 = algo.execute_with_metrics(data, capacity=None)[0]
    result2 = algo.execute_with_metrics(data, capacity=None)[0]

    assert result1 == result2


def test_memoization_performance():
    """Second call should be faster (or comparable) due to result caching."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "06:30", "passengers": 100},
        {"bus_id": "B1", "start_time": "06:30", "end_time": "07:00", "passengers": 120},
    ]

    result1, time1 = algo.execute_with_metrics(data, capacity=None)
    result2, time2 = algo.execute_with_metrics(data, capacity=None)

    assert time2 <= time1 * 1.5