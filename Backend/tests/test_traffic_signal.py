import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from algorithms.greedy.traffic_signal import TrafficSignalOptimizer
from models.enums import TimePeriod
from utils.data_loader import DataLoader
from graph.graph_builder import GraphBuilder
from models.enums import LocationType


def test_real_optimizer():

    print("\nRunning REAL DATA Traffic Signal Test\n")


    # 1. LOAD REAL DATA (CSV)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
    roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")
    traffic_path = os.path.join(script_dir, "..", "data", "processed", "traffic_flow.csv")

    nodes = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    edges = DataLoader.load_edges(roads_path, traffic_path)

   
    # 2. BUILD GRAPH

    graph = GraphBuilder.build_graph(nodes, edges)

    print(f"Graph loaded with {len(graph.get_all_nodes())} nodes")

    # 3. RUN TEST FOR ALL TIMES

    optimizer = TrafficSignalOptimizer()

    time_periods = [
        TimePeriod.MORNING_PEAK,
        TimePeriod.AFTERNOON,
        TimePeriod.EVENING_PEAK,
        TimePeriod.NIGHT
    ]

    for tp in time_periods:
        print("TIME PERIOD:", tp.value)

        result = optimizer.run(graph, time_period=tp)

        for node, signals in result["signal_plan"].items():
            print(f"{node}: {signals}")

        print("\nMetadata:", result["metadata"])


if __name__ == "__main__":
    test_real_optimizer()