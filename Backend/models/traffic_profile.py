from typing import Dict
from Backend.models.enums import TimePeriod

class TrafficProfile:
    """Handles time-dependent traffic flow data for a specific road (Edge)."""
    
    def __init__(self):
        # Maps TimePeriod enum to vehicle flow (int)
        self.flow_data: Dict[TimePeriod, int] = {}

    def update_flow(self, period: TimePeriod, flow: int):
        self.flow_data[period] = flow

    def get_flow(self, period: TimePeriod) -> int:
        return self.flow_data.get(period, 0)