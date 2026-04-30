from Backend.algorithms.common.base_algorithm import BaseAlgorithm
from collections import defaultdict


class SchedulingDP(BaseAlgorithm):

    def __init__(self):
        super().__init__("SchedulingDP")

    def run(self, data_list, capacity=None, **kwargs):
        if not data_list:
            return {
                "schedule": {},
                "cost": 0,
                "metadata": {"total_passengers_covered": 0},
            }

        def time_to_minutes(t):
            h, m = map(int, t.split(":"))
            return h * 60 + m

        # Group by bus
        buses = defaultdict(list)
        for d in data_list:
            bus_id = d.get("bus_id", "B?")
            buses[bus_id].append(d)

        total_cost = 0

        # Calculate waiting per bus
        for bus_id, trips in buses.items():
            trips.sort(key=lambda x: x["time"])

            for i in range(len(trips) - 1):
                t1 = time_to_minutes(trips[i]["time"])
                t2 = time_to_minutes(trips[i + 1]["time"])

                passengers = trips[i].get("passengers", 0)

                total_cost += passengers * max(0, t2 - t1)

        # Build schedule
        schedule = {}
        for d in data_list:
            bus_id = d.get("bus_id", "B?")
            schedule.setdefault(bus_id, []).append(d["time"])

        for k in schedule:
            schedule[k].sort()

        total_passengers = sum(d.get("passengers", 0) for d in data_list)

        return {
            "schedule": schedule,
            "cost": total_cost,
            "metadata": {"total_passengers_covered": total_passengers},
        }