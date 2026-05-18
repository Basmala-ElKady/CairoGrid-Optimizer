from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TimePeriodKey(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"


class ModeKey(str, Enum):
    normal = "normal"
    emergency = "emergency"


class Coordinate(BaseModel):
    lat: float
    lng: float


class NodeSchema(BaseModel):
    id: str
    name: str
    type: str
    x: float
    y: float
    metadata: dict[str, Any]


class EdgeSchema(BaseModel):
    source: str
    target: str
    distance: float
    capacity: int
    traffic: dict[str, float]
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphSchema(BaseModel):
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]


class HealthSchema(BaseModel):
    status: str
    graph_loaded: bool
    nodes_count: int
    edges_count: int
    ml_ready: bool


class RouteRequest(BaseModel):
    source: str
    destination: str | None = None
    time_period: TimePeriodKey = TimePeriodKey.morning
    mode: ModeKey = ModeKey.normal

    @field_validator("source", "destination")
    @classmethod
    def strip_values(cls, value: str | None):
        if value is None:
            return value
        value = value.strip()
        return value or None


class RouteStepSchema(BaseModel):
    source: str
    source_name: str
    target: str
    target_name: str
    distance: float
    travel_time: float
    traffic_ratio: float


class RouteResponse(BaseModel):
    path: list[str]
    distance: float
    travel_time: float
    runtime_ms: float
    nodes_explored: int
    traffic_level: str
    steps: list[RouteStepSchema]
    path_coordinates: list[Coordinate]
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompareResponse(BaseModel):
    astar: RouteResponse
    dijkstra: RouteResponse
    winner: str


class MstResponse(BaseModel):
    edges: list[EdgeSchema]
    total_cost: float
    nodes_connected: int
    savings: float
    critical_facilities: list[str]
    runtime_ms: float = 0.0
    nodes_explored: int = 0


class TrafficOptimizeRequest(BaseModel):
    time_period: TimePeriodKey = TimePeriodKey.morning
    source: str | None = None
    destination: str | None = None
    mode: ModeKey = ModeKey.normal


class TrafficOptimizeResponse(BaseModel):
    signal_plan: dict[str, dict[str, int]]
    congestion_metrics: dict[str, Any]
    improvement_percent: float
    affected_intersections: list[str]
    runtime_ms: float = 0.0


class TransitTripInput(BaseModel):
    bus_id: str | None = None
    route_id: str | None = None
    time: str = "00:00"
    passengers: int = 0
    buses: int | None = None


class TransitOptimizeRequest(BaseModel):
    time_period: TimePeriodKey = TimePeriodKey.morning
    capacity: int = 8
    schedule_data: list[TransitTripInput] | None = None
    resource_data: list[TransitTripInput] | None = None


class TransitOptimizeResponse(BaseModel):
    schedule: dict[str, list[str]]
    allocations: dict[str, list[str]]
    resource_usage: dict[str, Any]
    optimization_metrics: dict[str, Any]
    runtime_ms: float = 0.0


class MLPredictRequest(BaseModel):
    source: str
    destination: str
    time_period: TimePeriodKey = TimePeriodKey.morning
    prediction_horizon: int = 30

    @field_validator("prediction_horizon")
    @classmethod
    def validate_horizon(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("prediction_horizon must be greater than zero")
        return value


class TrendPointSchema(BaseModel):
    horizon_minutes: int
    congestion_ratio: float


class MLPredictResponse(BaseModel):
    predicted_congestion: str
    forecast_score: float
    recommended_delay: float
    suggested_alternative: list[str]
    trend_data: list[TrendPointSchema]


class MLEdgePredictionRequest(BaseModel):
    source: str
    target: str


class MLEdgeStatusSchema(BaseModel):
    flow: float
    congestion: float
    status: str


class MLEdgePredictionResponse(BaseModel):
    edge_id: str
    source: str
    target: str
    source_name: str
    target_name: str
    capacity: float
    distance_km: float
    current: MLEdgeStatusSchema
    prediction: MLEdgeStatusSchema
    delta: float
    trend: str
    runtime_ms: float = 0.0
