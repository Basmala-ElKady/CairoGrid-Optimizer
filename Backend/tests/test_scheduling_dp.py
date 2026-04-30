import pytest
from Backend.algorithms.dp.scheduling import SchedulingDP


def test_empty_input():
    algo = SchedulingDP()
    result = algo.execute_with_metrics([], capacity=None)[0]

    assert result["schedule"] == {}
    assert result["cost"] == 0
    assert result["metadata"]["total_passengers_covered"] == 0


def test_basic_schedule():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
        {"bus_id": "B2", "time": "06:05", "passengers": 80},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert "schedule" in result
    assert "cost" in result
    assert "metadata" in result
    assert isinstance(result["schedule"], dict)
    assert result["metadata"]["total_passengers_covered"] == 300


def test_time_ordering():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    times = result["schedule"]["B1"]
    assert times == sorted(times)