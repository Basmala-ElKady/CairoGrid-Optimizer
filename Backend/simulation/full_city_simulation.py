import os
import sys
import statistics
import csv
from typing import List

# Ensure script can be run directly from repo root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Backend.utils.data_loader import DataLoader
from Backend.graph.graph_builder import GraphBuilder
from Backend.graph.transport_graph import TransportGraph
from Backend.services.emergency_service import EmergencyService
from Backend.models.edge import Edge


# =========================
# BUILD GRAPH
# =========================
def build_full_graph(base_path: str) -> TransportGraph:
    nodes_file = os.path.join(base_path, 'data', 'processed', 'neighborhoods_districts.csv')
    facilities_file = os.path.join(base_path, 'data', 'processed', 'facilities.csv')
    roads_file = os.path.join(base_path, 'data', 'processed', 'existing_roads.csv')
    traffic_file = os.path.join(base_path, 'data', 'processed', 'traffic_flow.csv')

    print('Loading nodes...')
    nodes = DataLoader.load_nodes(nodes_file)
    print(f'Loaded {len(nodes)} district nodes')

    print('Loading facility nodes...')
    facilities = DataLoader.load_nodes(facilities_file, location_type=None)
    print(f'Loaded {len(facilities)} facilities')

    print('Loading edges...')
    edges = DataLoader.load_edges(roads_file, traffic_file)
    print(f'Loaded {len(edges)} edges')

    graph = GraphBuilder.build_graph(nodes + facilities, edges)
    return graph


# =========================
# MAIN SIMULATION
# =========================
def run_full_city(base_path: str, sample_limit: int = 200, time_of_day: float = 8.0):
    graph = build_full_graph(base_path)

    print('\n[START] full_city_simulation')
    print(f"[DEBUG] Graph nodes: {len(graph.nodes)}")

    # =========================
    # AUGMENT GRAPH
    # =========================
    def augment_connect_facilities(g):
        district_nodes = [n for nid, n in g.nodes.items() if nid.isdigit()]
        facility_nodes = [n for nid, n in g.nodes.items() if not nid.isdigit()]

        for f in facility_nodes:
            fid = f.id

            if g.get_neighbors(fid) or g.get_incoming_edges(fid):
                continue

            fx, fy = f.pos
            best = None
            best_d = float('inf')

            for d in district_nodes:
                dx, dy = d.pos
                d2 = (dx - fx) ** 2 + (dy - fy) ** 2

                if d2 < best_d:
                    best_d = d2
                    best = d

            if best:
                import math
                dist = math.hypot(best.pos[0] - fx, best.pos[1] - fy)

                e1 = Edge(str(best.id), fid, distance=round(dist, 3), capacity=2000, condition=8)
                e2 = Edge(fid, str(best.id), distance=round(dist, 3), capacity=2000, condition=8)

                g.add_edge(e1)
                g.add_edge(e2)

    augment_connect_facilities(graph)

    # =========================
    # LOAD MEDICAL FACILITIES
    # =========================
    facilities_path = os.path.join(base_path, 'data', 'processed', 'facilities.csv')
    medical = {}

    with open(facilities_path, newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get('Type', r.get('type', '')).strip().lower() == 'medical':
                fid = str(r.get('ID')).replace('.0', '')
                medical[fid] = (
                    float(r.get('X-coordinate', 0)),
                    float(r.get('Y-coordinate', 0))
                )

    med_ids = [mid for mid in medical.keys() if graph.get_node(mid) is not None]

    print(f"[DEBUG] Medical facilities in graph: {len(med_ids)}")

    if not med_ids:
        print("[ERROR] No medical facilities found!")
        return

    # =========================
    # START NODES
    # =========================
    all_nodes = list(graph.nodes.keys())
    start_nodes = all_nodes[:sample_limit] if sample_limit else all_nodes

    service = EmergencyService(graph)

    results = []

    print("\n========== SIMULATION START ==========\n")

    # =========================
    # RUN SCENARIOS
    # =========================
    for s in start_nodes:
        try:
            res_non = service.astar.run(
                graph,
                start_node=s,
                goal_nodes=med_ids,
                initial_time=time_of_day
            )

            res_em = service.astar.run(
                graph,
                start_node=s,
                goal_nodes=med_ids,
                initial_time=time_of_day,
                is_emergency=True
            )

        except Exception as e:
            print(f"[ERROR] node {s}: {e}")
            continue

        non_cost = res_non.get('cost', float('inf'))
        em_cost = res_em.get('cost', float('inf'))

        reduction = None if non_cost == float('inf') else non_cost - em_cost

        print(f"Node: {s}")
        print(f"  Normal cost: {non_cost}")
        print(f"  Emergency cost: {em_cost}")
        print(f"  Reduction: {reduction}")
        print("-" * 40)

        results.append(reduction)

    # =========================
    # SUMMARY
    # =========================
    valid = [r for r in results if r is not None]

    print("\n========== SUMMARY ==========")

    if valid:
        print(f"Average reduction: {statistics.mean(valid):.3f}")
        print(f"Median reduction: {statistics.median(valid):.3f}")
        print(f"Samples: {len(valid)}")
    else:
        print("No valid results")

    print("\n[DONE] full_city_simulation")


# =========================
# ENTRY POINT
# =========================
if __name__ == '__main__':
    repo_root = os.getcwd()
    base = os.path.join(repo_root, 'Backend')

    print("[START] Running full city simulation")
    run_full_city(base, sample_limit=200, time_of_day=8.0)
    print("[DONE] Finished")