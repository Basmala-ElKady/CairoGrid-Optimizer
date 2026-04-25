from typing import Dict, List

from models.node import Node
from models.edge import Edge


class TransportGraph:

    def __init__(self) -> None:
        """Initialize an empty transport graph."""
        self.adjacency_list: Dict[str, List[Edge]] = {}

    def add_node(self, node: Node) -> None:

        node_id = str(node.id)
        if node_id not in self.adjacency_list:
            self.adjacency_list[node_id] = []

    def add_edge(self, edge: Edge) -> None:

        source_id = str(edge.source_id)
        if source_id not in self.adjacency_list:
            self.adjacency_list[source_id] = []
        self.adjacency_list[source_id].append(edge)

    def get_neighbors(self, node_id: str) -> List[Edge]:

        return self.adjacency_list.get(str(node_id), [])

    def get_all_nodes(self) -> List[str]:

        return list(self.adjacency_list.keys())
