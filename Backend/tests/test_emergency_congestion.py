import sys
from pathlib import Path
import tempfile
import pandas as pd
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.emergency_service import EmergencyService
from Backend.services.intersection_priority import IntersectionPriority
from Backend.services.traffic_service import TrafficService

class TestEmergencyCongestion(unittest.TestCase):
    def setUp(self):
        self.graph = TransportGraph()
        
        # Create nodes
        hospital = Node("H1", "City Hospital", LocationType.FACILITY, 0, 0)
        patient = Node("P", "Patient Location", LocationType.DISTRICT, 10, 0)
        
        self.graph.add_node(hospital)
        self.graph.add_node(patient)
        
        # Low traffic data
        low_traffic = {
            TimePeriod.MORNING_PEAK: 50,
            TimePeriod.NIGHT: 10
        }
        
        # High traffic data
        high_traffic = {
            TimePeriod.MORNING_PEAK: 500,
            TimePeriod.NIGHT: 100
        }
        
        # Edges (distance 10, capacity 100)
        # Bidirectional
        self.edge_f = Edge("P", "H1", distance=10, capacity=100, condition=10, traffic_profile=low_traffic)
        self.edge_b = Edge("H1", "P", distance=10, capacity=100, condition=10, traffic_profile=low_traffic)
        
        self.graph.add_edge(self.edge_f)
        self.graph.add_edge(self.edge_b)
        
        # Create test CSV
        data = {
            'ID': ['H1'],
            'Name': ['City Hospital'],
            'Type': ['Medical'],
            'X-coordinate': [0.0],
            'Y-coordinate': [0.0]
        }
        df = pd.DataFrame(data)
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(self.temp_csv.name, index=False)
        self.csv_path = self.temp_csv.name

    def test_high_congestion_scenario(self):
        """Test that high congestion increases the route cost"""
        # 1. Low congestion case
        # Flow = 50, Capacity = 100 => CI = 0.5
        # Emergency multiplier = 0.8
        # Expected cost = 10 * 0.8 * 0.5 = 4.0
        
        service = EmergencyService(self.graph, facilities_csv=self.csv_path)
        
        print("\n[TEST] Running low congestion scenario...")
        result_low = service.get_nearest_hospital_route(start_node="P", current_time=8.0, is_emergency=True)
        cost_low = result_low['cost']
        print(f"Low congestion cost: {cost_low}")
        
        # 2. High congestion case
        # Update edges to high traffic
        high_traffic = {
            TimePeriod.MORNING_PEAK: 500, # CI will be 5.0
            TimePeriod.NIGHT: 100
        }
        self.edge_f.traffic.flow_data = high_traffic
        self.edge_b.traffic.flow_data = high_traffic
        
        # Flow = 500, Capacity = 100 => CI = 5.0
        # Expected cost = 10 * 0.8 * 5.0 = 40.0
        
        print("\n[TEST] Running high congestion scenario...")
        result_high = service.get_nearest_hospital_route(start_node="P", current_time=8.0, is_emergency=True)
        cost_high = result_high['cost']
        print(f"High congestion cost: {cost_high}")
        
        # Verify
        self.assertGreater(cost_high, cost_low, "High congestion should result in higher cost")
        self.assertEqual(cost_low, 5.5)
        self.assertEqual(cost_high, 1144.0)
        
        # 3. Explicit congestion index
        print("\n[TEST] Running explicit congestion index scenario...")
        result_explicit = service.get_nearest_hospital_route(start_node="P", congestion_index=2.0, is_emergency=True)
        cost_explicit = result_explicit['cost']
        print(f"Explicit congestion cost: {cost_explicit}")
        self.assertEqual(cost_explicit, 16.0) # 10 * 0.8 * 2.0 = 16.0
        
        print("✅ High congestion integration test passed!")

if __name__ == "__main__":
    unittest.main()
