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
    def run(self, *args, **kwargs) -> Any:
        """
        Abstract method to be implemented by each algorithm.
        Uses *args and **kwargs to maintain flexibility for different 
        input types (e.g., graphs for Dijkstra, data lists for DP).
        """
        raise NotImplementedError

    def execute_with_metrics(self, *args, **kwargs) -> Tuple[Any, float]:
        """
        Executes the algorithm and measures its performance in milliseconds.
        Passes all arguments directly to the run method to preserve order.
        """
        start_time = time.perf_counter()
        
        # Execute the specific algorithm implementation
        result = self.run(*args, **kwargs)
        
        # Calculate elapsed time in milliseconds
        end_time = time.perf_counter()
        self.execution_time = (end_time - start_time) * 1000
        
        return result, self.execution_time

    def get_complexity_report(self) -> Dict[str, str]:
        """
        Returns a dictionary containing the complexity metadata.
        """
        return {
            "algorithm": self.name,
            "time_complexity": self.metadata["time_complexity"],
            "space_complexity": self.metadata["space_complexity"]
        }