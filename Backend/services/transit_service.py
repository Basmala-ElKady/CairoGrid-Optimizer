"""
Transit service — orchestrates the full DP-based optimisation pipeline.

Pipeline:  CSV → DataLoader → dp_adapter → DP algorithms → merged result

Supports two modes:
  1. optimize(schedule_data, resource_data, capacity)   — manual / test data
  2. optimize_from_csv(capacity)                        — real CSV data
"""

import os
import pandas as pd
from typing import Any, Dict, List, Optional

from Backend.algorithms.dp.scheduling import SchedulingDP
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP
from Backend.utils.dp_adapter import adapt_bus_routes, adapt_transport_demand

# Default CSV directory (relative to this file)
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "processed"
)


class TransitService:
    def __init__(self):
        self.scheduler = SchedulingDP()
        self.allocator = ResourceAllocationDP()

    # ------------------------------------------------------------------
    # Public API — manual / test data
    # ------------------------------------------------------------------
    def optimize(
        self,
        schedule_data: List[Dict[str, Any]],
        resource_data: List[Dict[str, Any]],
        capacity: int,
    ) -> Dict[str, Any]:
        """
        Run both DP modules on caller-supplied data and merge results.

        Parameters
        ----------
        schedule_data : list[dict]
            Trip-level dicts for SchedulingDP.
        resource_data : list[dict]
            Route-level dicts for ResourceAllocationDP (knapsack items).
        capacity : int
            Total bus fleet capacity (knapsack weight limit).
        """
        allocation_result = self.allocator.execute_with_metrics(
            resource_data, capacity=capacity
        )[0]

        scheduling_result = self.scheduler.execute_with_metrics(
            schedule_data, capacity=capacity
        )[0]

        return self._merge(allocation_result, scheduling_result)

    # ------------------------------------------------------------------
    # Public API — end-to-end CSV pipeline
    # ------------------------------------------------------------------
    def optimize_from_csv(
        self,
        capacity: int,
        data_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full pipeline:  CSV → loader → adapter → DP → merged output.

        Parameters
        ----------
        capacity : int
            Total bus fleet capacity for the knapsack.
        data_dir : str, optional
            Override default CSV directory.
        """
        base = data_dir or _DATA_DIR

        # --- Load raw CSV rows as list-of-dicts ---
        bus_routes_path = os.path.join(base, "bus_routes.csv")
        demand_path = os.path.join(base, "transport_demand.csv")

        raw_routes = pd.read_csv(bus_routes_path).to_dict(orient="records")
        raw_demand = pd.read_csv(demand_path).to_dict(orient="records")

        # --- Adapt to DP-compatible schemas ---
        resource_data = adapt_bus_routes(raw_routes)
        schedule_data = adapt_transport_demand(raw_demand)

        # --- Run DP ---
        return self.optimize(schedule_data, resource_data, capacity)

    # ------------------------------------------------------------------
    # Internal — merge two DP results into a single response
    # ------------------------------------------------------------------
    @staticmethod
    def _merge(
        allocation_result: Dict[str, Any],
        scheduling_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        combined_schedule: Dict[str, list] = {}

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