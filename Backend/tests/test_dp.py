import unittest
from Backend.algorithms.dp.resource_allocation import ResourceAllocationDP

class TestDP(unittest.TestCase):
    def test_resource_allocation(self):
        data = [
            {"route_id": "R1", "buses": 2, "passengers": 100, "time": "08:00"},
            {"route_id": "R2", "buses": 1, "passengers": 60, "time": "09:00"},
            {"route_id": "R3", "buses": 3, "passengers": 150, "time": "10:00"}
        ]
        dp_alg = ResourceAllocationDP()
        result, exec_time = dp_alg.execute_with_metrics(data=data, capacity=4)
        
       
        self.assertIn('cost', result)
        self.assertGreater(exec_time, 0)
        print(f"\nDP Test Passed! Cost: {result['cost']}")

if __name__ == "__main__":
    unittest.main()