from typing import List

from models.node import Node
from models.edge import Edge
from .transport_graph import TransportGraph

class GraphBuilder:
    @staticmethod
    def build_graph(nodes: List[Node], edges: List[Edge]) -> TransportGraph:
        """
        Constructs a TransportGraph purely from primitive lists of Nodes and Edges.
        Adheres to separation of concerns - handles structure building without data loading logic.
        """
        graph = TransportGraph()
        
        for node in nodes:
            graph.add_node(node)
            
        for edge in edges:
            graph.add_edge(edge)
            
        return graph
