import pytest

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType
from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import DijkstraAlgorithm


def build_small_graph():
    g = TransportGraph()

    nodes = [
        Node('S', 'Start', LocationType.DISTRICT, 0, 0),
        Node('A', 'A', LocationType.DISTRICT, 1, 0),
        Node('B', 'B', LocationType.DISTRICT, 2, 0),
        Node('C', 'C', LocationType.DISTRICT, 3, 0),
        Node('G', 'Goal', LocationType.FACILITY, 4, 0),
    ]

    for n in nodes:
        g.add_node(n)

    edges = [
        Edge('S', 'A', distance=1.0, capacity=100, condition=8),
        Edge('A', 'B', distance=1.0, capacity=100, condition=8),
        Edge('B', 'C', distance=1.0, capacity=100, condition=8),
        Edge('C', 'G', distance=1.0, capacity=100, condition=8),
    ]

    for e in edges:
        g.add_edge(e)

    return g


def test_astar_equals_dijkstra():
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

    # Assertion: costs should be equal in benchmark mode
    assert dres['cost'] == ares['cost'], f"Dijkstra cost {dres['cost']} != A* cost {ares['cost']}"