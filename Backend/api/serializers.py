from __future__ import annotations

from Backend.api.runtime import BackendRuntime
from Backend.models.edge import Edge
from Backend.models.enums import TimePeriod
from Backend.models.node import Node


def serialize_node(runtime: BackendRuntime, node: Node) -> dict:
    x, y = runtime.normalize_position(node)
    return {
        "id": node.id,
        "name": node.name,
        "type": runtime.infer_node_kind(node),
        "x": x,
        "y": y,
        "metadata": {
            **node.metadata,
            "population": node.population,
        },
    }


def serialize_edge(edge: Edge) -> dict:
    return {
        "source": str(edge.source_id),
        "target": str(edge.target_id),
        "distance": round(float(edge.distance), 3),
        "capacity": int(edge.capacity),
        "traffic": {
            "morning": float(edge.traffic.get_flow(TimePeriod.MORNING_PEAK)),
            "afternoon": float(edge.traffic.get_flow(TimePeriod.AFTERNOON)),
            "evening": float(edge.traffic.get_flow(TimePeriod.EVENING_PEAK)),
            "night": float(edge.traffic.get_flow(TimePeriod.NIGHT)),
        },
        "metadata": dict(edge.metadata),
    }


def build_route_response(runtime: BackendRuntime, path: list[str], time_period: str, mode: str, runtime_ms: float, nodes_explored: int, metadata: dict | None = None) -> dict:
    metrics = runtime.compute_path_metrics(path, time_period, mode)
    return {
        "path": path,
        "distance": metrics["distance"],
        "travel_time": metrics["travel_time"],
        "runtime_ms": round(runtime_ms, 3),
        "nodes_explored": int(nodes_explored),
        "traffic_level": metrics["traffic_level"],
        "steps": metrics["steps"],
        "path_coordinates": metrics["path_coordinates"],
        "metadata": metadata or {},
    }
