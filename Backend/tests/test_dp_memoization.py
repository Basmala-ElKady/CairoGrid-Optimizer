import pytest
from Backend.algorithms.dp.scheduling import SchedulingDP


def test_memoization_consistency():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
    ]

    result1 = algo.execute_with_metrics(data, capacity=None)[0]
    result2 = algo.execute_with_metrics(data, capacity=None)[0]

    assert result1 == result2


def test_memoization_performance():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
    ]

    result1, time1 = algo.execute_with_metrics(data, capacity=None)
    result2, time2 = algo.execute_with_metrics(data, capacity=None)

    assert time2 <= time1 * 1.5