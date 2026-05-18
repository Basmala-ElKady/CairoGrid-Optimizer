from Backend.algorithms.common.base_algorithm import BaseAlgorithm

class EmergencyPrioritySystem(BaseAlgorithm):
    def __init__(self):
        super().__init__("Emergency Priority Overrider")

    def run(self, *args, **kwargs):
        graph = kwargs.pop("graph", args[0] if len(args) > 0 else None)
        base_plan = kwargs.get('base_signal_plan', {})
        emergency_path = kwargs.get('emergency_path', [])

        if not emergency_path:
            return base_plan

        emergency_path = [str(n) for n in emergency_path]

        for i in range(len(emergency_path) - 1):
            current_node = emergency_path[i]
            next_node = emergency_path[i + 1]
            node_key = f"node_{next_node}"

            if node_key not in base_plan:
                continue

            edges = base_plan[node_key]
            possible_edges = [
                f"{current_node}-{next_node}",
                f"{next_node}-{current_node}",
            ]

            found = False
            for edge_id in possible_edges:
                if edge_id in edges:
                    edges[edge_id] = 90
                    found = True
                    break

            if not found:
                for edge in edges:
                    edges[edge] = max(edges[edge], 70)

        return base_plan
