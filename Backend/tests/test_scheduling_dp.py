import sys
from pathlib import Path
import pytest

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Backend.algorithms.dp.scheduling import SchedulingDP

def test_empty_input():
    algo = SchedulingDP()
    result = algo.run([], capacity=None)

    assert result["schedule"] == {}
    assert result["cost"] == 0
    assert result["metadata"]["total_passengers_covered"] == 0


def test_basic_schedule():
    algo = SchedulingDP()
    
    # We will provide trips that DO NOT overlap so they can be summed
    # Each trip lasts 30 mins (0.5 hours) by default in our code
    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100}, # Ends at 06:30
        {"bus_id": "B1", "time": "06:30", "passengers": 120}, # Starts when 1st ends (Compatible)
        {"bus_id": "B2", "time": "07:00", "passengers": 80},  # Starts after 2nd ends (Compatible)
    ]
    
    # Use execute_with_metrics to test the full flow
    result, exec_time = algo.execute_with_metrics(data, capacity=None)
    
    assert "schedule" in result
    assert "cost" in result
    assert isinstance(result["schedule"], dict)
    
    # Now they should be summed: 100 + 120 + 80 = 300
    assert result["metadata"]["total_passengers_covered"] == 300
    print(f"Test Passed! Execution time: {exec_time}ms")


def test_time_ordering():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
    ]

    result = algo.run(data, capacity=None)

    times = result["schedule"]["B1"]
    assert times == sorted(times)
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
