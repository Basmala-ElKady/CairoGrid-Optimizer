import os
import sys
import time
from typing import List

# Ensure script can be run directly from repo root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Backend.graph.transport_graph import TransportGraph
from Backend.services.emergency_service import EmergencyService
from Backend.services.intersection_priority import IntersectionPriority


class EmergencyVehicle:
    def __init__(self, vehicle_id: str, start_node: str):
        self.id = vehicle_id
        self.current_node = start_node
        self.path: List[str] = []
        self.next_index = 0
        self.time = 0.0

    def load_path(self, path: List[str]):
        self.path = path
        self.next_index = 1 if len(path) > 1 else 0


class SimulationEngine:
    def __init__(self, graph: TransportGraph, intersection_priority: IntersectionPriority = None):
        self.graph = graph
        self.intersection_priority = intersection_priority or IntersectionPriority()
        # Ensure EmergencyService uses the same IntersectionPriority instance
        self.service = EmergencyService(graph, intersection_priority=self.intersection_priority)

    def step_along(self, vehicle: EmergencyVehicle, dt: float = 0.0):
        # Advance vehicle along path by simulating edge traversal time using edge.get_weight
        if vehicle.next_index == 0 or vehicle.next_index >= len(vehicle.path):
            return False

        cur = vehicle.path[vehicle.next_index - 1]
        nxt = vehicle.path[vehicle.next_index]

        # find edge
        edges = self.graph.get_neighbors(cur)
        edge = next((e for e in edges if str(e.target_id) == str(nxt)), None)
        if not edge:
            # broken path
            vehicle.next_index = len(vehicle.path)
            return False

        # compute period-weighted cost
        # _map_time_to_period is an internal helper in A*; use it if present, otherwise default to MORNING_PEAK
        try:
            period = self.service.astar._map_time_to_period(vehicle.time)
        except Exception:
            from Backend.models.enums import TimePeriod
            period = TimePeriod.MORNING_PEAK
        travel_cost = edge.get_weight(period)

        # if leaving an intersection, apply intersection priority multiplier for emergencies
        multiplier = self.intersection_priority.get_multiplier(cur, True)
        travel_time = travel_cost * multiplier

        # advance vehicle time
        vehicle.time += travel_time
        vehicle.current_node = nxt
        vehicle.next_index += 1
        return True

    def run_scenario(self, start_node: str, time_of_day: float = 8.0):
        print('[START] SimulationEngine.run_scenario', flush=True)
        print(f"[DEBUG] start_node={start_node}, time_of_day={time_of_day}", flush=True)

        vehicle = EmergencyVehicle('E1', start_node)
        # compute route
        res = self.service.get_nearest_hospital_route(start_node, current_time=time_of_day)

        vehicle.time = time_of_day
        # load path defensively
        path = res.get('path') or []
        vehicle.load_path(path)

        timeline = []
        timeline.append((vehicle.time, vehicle.current_node))

        if not path:
            print('[RESULT] WARNING: No path to follow from start', flush=True)
            print('[RESULT] Metadata:', res.get('metadata', {}), flush=True)
            print('[DONE] SimulationEngine.run_scenario', flush=True)
            return res, timeline

        while self.step_along(vehicle):
            timeline.append((round(vehicle.time, 3), vehicle.current_node))

        print('[RESULT] Route found', flush=True)
        print(f"[DEBUG] steps={len(timeline)}", flush=True)
        print('[DONE] SimulationEngine.run_scenario', flush=True)
        return res, timeline


if __name__ == '__main__':
    # Minimal demo when running this file directly
    try:
        print('[START] emergency_simulation_engine demo', flush=True)
        from Backend.graph.transport_graph import TransportGraph
        from Backend.models.node import Node
        from Backend.models.edge import Edge
        from Backend.models.enums import LocationType, TimePeriod
        from Backend.services.intersection_priority import IntersectionPriority

        g = TransportGraph()
        A = Node('A', 'Start', LocationType.DISTRICT, 31.22, 30.02)
        F9 = Node('F9', 'Hospital', LocationType.FACILITY, 31.23, 30.03)
        g.add_node(A)
        g.add_node(F9)
        profile = {TimePeriod.MORNING_PEAK: 200}
        e = Edge('A', 'F9', distance=1.0, capacity=100, condition=8, traffic_profile=profile)
        g.add_edge(e)

        engine = SimulationEngine(g, intersection_priority=IntersectionPriority())
        res, timeline = engine.run_scenario('A', time_of_day=8.0)
        print('[RESULT] route:', res, flush=True)
        print('[RESULT] timeline:', timeline, flush=True)
        print('[DONE] emergency_simulation_engine demo', flush=True)
    except Exception as e:
        print(f"[ERROR] demo failed: {e}", flush=True)
