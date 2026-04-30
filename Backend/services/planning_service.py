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
        result, execution_time = self.algorithm.execute_with_metrics(
            edge_list=edge_list,
            nodes=nodes
        )
        
        return {
            "result": result,
            "metrics": {
                "execution_time_ms": execution_time
            }
        }
