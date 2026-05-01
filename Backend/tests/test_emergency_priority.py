import sys
import os

# allow imports from Backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algorithms.greedy.traffic_signal import TrafficSignalOptimizer
from algorithms.greedy.emergency_priority import EmergencyPrioritySystem
from models.enums import TimePeriod, LocationType
from utils.data_loader import DataLoader
from graph.graph_builder import GraphBuilder


def test_emergency_priority():

    print("\nRunning Emergency Priority Test\n")

    # 1. LOAD REAL DATA

    script_dir = os.path.dirname(os.path.abspath(__file__))

    districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
    roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")
    traffic_path = os.path.join(script_dir, "..", "data", "processed", "traffic_flow.csv")

    nodes = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    edges = DataLoader.load_edges(roads_path, traffic_path)

    graph = GraphBuilder.build_graph(nodes, edges)

    print(f"Graph loaded with {len(graph.get_all_nodes())} nodes")


    # 2. RUN GREEDY

    optimizer = TrafficSignalOptimizer()
    base_result = optimizer.run(graph, time_period=TimePeriod.MORNING_PEAK)

    print("\nBase Signal Plan (Greedy):")
    for node, signals in base_result["signal_plan"].items():
        print(f"{node}: {signals}")


    # 3. EMERGENCY PATH

    emergency_path = ["12", "1", "3", "11"]

    # 4. APPLY EMERGENCY OVERRIDE

    emergency = EmergencyPrioritySystem()

    final_result = emergency.run(
        graph,
        base_signal_plan=base_result["signal_plan"],
        emergency_path=emergency_path
    )


    # 5. FINAL OUTPUT

    print("\nFinal Signal Plan (After Emergency):\n")

    for node, signals in final_result.items():
        print(f"{node}: {signals}")


if __name__ == "__main__":
    test_emergency_priority()