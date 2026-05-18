from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends

from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import Dijkstra
from Backend.api.dependencies import get_runtime
from Backend.api.errors import ApiError
from Backend.api.runtime import BackendRuntime
from Backend.api.schemas import (
    MLEdgePredictionRequest,
    MLEdgePredictionResponse,
    MLPredictRequest,
    MLPredictResponse,
)

router = APIRouter(tags=["ml"])


def _congestion_label(ratio: float) -> str:
    if ratio >= 0.9:
        return "SEVERE"
    if ratio >= 0.7:
        return "HEAVY"
    if ratio >= 0.45:
        return "MODERATE"
    return "LOW"


def _status_phrase(ratio: float) -> str:
    """Matches the interpret_congestion() output structure of Backend/tests/test_ml.py."""
    if ratio < 0.3:
        return "LOW traffic (smooth flow)"
    if ratio < 0.6:
        return "MODERATE traffic (some delays)"
    if ratio < 0.8:
        return "HEAVY traffic (slow movement)"
    return "SEVERE congestion (possible jam)"


@router.post("/api/ml/edge-prediction", response_model=MLEdgePredictionResponse)
def predict_edge_traffic(request: MLEdgePredictionRequest, runtime: BackendRuntime = Depends(get_runtime)):
    """
    Per-edge traffic forecast mirroring Backend/tests/test_ml.py.
    Takes a single road segment (source-target) and returns its current flow/congestion
    plus a next-step prediction. NO route advice, NO alternative paths.
    """
    source_node = runtime.get_node(request.source)
    target_node = runtime.get_node(request.target)
    if source_node is None:
        raise ApiError(404, "invalid_source", f"Unknown source node '{request.source}'.")
    if target_node is None:
        raise ApiError(404, "invalid_target", f"Unknown target node '{request.target}'.")

    edge = runtime.get_edge(request.source, request.target) or runtime.get_edge(request.target, request.source)
    if edge is None:
        raise ApiError(404, "invalid_edge", f"No road exists between '{request.source}' and '{request.target}'.")

    capacity = float(edge.capacity) if edge.capacity else 1e-6
    flows = list(edge.traffic.flows.values())
    current_flow = float(flows[-1]) if flows else 0.0
    current_ratio = current_flow / capacity

    started = perf_counter()
    predicted_ratio = float(runtime.ml_service.predict_congestion(edge))
    runtime_ms = (perf_counter() - started) * 1000
    predicted_flow = predicted_ratio * capacity

    delta = predicted_ratio - current_ratio
    trend = "INCREASING" if delta > 0.001 else ("DECREASING" if delta < -0.001 else "STABLE")

    edge_id = f"{edge.source_id}-{edge.target_id}"
    distance_km = float(edge.metadata.get("distance_km", edge.distance) if hasattr(edge, "metadata") and edge.metadata else edge.distance)

    return {
        "edge_id": edge_id,
        "source": edge.source_id,
        "target": edge.target_id,
        "source_name": source_node.name,
        "target_name": target_node.name,
        "capacity": round(capacity, 1),
        "distance_km": round(distance_km, 3),
        "current": {
            "flow": round(current_flow, 1),
            "congestion": round(current_ratio, 3),
            "status": _status_phrase(current_ratio),
        },
        "prediction": {
            "flow": round(predicted_flow, 1),
            "congestion": round(predicted_ratio, 3),
            "status": _status_phrase(predicted_ratio),
        },
        "delta": round(delta, 3),
        "trend": trend,
        "runtime_ms": round(runtime_ms, 3),
    }


@router.post("/api/ml/predict", response_model=MLPredictResponse)
def predict_traffic(request: MLPredictRequest, runtime: BackendRuntime = Depends(get_runtime)):
    if runtime.get_node(request.source) is None:
        raise ApiError(404, "invalid_source", f"Unknown source node '{request.source}'.")
    if runtime.get_node(request.destination) is None:
        raise ApiError(404, "invalid_destination", f"Unknown destination node '{request.destination}'.")
    if request.source == request.destination:
        raise ApiError(400, "same_source_destination", "Source and destination must be different.")

    base_route = runtime.execute_route_algorithm(
        Dijkstra(),
        request.source,
        request.destination,
        request.time_period.value,
        "normal",
    )
    if not base_route.path:
        raise ApiError(404, "no_route", "No baseline route could be found for prediction.")

    current_metrics = runtime.compute_path_metrics(base_route.path, request.time_period.value, "normal")
    forecast_steps = max(1, request.prediction_horizon // 15)
    period = runtime.time_period_enum(request.time_period.value)

    route_edges = []
    for source, target in zip(base_route.path, base_route.path[1:]):
        edge = runtime.get_edge(source, target) or runtime.get_edge(target, source)
        if edge is not None:
            route_edges.append(edge)

    trend_data = []
    for step in range(1, forecast_steps + 1):
        step_ratios = []
        for edge in route_edges:
            forecast_flow = runtime.ml_service.forecast_edge_flows(edge, steps=step)[-1]
            step_ratios.append(forecast_flow / max(float(edge.capacity), 1.0))
        avg_ratio = sum(step_ratios) / max(1, len(step_ratios))
        trend_data.append(
            {
                "horizon_minutes": step * 15,
                "congestion_ratio": round(avg_ratio, 3),
            }
        )

    forecast_graph = runtime.build_forecast_graph(forecast_steps, request.time_period.value)
    alt_algo = AStarAlgorithm()
    started = perf_counter()
    alternative_result = alt_algo.run(
        graph=forecast_graph,
        start_node=request.source,
        end_node=request.destination,
        **runtime.route_kwargs(request.time_period.value, "normal"),
    )
    _ = (perf_counter() - started) * 1000
    alternative_path = alternative_result.get("path", []) or base_route.path
    forecast_metrics = runtime.compute_path_metrics(alternative_path, request.time_period.value, "normal")

    final_ratio = trend_data[-1]["congestion_ratio"] if trend_data else 0.0
    recommended_delay = max(0.0, forecast_metrics["travel_time"] - current_metrics["travel_time"])

    return {
        "predicted_congestion": f"{_congestion_label(final_ratio)} ({round(final_ratio * 100, 1)}%)",
        "forecast_score": round(final_ratio, 3),
        "recommended_delay": round(recommended_delay, 3),
        "suggested_alternative": alternative_path,
        "trend_data": trend_data,
    }
