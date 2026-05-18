from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends

from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import Dijkstra
from Backend.api.dependencies import get_runtime
from Backend.api.errors import ApiError
from Backend.api.runtime import BackendRuntime
from Backend.api.schemas import CompareResponse, RouteRequest, RouteResponse
from Backend.api.serializers import build_route_response

router = APIRouter(tags=["routing"])


def _validate_route_request(runtime: BackendRuntime, source: str, destination: str | None) -> None:
    if runtime.get_node(source) is None:
        raise ApiError(404, "invalid_source", f"Unknown source node '{source}'.")
    if destination is not None and runtime.get_node(destination) is None:
        raise ApiError(404, "invalid_destination", f"Unknown destination node '{destination}'.")
    if destination is not None and source == destination:
        raise ApiError(400, "same_source_destination", "Source and destination must be different.")


def _run_pathfinding(runtime: BackendRuntime, algorithm: Dijkstra | AStarAlgorithm, request: RouteRequest) -> dict:
    _validate_route_request(runtime, request.source, request.destination)
    executed = runtime.execute_route_algorithm(
        algorithm=algorithm,
        source=request.source,
        destination=request.destination,
        time_period=request.time_period.value,
        mode=request.mode.value,
    )
    if not executed.path:
        raise ApiError(404, "no_route", "No route could be found for the requested nodes.")
    return build_route_response(
        runtime,
        executed.path,
        request.time_period.value,
        request.mode.value,
        executed.runtime_ms,
        executed.nodes_explored,
        executed.metadata,
    )


@router.post("/api/route/dijkstra", response_model=RouteResponse)
def route_dijkstra(request: RouteRequest, runtime: BackendRuntime = Depends(get_runtime)):
    if not request.destination:
        raise ApiError(400, "missing_destination", "Destination is required for Dijkstra routing.")
    return _run_pathfinding(runtime, Dijkstra(), request)


@router.post("/api/route/emergency", response_model=RouteResponse)
def route_emergency(request: RouteRequest, runtime: BackendRuntime = Depends(get_runtime)):
    if runtime.get_node(request.source) is None:
        raise ApiError(404, "invalid_source", f"Unknown source node '{request.source}'.")

    if request.destination:
        started = perf_counter()
        result = runtime.emergency_service.get_route(
            request.source,
            request.destination,
            current_time=runtime.period_start_hour(request.time_period.value),
            is_emergency=True
        )
        runtime_ms = (perf_counter() - started) * 1000
        path = result.get("path", [])
        if not path:
            raise ApiError(404, "no_route", "No emergency route could be found to the requested destination.")
        return build_route_response(
            runtime,
            path,
            request.time_period.value,
            "emergency",
            runtime_ms=runtime_ms,
            nodes_explored=int(result.get("nodes_explored", 0)),
            metadata=result.get("metadata", {}),
        )

    started = perf_counter()
    result = runtime.emergency_service.get_nearest_hospital_route(
        request.source,
        current_time=runtime.period_start_hour(request.time_period.value),
        is_emergency=True,
    )
    runtime_ms = (perf_counter() - started) * 1000
    path = result.get("path", [])
    if not path:
        raise ApiError(404, "no_route", "No emergency route could be found to a reachable hospital.")
    return build_route_response(
        runtime,
        path,
        request.time_period.value,
        "emergency",
        runtime_ms=runtime_ms,
        nodes_explored=int(result.get("nodes_explored", 0)),
        metadata=result.get("metadata", {}),
    )


@router.post("/api/route/compare", response_model=CompareResponse)
def compare_routes(request: RouteRequest, runtime: BackendRuntime = Depends(get_runtime)):
    if not request.destination:
        raise ApiError(400, "missing_destination", "Destination is required for route comparison.")

    astar_response = _run_pathfinding(runtime, AStarAlgorithm(), request)
    dijkstra_response = _run_pathfinding(runtime, Dijkstra(), request)

    astar_runtime = astar_response["runtime_ms"]
    dijkstra_runtime = dijkstra_response["runtime_ms"]
    if astar_runtime < dijkstra_runtime:
        winner = "astar"
    elif dijkstra_runtime < astar_runtime:
        winner = "dijkstra"
    else:
        winner = "tie"

    return {
        "astar": astar_response,
        "dijkstra": dijkstra_response,
        "winner": winner,
    }
