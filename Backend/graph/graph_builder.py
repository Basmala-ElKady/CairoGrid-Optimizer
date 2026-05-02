from typing import List
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.graph.transport_graph import TransportGraph

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