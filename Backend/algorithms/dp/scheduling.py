"""
Weighted Interval Scheduling via Dynamic Programming — with optional
capacity-constrained selection.

When ``capacity`` is None (unlimited):
    1D DP:  dp[i] = max(dp[i-1], value[i] + dp[p(i)+1])
    Complexity: O(n log n) time, O(n) space.

When ``capacity`` is an integer K:
    2D DP:  dp[i][k] = max(dp[i-1][k], value[i] + dp[p(i)+1][k-1])
    Selects the optimal non-overlapping subset of at most K trips.
    Complexity: O(n * K * log n) time, O(n * K) space.
"""

from Backend.algorithms.common.base_algorithm import BaseAlgorithm
import json


class SchedulingDP(BaseAlgorithm):
    """
    Weighted Interval Scheduling via Dynamic Programming.

    Unconstrained recurrence:
        dp[i] = max(dp[i-1], value[i] + dp[p(i)+1])
        where p(i) = last trip ending before trip i starts (binary search).

    Capacity-constrained recurrence (at most K trips):
        dp[i][k] = max(dp[i-1][k], value[i] + dp[p(i)+1][k-1])
    """

    DEFAULT_TRIP_DURATION = 0.25  # 15 minutes in hours

    def __init__(self):
        super().__init__("SchedulingDP")
        self.metadata.update({
            "time_complexity": "O(n log n) / O(n * K * log n)",
            "space_complexity": "O(n) / O(n * K)"
        })
        self._memo_cache = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_time(time_str):
        """Convert 'HH:MM' to decimal hours (e.g. '06:15' -> 6.25)."""
        if isinstance(time_str, (int, float)):
            return float(time_str)
        parts = str(time_str).split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return hours + minutes / 60.0

    def _build_intervals(self, data_list, trip_duration):
        """Convert trip dicts to (start, end, value, original) tuples."""
        intervals = []
        for item in data_list:
            value = item.get("passengers", 0)

            if "start_time" in item and "end_time" in item:
                start = self._parse_time(item["start_time"])
                end = self._parse_time(item["end_time"])
            elif "time" in item:
                start = self._parse_time(item["time"])
                end = start + trip_duration
            else:
                continue

            if end <= start:
                end = start + trip_duration

            intervals.append((start, end, value, item))
        return intervals

    @staticmethod
    def _find_last_compatible(end_times, index, start_of_current):
        """Binary search for rightmost trip j < index where end[j] <= start[index]."""
        lo, hi = 0, index - 1
        result = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if end_times[mid] <= start_of_current:
                result = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return result

    # ------------------------------------------------------------------
    # Unconstrained DP  —  dp[i] (1-D)
    # ------------------------------------------------------------------
    def _solve_unconstrained(self, intervals, end_times):
        """Standard weighted interval scheduling (no trip-count limit)."""
        n = len(intervals)
        dp = [0] * (n + 1)

        for i in range(1, n + 1):
            start_i = intervals[i - 1][0]
            value_i = intervals[i - 1][2]
            p_i = self._find_last_compatible(end_times, i - 1, start_i)
            dp[i] = max(dp[i - 1], value_i + dp[p_i + 1])

        # Reconstruct
        selected = []
        i = n
        while i >= 1:
            start_i = intervals[i - 1][0]
            p_i = self._find_last_compatible(end_times, i - 1, start_i)
            include_val = intervals[i - 1][2] + dp[p_i + 1]
            if include_val > dp[i - 1]:
                selected.append(intervals[i - 1])
                i = p_i + 1
            else:
                i -= 1
        selected.reverse()
        return dp[n], selected, n + 1

    # ------------------------------------------------------------------
    # Capacity-constrained DP  —  dp[i][k] (2-D)
    # ------------------------------------------------------------------
    def _solve_constrained(self, intervals, end_times, capacity):
        """
        Select at most ``capacity`` non-overlapping trips maximising
        total passenger value.

        dp[i][k] = max value using first i trips, selecting at most k.
        Recurrence:
            dp[i][k] = max(
                dp[i-1][k],                                    # exclude trip i
                value[i] + dp[p(i)+1][k-1]   if k >= 1         # include trip i
            )
        """
        n = len(intervals)
        K = min(capacity, n)

        # dp[i][k] — (n+1) x (K+1) table
        dp = [[0] * (K + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            start_i = intervals[i - 1][0]
            value_i = intervals[i - 1][2]
            p_i = self._find_last_compatible(end_times, i - 1, start_i)

            for k in range(K + 1):
                dp[i][k] = dp[i - 1][k]  # exclude
                if k >= 1:
                    include_val = value_i + dp[p_i + 1][k - 1]
                    if include_val > dp[i][k]:
                        dp[i][k] = include_val

        # Reconstruct from dp[n][K]
        selected = []
        i, k = n, K
        while i >= 1 and k >= 1:
            if dp[i][k] != dp[i - 1][k]:
                selected.append(intervals[i - 1])
                start_i = intervals[i - 1][0]
                p_i = self._find_last_compatible(end_times, i - 1, start_i)
                i = p_i + 1
                k -= 1
            else:
                i -= 1
        selected.reverse()

        table_size = (n + 1) * (K + 1)
        return dp[n][K], selected, table_size

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self, data_list, capacity=None, **kwargs):
        if not data_list:
            return {"schedule": {}, "cost": 0,
                    "metadata": {"total_passengers_covered": 0}}

        # Result-level cache
        trip_duration = kwargs.get("trip_duration", self.DEFAULT_TRIP_DURATION)
        cache_key = (json.dumps(data_list, sort_keys=True), capacity, trip_duration)
        if cache_key in self._memo_cache:
            return self._memo_cache[cache_key]

        # Step 1: Build and sort intervals by end time
        intervals = self._build_intervals(data_list, trip_duration)
        if not intervals:
            empty = {"schedule": {}, "cost": 0,
                     "metadata": {"total_passengers_covered": 0}}
            self._memo_cache[cache_key] = empty
            return empty

        intervals.sort(key=lambda x: x[1])
        end_times = [iv[1] for iv in intervals]

        # Step 2: DP — choose unconstrained or constrained solver
        if capacity is None:
            optimal_value, selected, dp_table_size = self._solve_unconstrained(
                intervals, end_times
            )
        else:
            optimal_value, selected, dp_table_size = self._solve_constrained(
                intervals, end_times, capacity
            )

        # Step 3: Format output grouped by bus_id
        schedule = {}
        total_passengers = 0
        for start, end, value, original in selected:
            bus_id = original.get("bus_id", "Unknown")
            trip_time = original.get("time",
                                     original.get("start_time",
                                                   f"{int(start):02d}:{int((start % 1) * 60):02d}"))
            schedule.setdefault(bus_id, []).append(trip_time)
            total_passengers += value

        for bus_id in schedule:
            schedule[bus_id].sort()

        result = {
            "schedule": schedule,
            "cost": total_passengers,
            "metadata": {
                "total_passengers_covered": total_passengers,
                "trips_considered": len(intervals),
                "trips_selected": len(selected),
                "dp_table_size": dp_table_size
            }
        }

        self._memo_cache[cache_key] = result
        return result