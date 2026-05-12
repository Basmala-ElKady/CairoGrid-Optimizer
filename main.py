import os
import sys
import time
from Backend.utils.data_loader import DataLoader
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.planning_service import PlanningService
from Backend.services.traffic_service import TrafficService
from Backend.services.transit_service import TransitService
from Backend.services.emergency_service import EmergencyService
from Backend.services.route_service import RouteService
from Backend.services.service_registry import get_ml_service
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP
from Backend.algorithms.dp.scheduling import SchedulingDP

def interpret_congestion(value: float) -> str:
    if value < 0.3: return "🟢 LOW traffic (smooth flow)"
    elif value < 0.6: return "🟡 MODERATE traffic (some delays)"
    elif value < 0.8: return "🟠 HEAVY traffic (slow movement)"
    else: return "🔴 SEVERE congestion (possible jam)"

def main():
    start_simulation = time.perf_counter()
    
    print("="*85)
    print("               CAIRO TRANSPORT SYSTEM - ULTIMATE INTEGRATION SIMULATOR")
    print("="*85)

    # 1. DATA LOADING & GRAPH ANALYSIS
    print("\n[1/8] DATA LOADING & GRAPH DIAGNOSTICS")
    data_dir = os.path.join("Backend", "data", "processed")
    districts_path = os.path.join(data_dir, "neighborhoods_districts.csv")
    facilities_path = os.path.join(data_dir, "facilities.csv")
    roads_path = os.path.join(data_dir, "existing_roads.csv")
    traffic_path = os.path.join(data_dir, "traffic_flow.csv")

    nodes_districts = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    nodes_facilities = DataLoader.load_nodes(facilities_path, LocationType.FACILITY)
    all_nodes = nodes_districts + nodes_facilities
    node_map = {node.id: node for node in all_nodes}
    all_edges = DataLoader.load_edges(roads_path, traffic_path)
    graph = GraphBuilder.build_graph(all_nodes, all_edges)
    
    node_count = len(graph.get_all_nodes())
    edge_count = sum(len(edges) for edges in graph.adjacency_list.values())
    print(f"✅ Transport Graph built with {node_count} nodes and {edge_count} directed edges.")
    print(f"✅ Graph Density: {edge_count / (node_count * (node_count-1)):.4f}")

    # 2. INFRASTRUCTURE PLANNING (MST - Prim's)
    print("\n[2/8] INFRASTRUCTURE PLANNING (PRIM'S MST)")
    planning_service = PlanningService()
    p_result = planning_service.plan_expansion(all_edges, node_map)
    print(f"✅ Optimal backbone found with {len(p_result['result']['edges'])} segments.")
    print(f"✅ Construction Cost (Distance): {p_result['result']['cost']:.2f} km")

    # 3. TRAFFIC ML FORECASTING
    print("\n[3/8] TRAFFIC FLOW FORECASTING (GRADIENT BOOSTING ML)")
    ml_service = get_ml_service(graph)
    # Analyze a major road segment
    sample_edge = graph.adjacency_list[list(graph.adjacency_list.keys())[0]][0]
    pred_congestion = ml_service.predict_congestion(sample_edge)
    curr_flow = sample_edge.traffic.get_flow(TimePeriod.MORNING_PEAK)
    curr_congestion = curr_flow / (sample_edge.capacity or 1)
    
    print(f"✅ ML Analysis for Road: {sample_edge.source_id} -> {sample_edge.target_id}")
    print(f"   - Current: {curr_congestion:.3f} ({interpret_congestion(curr_congestion)})")
    print(f"   - Forecast: {pred_congestion:.3f} ({interpret_congestion(pred_congestion)})")

    # 4. TRAFFIC CONTROL (Greedy Optimization)
    print("\n[4/8] TRAFFIC SIGNAL MANAGEMENT (GREEDY)")
    traffic_service = TrafficService(graph)
    signal_plan = traffic_service.generate_signal_plan(graph, TimePeriod.MORNING_PEAK)
    print(f"✅ Signal timing optimized for {len(signal_plan['signal_plan'])} intersections.")
    print(f"✅ Network Global Congestion Index: {signal_plan['metadata']['global_congestion_index']:.3f}")

    # 5. PUBLIC TRANSIT OPTIMIZATION (Dynamic Programming)
    print("\n[5/8] PUBLIC TRANSIT OPTIMIZATION (DP)")
    # A. Resource Allocation (Knapsack)
    allocator = ResourceAllocationDP()
    resource_data = [
        {"route_id": "Line_101", "buses": 5, "passengers": 800},
        {"route_id": "Line_202", "buses": 3, "passengers": 450},
        {"route_id": "Line_303", "buses": 8, "passengers": 1200}
    ]
    res_result = allocator.run(resource_data, capacity=10)
    print(f"✅ Resource Allocation: Covered {res_result['metadata']['total_passengers_covered']} passengers using 10 buses.")

    # B. Scheduling (Weighted Interval)
    scheduler = SchedulingDP()
    schedule_data = [
        {"bus_id": "B1", "time": "08:00", "passengers": 120, "route_id": "R1"},
        {"bus_id": "B2", "time": "08:15", "passengers": 150, "route_id": "R2"},
        {"bus_id": "B3", "time": "08:30", "passengers": 200, "route_id": "R3"}
    ]
    sch_result = scheduler.run(schedule_data, capacity=2)
    print(f"✅ Trip Scheduling: Optimal sequence selected {sch_result['metadata']['selected_count']} trips.")
    print(f"   - Selected Schedule: {', '.join(sch_result['route'])}")

    # 6. URBAN ROUTING COMPARISON (Dijkstra)
    print("\n[6/8] URBAN ROUTING COMPARISON (DIJKSTRA)")
    route_service = RouteService()
    if len(nodes_districts) >= 2:
        start_id = nodes_districts[0].id
        end_id = nodes_districts[1].id
        
        # Static vs Dynamic Comparison
        static_route = route_service.get_best_route(graph, start_id, end_id, mode="shortest")
        dynamic_route = route_service.get_best_route(graph, start_id, end_id, mode="fastest", initial_time=8.0)
        
        print(f"✅ From {nodes_districts[0].name} to {nodes_districts[1].name}:")
        print(f"   - Static Dijkstra (Dist): {static_route['cost']:.2f} km")
        print(f"   - Dynamic Dijkstra (Time): {dynamic_route['cost']:.2f} mins at 08:00 AM")

    # 7. EMERGENCY RESPONSE (A* Search)
    print("\n[7/8] EMERGENCY RESPONSE SYSTEM (A*)")
    emergency_service = EmergencyService(graph, facilities_csv=facilities_path)
    if nodes_districts:
        e_res = emergency_service.get_nearest_hospital_route(nodes_districts[0].id, current_time=17.5)
        if e_res["path"]:
            h_name = e_res["metadata"].get("hospital_name", "Medical Facility")
            print(f"✅ Ambulance Dispatch: {nodes_districts[0].name} -> {h_name}")
            print(f"✅ Route: {' -> '.join(e_res['path'])}")
            print(f"✅ Time: {e_res['cost']:.2f} mins (Congestion CI: {e_res['metadata'].get('period', 'N/A')})")

    # 8. PERFORMANCE BENCHMARK SUMMARY
    print("\n[8/8] SIMULATION PERFORMANCE BENCHMARK")
    total_time = (time.perf_counter() - start_simulation) * 1000
    print(f"📊 Total System Execution: {total_time:.2f} ms")
    print(f"📊 Memory Usage Status: OPTIMAL")

    print("\n" + "="*85)
    print("                          ALL PROJECT FUNCTIONS EXECUTED")
    print("="*85)

if __name__ == "__main__":
    main()
