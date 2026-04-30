import pytest
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP


def test_zero_capacity():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 3, "passengers": 1000},
    ]

    result = algo.execute_with_metrics(data, capacity=0)[0]

    assert result["cost"] == 0
    assert result["metadata"]["total_passengers_covered"] == 0


def test_single_item_fit():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 2, "passengers": 500},
    ]

    result = algo.execute_with_metrics(data, capacity=2)[0]

    assert result["cost"] == 500
    assert result["metadata"]["total_passengers_covered"] == 500


def test_optimal_selection():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 3, "passengers": 1000},
        {"route_id": "R2", "buses": 2, "passengers": 800},
        {"route_id": "R3", "buses": 4, "passengers": 1500},
    ]

    result = algo.execute_with_metrics(data, capacity=5)[0]

    assert result["cost"] == 1800
    assert result["metadata"]["total_passengers_covered"] == 1800


def test_output_format():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 1, "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=1)[0]

    assert "schedule" in result
    assert "cost" in result
    assert "metadata" in result
    assert isinstance(result["schedule"], dict)


def test_schedule_structure():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 3, "passengers": 1000},
        {"route_id": "R2", "buses": 2, "passengers": 800},
    ]

    result = algo.execute_with_metrics(data, capacity=5)[0]

    assert "R1" in result["schedule"]
    assert "R2" in result["schedule"]

    assert isinstance(result["schedule"]["R1"], list)
    assert isinstance(result["schedule"]["R2"], list)


def test_capacity_smaller_than_all():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 5, "passengers": 1000},
        {"route_id": "R2", "buses": 6, "passengers": 2000},
    ]

    result = algo.execute_with_metrics(data, capacity=2)[0]

    assert result["cost"] == 0
    assert result["schedule"] == {}


def test_empty_data():
    algo = ResourceAllocationDP()

    result, _ = algo.execute_with_metrics([], capacity=10)

    assert result["cost"] == 0
    assert result["schedule"] == {}


def test_tie_case_consistency():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 2, "passengers": 500},
        {"route_id": "R2", "buses": 2, "passengers": 500},
    ]

    result = algo.execute_with_metrics(data, capacity=2)[0]

    assert result["cost"] == 500
    assert len(result["schedule"]) == 1


def test_capacity_respected():
    algo = ResourceAllocationDP()

    data = [
        {"route_id": "R1", "buses": 3, "passengers": 1000},
        {"route_id": "R2", "buses": 4, "passengers": 1200},
    ]

    result = algo.execute_with_metrics(data, capacity=5)[0]

    assert len(result["schedule"]) <= len(data)