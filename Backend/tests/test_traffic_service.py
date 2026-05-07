import sys
import os
from pathlib import Path

# Add project root and Backend directory to sys.path
project_root = Path(__file__).parent.parent.parent
backend_root = project_root / "Backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

from Backend.services.traffic_service import TrafficService
from Backend.utils.data_loader import DataLoader
from Backend.graph.graph_builder import GraphBuilder
from Backend.models.enums import TimePeriod, LocationType

def test_traffic_service():

    print("\nRunning Traffic Service Full Test\n")

    # LOAD REAL DATA

    script_dir = os.path.dirname(os.path.abspath(__file__))

    districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
    roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")
    traffic_path = os.path.join(script_dir, "..", "data", "processed", "traffic_flow.csv")

    nodes = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    edges = DataLoader.load_edges(roads_path, traffic_path)

    graph = GraphBuilder.build_graph(nodes, edges)

    print(f"Graph loaded: {len(graph.get_all_nodes())} nodes\n")

    # INIT SERVICE

    service = TrafficService()

   
    # TEST 1: NORMAL for the entire graph (NO EMERGENCY)

    print("\nTEST 1: Normal Flow (no emergency)")

    result1 = service.generate_signal_plan(
        graph,
        time_period=TimePeriod.NIGHT,
        emergency_path=None
    )

    print("\nSignal Plan:")
    for node, signals in result1["signal_plan"].items():
        print(node, signals)

    print("\nMetadata:", result1["metadata"])

    #Test2: Normal Route Congestion Index

    print("\nTEST 2: Normal Route Congestion Index\n")

    normal_path = ["12", "1", "3", "5"]

    route_ci = service.calculate_route_congestion_index(
        graph,
        TimePeriod.NIGHT,
        normal_path
    )

    print("Normal Path CI:", route_ci)
    

    # TEST 3: EMERGENCY MODE

    print("\nTEST 3: Emergency Flow (ambulance priority)")

    emergency_path = ["12", "1", "3", "5"]

    result2 = service.generate_signal_plan(
        graph,
        time_period=TimePeriod.NIGHT,
        emergency_path=emergency_path
    )

    print("\nEmergency Signal Plan:")
    for node, signals in result2["signal_plan"].items():
        print(node, signals)

    print("\nMetadata:", result2["metadata"])

      #Test4: Normal Route Congestion Index

    print("\nTEST 4: Normal Route Congestion Index\n")

    normal_path = ["12", "1", "3", "5"]

    route_ci = service.calculate_route_congestion_index(
        graph,
        TimePeriod.NIGHT,
        normal_path
    )

    print("Normal Path CI:", route_ci)


if __name__ == "__main__":
    test_traffic_service()