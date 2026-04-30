from Backend.algorithms.common.base_algorithm import BaseAlgorithm


class ResourceAllocationDP(BaseAlgorithm):

    def __init__(self):
        super().__init__("ResourceAllocationDP")

    def run(self, data_list, capacity, **kwargs):
        if not data_list or capacity <= 0:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0},
            }

        n = len(data_list)

        weights = [max(1, item.get("buses", 0)) for item in data_list]
        values = [item.get("passengers", 0) for item in data_list]

        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            for w in range(capacity + 1):
                if weights[i - 1] <= w:
                    dp[i][w] = max(
                        values[i - 1] + dp[i - 1][w - weights[i - 1]],
                        dp[i - 1][w],
                    )
                else:
                    dp[i][w] = dp[i - 1][w]

        # reconstruct solution
        w = capacity
        selected = []

        for i in range(n, 0, -1):
            if w <= 0:
                break

            if dp[i][w] != dp[i - 1][w]:
                selected.append(data_list[i - 1])
                w -= weights[i - 1]

        # build schedule
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