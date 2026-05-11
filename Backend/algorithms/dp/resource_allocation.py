import logging
from Backend.algorithms.common.base_algorithm import BaseAlgorithm

logger = logging.getLogger(__name__)

class ResourceAllocationDP(BaseAlgorithm):
    def __init__(self):
        super().__init__("ResourceAllocationDP")
        self.metadata.update({
            "time_complexity": "O(n * capacity)",
            "space_complexity": "O(n * capacity)"
        })

    def run(self, *args, **kwargs):
        """
        Look how clean this is! It matches Dijkstra's signature perfectly.
        We extract what we need from args or kwargs internally.
        """
        # 1. Extraction Logic (The Smart Way)
        # If called as run(data_list, 10) -> args[0] is data, args[1] is capacity
        # If called as run(data=my_list, capacity=10) -> kwargs will have them
        data_list = kwargs.get("data_list", kwargs.get("data", args[0] if len(args) > 0 else []))
        capacity = kwargs.get("capacity", args[1] if len(args) > 1 else 0)

        # 2. Validation
        if not data_list or capacity <= 0:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0},
            }

        # 3. Core DP Logic (Knapsack)
        n = len(data_list)
        weights = [max(1, int(item.get("buses", 0))) for item in data_list]
        values = [int(item.get("passengers", 0)) for item in data_list]

        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            for w in range(capacity + 1):
                if weights[i - 1] <= w:
                    dp[i][w] = max(values[i - 1] + dp[i - 1][w - weights[i - 1]], dp[i - 1][w])
                else:
                    dp[i][w] = dp[i - 1][w]

        # 4. Reconstruction
        w_rem = capacity
        selected = []
        for i in range(n, 0, -1):
            if w_rem <= 0: break
            if dp[i][w_rem] != dp[i - 1][w_rem]:
                selected.append(data_list[i - 1])
                w_rem -= weights[i - 1]

        # 5. Result Formatting
        schedule = {route.get("route_id", f"R{idx}"): [route.get("time", "00:00")] 
                    for idx, route in enumerate(selected)}

        return {
            "schedule": schedule,
            "cost": dp[n][capacity],
            "metadata": {"total_passengers_covered": dp[n][capacity]},
        }