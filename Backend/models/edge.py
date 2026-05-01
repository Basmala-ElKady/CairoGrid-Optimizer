from .traffic_profile import TrafficProfile
from .enums import TimePeriod

class Edge:
    """Represents a road connection between two Nodes with dynamic weighting."""
    
    def __init__(self, source_id: str, target_id: str, distance: float, 
                 capacity: int, condition: int, traffic_profile: dict = None):
        self.source_id = source_id
        self.target_id = target_id
        self.distance = distance
        self.capacity = capacity
        self.condition = condition
        
        # Initialize the TrafficProfile object
        self.traffic = TrafficProfile()
        
        # If a dictionary was passed from the DataLoader, hydrate the profile
        if traffic_profile:
            for period, flow in traffic_profile.items():
                self.traffic.update_flow(period, flow)

    def get_weight(self, period: TimePeriod, debug: bool = False) -> float:
        """
        Calculates dynamic travel cost with STRONG time-dependent effect.
        
        Formula: distance * (1 + (flow/capacity)^2) * (11/condition)
        
        - Quadratic congestion: high traffic has exponential cost increase
        - Condition multiplier: poor road condition dramatically increases cost
        - Morning peak / evening peak produce HIGH cost
        - Night produces LOW cost
        """
        flow = self.traffic.get_flow(period)
        
        # STRONG quadratic congestion factor: (flow/capacity)^2
        # This ensures rush hour (high flow) produces much higher cost
        congestion = (flow / self.capacity) if self.capacity > 0 else 0
        congestion_factor = 1.0 + (congestion ** 2)  # Quadratic: 1-100 range for typical flows
        
        # Condition multiplier: lower condition (1-10 scale) increases cost
        # condition=10 → 1.1x, condition=1 → 11x multiplier
        condition_multiplier = 11.0 / max(1, self.condition)
        
        # Final weight calculation: distance * congestion * condition
        dynamic_weight = self.distance * congestion_factor * condition_multiplier
        
        if debug:
            print(f"[EDGE DEBUG] {self.source_id}->{self.target_id} | period={period.value} | "
                  f"flow={flow:.0f} cap={self.capacity} | congestion_factor={congestion_factor:.2f} | "
                  f"condition={self.condition} cond_mult={condition_multiplier:.2f} | "
                  f"cost={dynamic_weight:.3f}", flush=True)
        
        return round(dynamic_weight, 3)

    def __repr__(self):
        return f"Edge({self.source_id} -> {self.target_id}, Dist={self.distance})"