import heapq
from typing import Any, Dict, List

from Backend.algorithms.common.base_algorithm import BaseAlgorithm
from Backend.models.edge import Edge
from Backend.models.node import Node


class PrimAlgorithm(BaseAlgorithm):
    """
    Prim's Minimum Spanning Tree Algorithm for infrastructure expansion planning.
    Uses construction cost (distance) for edge weights and population for tie-breaking.
    """
    
    def __init__(self):
        super().__init__("Prim")
        self.metadata = {
            "time_complexity": "O(E log V)",
            "space_complexity": "O(V + E)"
        }

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        graph = kwargs.pop("graph", args[0] if len(args) > 0 else None)
        edge_list: List[Edge] = kwargs.get('edge_list', [])
        nodes: Dict[str, Node] = kwargs.get('nodes', {})
        
        if not edge_list or not nodes:
            return {
                "edges": [],
                "cost": 0.0,
                "metadata": {
                    "algorithm": "Prim",
                    "districts_connected": 0,
                    "total_population_reached": 0
                }
            }

        # 1. Build Adjacency List for undirected graph processing
        # Each edge connection is bidirectional for the MST construction
        adj: Dict[str, List] = {node_id: [] for node_id in nodes}
        for edge in edge_list:
            u, v = edge.source_id, edge.target_id
            
            # Use distance as proxy for construction cost due to Edge object fields
            cost = getattr(edge, 'cost', getattr(edge, 'distance', 0.0))
            
            # Ensure nodes exist in adjacency list if they aren't provided in the `nodes` dict
            if u not in adj:
                adj[u] = []
            if v not in adj:
                adj[v] = []
                
            edge_str = f"{u}-{v}"
            adj[u].append((cost, v, edge_str))
            adj[v].append((cost, u, edge_str))

        visited = set()
        mst_edges = []
        total_cost = 0.0
        total_population = 0

        # Processing handle for disconnected graphs (spanning forest)
        # We start from an arbitrary node, then repeat for unvisited disconnected components
        for start_node in sorted(adj.keys()):
            # Skip if already visited or if isolated node (no edges to connect)
            if start_node in visited or not adj[start_node]:
                continue
                
            # Initialize component traversal
            visited.add(start_node)
            total_population += getattr(nodes.get(start_node, None), 'population', 0)
            
            # min_heap elements: (cost, -population_of_target, edge_string, target_node)
            # Negative population makes largest-population node popped first on ties
            min_heap = []
            for cost, neighbor, edge_str in adj[start_node]:
                target_pop = getattr(nodes.get(neighbor, None), 'population', 0)
                heapq.heappush(min_heap, (cost, -target_pop, edge_str, neighbor))
                
            while min_heap:
                cost, neg_pop, edge_str, current_node = heapq.heappop(min_heap)
                
                if current_node in visited:
                    continue
                    
                # 2. Add minimal cost edge to MST
                visited.add(current_node)
                mst_edges.append(edge_str)
                total_cost += cost
                total_population += getattr(nodes.get(current_node, None), 'population', 0)
                
                # 3. Queue unvisited neighbors
                for nxt_cost, nxt_neighbor, nxt_edge_str in adj[current_node]:
                    if nxt_neighbor not in visited:
                        nxt_pop = getattr(nodes.get(nxt_neighbor, None), 'population', 0)
                        heapq.heappush(min_heap, (nxt_cost, -nxt_pop, nxt_edge_str, nxt_neighbor))

        return {
            "edges": mst_edges,
            "cost": round(total_cost, 2),
            "metadata": {
                "algorithm": "Prim",
                "districts_connected": len(visited),
                "total_population_reached": total_population
            }
        }
