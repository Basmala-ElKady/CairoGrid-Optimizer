import sys
from pathlib import Path
import unittest

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Backend.services.route_service import RouteService
from Backend.services.emergency_service import EmergencyService
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.intersection_priority import IntersectionPriority

class TestCairoRoutingSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize a robust test environment with Cairo-like data."""
        cls.nodes = [
            Node("12", "Helwan", LocationType.DISTRICT, 31.33, 29.85, 350000),
            Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96, 250000),
            Node("3", "Downtown", LocationType.DISTRICT, 31.24, 30.04, 100000),
            Node("F9", "Medical Center", LocationType.FACILITY, 31.26, 30.05, 0)
        ]

        # Heavy traffic during morning peak
        heavy_traffic = {
            TimePeriod.MORNING_PEAK: 2900,
            TimePeriod.NIGHT: 400
        }

        cls.edges = [
            Edge("12", "1", distance=12.7, capacity=3000, condition=6, traffic_profile=heavy_traffic),
            Edge("1", "3", distance=8.5, capacity=3000, condition=7, traffic_profile=heavy_traffic),
            Edge("1", "F9", distance=2.0, capacity=2000, condition=9)
        ]

        cls.graph = GraphBuilder.build_graph(cls.nodes, cls.edges)
        
        # We test both services
        cls.route_service = RouteService()
        # For EmergencyService, we point to a dummy/real CSV if needed, 
        # but here it will use the graph nodes we provided.
        cls.emergency_service = EmergencyService(cls.graph)

    def test_shortest_path_standard(self):
        """Test standard Dijkstra routing via RouteService."""
        result = self.route_service.get_best_route(
            self.graph, start_node="1", end_node="3", mode="shortest"
        )
        self.assertEqual(result["path"], ["1", "3"])
        self.assertEqual(result["cost"], 8.5)

    def test_traffic_impact_on_fastest_route(self):
        """Verify that RouteService considers time/traffic in dynamic mode."""
        # Night route (low traffic)
        night_res = self.route_service.get_best_route(
            self.graph, start_node="12", end_node="1", mode="fastest", initial_time=2
        )
        # Peak route (high traffic)
        peak_res = self.route_service.get_best_route(
            self.graph, start_node="12", end_node="1", mode="fastest", initial_time=8
        )
        self.assertGreater(peak_res["cost"], night_res["cost"])

    def test_emergency_service_hospital_routing(self):
        """
        Test EmergencyService specifically for its ability to find hospitals
        and apply emergency multipliers.
        """
        # We use a custom priority to see its effect
        ip = IntersectionPriority(default_emergency_multiplier=0.5)
        emergency_svc = EmergencyService(self.graph, intersection_priority=ip)
        
        # This will use A* inside EmergencyService
        result = emergency_svc.get_nearest_hospital_route(
            start_node="1", current_time=8.0, is_emergency=True
        )
        
        self.assertIsNotNone(result["path"])
        self.assertIn("F9", result["path"]) # F9 is the medical facility
        self.assertIn("hospital_name", result["metadata"])

    def test_routing_robustness(self):
        """Ensure the RouteService doesn't crash on invalid nodes but returns logical empty results."""
        # Most RouteServices return empty paths or inf cost for invalid nodes
        result = self.route_service.get_best_route(
            self.graph, "NOT_EXIST", "3", mode="shortest"
        )
        self.assertEqual(result["path"], [])

if __name__ == "__main__":
    unittest.main()