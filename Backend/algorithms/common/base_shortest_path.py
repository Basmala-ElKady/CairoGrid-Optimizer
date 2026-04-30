from Backend.algorithms.common.base_algorithm import BaseAlgorithm

class BaseShortestPath(BaseAlgorithm):
    def __init__(self, name: str):
        super().__init__(name)

    def _init_structures(self, graph, start):
        distances = {node: float('inf') for node in graph.get_all_nodes()}
        previous = {}

        distances[start] = 0
        return distances, previous

    def _reconstruct_path(self, previous, start, end):
        path = []
        current = end

        while current in previous:
            path.append(current)
            current = previous[current]

        if current == start:
            path.append(start)
            path.reverse()
            return path

        return []