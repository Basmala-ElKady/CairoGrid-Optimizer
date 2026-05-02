import unittest
import sys
import os

def run_project_pipeline():
    """
    Finalized Automated Test Pipeline.
    This version uses Root Discovery to avoid needing __init__.py files.
    """
    print("🚀 Starting Cairo Smart City Automation Pipeline...")
    
    # Define the project root directory
    project_root = os.path.abspath(os.getcwd())
    
    print(f"🔍 Working Directory: {project_root}")
    
    loader = unittest.TestLoader()
    
    try:
        # Discover tests specifically from Backend/tests
        # top_level_dir=project_root ensures 'from Backend.xxx import ...' works
        test_dir = os.path.join(project_root, 'Backend', 'tests')
        print(f"🔍 Searching for tests in: {test_dir}")
        suite = loader.discover(
            start_dir=test_dir,
            pattern='test_*.py',
            top_level_dir=project_root
        )
        
        # Run the discovered test suite
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Final reporting summary
        print("\n" + "="*30)
        print("📊 PIPELINE SUMMARY")
        print(f"Total Tests Run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print("="*30)

        # Exit with error if any tests failed or crashed
        if not result.wasSuccessful():
            print("\n❌ Pipeline Failed: Review the errors above.")
            sys.exit(1)
        
        print("\n✅ Pipeline Passed: All modules are stable.")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Critical Error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_project_pipeline()