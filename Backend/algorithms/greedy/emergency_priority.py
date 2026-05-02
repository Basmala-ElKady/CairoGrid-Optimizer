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
        print("\nEmergency Path:", " → ".join(emergency_path))

        # Start from the second node in the path, because that's where the 
        # signal for the incoming path segment is located.
        for i in range(len(emergency_path) - 1):
            current_node = emergency_path[i]
            next_node = emergency_path[i + 1]

            #Look at the 'next_node' (the intersection the vehicle is entering)
            node_key = f"node_{next_node}"

            if node_key not in base_plan:
                print(f"Skipping {node_key}: No signal plan found.")
                continue

            edges = base_plan[node_key]

            # We check for both directions in case the edge naming convention is flipped
            possible_edges = [
                f"{current_node}-{next_node}",
                f"{next_node}-{current_node}"
            ]

            found = False
            for edge_id in possible_edges:
                if edge_id in edges:
                    edges[edge_id] = 90
                    print(f"Emergency boost: {edge_id} → 90 at {node_key}")
                    found = True
                    break

            if not found:
                print(f"No exact match for incoming {current_node} at {node_key}, boosting all signals at this node.")
                for edge in edges:
                    edges[edge] = max(edges[edge], 70)

        return base_plan
