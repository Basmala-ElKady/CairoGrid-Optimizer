import pandas as pd
from typing import Dict, Optional

from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.services.intersection_priority import IntersectionPriority
from Backend.graph.transport_graph import TransportGraph
from Backend.services.traffic_service import TrafficService
from Backend.models.enums import TimePeriod
from Backend.algorithms.common.cost_evaluator import CostEvaluator


class EmergencyService:
    def __init__(self, graph: TransportGraph, facilities_csv: str = None, intersection_priority: IntersectionPriority = None, traffic_service: TrafficService = None):
        self.graph = graph
        self.facilities_csv = facilities_csv or "Backend/data/processed/facilities.csv"
        self.astar = AStarAlgorithm()
        # IntersectionPriority instance used for emergency routing; allow injection for tests
        self.intersection_priority = intersection_priority or IntersectionPriority()
        self.traffic_service = traffic_service or TrafficService()

    def _load_medical_facilities(self) -> Dict[str, Dict]:
        try:
            df = pd.read_csv(self.facilities_csv)
            facilities = {}

            for _, row in df.iterrows():
                if str(row.get('Type', '')).lower() == 'medical':
                    fid = str(row['ID']).replace('.0', '')
                    facilities[fid] = {
                        'name': row.get('Name', ''),
                        'pos': (
                            float(row.get('X-coordinate', 0)),
                            float(row.get('Y-coordinate', 0))
                        )
                    }
            return facilities

        except Exception:
            return {}

    def _select_nearest_facility(self, start_node: str, facilities: Dict) -> Optional[str]:
        """
        Select closest reachable facility by Euclidean distance.
        ONLY returns hospitals that exist in the graph.
        """
        start_node_obj = self.graph.get_node(start_node)
        if not start_node_obj:
            return None

        sx, sy = start_node_obj.pos
        best_id = None
        best_dist = float('inf')

        # Filter: only consider facilities that exist in graph
        reachable_facilities = {fid: info for fid, info in facilities.items() if self.graph.get_node(fid) is not None}

        if not reachable_facilities:
            print(f"[WARNING] EmergencyService: No reachable hospitals in graph. Facilities in CSV: {list(facilities.keys())}, Nodes in graph: {list(self.graph.nodes.keys())}", flush=True)
            return None

        for fid, info in reachable_facilities.items():
            fx, fy = info['pos']
            dist = ((sx - fx) ** 2 + (sy - fy) ** 2) ** 0.5

            if dist < best_dist:
                best_dist = dist
                best_id = fid

        if best_id:
            print(f"[DEBUG] EmergencyService: Selected hospital {best_id} at distance {best_dist:.3f}", flush=True)
        return best_id

    def get_nearest_hospital_route(self, start_node: str, current_time: Optional[float] = None, is_emergency: bool = True, congestion_index: Optional[float] = None) -> Dict:
        print(f"[DEBUG] EmergencyService.get_nearest_hospital_route: start={start_node}, time={current_time}, is_emergency={is_emergency}, congestion_index={congestion_index}", flush=True)
        
        facilities = self._load_medical_facilities()
        print(f"[DEBUG] EmergencyService: Loaded {len(facilities)} medical facilities from CSV", flush=True)

        if not facilities:
            print("[ERROR] EmergencyService: No medical facilities loaded from CSV", flush=True)
            return {"path": [], "cost": float('inf'), "metadata": {}}

        # 1. select ONE target (only reachable hospitals)
        hospital_id = self._select_nearest_facility(start_node, facilities)

        if not hospital_id:
            print("[ERROR] EmergencyService: No reachable hospital found", flush=True)
            return {"path": [], "cost": float('inf'), "metadata": {}}

        print(f"[DEBUG] EmergencyService: Running A* to {hospital_id}", flush=True)
        
        # Calculate live congestion index if not provided
        if congestion_index is None:
            period = CostEvaluator.map_time_to_period(current_time) if current_time is not None else TimePeriod.NIGHT
            congestion_index = self.traffic_service.calculate_congestion_index(self.graph, period)
            print(f"[DEBUG] EmergencyService: Calculated live congestion index for {period.value} is {congestion_index}", flush=True)
        else:
            print(f"[DEBUG] EmergencyService: Using provided congestion index {congestion_index}", flush=True)

        # 2. run A* with single goal
        # Emergency vehicles get 20% speed boost globally (base_emergency_multiplier=0.8)
        # Plus optional additional discount at intersections via intersection_priority
        result = self.astar.run(
            graph=self.graph,
            start_node=start_node,
            end_node=hospital_id,
            initial_time=current_time,
            is_emergency=is_emergency,
            base_emergency_multiplier=0.8 if is_emergency else 1.0,  # 20% faster when emergency
            intersection_priority=self.intersection_priority,
            congestion_index=congestion_index,
            mode="realistic"
        )

        print(f"[DEBUG] EmergencyService: A* result - path_length={len(result.get('path', []))}, cost={result.get('cost', 'N/A')}", flush=True)
        
        # 3. enrich metadata
        result.setdefault("metadata", {})
        result["metadata"]["hospital_id"] = hospital_id
        result["metadata"]["hospital_name"] = facilities[hospital_id]["name"]

        return result
