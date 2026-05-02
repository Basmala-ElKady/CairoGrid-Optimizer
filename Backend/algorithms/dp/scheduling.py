from Backend.algorithms.common.base_algorithm import BaseAlgorithm
import json

class SchedulingDP(BaseAlgorithm):
    """
    Scheduling algorithm using Dynamic Programming (Knapsack variation)
    to optimize bus trip scheduling based on passenger demand and capacity.
    """
    def __init__(self):
        super().__init__("SchedulingDP")
        self.metadata.update({
            "time_complexity": "O(n * capacity)",
            "space_complexity": "O(n * capacity)"
        })
        self._memo_cache = {}

    def run(self, data_list, capacity=None, **kwargs):
        """
        Executes the scheduling optimization.
        
        Args:
            data_list (list): List of trip data dictionaries.
            capacity (int, optional): Max capacity (e.g., number of trips). 
                                     If None, all trips are considered.
        """
        if not data_list:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0}
            }

        # Use a stable key for memoization
        # In a real scenario, we'd hash the data_list and capacity
        cache_key = (json.dumps(data_list, sort_keys=True), capacity)
        if cache_key in self._memo_cache:
            return self._memo_cache[cache_key]

        n = len(data_list)
        # For scheduling, if capacity is None, we take all trips.
        # If capacity is provided, we assume each trip has a 'weight' of 1.
        if capacity is None:
            actual_capacity = n
        else:
            actual_capacity = capacity

        # weights = [1 for _ in data_list] # Each trip counts as 1 towards capacity
        # values = [item.get("passengers", 0) for item in data_list]

        # Standard 0/1 Knapsack DP
        dp = [[0] * (actual_capacity + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            val = data_list[i-1].get("passengers", 0)
            wt = 1 # Weight of one trip
            for w in range(actual_capacity + 1):
                if wt <= w:
                    dp[i][w] = max(val + dp[i-1][w-wt], dp[i-1][w])
                else:
                    dp[i][w] = dp[i-1][w]

        # Reconstruct selected items
        selected_items = []
        w = actual_capacity
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i-1][w]:
                selected_items.append(data_list[i-1])
                w -= 1

        # Format output
        schedule = {}
        total_passengers = 0
        for item in selected_items:
            bus_id = item.get("bus_id", "Unknown")
            trip_time = item.get("time", "00:00")
            if bus_id not in schedule:
                schedule[bus_id] = []
            schedule[bus_id].append(trip_time)
            total_passengers += item.get("passengers", 0)

        # Sort times for each bus as required by tests
        for bus_id in schedule:
            schedule[bus_id].sort()

        result = {
            "schedule": schedule,
            "cost": total_passengers,
            "metadata": {
                "total_passengers_covered": total_passengers
            }
        }

        # Store in cache
        self._memo_cache[cache_key] = result
        return result