import time

from Backend.algorithms.shortest_path.dijkstra import Dijkstra
from Backend.algorithms.shortest_path.time_dependent_dijkstra import TimeDependentDijkstra


class RouteService:

    def __init__(self):
        self.static_algo = Dijkstra()
        self.dynamic_algo = TimeDependentDijkstra()

    def get_best_route(self, graph, start_node, end_node, mode="shortest", initial_time=0):

        start_time = time.perf_counter()

        if mode == "shortest":
            result = self.static_algo.run(
                graph,
                start_node=start_node,
                end_node=end_node
            )
        else:
            result = self.dynamic_algo.run(
                graph,
                start_node=start_node,
                end_node=end_node,
                initial_time=initial_time
            )

        exec_time = (time.perf_counter() - start_time) * 1000

        result["metadata"]["execution_time"] = exec_time
        result["metadata"]["mode"] = mode

        return result