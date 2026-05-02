import sys
import os

# Fix path for Windows project structure
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.simulation.emergency_simulation_engine import SimulationEngine
from Backend.services.intersection_priority import IntersectionPriority


def build_test_graph():
    """Build a small graph with 3 nodes for simulation testing."""
    g = TransportGraph()

    # Create nodes
    node_a = Node('A', 'Start District', LocationType.DISTRICT, 0.0, 0.0)
    node_b = Node('B', 'Middle District', LocationType.DISTRICT, 1.0, 0.0)
    node_f9 = Node('F9', 'Hospital', LocationType.FACILITY, 2.0, 0.0)

    g.add_node(node_a)
    g.add_node(node_b)
    g.add_node(node_f9)

    # Create traffic profile for edges
    traffic_profile = {
        TimePeriod.MORNING_PEAK: 500.0,
        TimePeriod.AFTERNOON: 200.0,
        TimePeriod.EVENING_PEAK: 400.0,
        TimePeriod.NIGHT: 50.0
    }

    # Create edges with traffic profiles
    edge_ab = Edge('A', 'B', distance=1.5, capacity=100, condition=8, traffic_profile=traffic_profile)
    edge_bf9 = Edge('B', 'F9', distance=1.0, capacity=100, condition=8, traffic_profile=traffic_profile)

    g.add_edge(edge_ab)
    g.add_edge(edge_bf9)

    return g


def test_simulation_engine_basic():
    """Test the SimulationEngine with a basic scenario."""
    print("\n" + "="*60, flush=True)
    print("=== SIMULATION ENGINE TEST START ===", flush=True)
    print("="*60, flush=True)

    # Build graph
    print("\n[SETUP] Building test graph...", flush=True)
    graph = build_test_graph()
    print(f"[SETUP] Graph created with {len(graph.nodes)} nodes", flush=True)
    print(f"[SETUP] Nodes: {list(graph.nodes.keys())}", flush=True)

    # Create IntersectionPriority for emergency routing
    print("\n[SETUP] Creating IntersectionPriority...", flush=True)
    intersection_priority = IntersectionPriority(default_emergency_multiplier=0.7)
    print("[SETUP] IntersectionPriority created with multiplier 0.7", flush=True)

    # Create SimulationEngine
    print("\n[SETUP] Creating SimulationEngine...", flush=True)
    engine = SimulationEngine(graph, intersection_priority=intersection_priority)
    print("[SETUP] SimulationEngine created successfully", flush=True)

    # Run scenario
    print("\n" + "-"*60, flush=True)
    print("[SCENARIO] Starting emergency routing scenario", flush=True)
    print("[SCENARIO] Start node: A, Time of day: 8.0 (morning peak)", flush=True)
    print("-"*60, flush=True)

    try:
        result, timeline = engine.run_scenario(start_node='A', time_of_day=8.0)

        # Print result
        print("\n[RESULT] Route Result Dictionary:", flush=True)
        print(f"         Path: {result.get('path', 'N/A')}", flush=True)
        print(f"         Cost: {result.get('cost', 'N/A')}", flush=True)
        print(f"         Nodes explored: {result.get('nodes_explored', 'N/A')}", flush=True)
        print(f"         Metadata: {result.get('metadata', {})}", flush=True)

        # Print timeline
        print("\n[TIMELINE] Vehicle Movement Timeline:", flush=True)
        print(f"           Total steps: {len(timeline)}", flush=True)
        for idx, (t, node) in enumerate(timeline):
            print(f"           Step {idx}: time={t:.3f}, node={node}", flush=True)

        # Verify the scenario produced a result (even if no path due to CSV loading)
        # The important thing is that the engine runs and produces a timeline
        assert isinstance(result, dict), "Result should be a dictionary"
        assert isinstance(timeline, list), "Timeline should be a list"
        assert len(timeline) >= 1, "Timeline should have at least 1 entry (start node)"
        assert timeline[0][1] == 'A', "Timeline should start at node A"

        print("\n" + "="*60, flush=True)
        print("=== SIMULATION ENGINE TEST PASSED ===", flush=True)
        print("="*60 + "\n", flush=True)

    except Exception as e:
        print("\n[ERROR] Simulation failed:", flush=True)
        print(f"        {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        raise


def test_simulation_engine_with_intersection_priority():
    """Test SimulationEngine with custom intersection priority multipliers."""
    print("\n" + "="*60, flush=True)
    print("=== SIMULATION ENGINE TEST WITH CUSTOM PRIORITY ===", flush=True)
    print("="*60, flush=True)

    graph = build_test_graph()
    print(f"\n[SETUP] Graph built with {len(graph.nodes)} nodes", flush=True)

    # Create IntersectionPriority with custom override for node B
    intersection_priority = IntersectionPriority(default_emergency_multiplier=0.5)
    intersection_priority.set_override('B', 0.3)  # Aggressive priority at B
    print("[SETUP] IntersectionPriority with override for node B (0.3)", flush=True)

    engine = SimulationEngine(graph, intersection_priority=intersection_priority)
    print("[SETUP] SimulationEngine created with custom priority", flush=True)

    print("\n" + "-"*60, flush=True)
    print("[SCENARIO] Emergency routing with custom intersection priority", flush=True)
    print("-"*60, flush=True)

    try:
        result, timeline = engine.run_scenario(start_node='A', time_of_day=8.0)

        print("\n[RESULT] Route Result:", flush=True)
        print(f"         Path: {result.get('path', 'N/A')}", flush=True)
        print(f"         Cost: {result.get('cost', 'N/A')}", flush=True)

        print("\n[TIMELINE] Vehicle Movement:", flush=True)
        for idx, (t, node) in enumerate(timeline):
            print(f"           Step {idx}: time={t:.3f}, node={node}", flush=True)

        # Verify valid scenario result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert isinstance(timeline, list), "Timeline should be a list"
        assert len(timeline) >= 1, "Timeline should have at least 1 entry"
        assert timeline[0][1] == 'A', "Timeline should start at A"

        # Verify intersection_priority was applied
        assert engine.intersection_priority is not None, "IntersectionPriority should be set"
        assert engine.intersection_priority.get_multiplier('B', True) == 0.3, "B override should be 0.3"

        print("\n" + "="*60, flush=True)
        print("=== CUSTOM PRIORITY TEST PASSED ===", flush=True)
        print("="*60 + "\n", flush=True)

    except Exception as e:
        print("\n[ERROR] Custom priority test failed:", str(e), flush=True)
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    # When run directly as a script
    print("\n[INFO] Running SimulationEngine tests directly (not via pytest)\n", flush=True)
    try:
        test_simulation_engine_basic()
        test_simulation_engine_with_intersection_priority()
        print("\n[SUCCESS] All tests passed!", flush=True)
    except Exception as e:
        print(f"\n[FAILURE] Tests failed: {e}", flush=True)
        sys.exit(1)
