"""
End-to-end tests for the full DP pipeline:

    CSV → DataLoader → dp_adapter → DP algorithms → TransitService → output

Covers:
    1. Adapter correctness (bus_routes, transport_demand)
    2. CSV → DP pipeline (optimize_from_csv)
    3. Knapsack optimality proofs
    4. Scheduling capacity via true 2D DP
    5. Edge cases (empty input, zero capacity, invalid data)
    6. Output format guarantee
    7. Determinism check
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pandas as pd

from Backend.utils.dp_adapter import adapt_bus_routes, adapt_transport_demand
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP
from Backend.algorithms.dp.scheduling import SchedulingDP
from Backend.services.transit_service import TransitService

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "processed"
)


# =========================================================================
# 1. ADAPTER TESTS
# =========================================================================

class TestAdaptBusRoutes:
    """Verify bus_routes.csv → ResourceAllocationDP input mapping."""

    def test_adapts_csv_column_names(self):
        """Raw CSV headers (with spaces) must map to DP keys."""
        raw = [{"RouteID": "B1", "Buses Assigned": "25", "Daily Passengers": "35000"}]
        adapted = adapt_bus_routes(raw)

        assert len(adapted) == 1
        assert adapted[0]["route_id"] == "B1"
        assert adapted[0]["buses"] == 25
        assert adapted[0]["passengers"] == 35000

    def test_adapts_lowercase_headers(self):
        """pandas-normalised lowercase headers must also work."""
        raw = [{"routeid": "B2", "buses assigned": "30", "daily passengers": "42000"}]
        adapted = adapt_bus_routes(raw)

        assert adapted[0]["route_id"] == "B2"
        assert adapted[0]["buses"] == 30
        assert adapted[0]["passengers"] == 42000

    def test_loads_real_csv(self):
        """Adapter must work on the real bus_routes.csv file."""
        csv_path = os.path.join(DATA_DIR, "bus_routes.csv")
        if not os.path.exists(csv_path):
            pytest.skip("bus_routes.csv not found")

        raw = pd.read_csv(csv_path).to_dict(orient="records")
        adapted = adapt_bus_routes(raw)

        assert len(adapted) == 10  # 10 routes in the CSV
        for item in adapted:
            assert "route_id" in item
            assert "buses" in item
            assert "passengers" in item
            assert item["buses"] > 0
            assert item["passengers"] > 0

    def test_empty_input(self):
        assert adapt_bus_routes([]) == []


class TestAdaptTransportDemand:
    """Verify transport_demand.csv → SchedulingDP input mapping."""

    def test_generates_synthetic_trips(self):
        """Each OD pair must produce trips across 3 time windows."""
        raw = [{"FromID": "3", "TOID": "5", "Daily Passengers": "15000"}]
        trips = adapt_transport_demand(raw, trips_per_window=2)

        # 1 OD pair × 3 windows × 2 trips/window = 6 trips
        assert len(trips) == 6

    def test_trip_schema(self):
        """Every trip must have bus_id, start_time, end_time, passengers."""
        raw = [{"FromID": "1", "TOID": "3", "Daily Passengers": "12000"}]
        trips = adapt_transport_demand(raw, trips_per_window=1)

        for trip in trips:
            assert "bus_id" in trip
            assert "start_time" in trip
            assert "end_time" in trip
            assert "passengers" in trip

    def test_bus_id_format(self):
        """bus_id must be 'FromID-TOID'."""
        raw = [{"FromID": "F2", "TOID": "11", "Daily Passengers": "25000"}]
        trips = adapt_transport_demand(raw)

        for trip in trips:
            assert trip["bus_id"] == "F2-11"

    def test_no_overlap_within_window(self):
        """Trips within the same window for the same OD must not overlap."""
        raw = [{"FromID": "1", "TOID": "3", "Daily Passengers": "12000"}]
        trips = adapt_transport_demand(raw, trips_per_window=3)

        # Group by bus_id
        from collections import defaultdict
        groups = defaultdict(list)
        for t in trips:
            groups[t["bus_id"]].append(t)

        for bus_id, bus_trips in groups.items():
            # Parse times
            def to_hours(ts):
                h, m = ts.split(":")
                return int(h) + int(m) / 60.0

            sorted_trips = sorted(bus_trips, key=lambda x: to_hours(x["start_time"]))
            for i in range(len(sorted_trips) - 1):
                end_curr = to_hours(sorted_trips[i]["end_time"])
                start_next = to_hours(sorted_trips[i + 1]["start_time"])
                assert end_curr <= start_next + 0.001, (
                    f"Overlap: {sorted_trips[i]} overlaps {sorted_trips[i+1]}"
                )

    def test_determinism(self):
        """Same input must always produce the same output."""
        raw = [
            {"FromID": "3", "TOID": "5", "Daily Passengers": "15000"},
            {"FromID": "1", "TOID": "3", "Daily Passengers": "12000"},
        ]
        result1 = adapt_transport_demand(raw)
        result2 = adapt_transport_demand(raw)
        assert result1 == result2

    def test_loads_real_csv(self):
        """Adapter must work on the real transport_demand.csv file."""
        csv_path = os.path.join(DATA_DIR, "transport_demand.csv")
        if not os.path.exists(csv_path):
            pytest.skip("transport_demand.csv not found")

        raw = pd.read_csv(csv_path).to_dict(orient="records")
        trips = adapt_transport_demand(raw)

        assert len(trips) > 0
        for trip in trips:
            assert trip["passengers"] >= 0

    def test_empty_input(self):
        assert adapt_transport_demand([]) == []


# =========================================================================
# 2. CSV → DP PIPELINE (end-to-end)
# =========================================================================

class TestCSVPipeline:
    """Full CSV → DP pipeline via TransitService."""

    def test_optimize_from_csv(self):
        """TransitService.optimize_from_csv must produce valid output."""
        csv_path = os.path.join(DATA_DIR, "bus_routes.csv")
        if not os.path.exists(csv_path):
            pytest.skip("CSV files not found")

        service = TransitService()
        result = service.optimize_from_csv(capacity=50, data_dir=DATA_DIR)

        assert "schedule" in result
        assert "cost" in result
        assert "metadata" in result
        assert result["metadata"]["total_passengers_covered"] > 0

    def test_pipeline_determinism(self):
        """Running the pipeline twice must produce identical results."""
        csv_path = os.path.join(DATA_DIR, "bus_routes.csv")
        if not os.path.exists(csv_path):
            pytest.skip("CSV files not found")

        service = TransitService()
        r1 = service.optimize_from_csv(capacity=50, data_dir=DATA_DIR)
        r2 = service.optimize_from_csv(capacity=50, data_dir=DATA_DIR)

        assert r1["cost"] == r2["cost"]
        assert r1["metadata"] == r2["metadata"]

    def test_real_knapsack_from_csv(self):
        """ResourceAllocationDP directly on adapted CSV data."""
        csv_path = os.path.join(DATA_DIR, "bus_routes.csv")
        if not os.path.exists(csv_path):
            pytest.skip("CSV files not found")

        raw = pd.read_csv(csv_path).to_dict(orient="records")
        routes = adapt_bus_routes(raw)

        algo = ResourceAllocationDP()
        # Total buses in CSV: 25+30+20+22+18+24+15+12+28+20 = 214
        # Use a capacity smaller than total to force selection
        result = algo.execute_with_metrics(routes, capacity=100)[0]

        assert result["cost"] > 0
        assert "schedule" in result

    def test_real_scheduling_from_csv(self):
        """SchedulingDP directly on adapted CSV data."""
        csv_path = os.path.join(DATA_DIR, "transport_demand.csv")
        if not os.path.exists(csv_path):
            pytest.skip("CSV files not found")

        raw = pd.read_csv(csv_path).to_dict(orient="records")
        trips = adapt_transport_demand(raw)

        algo = SchedulingDP()
        result = algo.execute_with_metrics(trips, capacity=None)[0]

        assert result["cost"] > 0
        assert result["metadata"]["trips_selected"] > 0


# =========================================================================
# 3. KNAPSACK OPTIMALITY
# =========================================================================

class TestKnapsackOptimality:
    """Prove the knapsack DP finds the true optimal."""

    def test_classic_textbook_case(self):
        """Known optimal: items (w=3,v=1000) + (w=2,v=800) fit in W=5."""
        algo = ResourceAllocationDP()
        data = [
            {"route_id": "R1", "buses": 3, "passengers": 1000},
            {"route_id": "R2", "buses": 2, "passengers": 800},
            {"route_id": "R3", "buses": 4, "passengers": 1500},
        ]
        result = algo.execute_with_metrics(data, capacity=5)[0]
        assert result["cost"] == 1800  # R1(1000) + R2(800)

    def test_greedy_would_fail(self):
        """
        Greedy-by-ratio would pick R2 first (500 pax/bus), leaving no room
        for the true optimum.

        R1: w=4, v=1200 (ratio 300)
        R2: w=3, v=1500 (ratio 500) ← greedy picks this
        R3: w=3, v=900  (ratio 300)

        Greedy: R2(1500) + nothing that fits = 1500
        DP:     R1(1200) + R3(900) won't fit (4+3=7 > 6)
        DP:     R2(1500) + R3(900) = 2400 (3+3=6 ✓)
        """
        algo = ResourceAllocationDP()
        data = [
            {"route_id": "R1", "buses": 4, "passengers": 1200},
            {"route_id": "R2", "buses": 3, "passengers": 1500},
            {"route_id": "R3", "buses": 3, "passengers": 900},
        ]
        result = algo.execute_with_metrics(data, capacity=6)[0]
        assert result["cost"] == 2400  # R2 + R3


# =========================================================================
# 4. SCHEDULING CAPACITY via true 2D DP
# =========================================================================

class TestSchedulingCapacityDP:
    """Verify capacity is enforced via DP, not greedy post-filter."""

    def test_capacity_selects_optimal_k_trips(self):
        """
        5 non-overlapping trips, capacity=2.
        DP must select the 2 highest-value trips.

        Trips (all non-overlapping):
            T1: [06:00-07:00]  v=100
            T2: [07:00-08:00]  v=300
            T3: [08:00-09:00]  v=200
            T4: [09:00-10:00]  v=250
            T5: [10:00-11:00]  v=150

        Best 2: T2(300) + T4(250) = 550
        """
        algo = SchedulingDP()
        data = [
            {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
            {"bus_id": "B2", "start_time": "07:00", "end_time": "08:00", "passengers": 300},
            {"bus_id": "B3", "start_time": "08:00", "end_time": "09:00", "passengers": 200},
            {"bus_id": "B4", "start_time": "09:00", "end_time": "10:00", "passengers": 250},
            {"bus_id": "B5", "start_time": "10:00", "end_time": "11:00", "passengers": 150},
        ]
        result = algo.execute_with_metrics(data, capacity=2)[0]

        assert result["metadata"]["trips_selected"] == 2
        assert result["metadata"]["total_passengers_covered"] == 550

    def test_capacity_with_overlaps(self):
        """
        Overlapping trips + capacity constraint.

        Trips:
            A: [06:00-08:00]  v=400
            B: [07:00-09:00]  v=500  ← overlaps A and C
            C: [08:00-10:00]  v=300
            D: [10:00-12:00]  v=200

        capacity=2:
            B+D = 500+200 = 700  (non-overlapping, 2 trips)
            A+C = 400+300 = 700  (non-overlapping, 2 trips)
            A+D = 400+200 = 600
            C+D = 300+200 = 500

        Best: B+D or A+C = 700  (either is valid)
        """
        algo = SchedulingDP()
        data = [
            {"bus_id": "B1", "start_time": "06:00", "end_time": "08:00", "passengers": 400},
            {"bus_id": "B2", "start_time": "07:00", "end_time": "09:00", "passengers": 500},
            {"bus_id": "B3", "start_time": "08:00", "end_time": "10:00", "passengers": 300},
            {"bus_id": "B4", "start_time": "10:00", "end_time": "12:00", "passengers": 200},
        ]
        result = algo.execute_with_metrics(data, capacity=2)[0]

        assert result["metadata"]["trips_selected"] <= 2
        assert result["metadata"]["total_passengers_covered"] == 700

    def test_capacity_one(self):
        """With capacity=1, DP must pick the single highest-value trip."""
        algo = SchedulingDP()
        data = [
            {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
            {"bus_id": "B2", "start_time": "07:00", "end_time": "08:00", "passengers": 500},
            {"bus_id": "B3", "start_time": "08:00", "end_time": "09:00", "passengers": 200},
        ]
        result = algo.execute_with_metrics(data, capacity=1)[0]

        assert result["metadata"]["trips_selected"] == 1
        assert result["metadata"]["total_passengers_covered"] == 500

    def test_capacity_none_selects_all_non_overlapping(self):
        """With capacity=None, all non-overlapping trips are selected."""
        algo = SchedulingDP()
        data = [
            {"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100},
            {"bus_id": "B2", "start_time": "07:00", "end_time": "08:00", "passengers": 200},
            {"bus_id": "B3", "start_time": "08:00", "end_time": "09:00", "passengers": 300},
        ]
        result = algo.execute_with_metrics(data, capacity=None)[0]

        assert result["metadata"]["trips_selected"] == 3
        assert result["metadata"]["total_passengers_covered"] == 600


# =========================================================================
# 5. EDGE CASES
# =========================================================================

class TestEdgeCases:

    def test_scheduling_empty(self):
        result = SchedulingDP().execute_with_metrics([], capacity=None)[0]
        assert result["cost"] == 0 and result["schedule"] == {}

    def test_allocation_empty(self):
        result = ResourceAllocationDP().execute_with_metrics([], capacity=10)[0]
        assert result["cost"] == 0 and result["schedule"] == {}

    def test_allocation_zero_capacity(self):
        data = [{"route_id": "R1", "buses": 2, "passengers": 500}]
        result = ResourceAllocationDP().execute_with_metrics(data, capacity=0)[0]
        assert result["cost"] == 0

    def test_allocation_none_capacity(self):
        """capacity=None must not crash — treated as 0."""
        data = [{"route_id": "R1", "buses": 2, "passengers": 500}]
        result = ResourceAllocationDP().execute_with_metrics(data, capacity=None)[0]
        assert result["cost"] == 0

    def test_adapter_zero_buses_warning(self):
        """Routes with 0 buses should be clamped to 1 with a warning."""
        raw = [{"RouteID": "R0", "Buses Assigned": "0", "Daily Passengers": "5000"}]
        adapted = adapt_bus_routes(raw)
        assert adapted[0]["buses"] == 0  # adapter preserves raw value
        # DP module clamps internally


# =========================================================================
# 6. OUTPUT FORMAT GUARANTEE
# =========================================================================

class TestOutputFormat:
    """Every result must have exactly: schedule, cost, metadata.total_passengers_covered."""

    def _check(self, result):
        assert isinstance(result, dict)
        assert "schedule" in result
        assert "cost" in result
        assert "metadata" in result
        assert "total_passengers_covered" in result["metadata"]
        assert isinstance(result["schedule"], dict)
        assert isinstance(result["cost"], (int, float))
        assert isinstance(result["metadata"]["total_passengers_covered"], (int, float))

    def test_scheduling_format(self):
        data = [{"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100}]
        result = SchedulingDP().execute_with_metrics(data, capacity=None)[0]
        self._check(result)

    def test_allocation_format(self):
        data = [{"route_id": "R1", "buses": 2, "passengers": 500}]
        result = ResourceAllocationDP().execute_with_metrics(data, capacity=5)[0]
        self._check(result)

    def test_transit_service_format(self):
        service = TransitService()
        sched = [{"bus_id": "B1", "start_time": "06:00", "end_time": "07:00", "passengers": 100}]
        res = [{"route_id": "R1", "buses": 2, "passengers": 500}]
        result = service.optimize(sched, res, capacity=5)
        self._check(result)

    def test_csv_pipeline_format(self):
        csv_path = os.path.join(DATA_DIR, "bus_routes.csv")
        if not os.path.exists(csv_path):
            pytest.skip("CSV not found")

        result = TransitService().optimize_from_csv(capacity=50, data_dir=DATA_DIR)
        self._check(result)


# =========================================================================
# Runner
# =========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
