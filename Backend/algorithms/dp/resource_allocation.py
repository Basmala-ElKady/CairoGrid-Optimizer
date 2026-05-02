"""
0/1 Knapsack via Dynamic Programming for bus fleet resource allocation.

    dp[i][w] = max(values[i-1] + dp[i-1][w - weights[i-1]], dp[i-1][w])

Items  = bus routes
Weight = buses assigned to each route
Value  = daily passengers served

Complexity: O(n * capacity) time, O(n * capacity) space.
"""

import logging
from Backend.algorithms.common.base_algorithm import BaseAlgorithm

logger = logging.getLogger(__name__)


class ResourceAllocationDP(BaseAlgorithm):
    """
    0/1 Knapsack DP for allocating a limited bus fleet across routes
    to maximise total daily passenger coverage.

    State definition:
        dp[i][w] = maximum passengers achievable considering the first
                   i routes with at most w buses available.

    Recurrence:
        if weight[i] <= w:
            dp[i][w] = max(value[i] + dp[i-1][w - weight[i]], dp[i-1][w])
        else:
            dp[i][w] = dp[i-1][w]
    """

    def __init__(self):
        super().__init__("ResourceAllocationDP")
        self.metadata.update({
            "time_complexity": "O(n * capacity)",
            "space_complexity": "O(n * capacity)"
        })

    def run(self, data_list, capacity=None, **kwargs):
        # Guard: capacity must be a positive integer for knapsack
        if capacity is None:
            capacity = 0
        capacity = int(capacity)

        if not data_list or capacity <= 0:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0},
            }

        n = len(data_list)

        # Extract weights and values with validation
        weights = []
        values = []
        for item in data_list:
            buses = item.get("buses", 0)
            if buses <= 0:
                logger.warning(
                    "Route %s has buses=%s — clamped to 1 for knapsack weight.",
                    item.get("route_id", "?"), buses,
                )
            weights.append(max(1, int(buses)))
            values.append(int(item.get("passengers", 0)))

        # DP table: dp[i][w] = max value using first i items with capacity w
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            for w in range(capacity + 1):
                if weights[i - 1] <= w:
                    # Recurrence: include or exclude item i
                    dp[i][w] = max(
                        values[i - 1] + dp[i - 1][w - weights[i - 1]],
                        dp[i - 1][w],
                    )
                else:
                    dp[i][w] = dp[i - 1][w]

        # Backtrack to reconstruct the optimal subset
        w = capacity
        selected = []

        for i in range(n, 0, -1):
            if w <= 0:
                break

            if dp[i][w] != dp[i - 1][w]:
                selected.append(data_list[i - 1])
                w -= weights[i - 1]

        # Build schedule dict from selected routes
        schedule = {}
        for idx, route in enumerate(selected):
            bus_id = route.get("route_id", f"B{idx+1}")
            schedule[bus_id] = [route.get("time", "00:00")]

        for k in schedule:
            schedule[k].sort()

        total_value = dp[n][capacity]

        return {
            "schedule": schedule,
            "cost": total_value,
            "metadata": {"total_passengers_covered": total_value},
        }