import time
from typing import Dict, List, Any
from Backend.algorithms.mst.prim import PrimAlgorithm
from Backend.models.edge import Edge
from Backend.models.node import Node

class PlanningService:
    """
    Service layer for orchestrating infrastructure expansion planning algorithms.
    Maintains strictly service logic, delegating pure logic to the algorithms layer.
    """
    def __init__(self):
        self.algorithm = PrimAlgorithm()

    def plan_expansion(self, edge_list: List[Edge], nodes: Dict[str, Node]) -> Dict[str, Any]:
        """
        Executes Prim's Algorithm to find minimum spanning constraints 
        for new transport expansion lines.
        """
        start_time = time.perf_counter()

        result = self.algorithm.run(
            edge_list=edge_list,
            nodes=nodes
        )

        execution_time = (time.perf_counter() - start_time) * 1000
        
        return {
            "result": result,
            "metrics": {
                "execution_time_ms": execution_time
            }
        }
