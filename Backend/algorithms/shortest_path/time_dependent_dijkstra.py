import heapq
from Backend.algorithms.common.base_shortest_path import BaseShortestPath
from Backend.models.enums import TimePeriod

class TimeDependentDijkstra(BaseShortestPath):
    def __init__(self):
        super().__init__("TimeDependentDijkstra")
        self.metadata["time_complexity"] = "O(E log V)"
        self.metadata["space_complexity"] = "O(V)"

    def run(self, graph=None, **kwargs):
        start = kwargs.get("start_node")
        end = kwargs.get("end_node")
        current_time = kwargs.get("initial_time", 0)

        distances, previous = self._init_structures(graph, start)
        pq = [(0, start, current_time)]

        while pq:
            current_dist, current_node, arrival_time = heapq.heappop(pq)

            if current_node == end:
                break

            for edge in graph.get_neighbors(current_node):
                neighbor = edge.target_id
                period = self._map_time_to_period(arrival_time)
                weight = edge.get_weight(period)

                new_dist = current_dist + weight
                new_time = arrival_time + weight

                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor, new_time))

       
        if distances.get(end, float('inf')) == float('inf'):
            return {
                "path": [],
                "cost": float('inf'),
                "metadata": {"mode": "fastest"}
            }

        path = self._reconstruct_path(previous, start, end)
        return {
            "path": path,
            "cost": distances[end],
            "metadata": {"mode": "fastest"}
        }

    def _map_time_to_period(self, time_value):
        time_value = time_value % 24
        if 6 <= time_value < 10: return TimePeriod.MORNING_PEAK
        elif 10 <= time_value < 16: return TimePeriod.AFTERNOON
        elif 16 <= time_value < 20: return TimePeriod.EVENING_PEAK
        else: return TimePeriod.NIGHT