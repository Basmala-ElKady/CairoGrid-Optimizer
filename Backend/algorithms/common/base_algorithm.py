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
        Implemented by each algorithm. 
        Example kwargs: start_node='1', end_node='F9'
        """
        raise NotImplementedError

    def get_complexity_report(self) -> Dict[str, str]:
        return {
            "algorithm": self.name,
            "time_complexity": self.metadata["time_complexity"],
            "space_complexity": self.metadata["space_complexity"]
        }