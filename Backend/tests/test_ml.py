import pandas as pd
import sys
import os
from pathlib import Path

# Fix import path for running script directly
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Backend.graph.graph_builder import GraphBuilder
from Backend.services.service_registry import get_ml_service
from Backend.models.node import Node
from Backend.models.edge import Edge


# ----------------------------
# INTERPRETATION FUNCTION
# ----------------------------

def interpret_congestion(value: float) -> str:
    if value < 0.3:
        return "LOW traffic (smooth flow)"
    elif value < 0.6:
        return "MODERATE traffic (some delays)"
    elif value < 0.8:
        return "HEAVY traffic (slow movement)"
    else:
        return "SEVERE congestion (possible jam)"


# ----------------------------
# LOAD GRAPH
# ----------------------------

def load_graph():
    districts_df = pd.read_csv("Backend/data/processed/neighborhoods_districts.csv")
    facilities_df = pd.read_csv("Backend/data/processed/facilities.csv")
    edges_df = pd.read_csv("Backend/data/processed/existing_roads.csv")
    traffic_df = pd.read_csv("Backend/data/processed/traffic_flow.csv")

    nodes_df = pd.concat([districts_df, facilities_df], ignore_index=True)

    nodes = [
        Node(
            str(r["ID"]),
            str(r["Name"]),
            r["Type"],
            r["X-coordinate"],
            r["Y-coordinate"],
            r.get("Population", 0),
        )
        for _, r in nodes_df.iterrows()
    ]

    edges = [
        Edge(
            str(r["FromID"]),
            str(r["TOID"]),
            r["Distance(km)"],
            r["Current Capacity(vehicles/hour)"],
            r["Condition(1-10)"],
        )
        for _, r in edges_df.iterrows()
    ]

    # attach traffic
    traffic_map = {}

    for _, r in traffic_df.iterrows():
        road_id = r["RoadID"]
        traffic_map[road_id] = [
            r["Morning Peak(veh/h)"],
            r["Afternoon(veh/h)"],
            r["Evening Peak(veh/h)"],
            r["Night(veh/h)"],
        ]

    for edge in edges:
        edge_id = f"{edge.source_id}-{edge.target_id}"
        if edge_id in traffic_map:
            edge.traffic.flows = {
                "t0": traffic_map[edge_id][0],
                "t1": traffic_map[edge_id][1],
                "t2": traffic_map[edge_id][2],
                "t3": traffic_map[edge_id][3],
            }

    return GraphBuilder.build_graph(nodes, edges)


# ----------------------------
# MAIN TEST
# ----------------------------

def test_ml_prediction():
    print("Loading graph...")

    graph = load_graph()

    print(f"Nodes: {len(graph.get_all_nodes())}")
    print(f"Edges: {sum(len(v) for v in graph.adjacency_list.values())}")
    print("Graph loaded successfully")

    ml = get_ml_service(graph)

    # collect edges safely
    edges_list = []
    for e_list in graph.adjacency_list.values():
        edges_list.extend(e_list)

    if not edges_list:
        raise RuntimeError("No edges found in graph")

    sample_edge = edges_list[5]
    edge_id = f"{sample_edge.source_id}-{sample_edge.target_id}"

    # ----------------------------
    # DATA EXTRACTION
    # ----------------------------

    capacity = sample_edge.capacity or 1e-6

    flows = list(sample_edge.traffic.flows.values())
    current_flow = flows[-1] if flows else 0

    current_congestion = current_flow / capacity

    # ----------------------------
    # ML PREDICTION
    # ----------------------------

    predicted = ml.predict_congestion(sample_edge)
    predicted_flow = predicted * capacity

    # ----------------------------
    # REPORT OUTPUT
    # ----------------------------

    print("\n================ TRAFFIC ANALYSIS REPORT ================\n")

    print(f"Road: {edge_id}")
    print(f"Capacity: {capacity:.0f} vehicles/hour")

    print("\nCURRENT STATUS:")
    print(f"Flow: {current_flow:.0f} vehicles/hour")
    print(f"Congestion: {current_congestion:.3f}")
    print(f"Status: {interpret_congestion(current_congestion)}")

    print("\nPREDICTION (NEXT STEP):")
    print(f"Predicted Flow: {predicted_flow:.0f} vehicles/hour")
    print(f"Predicted Congestion: {predicted:.3f}")
    print(f"Status: {interpret_congestion(predicted)}")

    print("\nCHANGE ANALYSIS:")

    diff = predicted - current_congestion

    if diff > 0:
        print(f"Traffic is INCREASING by {diff:.3f}")
    else:
        print(f"Traffic is DECREASING by {abs(diff):.3f}")

    print("\n=========================================================\n")


if __name__ == "__main__":
    test_ml_prediction()