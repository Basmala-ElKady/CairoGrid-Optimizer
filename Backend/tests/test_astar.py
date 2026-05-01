from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.algorithms.shortest_path.astar import AStarAlgorithm


# =========================
# GRAPH 1 (Static)
# =========================
def build_graph_static():
    g = TransportGraph()

    A = Node('A', 'Start', LocationType.DISTRICT, 0, 0)
    F9 = Node('F9', 'Hospital', LocationType.FACILITY, 1, 1)

    g.add_node(A)
    g.add_node(F9)

    g.add_edge(Edge('A', 'F9', distance=2.0, capacity=100, condition=8))

    return g


def test_astar_basic_path():
    g = build_graph_static()
    algo = AStarAlgorithm()

    res = algo.run(
        g,
        'A',
        goal_nodes=['F9'],
        goal_positions={'F9': g.get_node('F9').pos}
    )

    print("\n========== BASIC PATH TEST ==========")
    print("PATH:", res['path'])
    print("COST:", res['cost'])
    print("NODES EXPLORED:", res.get('nodes_explored'))
    print("====================================")

    assert res['path'] == ['A', 'F9']
    assert abs(res['cost'] - 2.0) < 1e-6


# =========================
# GRAPH 2 (Time-dependent)
# =========================
def build_graph_time_dependent():
    g = TransportGraph()

    A = Node('A', 'Start', LocationType.DISTRICT, 0, 0)
    B = Node('B', 'Mid', LocationType.DISTRICT, 0.5, 0.5)
    F9 = Node('F9', 'Hospital', LocationType.FACILITY, 1, 1)

    for n in (A, B, F9):
        g.add_node(n)

    profile_heavy = {
        TimePeriod.MORNING_PEAK: 1000.0,
        TimePeriod.AFTERNOON: 100.0,
        TimePeriod.EVENING_PEAK: 200.0,
        TimePeriod.NIGHT: 10.0,
    }

    g.add_edge(Edge('A', 'F9', distance=5.0, capacity=100, condition=8, traffic_profile=profile_heavy))
    g.add_edge(Edge('A', 'B', distance=2.0, capacity=200, condition=9))
    g.add_edge(Edge('B', 'F9', distance=2.0, capacity=200, condition=9))

    return g


def test_astar_time_dependent_prefers_alternate_in_morning():
    g = build_graph_time_dependent()
    algo = AStarAlgorithm()

    res = algo.run(
        g,
        'A',
        goal_nodes=['F9'],
        goal_positions={'F9': g.get_node('F9').pos},
        initial_time=8.0
    )

    print("\n========== TIME DEPENDENT TEST ==========")
    print("PATH:", res['path'])
    print("COST:", res['cost'])
    print("NODES EXPLORED:", res.get('nodes_explored'))
    print("=========================================")

    assert res['path'] == ['A', 'B', 'F9']


def test_astar_emergency_priority_effect():
    g = build_graph_time_dependent()
    algo = AStarAlgorithm()

    res_normal = algo.run(
        g,
        'A',
        goal_nodes=['F9'],
        goal_positions={'F9': g.get_node('F9').pos},
        initial_time=8.0,
        emergency_priority=1.0
    )

    res_em = algo.run(
        g,
        'A',
        goal_nodes=['F9'],
        goal_positions={'F9': g.get_node('F9').pos},
        initial_time=8.0,
        emergency_priority=0.05
    )

    print("\n========== EMERGENCY TEST ==========")
    print("NORMAL COST:", res_normal['cost'])
    print("EMERGENCY COST:", res_em['cost'])
    print("IMPROVEMENT:", res_normal['cost'] - res_em['cost'])
    print("====================================")

    assert res_em['cost'] <= res_normal['cost']


def test_intersection_priority_effect():
    """Construct a small graph where a central intersection has degree > 2 and verify
    that providing an IntersectionPriority with a lowered multiplier reduces the
    emergency route cost compared to non-emergency routing.
    """
    from Backend.services.intersection_priority import IntersectionPriority

    g = TransportGraph()
    # central intersection I connects to three branches
    I = Node('I', 'Intersection', LocationType.DISTRICT, 0, 0)
    A = Node('A', 'A', LocationType.DISTRICT, -1, 0)
    B = Node('B', 'B', LocationType.DISTRICT, 1, 0)
    G = Node('G', 'Goal', LocationType.FACILITY, 0, 2)

    for n in (I, A, B, G):
        g.add_node(n)

    # edges: A->I, B->I, I->G (I has degree 3 considering incoming/outgoing)
    g.add_edge(Edge('A', 'I', distance=1.0, capacity=100, condition=8))
    g.add_edge(Edge('B', 'I', distance=1.0, capacity=100, condition=8))
    g.add_edge(Edge('I', 'G', distance=1.0, capacity=100, condition=8))

    algo = AStarAlgorithm()

    # baseline (no emergency)
    res_norm = algo.run(g, 'A', end_node='G')

    # setup intersection priority to favor emergency through node I
    ip = IntersectionPriority(default_emergency_multiplier=0.5)
    ip.set_override('I', 0.4)

    res_em = algo.run(g, 'A', end_node='G', is_emergency=True, intersection_priority=ip)

    assert res_em['cost'] <= res_norm['cost']