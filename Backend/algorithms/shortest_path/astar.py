import heapq
import math
from typing import Dict, Tuple, List, Optional

from Backend.algorithms.common.base_shortest_path import BaseShortestPath
from Backend.algorithms.common.cost_evaluator import CostEvaluator
from Backend.models.enums import TimePeriod
from Backend.services.intersection_priority import IntersectionPriority


class AStarAlgorithm(BaseShortestPath):
    def __init__(self):
        super().__init__("AStar")
        self.metadata["time_complexity"] = "O(E log V)"
        self.metadata["space_complexity"] = "O(V)"
        self.nodes_explored = 0   # ⭐ مهم جدًا
        # Optional IntersectionPriority instance can be provided at construction
        self.intersection_priority: Optional[IntersectionPriority] = None
        self.cost_evaluator = CostEvaluator()

    def run(self, graph, start_node, **kwargs):
        end = kwargs.get("end_node")
        goal_nodes = kwargs.get("goal_nodes")
        initial_time = kwargs.get("initial_time", None)
        debug = kwargs.get("debug", False)

        # Backward-compatible options are still accepted through kwargs.
        # If no explicit IP is passed, use algorithm-level injected instance.
        if kwargs.get('intersection_priority', None) is None and self.intersection_priority is not None:
            kwargs['intersection_priority'] = self.intersection_priority

        goal_positions: Dict[str, Tuple[float, float]] = kwargs.get("goal_positions", {})

        # =========================
        # BUILD GOALS
        # =========================
        goals = set()

        if end:
            end_str = str(end)
            goals.add(end_str)
            if graph.get_node(end):
                if end_str not in goal_positions:
                    goal_positions[end_str] = graph.get_node(end).pos
                if debug:
                    print(f"[A* DEBUG] Added end_node {end_str} with pos {goal_positions[end_str]}", flush=True)
            else:
                print(f"[A* ERROR] end_node {end_str} does not exist in graph! Available nodes: {list(graph.nodes.keys())}", flush=True)

        if goal_nodes:
            for g in goal_nodes:
                g_str = str(g)
                goals.add(g_str)
                if graph.get_node(g):
                    if g_str not in goal_positions:
                        goal_positions[g_str] = graph.get_node(g).pos
                    if debug:
                        print(f"[A* DEBUG] Added goal_node {g_str} with pos {goal_positions[g_str]}", flush=True)
                else:
                    print(f"[A* WARNING] goal_node {g_str} does not exist in graph", flush=True)

        # Validate that at least ONE goal exists in graph
        if not goal_positions:
            print(f"[A* FATAL] No valid goal nodes! Requested goals: {goals}, Graph nodes: {list(graph.nodes.keys())}", flush=True)
            return {
                "path": [],
                "cost": float('inf'),
                "nodes_explored": 0,
                "metadata": {"error": "no_valid_goals"}
            }

        if debug:
            print(f"[A* DEBUG] Valid goals: {list(goal_positions.keys())}", flush=True)

        # =========================
        # HEURISTIC
        # =========================
        # Determine heuristic scaling to preserve admissibility when emergency multipliers < 1
        # User can also pass `min_priority_multiplier` to indicate the smallest multiplier applied anywhere
        min_priority = self.cost_evaluator.min_multiplier_for_heuristic(**kwargs)
        heuristic_scale = min(1.0, min_priority)

        def heuristic(node_id: str) -> float:
            node = graph.get_node(node_id)
            if not node:
                return 0.0

            x1, y1 = node.pos
            min_d = float('inf')

            for pos in goal_positions.values():
                x2, y2 = pos
                d = math.hypot(x2 - x1, y2 - y1)
                min_d = min(min_d, d)

            # ✅ FIX: If no goals found (shouldn't happen but just in case), return 0
            if min_d == float('inf'):
                return 0.0
            
            # Scale heuristic by heuristic_scale to keep it admissible if some edges are reduced
            return min_d * heuristic_scale

        # =========================
        # EDGE WEIGHT
        # =========================
        def edge_weight(edge, current_node: str, arrival_time_at_current: float):
            return self.cost_evaluator.edge_weight(
                graph,
                edge,
                current_node,
                arrival_time_at_current,
                **kwargs
            )

        # =========================
        # INIT
        # =========================
        g_score = {node: float('inf') for node in graph.get_all_nodes()}
        f_score = {node: float('inf') for node in graph.get_all_nodes()}
        came_from: Dict[str, str] = {}

        start = str(start_node)
        g_score[start] = 0.0
        f_score[start] = heuristic(start)

        open_heap = [(f_score[start], start)]
        closed = set()

        reached_goal: Optional[str] = None
        self.nodes_explored = 0  # reset per run

        if debug:
            print(f"[A* DEBUG] Starting A* search: start={start}, goals={list(goal_positions.keys())}", flush=True)
            print(f"[A* DEBUG] Heuristic scale factor: {heuristic_scale:.3f} (min_priority={min_priority:.3f})", flush=True)
            print(f"[A* DEBUG] Goal positions: {goal_positions}", flush=True)
            print(f"[A* DEBUG] Start heuristic value: {heuristic(start):.3f}", flush=True)

        # =========================
        # A* LOOP (with dynamic time tracking)
        # =========================
        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current in closed:
                continue

            closed.add(current)
            self.nodes_explored += 1   # ⭐ COUNT HERE

            # Compute accumulated time and current period
            initial_t = kwargs.get('initial_time', 0.0) or 0.0
            accumulated_time = initial_t + g_score[current]
            current_period = self.cost_evaluator.map_time_to_period(accumulated_time)
            
            # ✅ DEBUG: Show g, h, f values for this node
            current_g = g_score[current]
            current_h = heuristic(current)
            current_f = f_score[current]
            if debug:
                print(f"[A* EXPANDING] node={current} | g={current_g:.3f} | h={current_h:.3f} | f={current_f:.3f} | time={accumulated_time:.2f} ({current_period.value})", flush=True)
            
            if debug:
                print(f"[TIME DEBUG] node={current} | accumulated_time={accumulated_time:.2f} -> period={current_period.value}", flush=True)

            if current in goals:
                reached_goal = current
                if debug:
                    print(f"[A* DEBUG] Goal reached: {reached_goal} with cost {g_score[current]:.3f} at time {accumulated_time:.2f} ({current_period.value})", flush=True)
                break

            for edge in graph.get_neighbors(current):
                neighbor = str(edge.target_id)

                # Pass elapsed travel cost/time from start; the shared cost evaluator
                # combines it with initial_time when dynamic weighting is enabled.
                arrival_time = g_score[current]

                tentative_g = g_score[current] + edge_weight(edge, current, arrival_time)

                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    neighbor_h = heuristic(neighbor)
                    f_score[neighbor] = tentative_g + neighbor_h
                    heapq.heappush(open_heap, (f_score[neighbor], neighbor))
                    
                    # ✅ DEBUG: Show why this neighbor was added
                    if debug:
                        print(f"[A* ADD-NEIGHBOR] from {current} -> {neighbor} | edge_cost={edge_weight(edge, current, arrival_time):.3f} | g={tentative_g:.3f} | h={neighbor_h:.3f} | f={f_score[neighbor]:.3f}", flush=True)

        # =========================
        # NO PATH
        # =========================
        if reached_goal is None:
            print(f"[A* WARNING] No path found. Nodes explored: {self.nodes_explored}. Start: {start}, Goals: {list(goal_positions.keys())}", flush=True)
            return {
                "path": [],
                "cost": float('inf'),
                "nodes_explored": self.nodes_explored,
                "metadata": {"error": "no_path_found"}
            }

        # =========================
        # RECONSTRUCT PATH
        # =========================
        path = []
        node = reached_goal

        if debug:
            print(f"[A* DEBUG] Reconstructing path from goal {reached_goal}", flush=True)

        while node in came_from:
            path.append(node)
            node = came_from[node]

        if node == start:
            path.append(start)
            path.reverse()
            if debug:
                print(f"[A* DEBUG] Path reconstructed successfully: {path}", flush=True)
        else:
            print(f"[A* ERROR] Path reconstruction failed! node={node}, start={start}, came_from keys={list(came_from.keys())}", flush=True)
            path = []

        metadata = {"mode": "a_star"}

        # Add time-of-day and period information if initial_time was provided
        if initial_time is not None:
            final_time = initial_time + (g_score.get(reached_goal, 0.0) if reached_goal else 0.0)
            final_period = self.cost_evaluator.map_time_to_period(final_time)
            metadata["time_of_day"] = initial_time
            metadata["final_time"] = round(final_time, 2)
            metadata["period"] = final_period.value
            if debug:
                print(f"[TIME RESULT] started at {initial_time:.1f} ({self.cost_evaluator.map_time_to_period(initial_time).value}), "
                      f"finished at {final_time:.2f} ({final_period.value})", flush=True)

        if reached_goal in goal_positions:
            metadata["hospital_id"] = reached_goal

        if debug:
            print(f"[A* DEBUG] Final result: path_length={len(path)}, cost={g_score.get(reached_goal, float('inf'))}, nodes_explored={self.nodes_explored}", flush=True)

        return {
            "path": path,
            "cost": g_score.get(reached_goal, float('inf')),
            "nodes_explored": self.nodes_explored,
            "metadata": metadata
        }

    def _map_time_to_period(self, time_value):
        if 6 <= time_value < 10:
            return TimePeriod.MORNING_PEAK
        elif 10 <= time_value < 16:
            return TimePeriod.AFTERNOON
        elif 16 <= time_value < 20:
            return TimePeriod.EVENING_PEAK
        else:
            return TimePeriod.NIGHT