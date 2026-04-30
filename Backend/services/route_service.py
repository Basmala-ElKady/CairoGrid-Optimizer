from Backend.algorithms.shortest_path.dijkstra import DijkstraAlgorithm
from Backend.algorithms.shortest_path.time_dependent_dijkstra import TimeDependentDijkstra

class RouteService:
    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = DijkstraAlgorithm()
        self.time_dijkstra = TimeDependentDijkstra()

    def get_best_route(self, start_node, end_node, mode="shortest", initial_time=None):
        if mode == "shortest":
            result, exec_time = self.dijkstra.execute_with_metrics(
                self.graph,
                start_node=start_node,
                end_node=end_node
            )
        else:
            result, exec_time = self.time_dijkstra.execute_with_metrics(
                self.graph,
                start_node=start_node,
                end_node=end_node,
                initial_time=initial_time
            )

        result["metadata"]["execution_time"] = exec_time
        return result