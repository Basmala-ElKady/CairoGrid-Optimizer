from Backend.algorithms.common.base_algorithm import BaseAlgorithm

class EmergencyPrioritySystem(BaseAlgorithm):
    def __init__(self):
        super().__init__("Emergency Priority Overrider")
     
    def apply_emergency_boost(
        self,
        edges,
        preferred_edge
    ):
        """
        Give emergency route highest priority.
        """
     
        for edge_id in edges:
     
            # Main emergency direction
            if edge_id == preferred_edge:
                edges[edge_id] = 120
     
            # Reduce competing directions
            else:
                edges[edge_id] = min(edges[edge_id], 15)
     
    def run(self, *args, **kwargs):
     
        graph = kwargs.pop(
            "graph",
            args[0] if len(args) > 0 else None
        )
     
        base_plan = kwargs.get(
            "base_signal_plan",
            {}
        )
     
        emergency_path = kwargs.get(
            "emergency_path",
            []
        )
     
        if not emergency_path:
            return {
                "signal_plan": base_plan,
                "metadata": {
                    "emergency_override": False
                }
            }
     
        emergency_path = [str(node) for node in emergency_path]
     
        print("\nEmergency Path:")
        print(" → ".join(emergency_path))
     
        optimized_nodes = []
     
        for i in range(len(emergency_path) - 1):
     
            current_node = emergency_path[i]
            next_node = emergency_path[i + 1]
     
            node_key = f"node_{next_node}"
     
            if node_key not in base_plan:
                print(f"Skipping {node_key}: no signal plan found.")
                continue
     
            edges = base_plan[node_key]
     
            possible_edges = [
                f"{current_node}-{next_node}",
                f"{next_node}-{current_node}"
            ]
     
            found = False
     
            for edge_id in possible_edges:
     
                if edge_id in edges:
     
                    self.apply_emergency_boost(
                        edges,
                        edge_id
                    )
     
                    print(
                        f"Emergency priority applied "
                        f"to {edge_id} at {node_key}"
                    )
     
                    optimized_nodes.append(node_key)
     
                    found = True
                    break
     
            # Fallback handling
            if not found:
     
                print(
                    f"No exact edge match at {node_key}. "
                    f"Applying fallback optimization."
                )
     
                # Greedy fallback:
                # Increase all signals moderately
                for edge in edges:
                    edges[edge] = max(edges[edge], 70)
     
        return {
            "signal_plan": base_plan,
            "metadata": {
                "algorithm": "Emergency Priority Override",
                "emergency_override": True,
                "optimized_nodes": optimized_nodes,
                "emergency_path": emergency_path,
                "strategy":
                    "Greedy emergency preemption "
                    "with dynamic signal override"
            }
        }