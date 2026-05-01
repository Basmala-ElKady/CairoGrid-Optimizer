from typing import Optional

from Backend.models.enums import TimePeriod
from Backend.services.intersection_priority import IntersectionPriority


class CostEvaluator:
    """Shared path-cost evaluator used by shortest-path algorithms.

    Modes:
    - benchmark: fair algorithm comparison using same cost model for all algorithms.
    - realistic: traffic/emergency-aware simulation behavior.

    Benchmark model options:
    - static: edge.distance
    - dynamic: edge.get_weight(period) using initial_time + arrival_time
    """

    def __init__(self, intersection_priority: Optional[IntersectionPriority] = None):
        self.intersection_priority = intersection_priority

    @staticmethod
    def map_time_to_period(time_value: float) -> TimePeriod:
        if 6 <= time_value < 10:
            return TimePeriod.MORNING_PEAK
        if 10 <= time_value < 16:
            return TimePeriod.AFTERNOON
        if 16 <= time_value < 20:
            return TimePeriod.EVENING_PEAK
        return TimePeriod.NIGHT

    @staticmethod
    def _clamp_multiplier(value: float) -> float:
        try:
            v = float(value)
        except Exception:
            return 1.0
        if v <= 0:
            return 1.0
        if v > 1.0:
            return 1.0
        return v

    @staticmethod
    def is_intersection(graph, node_id: str) -> bool:
        degree = len(graph.get_neighbors(node_id)) + len(graph.get_incoming_edges(node_id))
        return degree > 2

    def _base_weight(self, edge, initial_time: Optional[float], arrival_time_at_current: float, use_dynamic: bool) -> float:
        if not use_dynamic:
            return float(edge.distance)
        if initial_time is None:
            return float(edge.distance)
        period = self.map_time_to_period(initial_time + arrival_time_at_current)
        return float(edge.get_weight(period))

    def _emergency_multiplier(self, graph, current_node: str, is_emergency: bool, kwargs) -> float:
        if not is_emergency:
            return 1.0

        ip = kwargs.get("intersection_priority") or self.intersection_priority
        if ip is not None:
            if self.is_intersection(graph, current_node):
                return self._clamp_multiplier(ip.get_multiplier(current_node, True))
            return 1.0

        # Backward-compatible fallback knobs
        emergency_priority_intersection = kwargs.get("emergency_priority_intersection", None)
        if emergency_priority_intersection is not None:
            if self.is_intersection(graph, current_node):
                return self._clamp_multiplier(emergency_priority_intersection)
            return 1.0

        emergency_priority = kwargs.get("emergency_priority", 1.0)
        return self._clamp_multiplier(emergency_priority)

    def should_apply_emergency(self, kwargs) -> bool:
        mode = kwargs.get("mode", "realistic")
        if mode == "benchmark":
            return bool(kwargs.get("benchmark_enable_emergency", False))
        return bool(kwargs.get("is_emergency", False))

    def should_use_dynamic(self, kwargs) -> bool:
        mode = kwargs.get("mode", "realistic")
        if mode == "benchmark":
            benchmark_model = kwargs.get("benchmark_cost_model", "static")
            return benchmark_model == "dynamic"
        return kwargs.get("initial_time", None) is not None

    def edge_weight(self, graph, edge, current_node: str, arrival_time_at_current: float, **kwargs) -> float:
        initial_time = kwargs.get("initial_time", None)
        use_dynamic = self.should_use_dynamic(kwargs)
        is_emergency = self.should_apply_emergency(kwargs)

        base = self._base_weight(edge, initial_time, arrival_time_at_current, use_dynamic)
        mult = self._emergency_multiplier(graph, current_node, is_emergency, kwargs)
        return base * mult

    def min_multiplier_for_heuristic(self, **kwargs) -> float:
        if not self.should_apply_emergency(kwargs):
            return 1.0

        explicit = kwargs.get("min_priority_multiplier", None)
        if explicit is not None:
            return self._clamp_multiplier(explicit)

        ip = kwargs.get("intersection_priority") or self.intersection_priority
        if ip is not None:
            values = [ip.default_emergency_multiplier] + list(ip.overrides.values())
            if values:
                return min(self._clamp_multiplier(v) for v in values)
            return 1.0

        if kwargs.get("emergency_priority_intersection", None) is not None:
            return self._clamp_multiplier(kwargs.get("emergency_priority_intersection"))

        return self._clamp_multiplier(kwargs.get("emergency_priority", 1.0))
