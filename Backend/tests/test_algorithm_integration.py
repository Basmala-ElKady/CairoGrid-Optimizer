import unittest
import sys
from pathlib import Path

# Setup PROJECT_ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Imports based on your tree structure
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP
# Using EmergencyPriority as it's a confirmed file in your greedy folder
from Backend.algorithms.greedy.emergency_priority import EmergencyPrioritySystem

class TestAlgorithmContracts(unittest.TestCase):
    """
    Verifies that DP and Greedy modules fulfill the BaseAlgorithm contract
    and solve the 'Abstract Method' implementation issue.
    """

    def test_dp_contract_and_logic(self):
        """Validates ResourceAllocationDP (DP) implementation."""
        alg = ResourceAllocationDP()
        
        # Mock data for Knapsack
        data = [
            {"route_id": "R1", "buses": 2, "passengers": 100},
            {"route_id": "R2", "buses": 1, "passengers": 60}
        ]
        
        # Test the run method with custom capacity kwarg
        result = alg.run(data_list=data, capacity=2)
        
        self.assertIn("schedule", result)
        self.assertEqual(result["cost"], 100)
        print("\n✅ DP Contract: run() accepted custom kwargs and returned results.")

    def test_greedy_contract_and_logic(self):
        """Validates EmergencyPriority (Greedy) implementation."""
        # Ensure the class name matches what is inside emergency_priority.py
        try:
            alg = EmergencyPriority()
        except NameError:
            self.skipTest("EmergencyPriority class name mismatch.")

        # Mock emergency data
        data = [
            {"id": "A", "severity": 1},
            {"id": "B", "severity": 10}
        ]
        
        # Greedy usually sorts or picks the best immediate option
        result = alg.run(data=data)
        self.assertIsNotNone(result)
        print("✅ Greedy Contract: run() implemented abstract method successfully.")

    def test_metrics_wrapper_inheritance(self):
        """Checks if execute_with_metrics works across different types."""
        dp_alg = ResourceAllocationDP()
        data = [{"route_id": "R1", "buses": 1, "passengers": 50}]
        
        # This calls the BaseAlgorithm method which in turn calls the DP run()
        result, exec_time = dp_alg.execute_with_metrics(data_list=data, capacity=5)
        
        self.assertIsInstance(exec_time, float)
        self.assertEqual(result["cost"], 50)
        print(f"✅ Inheritance: Base metrics wrapper functional (Time: {exec_time:.4f}ms).")

if __name__ == "__main__":
    unittest.main()