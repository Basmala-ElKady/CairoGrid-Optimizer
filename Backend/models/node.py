from Backend.models.enums import LocationType

class Node:
    def __init__(self, node_id: str, name: str, node_type: LocationType, 
                 x: float, y: float, population: int = 0):
        self.id = node_id
        self.name = name
        self.type = node_type
        self.pos = (x, y)
        self.population = population
        # Stores adjacent edges for graph traversal
        self.edges = []

    def __repr__(self):
        return f"Node({self.id}, {self.name})"