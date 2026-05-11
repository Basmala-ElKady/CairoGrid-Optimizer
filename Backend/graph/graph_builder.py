from typing import List
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import TimePeriod
from Backend.graph.transport_graph import TransportGraph

class GraphBuilder:
    
    @staticmethod
    def build_graph(nodes: List[Node], edges: List[Edge], bidirectional: bool = True) -> TransportGraph:
        """
        Constructs a TransportGraph purely from primitive lists of Nodes and Edges.
        If bidirectional is True, it adds reverse edges for each road segment.
        """
        graph = TransportGraph()
        
        for node in nodes:
            graph.add_node(node)
            
        for edge in edges:
            graph.add_edge(edge)
            if bidirectional:
                # Create a reverse edge for undirected connectivity
                # We reuse the same distance/capacity/condition for the reverse direction
                # but we need to ensure the source and target are swapped.
                reverse_edge = Edge(
                    source_id=edge.target_id,
                    target_id=edge.source_id,
                    distance=edge.distance,
                    capacity=edge.capacity,
                    condition=edge.condition,
                    traffic_profile=None # Use defaults or could copy if needed
                )
                # If the original edge had a traffic profile, copy it
                if hasattr(edge, 'traffic'):
                    for period in TimePeriod:
                        reverse_edge.traffic.update_flow(period, edge.traffic.get_flow(period))
                
                graph.add_edge(reverse_edge)
            
        return graph