from Backend.algorithms.common.base_algorithm import BaseAlgorithm


class BaseShortestPath(BaseAlgorithm):

    def __init__(self, name: str):
        super().__init__(name)

    def _init_structures(self, graph, start_node):
        distances = {node: float("inf") for node in graph.nodes}
        previous = {node: None for node in graph.nodes}

        distances[start_node] = 0

        return distances, previous

    def _reconstruct_path(self, previous, start, end):
        path = []
        current = end

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        if path[0] == start:
            return path
        return []