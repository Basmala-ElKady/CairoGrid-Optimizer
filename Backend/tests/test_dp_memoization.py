from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import pytest
from Backend.algorithms.dp.scheduling import SchedulingDP


def test_memoization_consistency():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
    ]

    result1 = algo.run(data, capacity=None)
    result2 = algo.run(data, capacity=None)

    assert result1 == result2


def test_memoization_performance():
    algo = SchedulingDP()

    data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B1", "time": "06:15", "passengers": 120},
    ]

    t0 = time.perf_counter()
    result1 = algo.run(data, capacity=None)
    time1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    result2 = algo.run(data, capacity=None)
    time2 = time.perf_counter() - t0

    assert time2 <= time1 * 1.5
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
