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
    def run(self, data=None, **kwargs) -> Any:
        """
        Implemented by each algorithm.

        Parameters
        ----------
        data : any
            Primary input — a TransportGraph for path/MST algorithms,
            or a list of dicts for DP algorithms.
        **kwargs
            Algorithm-specific options (e.g. start_node, end_node, capacity).
        """
        raise NotImplementedError

    def execute_with_metrics(self, data=None, **kwargs) -> Tuple[Any, float]:
        start_time = time.perf_counter()

        result = self.run(data, **kwargs)

        end_time = time.perf_counter()
        self.execution_time = (end_time - start_time) * 1000 

        return result, self.execution_time
    
    def get_complexity_report(self) -> Dict[str, str]:
        return {
            "algorithm": self.name,
            "time_complexity": self.metadata["time_complexity"],
            "space_complexity": self.metadata["space_complexity"]
        }