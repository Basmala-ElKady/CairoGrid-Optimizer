from Backend.algorithms.common.base_algorithm import BaseAlgorithm
from Backend.models.enums import TimePeriod

class TrafficSignalOptimizer(BaseAlgorithm):
    def __init__(self):
        super().__init__("Greedy Signal Optimization")
        
    def run(self, *args, **kwargs):
        graph = kwargs.pop("graph", args[0] if len(args) > 0 else None)
        """
        Greedy Logic: For any intersection, assign the longest 'Green Light' 
        duration to the road with the highest volume[cite: 1].

        """
        # Default to MORNING_PEAK if not provided
        time_period = kwargs.get('time_period', TimePeriod.MORNING_PEAK)
        signal_plan = {}

        for node_id in graph.nodes:
            # Get all edges entering this node
            incoming_edges = graph.get_incoming_edges(node_id)
            if not incoming_edges:
                continue

            # Greedy Choice: Find the edge with the max volume for the current time period[cite: 1]
            # Data derived from Traffic Flow Patterns in Project_Provided_Data.pdf[cite: 2]
            best_edge = max(
                incoming_edges, 
                key=lambda e: e.traffic.get_flow(time_period),
                default=None
            )
            if best_edge:
            # Assign 60s to the busiest road, 30s to others
               node_signals = {
               f"{edge.source_id}-{edge.target_id}": 30
               for edge in incoming_edges
            }

               node_signals[f"{best_edge.source_id}-{best_edge.target_id}"] = 60

               signal_plan[f"node_{node_id}"] = node_signals
        return {
            "signal_plan": signal_plan,
            "cost": 0.0,
            "metadata": {
                "algorithm": "Greedy Signal Optimization",
                "time_context": time_period.value
            }
        }
