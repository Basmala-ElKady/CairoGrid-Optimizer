from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Tuple

class BaseAlgorithm(ABC):
    def __init__(self, name: str):
        self.name = name
        self.execution_time = 0.0
        self.metadata = {
            "time_complexity": "O(?)",
            "space_complexity": "O(?)"
        }

    @abstractmethod
    def run(self, graph=None, **kwargs) -> Any:
        """
        Implemented by each algorithm. 
        Example kwargs: start_node='1', end_node='F9'
        """
        raise NotImplementedError

    def execute_with_metrics(self, graph=None, **kwargs) -> Tuple[Any, float]:
        start_time = time.perf_counter()

        result = self.run(graph, **kwargs)

        end_time = time.perf_counter()
        self.execution_time = (end_time - start_time) * 1000 

        return result, self.execution_time
    
    def get_complexity_report(self) -> Dict[str, str]:
        return {
            "algorithm": self.name,
            "time_complexity": self.metadata["time_complexity"],
            "space_complexity": self.metadata["space_complexity"]
        }