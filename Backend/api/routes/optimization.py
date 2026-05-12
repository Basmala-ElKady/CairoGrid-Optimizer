from __future__ import annotations

from fastapi import APIRouter, Depends

from Backend.api.dependencies import get_runtime
from Backend.api.errors import ApiError
from Backend.api.runtime import BackendRuntime
from Backend.api.schemas import MstResponse, TrafficOptimizeRequest, TrafficOptimizeResponse, TransitOptimizeRequest, TransitOptimizeResponse
from Backend.api.serializers import serialize_edge
from Backend.models.enums import TimePeriod

router = APIRouter(tags=["optimization"])


def _calculate_signal_balance(runtime: BackendRuntime, signal_plan: dict[str, dict[str, int]], period: TimePeriod) -> float:
    score = 0.0
    for node_key, allocations in signal_plan.items():
        node_id = node_key.replace("node_", "", 1)
        incoming = runtime.graph.get_incoming_edges(node_id)
        if not incoming:
            continue
        total_flow = sum(float(edge.traffic.get_flow(period)) for edge in incoming) or 1.0
        total_green = sum(allocations.values()) or 1.0
        for edge in incoming:
            edge_id = f"{edge.source_id}-{edge.target_id}"
            flow_share = float(edge.traffic.get_flow(period)) / total_flow
            green_share = allocations.get(edge_id, 0) / total_green
            score += flow_share * green_share
    return round(score, 4)


@router.get("/api/mst", response_model=MstResponse)
def get_mst(runtime: BackendRuntime = Depends(get_runtime)):
    result = runtime.planning_service.plan_expansion(runtime.potential_edges, runtime.node_map)
    selected_edges = result["result"]["edges"]
    selected_by_id = {edge.metadata.get("road_id"): edge for edge in runtime.potential_edges}
    mst_edges = [selected_by_id[edge_id] for edge_id in selected_edges if edge_id in selected_by_id]

    selected_nodes = set()
    for edge in mst_edges:
        selected_nodes.add(edge.source_id)
        selected_nodes.add(edge.target_id)

    total_candidate_cost = sum(float(edge.metadata.get("construction_cost_million_egp", edge.distance)) for edge in runtime.potential_edges)
    mst_cost = sum(float(edge.metadata.get("construction_cost_million_egp", edge.distance)) for edge in mst_edges)
    facilities = [
        runtime.node_map[node_id].name
        for node_id in selected_nodes
        if node_id in runtime.node_map and runtime.infer_node_kind(runtime.node_map[node_id]) in {"facility", "hospital", "hub"}
    ]

    return {
        "edges": [serialize_edge(edge) for edge in mst_edges],
        "total_cost": round(mst_cost, 3),
        "nodes_connected": int(result["result"]["metadata"].get("districts_connected", 0)),
        "savings": round(total_candidate_cost - mst_cost, 3),
        "critical_facilities": sorted(set(facilities)),
    }


@router.post("/api/traffic/optimize", response_model=TrafficOptimizeResponse)
def optimize_traffic(request: TrafficOptimizeRequest, runtime: BackendRuntime = Depends(get_runtime)):
    emergency_path = None
    if request.mode.value == "emergency":
        if not request.source or not request.destination:
            raise ApiError(400, "missing_route", "Emergency traffic optimization requires source and destination.")
        emergency_request = {
            "source": request.source,
            "destination": request.destination,
            "time_period": request.time_period.value,
            "mode": "emergency",
        }
        executed = runtime.execute_route_algorithm(
            runtime.emergency_service.astar,
            emergency_request["source"],
            emergency_request["destination"],
            emergency_request["time_period"],
            emergency_request["mode"],
        )
        emergency_path = executed.path

    period = runtime.time_period_enum(request.time_period.value)
    result = runtime.traffic_service.generate_signal_plan(
        runtime.graph,
        time_period=period,
        emergency_path=emergency_path,
    )
    signal_plan = result["signal_plan"]
    optimized_score = _calculate_signal_balance(runtime, signal_plan, period)

    baseline_plan = {}
    for node_key, allocations in signal_plan.items():
        baseline_plan[node_key] = {edge_id: 45 for edge_id in allocations}
    baseline_score = _calculate_signal_balance(runtime, baseline_plan, period)
    if baseline_score == 0:
        improvement = 0.0
    else:
        improvement = ((optimized_score - baseline_score) / baseline_score) * 100.0

    return {
        "signal_plan": signal_plan,
        "congestion_metrics": {
            "global_congestion_index": result["metadata"]["global_congestion_index"],
            "route_emergency_congestion_index": result["metadata"]["route_emergency_congestion_index"],
            "efficiency_score_before": baseline_score,
            "efficiency_score_after": optimized_score,
        },
        "improvement_percent": round(improvement, 3),
        "affected_intersections": sorted(signal_plan.keys()),
    }


@router.post("/api/transit/optimize", response_model=TransitOptimizeResponse)
def optimize_transit(request: TransitOptimizeRequest, runtime: BackendRuntime = Depends(get_runtime)):
    schedule_data, resource_data = runtime.build_default_transit_inputs(request.time_period.value)
    if request.schedule_data:
        schedule_data = [item.model_dump(exclude_none=True) for item in request.schedule_data]
    if request.resource_data:
        resource_data = [item.model_dump(exclude_none=True) for item in request.resource_data]

    allocation = runtime.transit_service.allocator.run(resource_data, capacity=request.capacity)
    scheduling = runtime.transit_service.scheduler.run(schedule_data, capacity=request.capacity)
    combined = runtime.transit_service.optimize(schedule_data, resource_data, capacity=request.capacity)

    buses_requested = sum(int(item.get("buses", 0)) for item in resource_data)
    selected_routes = list(allocation["schedule"].keys())

    return {
        "schedule": combined["schedule"],
        "allocations": allocation["schedule"],
        "resource_usage": {
            "capacity_limit": request.capacity,
            "buses_requested": buses_requested,
            "routes_selected": selected_routes,
        },
        "optimization_metrics": {
            "allocation_cost": allocation["cost"],
            "scheduling_cost": scheduling["cost"],
            "total_cost": combined["cost"],
            "resource_passengers_covered": allocation["metadata"]["total_passengers_covered"],
            "scheduled_passengers_covered": scheduling["metadata"]["total_passengers_covered"],
            "combined_passengers_covered": combined["metadata"]["total_passengers_covered"],
        },
    }
