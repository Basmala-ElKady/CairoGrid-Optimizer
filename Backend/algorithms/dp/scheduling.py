from Backend.algorithms.common.base_algorithm import BaseAlgorithm
import json


class SchedulingDP(BaseAlgorithm):
    """
    Weighted Interval Scheduling via Dynamic Programming.

    dp[i] = max(dp[i-1], value[i] + dp[p(i)+1])
    where p(i) = last trip ending before trip i starts (binary search).

    Complexity: O(n log n) time, O(n) space.
    """

    DEFAULT_TRIP_DURATION = 0.25  # 15 minutes in hours

    def __init__(self):
        super().__init__("SchedulingDP")
        self.metadata.update({
            "time_complexity": "O(n log n)",
            "space_complexity": "O(n)"
        })
        self._memo_cache = {}

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

    def _reconstruct(self, dp, intervals, end_times):
        """Backtrack through DP table to recover selected trips."""
        selected = []
        i = len(intervals)
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
        return selected

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
        n = len(intervals)
        end_times = [iv[1] for iv in intervals]

        # Step 2: DP — dp[i] = max(dp[i-1], value[i] + dp[p(i)+1])
        dp = [0] * (n + 1)
        for i in range(1, n + 1):
            start_i, end_i, value_i, _ = intervals[i - 1]
            p_i = self._find_last_compatible(end_times, i - 1, start_i)
            dp[i] = max(dp[i - 1], value_i + dp[p_i + 1])

        # Step 3: Reconstruct optimal non-overlapping selection
        selected = self._reconstruct(dp, intervals, end_times)

        # Step 4: Apply optional capacity limit (safe — subset of non-overlapping set)
        if capacity is not None and len(selected) > capacity:
            selected.sort(key=lambda x: x[2], reverse=True)
            selected = selected[:capacity]

        # Step 5: Format output grouped by bus_id
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
                "trips_considered": n,
                "trips_selected": len(selected),
                "dp_table_size": n + 1
            }
        }

        self._memo_cache[cache_key] = result
        return result