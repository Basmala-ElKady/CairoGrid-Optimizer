import unittest
import sys
import os

def run_project_pipeline():
    print("🚀 Starting Cairo Smart City Automation Pipeline...")
    
    # 1. Discover all tests in the 'Backend/tests' folder
    loader = unittest.TestLoader()
    # Assuming your tests are in Backend/tests
    start_dir = './Backend/tests'
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 2. Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 3. Exit with error code if tests fail
    # This tells GitHub Actions to stop and show a RED X
    if not result.wasSuccessful():
        print("\n❌ Pipeline Failed: Some tests did not pass.")
        sys.exit(1)
    
    print("\n✅ Pipeline Passed: All modules are stable.")
    sys.exit(0)

if __name__ == "__main__":
    run_project_pipeline()
    