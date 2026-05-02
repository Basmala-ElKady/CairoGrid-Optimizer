import sys
from pathlib import Path
import unittest

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from Backend.services.route_service import RouteService
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod

class TestDijkstraFullCycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Scenario: 'The Daily Commute'
        A Direct Road vs. A Peripheral Bypass.
        """
        cls.nodes = [
            Node("A", "Home", LocationType.DISTRICT, 0, 0, 0),
            Node("B", "Bypass_Point", LocationType.DISTRICT, 1, 1, 0),
            Node("C", "Work", LocationType.DISTRICT, 2, 2, 0)
        ]

        # Traffic Profiles
        # Direct road is heavily congested during morning peak (8 AM)
        direct_traffic = {TimePeriod.MORNING_PEAK: 9000, TimePeriod.NIGHT: 0}
        # Bypass road has constant low traffic
        bypass_traffic = {TimePeriod.MORNING_PEAK: 100, TimePeriod.NIGHT: 100}

        cls.edges = [
            # Road 1: Direct but prone to congestion
            Edge("A", "C", distance=10.0, capacity=1000, condition=10, traffic_profile=direct_traffic),
            
            # Road 2: Longer bypass (7km + 7km = 14km)
            Edge("A", "B", distance=7.0, capacity=5000, condition=10, traffic_profile=bypass_traffic),
            Edge("B", "C", distance=7.0, capacity=5000, condition=10, traffic_profile=bypass_traffic)
        ]

        cls.graph = GraphBuilder.build_graph(cls.nodes, cls.edges)
        cls.route_service = RouteService()

    def test_24h_adaptive_logic(self):
        """
        INTEGRATION TEST: Validates path switching across the 24h cycle.
        """
        print("\n" + "="*50)
        print("RUNNING 24-HOUR ADAPTIVE ROUTING TEST")
        print("="*50)

        # --- PHASE 1: NIGHT SHIFT (2 AM) ---
        print("\n[SCENARIO 1: NIGHT - 02:00 AM]")
        night_res = self.route_service.get_best_route(
            self.graph, "A", "C", mode="fastest", initial_time=2
        )
        print(f"-> Expected: Shortest Path | Actual: {night_res['path']}")
        print(f"-> Cost: {night_res['cost']:.2f}")
        
        self.assertEqual(night_res['path'], ['A', 'C'], "Night routing should prefer the direct 10km path.")

        # --- PHASE 2: MORNING RUSH (08 AM) ---
        print("\n[SCENARIO 2: RUSH HOUR - 08:00 AM]")
        rush_res = self.route_service.get_best_route(
            self.graph, "A", "C", mode="fastest", initial_time=8
        )
        print(f"-> Expected: Bypass Route | Actual: {rush_res['path']}")
        print(f"-> Cost: {rush_res['cost']:.2f}")
        
        self.assertEqual(rush_res['path'], ['A', 'B', 'C'], "Rush hour should trigger dynamic re-routing to bypass.")

        print("\n" + "="*50)
        print("✓ CONCLUSION: ALGORITHM SUCCESSFULLY ADAPTS TO TIME")
        print("="*50)

if __name__ == "__main__":
    unittest.main()