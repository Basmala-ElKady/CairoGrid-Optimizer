from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from Backend.algorithms.common.cost_evaluator import CostEvaluator
from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import Dijkstra
from Backend.graph.graph_builder import GraphBuilder
from Backend.graph.transport_graph import TransportGraph
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.models.node import Node
from Backend.services.emergency_service import EmergencyService
from Backend.services.planning_service import PlanningService
from Backend.services.route_service import RouteService
from Backend.services.service_registry import get_ml_service
from Backend.services.traffic_ml_service import TrafficMLService
from Backend.services.traffic_service import TrafficService
from Backend.services.transit_service import TransitService
from Backend.utils.data_loader import DataLoader


@dataclass
class ExecutedRoute:
    path: list[str]
    runtime_ms: float
    nodes_explored: int
    metadata: dict[str, Any]


class BackendRuntime:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "Backend" / "data" / "processed"
        self.graph: TransportGraph | None = None
        self.node_map: dict[str, Node] = {}
        self.base_edges: list[Edge] = []
        self.potential_edges: list[Edge] = []
        self.bus_routes_df = pd.DataFrame()
        self.transport_demand_df = pd.DataFrame()
        self.route_service: RouteService | None = None
        self.traffic_service: TrafficService | None = None
        self.emergency_service: EmergencyService | None = None
        self.planning_service: PlanningService | None = None
        self.transit_service: TransitService | None = None
        self.ml_service: TrafficMLService | None = None

    def load(self) -> "BackendRuntime":
        districts = DataLoader.load_nodes(str(self.data_dir / "neighborhoods_districts.csv"), LocationType.DISTRICT)
        facilities = DataLoader.load_nodes(str(self.data_dir / "facilities.csv"), LocationType.FACILITY)
        all_nodes = districts + facilities
        self.node_map = {node.id: node for node in all_nodes}

        self._enrich_node_metadata(self.data_dir / "neighborhoods_districts.csv", is_facility=False)
        self._enrich_node_metadata(self.data_dir / "facilities.csv", is_facility=True)

        self.base_edges = DataLoader.load_edges(
            str(self.data_dir / "existing_roads.csv"),
            str(self.data_dir / "traffic_flow.csv"),
        )
        self.potential_edges = self._load_potential_edges(self.data_dir / "potential_roads.csv")
        self.graph = GraphBuilder.build_graph(all_nodes, self.base_edges)

        self.bus_routes_df = pd.read_csv(self.data_dir / "bus_routes.csv")
        self.transport_demand_df = pd.read_csv(self.data_dir / "transport_demand.csv")

        self.ml_service = get_ml_service(self.graph)
        self.route_service = RouteService()
        self.traffic_service = TrafficService(self.graph, ml_service=self.ml_service)
        self.emergency_service = EmergencyService(
            self.graph,
            facilities_csv=str(self.data_dir / "facilities.csv"),
            traffic_service=self.traffic_service,
        )
        self.planning_service = PlanningService()
        self.transit_service = TransitService()
        return self

    def _enrich_node_metadata(self, csv_path: Path, is_facility: bool) -> None:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip().str.lower()
        for _, row in df.iterrows():
            node_id = str(row["id"]).replace(".0", "")
            node = self.node_map.get(node_id)
            if not node:
                continue
            node.metadata.update(
                {
                    "category": "facility" if is_facility else "district",
                    "raw_type": str(row.get("type", "")),
                    "population": int(float(row.get("population", 0))) if pd.notna(row.get("population")) else 0,
                    "lat": float(row.get("y-coordinate", 0)),
                    "lng": float(row.get("x-coordinate", 0)),
                }
            )

    def _load_potential_edges(self, csv_path: Path) -> list[Edge]:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip().str.lower()
        edges: list[Edge] = []
        for _, row in df.iterrows():
            source = str(row["fromid"]).replace(".0", "")
            target = str(row["toid"]).replace(".0", "")
            construction_cost = float(row.get("construction cost(million egp)", 0))
            estimated_capacity = int(float(row.get("estimated capacity(vehicles/hour)", 0)))
            distance_km = float(row.get("distance(km)", 0))
            edges.append(
                Edge(
                    source_id=source,
                    target_id=target,
                    distance=construction_cost,
                    capacity=estimated_capacity,
                    condition=10,
                    traffic_profile={period: 0 for period in TimePeriod},
                    metadata={
                        "road_id": f"{source}-{target}",
                        "source": "potential",
                        "distance_km": distance_km,
                        "construction_cost_million_egp": construction_cost,
                        "estimated_capacity": estimated_capacity,
                    },
                )
            )
        return edges

    def ensure_graph(self) -> TransportGraph:
        if self.graph is None:
            raise RuntimeError("Graph has not been loaded.")
        return self.graph

    def get_node(self, node_id: str) -> Node | None:
        return self.node_map.get(str(node_id))

    def require_node(self, node_id: str) -> Node:
        node = self.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        return node

    @property
    def nodes(self) -> list[Node]:
        return list(self.node_map.values())

    def unique_edges(self) -> list[Edge]:
        return self.base_edges

    def graph_counts(self) -> tuple[int, int]:
        graph = self.ensure_graph()
        return len(graph.get_all_nodes()), len(self.base_edges)

    def infer_node_kind(self, node: Node) -> str:
        raw_type = str(node.metadata.get("raw_type", "")).lower()
        if node.metadata.get("category") == "district":
            return "district"
        if "medical" in raw_type or "hospital" in raw_type:
            return "hospital"
        if "hub" in raw_type or "station" in raw_type or "airport" in raw_type:
            return "hub"
        return "facility"

    def normalize_position(self, node: Node) -> tuple[float, float]:
        lngs = [n.metadata.get("lng", n.pos[0]) for n in self.nodes]
        lats = [n.metadata.get("lat", n.pos[1]) for n in self.nodes]
        min_lng, max_lng = min(lngs), max(lngs)
        min_lat, max_lat = min(lats), max(lats)
        lng = node.metadata.get("lng", node.pos[0])
        lat = node.metadata.get("lat", node.pos[1])
        x = 0.5 if max_lng == min_lng else (lng - min_lng) / (max_lng - min_lng)
        y = 0.5 if max_lat == min_lat else (max_lat - lat) / (max_lat - min_lat)
        return round(float(x), 4), round(float(y), 4)

    def get_edge(self, source: str, target: str) -> Edge | None:
        graph = self.ensure_graph()
        for edge in graph.get_neighbors(str(source)):
            if str(edge.target_id) == str(target):
                return edge
        return None

    def time_period_enum(self, time_period: str) -> TimePeriod:
        mapping = {
            "morning": TimePeriod.MORNING_PEAK,
            "afternoon": TimePeriod.AFTERNOON,
            "evening": TimePeriod.EVENING_PEAK,
            "night": TimePeriod.NIGHT,
        }
        return mapping[time_period]

    def period_start_hour(self, time_period: str) -> float:
        return {
            "morning": 8.0,
            "afternoon": 13.0,
            "evening": 18.0,
            "night": 22.0,
        }[time_period]

    def route_kwargs(self, time_period: str, mode: str) -> dict[str, Any]:
        return {
            "initial_time": self.period_start_hour(time_period),
            "mode": "realistic",
            "is_emergency": mode == "emergency",
            "base_emergency_multiplier": 0.8 if mode == "emergency" else 1.0,
        }

    def execute_route_algorithm(
        self,
        algorithm: Dijkstra | AStarAlgorithm,
        source: str,
        destination: str,
        time_period: str,
        mode: str,
    ) -> ExecutedRoute:
        graph = self.ensure_graph()
        started = perf_counter()
        result = algorithm.run(
            graph=graph,
            start_node=source,
            end_node=destination,
            **self.route_kwargs(time_period, mode),
        )
        runtime_ms = (perf_counter() - started) * 1000
        return ExecutedRoute(
            path=result.get("path", []),
            runtime_ms=round(runtime_ms, 3),
            nodes_explored=int(result.get("nodes_explored", 0)),
            metadata=result.get("metadata", {}),
        )

    def path_coordinates(self, path: list[str]) -> list[dict[str, float]]:
        coordinates = []
        for node_id in path:
            node = self.require_node(node_id)
            coordinates.append(
                {
                    "lat": round(float(node.metadata.get("lat", node.pos[1])), 6),
                    "lng": round(float(node.metadata.get("lng", node.pos[0])), 6),
                }
            )
        return coordinates

    def compute_path_metrics(self, path: list[str], time_period: str, mode: str) -> dict[str, Any]:
        if len(path) < 2:
            return {
                "distance": 0.0,
                "travel_time": 0.0,
                "traffic_level": "low",
                "steps": [],
                "path_coordinates": self.path_coordinates(path),
            }

        period = self.time_period_enum(time_period)
        distance_km = 0.0
        travel_time_minutes = 0.0
        steps: list[dict[str, Any]] = []
        ratios: list[float] = []
        base_speed_kmph = 35.0

        for source, target in zip(path, path[1:]):
            edge = self.get_edge(source, target) or self.get_edge(target, source)
            if edge is None:
                continue
            flow = float(edge.traffic.get_flow(period))
            congestion_ratio = flow / max(float(edge.capacity), 1.0)
            congestion_factor = 1.0 + (congestion_ratio ** 2)
            condition_factor = 11.0 / max(1, int(edge.condition))
            emergency_factor = 0.8 if mode == "emergency" else 1.0
            segment_minutes = (edge.distance / base_speed_kmph) * 60.0 * congestion_factor * condition_factor * emergency_factor

            distance_km += edge.distance
            travel_time_minutes += segment_minutes
            ratios.append(congestion_ratio)

            source_node = self.require_node(source)
            target_node = self.require_node(target)
            steps.append(
                {
                    "source": source,
                    "source_name": source_node.name,
                    "target": target,
                    "target_name": target_node.name,
                    "distance": round(edge.distance, 3),
                    "travel_time": round(segment_minutes, 3),
                    "traffic_ratio": round(congestion_ratio, 3),
                }
            )

        avg_ratio = sum(ratios) / max(1, len(ratios))
        if avg_ratio >= 0.85:
            traffic_level = "severe"
        elif avg_ratio >= 0.65:
            traffic_level = "high"
        elif avg_ratio >= 0.4:
            traffic_level = "medium"
        else:
            traffic_level = "low"

        return {
            "distance": round(distance_km, 3),
            "travel_time": round(travel_time_minutes, 3),
            "traffic_level": traffic_level,
            "steps": steps,
            "path_coordinates": self.path_coordinates(path),
        }

    def build_forecast_graph(self, steps: int, time_period: str) -> TransportGraph:
        graph = self.ensure_graph()
        period = self.time_period_enum(time_period)
        cloned_nodes = [
            Node(
                node_id=node.id,
                name=node.name,
                node_type=node.type,
                x=node.pos[0],
                y=node.pos[1],
                population=node.population,
                metadata=dict(node.metadata),
            )
            for node in self.nodes
        ]

        cloned_edges: list[Edge] = []
        for edge in self.base_edges:
            forecast = self.ml_service.forecast_edge_flows(edge, steps=steps)[-1]
            traffic_profile = {period_key: edge.traffic.get_flow(period_key) for period_key in TimePeriod}
            traffic_profile[period] = forecast
            cloned_edges.append(
                Edge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    distance=edge.distance,
                    capacity=edge.capacity,
                    condition=edge.condition,
                    traffic_profile=traffic_profile,
                    metadata=dict(edge.metadata),
                )
            )
        return GraphBuilder.build_graph(cloned_nodes, cloned_edges)

    def build_default_transit_inputs(self, time_period: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        resource_data = []
        for _, row in self.bus_routes_df.iterrows():
            resource_data.append(
                {
                    "route_id": str(row["RouteID"]),
                    "buses": int(row["Buses Assigned"]),
                    "passengers": int(row["Daily Passengers"]),
                    "time": "00:00",
                }
            )

        period_hour = int(self.period_start_hour(time_period))
        schedule_data = []
        for idx, (_, row) in enumerate(self.transport_demand_df.iterrows()):
            hour = period_hour + (idx // 4)
            minute = (idx % 4) * 15
            schedule_data.append(
                {
                    "bus_id": f"{row['FromID']}-{row['TOID']}",
                    "time": f"{hour % 24:02d}:{minute:02d}",
                    "passengers": int(row["Daily Passengers"]),
                }
            )

        return schedule_data, resource_data
