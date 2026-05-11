import os
import sys
from Backend.utils.data_loader import DataLoader
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.planning_service import PlanningService
from Backend.services.traffic_service import TrafficService
from Backend.services.transit_service import TransitService
from Backend.services.emergency_service import EmergencyService
from Backend.services.route_service import RouteService

def main():
    """
    Central orchestration script for the CairoGrid Optimizer.
    Synchronizes Infrastructure Planning, Traffic Control, Public Transit, Emergency, and Routing Services.
    """
    print("="*75)
    print("               CAIRO GRID OPTIMIZER - END-TO-END SIMULATION")
    print("="*75)

    # 1. DATA LOADING
    print("\n[1/6] Loading Cairo Transport Data...")
    
    # Define paths relative to the root directory
    data_dir = os.path.join("Backend", "data", "processed")
    districts_path = os.path.join(data_dir, "neighborhoods_districts.csv")
    facilities_path = os.path.join(data_dir, "facilities.csv")
    roads_path = os.path.join(data_dir, "existing_roads.csv")
    traffic_path = os.path.join(data_dir, "traffic_flow.csv")

    # Load nodes (Districts and Facilities)
    nodes_districts = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    nodes_facilities = DataLoader.load_nodes(facilities_path, LocationType.FACILITY)
    all_nodes = nodes_districts + nodes_facilities
    
    # Create a node map for MST planning (dict of id -> Node object)
    node_map = {node.id: node for node in all_nodes}
    
    # Load edges (Roads merged with Traffic Flow)
    all_edges = DataLoader.load_edges(roads_path, traffic_path)
    
    # Build the unified Transport Graph (Bidirectional by default)
    graph = GraphBuilder.build_graph(all_nodes, all_edges)
    
    print(f"✅ Loaded {len(all_nodes)} nodes ({len(nodes_districts)} districts, {len(nodes_facilities)} facilities).")
    print(f"✅ Loaded {len(all_edges)} road segments with traffic profiles.")

    # 2. INFRASTRUCTURE PLANNING (MST)
    print("\n[2/6] Infrastructure Planning (Prim's MST)...")
    planning_service = PlanningService()
    # Find the core infrastructure segments that connect the city optimally using Minimum Spanning Tree
    planning_result = planning_service.plan_expansion(all_edges, node_map)
    mst_edges = planning_result["result"]["edges"]
    total_dist = planning_result["result"]["cost"]
    print(f"✅ MST calculated with {len(mst_edges)} core infrastructure segments.")
    print(f"✅ Total Construction Distance: {total_dist:.2f} km")

    # 3. TRAFFIC CONTROL (Greedy)
    print("\n[3/6] Traffic Control Optimization (Greedy Signal Plan)...")
    traffic_service = TrafficService(graph)
    # Generate optimized signal plan for Morning Peak traffic
    signal_plan_result = traffic_service.generate_signal_plan(graph, TimePeriod.MORNING_PEAK)
    print(f"✅ Signal plan generated for {len(signal_plan_result['signal_plan'])} intersections.")
    print(f"✅ Global Congestion Index: {signal_plan_result['metadata']['global_congestion_index']:.3f}")

    # 4. PUBLIC TRANSIT (DP)
    print("\n[4/6] Public Transit Scheduling (DP Optimization)...")
    transit_service = TransitService()
    # Sample resource allocation data
    resource_data = [
        {"route_id": "Line 1", "buses": 5, "passengers": 500},
        {"route_id": "Line 2", "buses": 3, "passengers": 300},
        {"route_id": "Line 3", "buses": 8, "passengers": 750}
    ]
    # Sample scheduling data
    schedule_data = [
        {"route_id": "Line 1", "time": "08:00", "passengers": 120},
        {"route_id": "Line 2", "time": "08:15", "passengers": 80},
        {"route_id": "Line 3", "time": "08:30", "passengers": 200}
    ]
    # Optimize transit capacity and timing using Dynamic Programming
    transit_result = transit_service.optimize(schedule_data, resource_data, capacity=12)
    print(f"✅ Optimized transit schedule covering {transit_result['metadata']['total_passengers_covered']} passengers.")

    # 5. EMERGENCY ROUTING (A*)
    print("\n[5/6] Emergency Routing (A* Algorithm)...")
    # Initialize emergency service with graph and medical facility locations
    emergency_service = EmergencyService(graph, facilities_csv=facilities_path)
    
    # Pick a start node (e.g., Helwan)
    if nodes_districts:
        helwan_node = next((n for n in nodes_districts if n.id == "12"), nodes_districts[0])
        start_node_id = helwan_node.id
        start_node_name = helwan_node.name
        
        # Route an ambulance from the district to the nearest hospital during peak hours
        emergency_result = emergency_service.get_nearest_hospital_route(start_node_id, current_time=8.5) # 8:30 AM
        
        if emergency_result["path"]:
            hospital_name = emergency_result["metadata"].get("hospital_name", "the nearest hospital")
            print(f"✅ Emergency route found from '{start_node_name}' ({start_node_id}) to {hospital_name}.")
            print(f"✅ Optimized Route: {' -> '.join(emergency_result['path'])}")
            print(f"✅ Estimated Travel Time: {emergency_result['cost']:.2f} minutes")
        else:
            print(f"⚠️ Warning: No emergency route found from '{start_node_name}' to any hospital.")

    # 6. GENERAL ROUTING (Dijkstra)
    print("\n[6/6] General Routing (Static Dijkstra)...")
    route_service = RouteService()
    
    if len(nodes_districts) >= 2:
        start_node = nodes_districts[0] # Maadi (ID 1)
        # Find another node that is likely reachable
        end_node = next((n for n in nodes_districts if n.id == "3"), nodes_districts[1]) # Downtown (ID 3)
        
        # Calculate the shortest physical distance using Dijkstra's algorithm
        route_result = route_service.get_best_route(
            graph, 
            start_node=start_node.id, 
            end_node=end_node.id, 
            mode="shortest"
        )
        
        if route_result["path"]:
            print(f"✅ Shortest route found from '{start_node.name}' to '{end_node.name}'.")
            print(f"✅ Dijkstra Path: {' -> '.join(route_result['path'])}")
            print(f"✅ Total Distance: {route_result['cost']:.2f} km")
            print(f"✅ Nodes Explored: {route_result.get('nodes_explored', 'N/A')}")
        else:
            print(f"⚠️ Warning: No shortest path found between '{start_node.name}' and '{end_node.name}'.")

    print("\n" + "="*75)
    print("                          SIMULATION COMPLETE")
    print("="*75)

if __name__ == "__main__":
    main()
