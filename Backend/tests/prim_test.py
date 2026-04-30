from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.algorithms.mst.prim import PrimAlgorithm
from Backend.models.edge import Edge
from Backend.models.enums import LocationType
from Backend.models.node import Node


def make_node(node_id, population=0):
    return Node(
        node_id=node_id,
        name=f"District {node_id}",
        node_type=LocationType.DISTRICT,
        x=0.0,
        y=0.0,
        population=population,
    )


def make_edge(source_id, target_id, cost):
    return Edge(
        source_id=source_id,
        target_id=target_id,
        distance=cost,
        capacity=1000,
        condition=10,
    )


@pytest.fixture
def prim_algorithm():
    return PrimAlgorithm()


@pytest.fixture
def basic_nodes():
    return {
        "A": make_node("A", population=100),
        "B": make_node("B", population=200),
        "C": make_node("C", population=300),
        "D": make_node("D", population=400),
    }


def assert_mst_output_shape(result):
    assert set(result.keys()) == {"edges", "cost", "metadata"}
    assert isinstance(result["edges"], list)
    assert isinstance(result["cost"], float)
    assert isinstance(result["metadata"], dict)
    assert result["metadata"]["algorithm"] == "Prim"


def test_mst_basic(prim_algorithm, basic_nodes):
    edge_list = [
        make_edge("A", "B", 1.0),
        make_edge("B", "C", 2.0),
        make_edge("A", "C", 5.0),
        make_edge("C", "D", 1.0),
        make_edge("B", "D", 4.0),
    ]

    result = prim_algorithm.run(edge_list=edge_list, nodes=basic_nodes)

    assert_mst_output_shape(result)
    assert result["cost"] == 4.0
    assert set(result["edges"]) == {"A-B", "B-C", "C-D"}
    assert result["metadata"]["districts_connected"] == 4
    assert result["metadata"]["total_population_reached"] == 1000


def test_graph_with_single_node(prim_algorithm):
    nodes = {"A": make_node("A", population=500)}

    result = prim_algorithm.run(edge_list=[], nodes=nodes)

    assert_mst_output_shape(result)
    assert result["edges"] == []
    assert result["cost"] == 0.0
    assert result["metadata"]["districts_connected"] == 0
    assert result["metadata"]["total_population_reached"] == 0


def test_disconnected_graph_returns_spanning_forest(prim_algorithm):
    nodes = {
        "A": make_node("A", population=100),
        "B": make_node("B", population=200),
        "C": make_node("C", population=300),
        "D": make_node("D", population=400),
    }
    edge_list = [
        make_edge("A", "B", 3.0),
        make_edge("C", "D", 2.0),
    ]

    result = prim_algorithm.run(edge_list=edge_list, nodes=nodes)

    assert_mst_output_shape(result)
    assert result["cost"] == 5.0
    assert set(result["edges"]) == {"A-B", "C-D"}
    assert result["metadata"]["districts_connected"] == 4
    assert result["metadata"]["total_population_reached"] == 1000


def test_tie_breaking_population(prim_algorithm):
    nodes = {
        "A": make_node("A", population=100),
        "B": make_node("B", population=200),
        "C": make_node("C", population=900),
    }
    edge_list = [
        make_edge("A", "B", 10.0),
        make_edge("A", "C", 10.0),
        make_edge("B", "C", 99.0),
    ]

    result = prim_algorithm.run(edge_list=edge_list, nodes=nodes)

    assert_mst_output_shape(result)
    assert result["cost"] == 20.0
    assert result["edges"][0] == "A-C"
    assert set(result["edges"]) == {"A-C", "A-B"}
    assert result["metadata"]["total_population_reached"] == 1200


def test_large_input_simulation(prim_algorithm):
    node_count = 100
    nodes = {
        f"N{i}": make_node(f"N{i}", population=i * 10)
        for i in range(node_count)
    }
    chain_edges = [
        make_edge(f"N{i}", f"N{i + 1}", 1.0)
        for i in range(node_count - 1)
    ]
    expensive_shortcuts = [
        make_edge(f"N{i}", f"N{i + 2}", 50.0)
        for i in range(node_count - 2)
    ]

    result = prim_algorithm.run(
        edge_list=chain_edges + expensive_shortcuts,
        nodes=nodes,
    )

    assert_mst_output_shape(result)
    assert len(result["edges"]) == node_count - 1
    assert result["cost"] == 99.0
    assert set(result["edges"]) == {f"N{i}-N{i + 1}" for i in range(node_count - 1)}
    assert result["metadata"]["districts_connected"] == node_count
    assert result["metadata"]["total_population_reached"] == sum(
        node.population for node in nodes.values()
    )


def test_empty_graph(prim_algorithm):
    result = prim_algorithm.run(edge_list=[], nodes={})

    assert_mst_output_shape(result)
    assert result["edges"] == []
    assert result["cost"] == 0.0
    assert result["metadata"]["districts_connected"] == 0
    assert result["metadata"]["total_population_reached"] == 0


def test_output_structure(prim_algorithm, basic_nodes):
    result = prim_algorithm.run(
        edge_list=[make_edge("A", "B", 7.25)],
        nodes=basic_nodes,
    )

    assert_mst_output_shape(result)
    assert set(result["metadata"].keys()) == {
        "algorithm",
        "districts_connected",
        "total_population_reached",
    }


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
