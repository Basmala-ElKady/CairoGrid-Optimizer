from .traffic_profile import TrafficProfile
from .enums import TimePeriod

class Edge:
    """Represents a road connection between two Nodes with dynamic weighting."""
    
    def __init__(self, source_id: str, target_id: str, distance: float, 
                 capacity: int, condition: int):
        self.source_id = source_id
        self.target_id = target_id
        self.distance = distance
        self.capacity = capacity # vehicles/hour
        self.condition = condition # Scale 1-10
        self.traffic = TrafficProfile()

    def get_weight(self, period: TimePeriod) -> float:
        """
        Calculates dynamic travel cost. 
        Formula: Distance * (1 + CongestionFactor + RoadPenalty)
        """
        flow = self.traffic.get_flow(period)
        
        # Congestion factor: ratio of current flow to max capacity
        congestion = (flow / self.capacity) if self.capacity > 0 else 0
        
        # Condition penalty: Lower condition score increases travel time/cost
        condition_penalty = (11 - self.condition) * 0.1 
        
        # Final weight calculation for Dijkstra/A*
        dynamic_weight = self.distance * (1 + congestion + condition_penalty)
        return round(dynamic_weight, 3)

    def __repr__(self):
        return f"Edge({self.source_id} -> {self.target_id}, Dist={self.distance})"