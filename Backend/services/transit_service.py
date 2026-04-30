from Backend.algorithms.dp.scheduling import SchedulingDP
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP


class TransitService:
    def __init__(self):
        self.scheduler = SchedulingDP()
        self.allocator = ResourceAllocationDP()

    def optimize(self, schedule_data, resource_data, capacity):
        allocation_result = self.allocator.execute_with_metrics(
            resource_data, capacity=capacity
        )[0]

        scheduling_result = self.scheduler.execute_with_metrics(
            schedule_data, capacity=capacity
        )[0]

        combined_schedule = {}

        for source in [allocation_result["schedule"], scheduling_result["schedule"]]:
            for k, v in source.items():
                combined_schedule.setdefault(k, []).extend(v)

        for k in combined_schedule:
            combined_schedule[k].sort()

        total_cost = allocation_result["cost"] + scheduling_result["cost"]

        total_passengers = (
            allocation_result["metadata"]["total_passengers_covered"]
            + scheduling_result["metadata"]["total_passengers_covered"]
        )

        return {
            "schedule": combined_schedule,
            "cost": total_cost,
            "metadata": {"total_passengers_covered": total_passengers},
        }