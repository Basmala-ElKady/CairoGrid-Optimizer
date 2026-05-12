from Backend.algorithms.common.base_algorithm import BaseAlgorithm
from Backend.models.enums import TimePeriod

class TrafficSignalOptimizer(BaseAlgorithm):
    def __init__(self):
        super().__init__("Greedy Signal Optimization")
    
    def calculate_priority_score(self, edge, time_period):
        """
        Greedy Priority Score
    
        Combines:
        - Traffic Flow
        - Waiting Time
        - Emergency Priority
        """
    
        traffic_flow = edge.traffic.get_flow(time_period)
    
        # Optional attributes with safe defaults
        waiting_time = getattr(edge.traffic, "waiting_time", 10)
    
        emergency_priority = 0
        if getattr(edge.traffic, "has_emergency_vehicle", False):
            emergency_priority = 100
    
        priority_score = (
            (traffic_flow * 0.6) +
            (waiting_time * 0.3) +
            (emergency_priority * 0.1)
        )
    
        return priority_score
    
    def calculate_green_time(self, traffic_flow, emergency=False):
        """
        Dynamic green light duration.
    
        Higher congestion → longer green signal.
        """
    
        if emergency:
            return 120
    
        green_time = 30 + (traffic_flow // 5)
    
        # Prevent unrealistic values
        green_time = max(30, min(green_time, 90))
    
        return green_time
    
    def run(self, *args, **kwargs):
    
        graph = kwargs.pop("graph", args[0] if len(args) > 0 else None)
    
        time_period = kwargs.get(
            "time_period",
            TimePeriod.MORNING_PEAK
        )
    
        signal_plan = {}
    
        total_waiting_time = 0
        processed_roads = 0
    
        for node_id in graph.nodes:
    
            incoming_edges = graph.get_incoming_edges(node_id)
    
            if not incoming_edges:
                continue
    
            # Greedy Choice:
            # Select edge with highest priority score
            best_edge = max(
                incoming_edges,
                key=lambda e: self.calculate_priority_score(
                    e,
                    time_period
                ),
                default=None
            )
    
            if not best_edge:
                continue
    
            node_signals = {}
    
            for edge in incoming_edges:
    
                edge_id = f"{edge.source_id}-{edge.target_id}"
    
                traffic_flow = edge.traffic.get_flow(time_period)
    
                emergency = getattr(
                    edge.traffic,
                    "has_emergency_vehicle",
                    False
                )
    
                # Default short signal
                green_time = 20
    
                # Greedy-selected edge gets optimized duration
                if edge == best_edge:
                    green_time = self.calculate_green_time(
                        traffic_flow,
                        emergency
                    )
    
                node_signals[edge_id] = green_time
    
                total_waiting_time += getattr(
                    edge.traffic,
                    "waiting_time",
                    10
                )
    
                processed_roads += 1
    
            signal_plan[f"node_{node_id}"] = node_signals
    
        avg_waiting_time = (
            total_waiting_time / processed_roads
            if processed_roads > 0 else 0
        )
    
        return {
            "signal_plan": signal_plan,
            "cost": 0.0,
            "metadata": {
                "algorithm": "Greedy Signal Optimization",
                "time_context": time_period.value,
                "average_waiting_time": round(avg_waiting_time, 2),
                "processed_intersections": len(signal_plan),
                "strategy":
                    "Greedy local optimization based on "
                    "traffic flow, waiting time, "
                    "and emergency priority"
            }
        }