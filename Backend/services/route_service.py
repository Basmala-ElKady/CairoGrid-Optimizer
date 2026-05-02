from Backend.algorithms.shortest_path.dijkstra import Dijkstra
from Backend.algorithms.shortest_path.time_dependent_dijkstra import TimeDependentDijkstra


class RouteService:

    def __init__(self):
        self.static_algo = Dijkstra()
        self.dynamic_algo = TimeDependentDijkstra()

    def get_best_route(self, graph, start_node, end_node, mode="shortest", initial_time=0):

        if mode == "shortest":
            result, exec_time = self.static_algo.execute_with_metrics(
                graph,
                start_node=start_node,
                end_node=end_node
            )
        else:
            result, exec_time = self.dynamic_algo.execute_with_metrics(
                graph,
                start_node=start_node,
                end_node=end_node,
                initial_time=initial_time
            )

        result["metadata"]["execution_time"] = exec_time
        result["metadata"]["mode"] = mode

        return result