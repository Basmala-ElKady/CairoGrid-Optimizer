# from Backend.algorithms.common.base_algorithm import BaseAlgorithm
# import json

# class SchedulingDP(BaseAlgorithm):
#     """
#     Scheduling algorithm using Dynamic Programming (Knapsack variation)
#     to optimize bus trip scheduling based on passenger demand and capacity.
#     """
#     def __init__(self):
#         super().__init__("SchedulingDP")
#         self.metadata.update({
#             "time_complexity": "O(n * capacity)",
#             "space_complexity": "O(n * capacity)"
#         })
#         self._memo_cache = {}

#     def run(self, *args, **kwargs):
#         data_list = kwargs.pop("data_list", args[0] if len(args) > 0 else [])
#         capacity = kwargs.pop("capacity", args[1] if len(args) > 1 else None)
#         """
#         Executes the scheduling optimization.
        
#         Args:
#             data_list (list): List of trip data dictionaries.
#             capacity (int, optional): Max capacity (e.g., number of trips). 
#                                      If None, all trips are considered.
#         """
#         if not data_list:
#             return {
#                 "schedule": {},
#                 "cost": 0,
#                 "metadata": {"total_passengers_covered": 0}
#             }

#         # Use a stable key for memoization
#         # In a real scenario, we'd hash the data_list and capacity
#         cache_key = (json.dumps(data_list, sort_keys=True), capacity)
#         if cache_key in self._memo_cache:
#             return self._memo_cache[cache_key]

#         n = len(data_list)
#         # For scheduling, if capacity is None, we take all trips.
#         # If capacity is provided, we assume each trip has a 'weight' of 1.
#         if capacity is None:
#             actual_capacity = n
#         else:
#             actual_capacity = capacity

#         # weights = [1 for _ in data_list] # Each trip counts as 1 towards capacity
#         # values = [item.get("passengers", 0) for item in data_list]

#         # Standard 0/1 Knapsack DP
#         dp = [[0] * (actual_capacity + 1) for _ in range(n + 1)]

#         for i in range(1, n + 1):
#             val = data_list[i-1].get("passengers", 0)
#             wt = 1 # Weight of one trip
#             for w in range(actual_capacity + 1):
#                 if wt <= w:
#                     dp[i][w] = max(val + dp[i-1][w-wt], dp[i-1][w])
#                 else:
#                     dp[i][w] = dp[i-1][w]

#         # Reconstruct selected items
#         selected_items = []
#         w = actual_capacity
#         for i in range(n, 0, -1):
#             if dp[i][w] != dp[i-1][w]:
#                 selected_items.append(data_list[i-1])
#                 w -= 1

#         # Format output
#         schedule = {}
#         total_passengers = 0
#         for item in selected_items:
#             bus_id = item.get("bus_id", "Unknown")
#             trip_time = item.get("time", "00:00")
#             if bus_id not in schedule:
#                 schedule[bus_id] = []
#             schedule[bus_id].append(trip_time)
#             total_passengers += item.get("passengers", 0)

#         # Sort times for each bus as required by tests
#         for bus_id in schedule:
#             schedule[bus_id].sort()

#         result = {
#             "schedule": schedule,
#             "cost": total_passengers,
#             "metadata": {
#                 "total_passengers_covered": total_passengers
#             }
#         }

#         # Store in cache
#         self._memo_cache[cache_key] = result
#         return result
import logging
from Backend.algorithms.common.base_algorithm import BaseAlgorithm

logger = logging.getLogger(__name__)

class SchedulingDP(BaseAlgorithm):
    """
    Weighted Interval Scheduling using Dynamic Programming.
    Optimizes task scheduling based on time compatibility and passenger weight.
    """

    def __init__(self):
        super().__init__("SchedulingDP")
        self.metadata.update({
            "time_complexity": "O(n log n)",  # Sorting + Binary Search
            "space_complexity": "O(n)"        # DP table and interval storage
        })

    def run(self, *args, **kwargs):
        """
        Main execution method for the scheduling algorithm.
        Supports flexible input via *args or **kwargs.
        """
        # 1. Flexible Data Extraction: Supports positional or keyword arguments
        data_list = kwargs.get("data", args[0] if len(args) > 0 else [])
        capacity = kwargs.get("capacity", args[1] if len(args) > 1 else None)
        
        # Edge case: Return empty structure if no data is provided
        if not data_list:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0}
            }

        # 2. Preprocessing: Convert raw data into sortable interval objects
        intervals = self._build_intervals(data_list)
        
        # Sort intervals by finish time - Crucial for the Greedy choice in DP
        intervals.sort(key=lambda x: x[1])
        
        n = len(intervals)
        # DP table to store the maximum value (passengers) at each step
        dp = [0] * (n + 1)
        
        # 3. Core DP Calculation
        for i in range(1, n + 1):
            current_start, current_end, current_val, _ = intervals[i-1]
            
            # Find the last task that finished before the current task started
            last_compatible = self._find_last_compatible(intervals, i - 1, current_start)
            
            # Decision: Maximize value by either including or excluding the current task
            # dp[i] = max(value_if_included, value_if_excluded)
            dp[i] = max(current_val + dp[last_compatible + 1], dp[i-1])

        # 4. Reconstruction: Backtrack the DP table to find which tasks were selected
        selected_intervals = self._reconstruct(dp, intervals)

        # 5. Capacity Management: Limit selection if bus capacity is defined
        if capacity is not None and len(selected_intervals) > capacity:
            selected_intervals.sort(key=lambda x: x[2], reverse=True)
            selected_intervals = selected_intervals[:capacity]

        # 6. Result Formatting: Convert intervals back to the expected output format
        schedule = {}
        total_passengers = 0
        for start, end, val, original_item in selected_intervals:
            bus_id = original_item.get("bus_id", f"Bus_{original_item.get('id', 'Unknown')}")
            time_str = original_item.get("time", "00:00")
            schedule[bus_id] = [time_str]
            total_passengers += val

        return {
            "schedule": schedule,
            "cost": total_passengers,
            "metadata": {"total_passengers_covered": total_passengers}
        }

    def _build_intervals(self, data):
        """Converts raw dictionary data into structured interval tuples."""
        intervals = []
        for item in data:
            try:
                # Convert "HH:MM" string to a float for mathematical comparison
                time_parts = item.get("time", "00:00").split(':')
                start_time = int(time_parts[0]) + int(time_parts[1])/60
                duration = 0.5  # Constant duration (e.g., 30 mins)
                intervals.append((start_time, start_time + duration, int(item.get("passengers", 0)), item))
            except Exception as e:
                logger.error(f"Error parsing item: {item}, error: {e}")
        return intervals

    def _find_last_compatible(self, intervals, current_index, current_start):
        """Uses Binary Search to find the nearest non-overlapping interval."""
        low = 0
        high = current_index - 1
        result = -1
        while low <= high:
            mid = (low + high) // 2
            if intervals[mid][1] <= current_start:
                result = mid
                low = mid + 1
            else:
                high = mid - 1
        return result

    def _reconstruct(self, dp, intervals):
        """Backtracks through the DP table to retrieve the chosen tasks."""
        selected = []
        i = len(intervals)
        while i > 0:
            current_start = intervals[i-1][0]
            current_val = intervals[i-1][2]
            last_comp = self._find_last_compatible(intervals, i - 1, current_start)
            
            # Check if this interval was part of the optimal solution
            if current_val + dp[last_comp + 1] >= dp[i-1]:
                selected.append(intervals[i-1])
                i = last_comp + 1
            else:
                i -= 1
        return selected