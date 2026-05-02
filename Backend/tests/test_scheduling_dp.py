import pytest
from Backend.algorithms.dp.scheduling import SchedulingDP


def test_empty_input():
    """DP must handle empty input gracefully."""
    algo = SchedulingDP()
    result = algo.execute_with_metrics([], capacity=None)[0]

    assert result["schedule"] == {}
    assert result["cost"] == 0
    assert result["metadata"]["total_passengers_covered"] == 0


def test_non_overlapping_trips_all_selected():
    """When no trips overlap, DP should select ALL of them."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "06:30", "passengers": 100},
        {"bus_id": "B1", "start_time": "06:30", "end_time": "07:00", "passengers": 120},
        {"bus_id": "B2", "start_time": "07:00", "end_time": "07:30", "passengers": 80},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert result["metadata"]["total_passengers_covered"] == 300
    assert result["metadata"]["trips_selected"] == 3


def test_overlapping_trips_optimal_selection():
    """
    DP must exclude overlapping trips and pick the optimal subset.

    Trips:
      A: [06:00, 07:00]  value=150
      B: [06:30, 07:30]  value=200   ← overlaps with A and C
      C: [07:00, 08:00]  value=180

    A+C = 330 (non-overlapping)
    B   = 200 (alone, since it overlaps both A and C)

    Optimal: select A + C = 330
    """
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 150},
        {"bus_id": "B2", "start_time": "06:30", "end_time": "07:30", "passengers": 200},
        {"bus_id": "B1", "start_time": "07:00", "end_time": "08:00", "passengers": 180},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    # DP should pick A + C = 330 over B alone = 200
    assert result["metadata"]["total_passengers_covered"] == 330
    assert result["metadata"]["trips_selected"] == 2


def test_single_high_value_vs_many_low():
    """
    One high-value trip that overlaps with several low-value ones.

    Trips:
      Big:   [06:00, 09:00]  value=500
      Small1:[06:00, 07:00]  value=100
      Small2:[07:00, 08:00]  value=100
      Small3:[08:00, 09:00]  value=100

    Small1+Small2+Small3 = 300, Big = 500
    DP should pick the single big trip.
    """
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "09:00", "passengers": 500},
        {"bus_id": "B2", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
        {"bus_id": "B3", "start_time": "07:00", "end_time": "08:00", "passengers": 100},
        {"bus_id": "B4", "start_time": "08:00", "end_time": "09:00", "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert result["metadata"]["total_passengers_covered"] == 500
    assert result["metadata"]["trips_selected"] == 1


def test_many_small_beat_one_big():
    """
    When many non-overlapping small trips collectively exceed a big one.

    Trips:
      Big:   [06:00, 09:00]  value=250
      Small1:[06:00, 07:00]  value=100
      Small2:[07:00, 08:00]  value=100
      Small3:[08:00, 09:00]  value=100

    Small1+Small2+Small3 = 300 > Big = 250
    DP should pick the three small trips.
    """
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "09:00", "passengers": 250},
        {"bus_id": "B2", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
        {"bus_id": "B3", "start_time": "07:00", "end_time": "08:00", "passengers": 100},
        {"bus_id": "B4", "start_time": "08:00", "end_time": "09:00", "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert result["metadata"]["total_passengers_covered"] == 300
    assert result["metadata"]["trips_selected"] == 3


def test_capacity_constraint():
    """Capacity limits the number of selected trips (post-DP pruning)."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
        {"bus_id": "B2", "start_time": "07:00", "end_time": "08:00", "passengers": 200},
        {"bus_id": "B3", "start_time": "08:00", "end_time": "09:00", "passengers": 150},
    ]

    result = algo.execute_with_metrics(data, capacity=2)[0]

    # All 3 are non-overlapping; DP selects all 3, then capacity prunes to top-2 by value
    assert result["metadata"]["trips_selected"] <= 2
    # Top 2 by value: 200 + 150 = 350
    assert result["metadata"]["total_passengers_covered"] == 350


def test_legacy_time_format():
    """Legacy format with single 'time' field should still work."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B2", "time": "08:00", "passengers": 120},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert "schedule" in result
    assert "cost" in result
    assert isinstance(result["schedule"], dict)
    # These trips are far apart (2h gap with 15min default duration), no overlap
    assert result["metadata"]["total_passengers_covered"] == 220


def test_time_ordering():
    """Times within each bus must be sorted in the output schedule."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "07:00", "end_time": "07:30", "passengers": 120},
        {"bus_id": "B1", "start_time": "06:00", "end_time": "06:30", "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    if "B1" in result["schedule"]:
        times = result["schedule"]["B1"]
        assert times == sorted(times)


def test_dp_prevents_time_conflict():
    """
    Core invariant: no two selected trips may overlap in time.

    Create trips where greedy-by-value would select overlapping ones,
    but DP must avoid it.
    """
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 300},
        {"bus_id": "B2", "start_time": "06:30", "end_time": "07:30", "passengers": 400},
        # If greedy picked both (300+400=700), they overlap.
        # DP must pick only one — the 400-value trip.
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert result["metadata"]["trips_selected"] == 1
    assert result["metadata"]["total_passengers_covered"] == 400


def test_output_structure():
    """Verify the output dict has the required keys and types."""
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "start_time": "06:00", "end_time": "06:30", "passengers": 100},
    ]

    result = algo.execute_with_metrics(data, capacity=None)[0]

    assert "schedule" in result
    assert "cost" in result
    assert "metadata" in result
    assert isinstance(result["schedule"], dict)
    assert isinstance(result["cost"], int)
    assert "total_passengers_covered" in result["metadata"]
    assert "trips_selected" in result["metadata"]
    assert "dp_table_size" in result["metadata"]