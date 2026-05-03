from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest
import os
import sys

# Ensure the project root is in the system path for imports
# This allows 'from Backend...' to work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Backend.graph.transport_graph import TransportGraph
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType
from Backend.utils.data_loader import DataLoader

class TestGraph(unittest.TestCase):
    """
    Verification test to ensure TransportGraph and GraphBuilder work correctly.
    """

    def test_graph_initialization(self):
        graph = TransportGraph()
        self.assertEqual(len(graph.nodes), 0, "Graph nodes should be empty initially")
        self.assertEqual(len(graph.adjacency_list), 0, "Graph adjacency list should be empty initially")

    def test_adding_nodes(self):
        graph = TransportGraph()
        node_a = Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96, 250000)
        node_b = Node("F1", "Cairo Airport", LocationType.FACILITY, 31.41, 30.11)
        
        graph.add_node(node_a)
        graph.add_node(node_b)
        
        self.assertIn("1", graph.nodes, "Node 1 should be in graph nodes")
        self.assertIn("F1", graph.adjacency_list, "Node F1 should be initialized in adjacency list")
        
        # Test no duplication (should handle overwriting metadata)
        graph.add_node(node_a)
        self.assertEqual(len(graph.nodes), 2, "Graph should handle duplicate node additions properly")

    def test_adding_edges(self):
        graph = TransportGraph()
        node_a = Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96)
        graph.add_node(node_a)
        
        road = Edge("1", "F1", 15.0, 3000, 8)
        graph.add_edge(road)
        
        self.assertEqual(len(graph.adjacency_list["1"]), 1, "Edge should be added to source node")
        self.assertEqual(graph.adjacency_list["1"][0].target_id, "F1", "Edge target should be correct")
        
        # Auto-handles missing nodes
        missing_edge = Edge("3", "4", 5.0, 1000, 5)
        graph.add_edge(missing_edge)
        self.assertIn("3", graph.adjacency_list)
        self.assertIn("4", graph.adjacency_list)
        self.assertIn("3", graph.nodes, "Auto-created nodes should be in nodes dict")
        self.assertIn("4", graph.nodes)

    def test_data_retrieval(self):
        graph = TransportGraph()
        node_a = Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96)
        graph.add_node(node_a)
        graph.add_edge(Edge("1", "2", 1.0, 100, 10))
        
        neighbors = graph.get_neighbors("1")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(graph.get_neighbors("999"), [])
        
        all_nodes = graph.get_all_nodes()
        self.assertIn("1", all_nodes)
        self.assertIn("2", all_nodes)

    def test_integration_graph_builder(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
        roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")
        traffic_path = os.path.join(script_dir, "..", "data", "processed", "traffic_flow.csv")
        
        # Load real data
        nodes = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
        edges = DataLoader.load_edges(roads_path, traffic_path)
        
        # Build graph
        full_graph = GraphBuilder.build_graph(nodes, edges)
        
        total_nodes = len(full_graph.get_all_nodes())
        total_edges = sum(len(neighbors) for neighbors in full_graph.adjacency_list.values())
        
        self.assertGreater(total_nodes, 0)
        self.assertGreater(total_edges, 0)
        
        # Data Consistency validation
        if edges:
            sample_edge = edges[0]
            self.assertIn(str(sample_edge.source_id), full_graph.get_all_nodes())
            self.assertIn(str(sample_edge.target_id), full_graph.adjacency_list)

if __name__ == "__main__":
    unittest.main()
