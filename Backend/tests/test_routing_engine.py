import unittest
from unittest.mock import MagicMock
from Backend.algorithms.shortest_path.dijkstra import DijkstraAlgorithm
from Backend.algorithms.shortest_path.time_dependent_dijkstra import TimeDependentDijkstra
from Backend.models.enums import TimePeriod

class TestRoutingEngine(unittest.TestCase):
    def setUp(self):
        """
        Set up a Mock Graph environment to test the algorithms without 
        relying on actual CSV data.
        """
        self.graph = MagicMock()
        
        # Define 3 nodes for testing
        self.nodes = ["District_1", "District_2", "District_3"]
        self.graph.get_all_nodes.return_value = self.nodes
        
        # Mock Edge 1: District_1 -> District_2
        self.edge_1_2 = MagicMock()
        self.edge_1_2.target_id = "District_2"
        self.edge_1_2.distance = 10.0
        # Dynamic weight: 50 during rush hour, 10 otherwise
        self.edge_1_2.get_weight.side_effect = lambda p: 50.0 if p == TimePeriod.MORNING_PEAK else 10.0
        
        # Mock Edge 2: District_2 -> District_3
        self.edge_2_3 = MagicMock()
        self.edge_2_3.target_id = "District_3"
        self.edge_2_3.distance = 5.0
        self.edge_2_3.get_weight.return_value = 5.0

        # Define adjacency logic
        self.graph.get_neighbors.side_effect = lambda n: {
            "District_1": [self.edge_1_2],
            "District_2": [self.edge_2_3],
            "District_3": []
        }.get(n, [])

    def test_static_dijkstra_accuracy(self):
        """
        Test if Static Dijkstra correctly calculates the shortest 
        path based only on distance.
        """
        algo = DijkstraAlgorithm()
        result = algo.run(graph=self.graph, start_node="District_1", end_node="District_3")
        
        self.assertEqual(result["path"], ["District_1", "District_2", "District_3"])
        self.assertEqual(result["cost"], 15.0)  # 10.0 + 5.0
        print("✔ Static Dijkstra Test: PASSED")

    def test_time_dependent_rush_hour(self):
        """
        Test if TimeDependentDijkstra correctly increases weight 
        during Morning Peak (8 AM).
        """
        algo = TimeDependentDijkstra()
        # initial_time = 8 corresponds to MORNING_PEAK
        result = algo.run(graph=self.graph, start_node="District_1", end_node="District_3", initial_time=8)
        
        # Expected Cost: 50.0 (Rush hour weight) + 5.0 = 55.0
        self.assertEqual(result["cost"], 55.0)
        self.assertEqual(result["metadata"]["mode"], "fastest")
        print("✔ Time-Dependent (Rush Hour) Test: PASSED")

    def test_time_dependent_night_flow(self):
        """
        Test if TimeDependentDijkstra uses normal weights 
        during off-peak hours (11 PM).
        """
        algo = TimeDependentDijkstra()
        # initial_time = 23 corresponds to NIGHT
        result = algo.run(graph=self.graph, start_node="District_1", end_node="District_3", initial_time=23)
        
        # Expected Cost: 10.0 (Normal weight) + 5.0 = 15.0
        self.assertEqual(result["cost"], 15.0)
        print("✔ Time-Dependent (Night Flow) Test: PASSED")

if __name__ == '__main__':
    unittest.main()