"""
Test emergency routing to verify the fix for empty path bug.
This test focuses on the core fixes:
1. EmergencyService filters facilities to only reachable ones
2. A* validates goal nodes exist in graph
3. A* doesn't return empty paths when goals are valid
"""
import sys
from pathlib import Path
import tempfile
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.emergency_service import EmergencyService
from Backend.services.intersection_priority import IntersectionPriority


def create_test_facilities_csv():
    """Create a temporary CSV with test medical facilities"""
    data = {
        'ID': ['H1', 'C2', 'OTHER'],
        'Name': ['City Hospital', 'Downtown Clinic', 'Other Facility'],
        'Type': ['Medical', 'Medical', 'Education'],
        'X-coordinate': [0.0, 10.0, 100.0],
        'Y-coordinate': [0.0, 0.0, 100.0]
    }
    df = pd.DataFrame(data)
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    return temp_file.name


def build_emergency_test_graph():
    """Build graph: Hospital -> Clinic -> Patient (to test facility finding)"""
    graph = TransportGraph()
    
    # Create nodes (x, y as separate args)
    hospital = Node("H1", "City Hospital", LocationType.FACILITY, 0, 0)
    clinic = Node("C2", "Downtown Clinic", LocationType.FACILITY, 10, 0)
    patient = Node("P", "Patient Location", LocationType.DISTRICT, 20, 0)
    
    graph.add_node(hospital)
    graph.add_node(clinic)
    graph.add_node(patient)
    
    # Create edges with traffic profile (bidirectional - important!)
    traffic_data = {
        TimePeriod.MORNING_PEAK: 1500,
        TimePeriod.EVENING_PEAK: 2000
    }
    
    # Forward edges
    edge1 = Edge("H1", "C2", distance=10, capacity=100, condition=8, traffic_profile=traffic_data)
    edge2 = Edge("C2", "P", distance=10, capacity=100, condition=8, traffic_profile=traffic_data)
    
    # Reverse edges (for bidirectional connectivity)
    edge3 = Edge("C2", "H1", distance=10, capacity=100, condition=8, traffic_profile=traffic_data)
    edge4 = Edge("P", "C2", distance=10, capacity=100, condition=8, traffic_profile=traffic_data)
    
    graph.add_edge(edge1)
    graph.add_edge(edge2)
    graph.add_edge(edge3)
    graph.add_edge(edge4)
    
    return graph


def test_emergency_routing_with_valid_graph():
    """Test that emergency routing finds path when hospital exists in graph"""
    print("\n" + "="*70)
    print("TEST: Emergency routing with valid graph")
    print("="*70)
    
    graph = build_emergency_test_graph()
    
    # Create test CSV
    csv_path = create_test_facilities_csv()
    
    # Create intersection priority
    ip = IntersectionPriority()
    ip.set_override("H1", 0.5)
    ip.set_override("C2", 0.6)
    
    # Create emergency service with test CSV
    emergency_service = EmergencyService(
        graph=graph,
        facilities_csv=csv_path,
        intersection_priority=ip
    )
    
    # Get route from patient to nearest hospital
    print("\n[TEST] Calling get_nearest_hospital_route...")
    result = emergency_service.get_nearest_hospital_route(
        start_node="P",
        current_time=8.0,
        is_emergency=True
    )
    
    # Verify result
    print(f"\n[VERIFY] Result structure:")
    print(f"  - path: {result.get('path', [])}")
    print(f"  - cost: {result.get('cost', 'N/A')}")
    print(f"  - nodes_explored: {result.get('nodes_explored', 'N/A')}")
    print(f"  - metadata: {result.get('metadata', {})}")
    
    # Assertions
    path = result.get('path', [])
    assert path, "Path should not be empty when hospital is reachable"
    assert path[0] == "P", f"Path should start at P, got {path[0]}"
    assert path[-1] in ["H1", "C2"], f"Path should end at hospital, got {path[-1]}"
    assert result.get('cost', float('inf')) < float('inf'), "Cost should be finite"
    assert result.get('nodes_explored', 0) > 0, "Should explore nodes"
    assert result.get('metadata', {}).get('hospital_id') in ["H1", "C2"], "Metadata should have hospital_id"
    
    print("\n✅ TEST PASSED: Emergency routing works correctly")


def test_astar_goal_validation():
    """Test that A* properly validates goal nodes exist"""
    print("\n" + "="*70)
    print("TEST: A* goal node validation")
    print("="*70)
    
    graph = build_emergency_test_graph()
    astar = AStarAlgorithm()
    
    # Test 1: Valid goal that exists in graph
    print("\n[TEST 1] Running A* with VALID goal...")
    result = astar.run(
        graph=graph,
        start_node="P",
        end_node="H1",
        debug=True
    )
    assert result['path'], "Path should exist for valid goal"
    assert result['cost'] < float('inf'), "Cost should be finite for valid goal"
    print("✅ Valid goal test passed")
    
    # Test 2: Invalid goal that does NOT exist in graph
    print("\n[TEST 2] Running A* with INVALID goal (should fail gracefully)...")
    result = astar.run(
        graph=graph,
        start_node="P",
        end_node="NONEXISTENT",
        debug=True
    )
    assert result['path'] == [], "Path should be empty for invalid goal"
    assert result['cost'] == float('inf'), "Cost should be inf for invalid goal"
    assert result['metadata'].get('error') == 'no_valid_goals', "Should have error metadata"
    print("✅ Invalid goal test passed")
    
    print("\n✅ TEST PASSED: A* goal validation works correctly")
    return True


def test_astar_path_reconstruction():
    """Test that A* path reconstruction doesn't return empty for valid paths"""
    print("\n" + "="*70)
    print("TEST: A* path reconstruction")
    print("="*70)
    
    graph = build_emergency_test_graph()
    astar = AStarAlgorithm()
    
    print("\n[TEST] Reconstructing path from patient to hospital...")
    result = astar.run(
        graph=graph,
        start_node="P",
        end_node="H1",
        debug=True
    )
    
    path = result['path']
    print(f"\n[RESULT] Reconstructed path: {path}")
    
    # Verify path is not empty
    assert path, "Path reconstruction should not return empty list for valid goal"
    
    # Verify path starts at start node
    assert path[0] == "P", f"Path should start at P, got {path[0]}"
    
    # Verify path ends at goal
    assert path[-1] == "H1", f"Path should end at H1, got {path[-1]}"
    
    # Verify path is continuous
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]
        neighbors = [e.target_id for e in graph.get_neighbors(current)]
        assert next_node in neighbors, f"Path not continuous: {current} -> {next_node}"
    
    print("\n✅ TEST PASSED: A* path reconstruction works correctly")
    return True


if __name__ == "__main__":
    try:
        test_emergency_routing_with_valid_graph()
        test_astar_goal_validation()
        test_astar_path_reconstruction()
        
        print("\n" + "="*70)
        print("🎉 ALL EMERGENCY ROUTING TESTS PASSED!")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
