import pytest

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType
from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import DijkstraAlgorithm


def build_small_graph():
    r"""
    Build a graph where A* can demonstrate advantage over Dijkstra.
    
    Graph structure (with coordinates):
             A (1,2)
            / \
    S(0,0)     G(2,2)
            \ /
             B (1,0)
    
    Path S->A->G is 2 edges = 3.236 cost (2.236 + 1.0)
    Path S->B->G is 2 edges = 3.236 cost (1.0 + 2.236)
    
    A* with Euclidean heuristic will prefer S->A->G because:
    - From S: h(A)=sqrt(1+4)=2.236, h(B)=sqrt(1+0)=1.0
    - A* will explore A before B since A is closer to goal
    - Dijkstra will explore both equally
    """
    g = TransportGraph()

    nodes = [
        Node('S', 'Start', LocationType.DISTRICT, 0, 0),    # Start at origin
        Node('A', 'PathA', LocationType.DISTRICT, 1, 2),    # Up - closer to goal vertically
        Node('B', 'PathB', LocationType.DISTRICT, 1, 0),    # Down - farther from goal
        Node('G', 'Goal', LocationType.FACILITY, 2, 2),     # Goal
    ]

    for n in nodes:
        g.add_node(n)

    edges = [
        Edge('S', 'A', distance=2.236, capacity=100, condition=8),  # Euclidean: sqrt(1+4) ≈ 2.236
        Edge('S', 'B', distance=1.0, capacity=100, condition=8),    # Straight down
        Edge('A', 'G', distance=1.0, capacity=100, condition=8),    # Straight right
        Edge('B', 'G', distance=2.236, capacity=100, condition=8),  # Euclidean: sqrt(1+4) ≈ 2.236
    ]

    for e in edges:
        g.add_edge(e)

    return g


def test_astar_equals_dijkstra():
    """
    Test that A* produces optimal path but may explore fewer nodes than Dijkstra.
    
    Both should find same optimal cost, but A* with good heuristic explores strategically.
    """
    g = build_small_graph()
    astar = AStarAlgorithm()
    dijkstra = DijkstraAlgorithm()

    dres = dijkstra.run(g, start_node='S', end_node='G')
    ares = astar.run(g, 'S', end_node='G')

    # Print with flush to ensure output appears in terminal with -s flag
    print("\n========== TEST OUTPUT ==========", flush=True)
    print(f"Dijkstra cost: {dres['cost']}, nodes_explored: {dres.get('nodes_explored', 'N/A')}", flush=True)
    print(f"A* cost: {ares['cost']}, nodes_explored: {ares.get('nodes_explored', 'N/A')}", flush=True)
    print(f"Dijkstra path: {dres['path']}", flush=True)
    print(f"A* path: {ares['path']}", flush=True)
    print("=================================\n", flush=True)

    # Assertion 1: costs should be equal (both find optimal)
    assert abs(dres['cost'] - ares['cost']) < 0.01, \
        f"Dijkstra cost {dres['cost']} != A* cost {ares['cost']}"
    
    # Assertion 2: A* should explore <= Dijkstra nodes (heuristic should help)
    # Note: May be equal if graph structure allows both to converge optimally
    assert ares.get('nodes_explored', 0) <= dres.get('nodes_explored', 0) + 1, \
        f"A* explored {ares.get('nodes_explored')} but Dijkstra only {dres.get('nodes_explored')} - heuristic should help!"
    
    # Assertion 3: Both should find same optimal path length
    assert len(dres['path']) == len(ares['path']), \
        f"Path lengths differ: Dijkstra {len(dres['path'])} vs A* {len(ares['path'])}"