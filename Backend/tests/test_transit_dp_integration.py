import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from Backend.services.transit_service import TransitService


def test_transit_integration():
    service = TransitService()

    schedule_data = [
        {"bus_id": "B1", "time": "06:00", "passengers": 100},
        {"bus_id": "B2", "time": "06:10", "passengers": 150},
    ]

    resource_data = [
        {"route_id": "R1", "buses": 2, "passengers": 1000},
        {"route_id": "R2", "buses": 3, "passengers": 1200},
    ]

    capacity = 4

    result = service.optimize(schedule_data, resource_data, capacity=capacity)

    assert "schedule" in result
    assert "cost" in result
    assert "metadata" in result
    assert isinstance(result["schedule"], dict)
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
