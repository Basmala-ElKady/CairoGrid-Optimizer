from typing import Dict, List, Optional

from models.node import Node
from models.edge import Edge


class TransportGraph:

    def __init__(self) -> None:
        """Initialize an empty transport graph."""
        self.adjacency_list: Dict[str, List[Edge]] = {}
        # Keep track of Node objects if required for metadata lookups
        self.nodes: Dict[str, Node] = {}

    def add_node(self, node: Node) -> None:
        """Add a Node to the graph."""
        node_id = str(node.id)
        if node_id not in self.adjacency_list:
            self.adjacency_list[node_id] = []
        self.nodes[node_id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add a directed Edge. Auto-creates node lists if they are missing."""
        source_id = str(edge.source_id)
        target_id = str(edge.target_id)
        
        # Auto-create node entry if missing to guarantee safe access
        if source_id not in self.adjacency_list:
            self.adjacency_list[source_id] = []
            
        if target_id not in self.adjacency_list:
            self.adjacency_list[target_id] = []
            
        self.adjacency_list[source_id].append(edge)

    def get_neighbors(self, node_id: str) -> List[Edge]:
        """Safely fetch outgoing edges for a given node string ID."""
        return self.adjacency_list.get(str(node_id), [])

    def get_all_nodes(self) -> List[str]:
        """Fetch all node IDs represented in the adjacency list."""
        return list(self.adjacency_list.keys())

    def get_node(self, node_id: str) -> Optional[Node]:
        """Fetch Node object if stored."""
        return self.nodes.get(str(node_id))
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        node_id = str(node_id)
        incoming = []

        for edges in self.adjacency_list.values():
            for edge in edges:
                if str(edge.target_id) == node_id:
                    incoming.append(edge)

        return incoming
