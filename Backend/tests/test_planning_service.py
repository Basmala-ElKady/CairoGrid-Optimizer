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
from Backend.services import planning_service
from Backend.services.planning_service import PlanningService


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
def expansion_nodes():
    return {
        "A": make_node("A", population=100),
        "B": make_node("B", population=200),
        "C": make_node("C", population=300),
        "D": make_node("D", population=400),
    }


@pytest.fixture
def expansion_edges():
    return [
        make_edge("A", "B", 1.0),
        make_edge("B", "C", 2.0),
        make_edge("A", "C", 5.0),
        make_edge("C", "D", 1.0),
        make_edge("B", "D", 4.0),
    ]


def assert_service_output_shape(response):
    assert set(response.keys()) == {"result", "metrics"}
    assert set(response["result"].keys()) == {"edges", "cost", "metadata"}
    assert isinstance(response["result"]["edges"], list)
    assert isinstance(response["result"]["cost"], float)
    assert isinstance(response["result"]["metadata"], dict)
    assert isinstance(response["metrics"]["execution_time_ms"], float)


def test_service_initializes_prim_algorithm():
    service = PlanningService()

    assert isinstance(service.algorithm, PrimAlgorithm)


def test_service_calls_run(monkeypatch, expansion_nodes, expansion_edges):
    calls = []

    class FakePrimAlgorithm:
        def run(self, graph=None, **kwargs):
            calls.append(kwargs)
            return {
                "edges": ["A-B"],
                "cost": 1.0,
                "metadata": {
                    "algorithm": "Prim",
                    "districts_connected": 2,
                    "total_population_reached": 300,
                },
            }

    monkeypatch.setattr(planning_service, "PrimAlgorithm", FakePrimAlgorithm)
    service = PlanningService()

    response = service.plan_expansion(expansion_edges, expansion_nodes)

    assert calls == [{"edge_list": expansion_edges, "nodes": expansion_nodes}]
    assert isinstance(response["metrics"]["execution_time_ms"], float)
    assert response["result"]["edges"] == ["A-B"]
    assert response["result"]["cost"] == 1.0


def test_service_aggregates_total_cost_districts_and_population(
    expansion_nodes,
    expansion_edges,
):
    service = PlanningService()

    response = service.plan_expansion(expansion_edges, expansion_nodes)

    assert_service_output_shape(response)
    result = response["result"]
    assert result["cost"] == 4.0
    assert set(result["edges"]) == {"A-B", "B-C", "C-D"}
    assert result["metadata"]["districts_connected"] == 4
    assert result["metadata"]["total_population_reached"] == 1000


def test_service_output_format(expansion_nodes, expansion_edges):
    service = PlanningService()

    response = service.plan_expansion(expansion_edges, expansion_nodes)

    assert_service_output_shape(response)
    assert response["result"]["metadata"]["algorithm"] == "Prim"
    assert set(response["result"]["metadata"].keys()) == {
        "algorithm",
        "districts_connected",
        "total_population_reached",
    }
    assert set(response["metrics"].keys()) == {"execution_time_ms"}


def test_service_no_edges_available(expansion_nodes):
    service = PlanningService()

    response = service.plan_expansion(edge_list=[], nodes=expansion_nodes)

    assert_service_output_shape(response)
    assert response["result"] == {
        "edges": [],
        "cost": 0.0,
        "metadata": {
            "algorithm": "Prim",
            "districts_connected": 0,
            "total_population_reached": 0,
        },
    }


def test_service_invalid_dataset_raises_attribute_error(expansion_nodes):
    service = PlanningService()
    invalid_edges = [{"source_id": "A", "target_id": "B", "distance": 1.0}]

    with pytest.raises(AttributeError):
        service.plan_expansion(edge_list=invalid_edges, nodes=expansion_nodes)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
