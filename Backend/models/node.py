from Backend.models.enums import LocationType


class Node:
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: LocationType,
        x: float,
        y: float,
        population: int = 0,
        metadata: dict | None = None,
    ):
        self.id = str(node_id)
        self.name = name
        self.type = node_type
        self.pos = (float(x), float(y))
        self.population = population
        self.metadata = metadata or {}
        # Stores adjacent edges for graph traversal
        self.edges = []

    def __repr__(self):
        return f"Node({self.id}, {self.name})"
