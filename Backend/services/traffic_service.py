from typing import List

from Backend.algorithms.greedy.traffic_signal import TrafficSignalOptimizer
from Backend.algorithms.greedy.emergency_priority import EmergencyPrioritySystem
from Backend.models.enums import TimePeriod
from services.traffic_ml_service import TrafficMLService


class TrafficService:
    """
    manages traffic signal optimization and congestion analysis:
    1. Greedy traffic signal optimization
    2. Emergency override (ambulance priority)
    3. Congestion index calculation
    """

    def __init__(self, graph):
        self.greedy = TrafficSignalOptimizer()
        self.emergency = EmergencyPrioritySystem()
        self.ml = TrafficMLService(graph).train()

    # MAIN PIPELINE

    def generate_signal_plan(
        self,
        graph,
        time_period: TimePeriod,
        emergency_path=None
    ):
        """
        Returns final optimized signal plan with optional emergency override.
        """

        # 1. Run greedy optimization
        base_result = self.greedy.run(graph, time_period=time_period)
        signal_plan = base_result["signal_plan"]

        emergency_active = bool(emergency_path)

        # 2. Apply emergency override if needed
        if emergency_active:
            signal_plan = self.emergency.run(
                graph,
                base_signal_plan=signal_plan,
                emergency_path=emergency_path
            )

        # 3. Compute congestion index
        global_ci = self.calculate_congestion_index(graph, time_period)

        if emergency_active:
            route_ci = self.calculate_congestion_index_on_emergency_path(
                graph,
                time_period,
                emergency_path
            )
        else:
            route_ci = 0.0

        # 4. Return standardized output
        return {
            "signal_plan": signal_plan,
            "cost": 0.0,
            "metadata": {
                "global_congestion_index": global_ci,
                "route_emergency_congestion_index": route_ci,
                "emergency_active": emergency_active,
                "time_period": time_period.value
            }
        }

    # GLOBAL CONGESTION for entire graph

    def calculate_congestion_index(self, graph, time_period: TimePeriod) -> float:
        """
        Global Index = Σ traffic flow / Σ capacity
        """

        total_flow = 0
        total_capacity = 0

        for node in graph.get_all_nodes():
            edges = graph.get_neighbors(node)

            for edge in edges:
                flow = edge.traffic.get_flow(time_period)
                capacity = getattr(edge, "capacity", 0)

                total_flow += flow
                total_capacity += capacity

        if total_capacity == 0:
            return 0.0

        return round(total_flow / total_capacity, 3)

    # ROUTE CONGESTION (EMERGENCY PATH)

    def calculate_congestion_index_on_emergency_path(self,graph,time_period: TimePeriod,emergency_path) -> float:

        if not emergency_path or len(emergency_path) < 2:
           return 0.0

        total_flow = 0
        total_capacity = 0

        for i in range(len(emergency_path) - 1):
            u = str(emergency_path[i])
            v = str(emergency_path[i + 1])

            edge = None

        # Use your adjacency list (correct design)
            for e in graph.get_neighbors(u):
                if str(e.target_id) == v:
                    edge = e
                    break

            if edge is None:
            # optional debug (VERY useful for routing bugs)
               print(f"[WARN] Missing edge: {u} → {v}")
               continue

            flow = edge.traffic.get_flow(time_period)
            capacity = getattr(edge, "capacity", 0)

            total_flow += flow
            total_capacity += capacity

        if total_capacity == 0:
          return 0.0

        return round(total_flow / total_capacity, 3)
    
    # Normal route congestion index
    def calculate_route_congestion_index(self,graph,time_period: TimePeriod,path: List[str]) -> float:
        """
        CI for a normal route (no emergency)
        """

        if not path or len(path) < 2:
            return 0.0

        total_flow = 0
        total_capacity = 0

        for i in range(len(path) - 1):
            u = str(path[i])
            v = str(path[i + 1])

            edge = None

            for e in graph.get_neighbors(u):
                if str(e.target_id) == v:
                    edge = e
                    break

            if edge is None:
                continue

            total_flow += edge.traffic.get_flow(time_period)
            total_capacity += getattr(edge, "capacity", 0)

        if total_capacity == 0:
            return 0.0

        return round(total_flow / total_capacity, 3)