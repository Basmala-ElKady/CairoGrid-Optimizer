import heapq
from Backend.algorithms.common.base_shortest_path import BaseShortestPath

class DijkstraAlgorithm(BaseShortestPath):
    def __init__(self):
        super().__init__("Dijkstra")
        self.metadata["time_complexity"] = "O(E log V)"
        self.metadata["space_complexity"] = "O(V)"

    def run(self, graph=None, **kwargs):
        start = kwargs.get("start_node")
        end = kwargs.get("end_node")

        distances, previous = self._init_structures(graph, start)

        pq = [(0, start)]

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            if current_node == end:
                break

            for edge in graph.get_neighbors(current_node):
                neighbor = edge.target_id
                weight = edge.distance

                new_dist = current_dist + weight

                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))

        path = self._reconstruct_path(previous, start, end)

        return {
            "path": path,
            "cost": distances[end],
            "metadata": {"mode": "shortest"}
        }