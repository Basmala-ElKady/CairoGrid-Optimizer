import sys
import os

# Ensure the project root is in the system path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph.transport_graph import TransportGraph
from graph.graph_builder import GraphBuilder
from models.node import Node
from models.edge import Edge
from models.enums import LocationType
from utils.data_loader import DataLoader

def run_graph_test():
    """
    Verification test to ensure TransportGraph and GraphBuilder work correctly.
    """
    print("🧪 Starting TransportGraph & GraphBuilder Verification Test...\n")

    try:
        # 1. Test Graph Initialization
        graph = TransportGraph()
        assert len(graph.nodes) == 0, "Graph nodes should be empty initially"
        assert len(graph.adjacency_list) == 0, "Graph adjacency list should be empty initially"
        print("✅ Graph Initialization: Empty graph created successfully.")

        # 2. Test Adding Nodes
        node_a = Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96, 250000)
        node_b = Node("F1", "Cairo Airport", LocationType.FACILITY, 31.41, 30.11)
        
        graph.add_node(node_a)
        graph.add_node(node_b)
        
        assert "1" in graph.nodes, "Node 1 should be in graph nodes"
        assert "F1" in graph.adjacency_list, "Node F1 should be initialized in adjacency list"
        
        # Test no duplication
        graph.add_node(node_a)
        assert len(graph.nodes) == 2, "Graph should handle duplicate node additions over-writing or ignoring"
        print("✅ Node Addition: Nodes handled and stored properly as strings.")

        # 3. Test Adding Edges
        road = Edge("1", "F1", 15.0, 3000, 8)
        graph.add_edge(road)
        
        assert len(graph.adjacency_list["1"]) == 1, "Edge should be added to source node"
        assert graph.adjacency_list["1"][0].target_id == "F1", "Edge target should be correct"
        
        # Auto-handles missing nodes
        missing_edge = Edge("3", "4", 5.0, 1000, 5)
        graph.add_edge(missing_edge)
        assert "3" in graph.adjacency_list and "4" in graph.adjacency_list, "Unseen nodes in edge should be auto-initialized"
        print("✅ Edge Addition: Directed edges added, missing nodes handled securely.")

        # 4. Test Get Neighbors & Nodes
        neighbors = graph.get_neighbors("1")
        assert len(neighbors) == 1, "Should return correct neighbor count"
        assert graph.get_neighbors("999") == [], "Non-existent node should return empty list without crashing"
        
        all_nodes = graph.get_all_nodes()
        assert len(all_nodes) >= 4, "Should correctly list all tracked node IDs from adjacency list"
        print("✅ Data Retrieval Methods: Get neighbors and Get all nodes passed safely.")

        # 5. Integration Test (GraphBuilder + DataLoader)
        print("\n🔥 Running Integration Test: Graph Builder with CSV Data...")
        
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
        
        print(f"   Built graph with {total_nodes} unique nodes and {total_edges} total directed edges.")
        
        # Data Consistency validation
        sample_edge = edges[0]
        assert str(sample_edge.source_id) in full_graph.get_all_nodes(), "Source node missing from built graph"
        assert str(sample_edge.target_id) in full_graph.adjacency_list, "Target node missing from adjacency list"

        if total_nodes > 0 and total_edges > 0:
            print("\n🟢 TEST PASSED: TransportGraph & GraphBuilder operate perfectly!")
        else:
            print("\n🔴 TEST FAILED: Graph is suspiciously empty after building.")

    except AssertionError as e:
        print(f"\n🔴 TEST FAILED (Assertion Error): {e}")
    except Exception as e:
        print(f"\n🔴 TEST FAILED (Unexpected Error): {e}")

if __name__ == "__main__":
    run_graph_test()
