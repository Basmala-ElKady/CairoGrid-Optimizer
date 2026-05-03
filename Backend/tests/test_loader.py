from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sys
import os



from Backend.utils.data_loader import DataLoader
from Backend.models.enums import LocationType, TimePeriod

def run_loader_test():
    """
    Verification test to ensure DataLoader correctly maps CSV data and merges traffic flows.
    """
    print("🧪 Starting DataLoader Verification Test...\n")

    # Paths to processed data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
    roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")
    traffic_path = os.path.join(script_dir, "..", "data", "processed", "traffic_flow.csv")

    # 1. Test Node Loading
    districts = DataLoader.load_nodes(districts_path, LocationType.DISTRICT)
    print(f"✅ Successfully loaded {len(districts)} District Nodes.")

    # 2. Test Edge Loading & Traffic Merge
    edges = DataLoader.load_edges(roads_path, traffic_path)
    print(f"✅ Successfully loaded {len(edges)} Road Edges.")

    # 3. Data Integrity Validation
    if edges and districts:
        sample_edge = edges[0]
        print(f"\n🔍 Data Integrity Check (Sample Edge):")
        print(f"   Connection: {sample_edge.source_id} -> {sample_edge.target_id}")
        
        # Verify if weights change based on the traffic profile we injected
        night_weight = sample_edge.get_weight(TimePeriod.NIGHT)
        peak_weight = sample_edge.get_weight(TimePeriod.MORNING_PEAK)
        
        print(f"   Night Weight: {night_weight:.2f}")
        print(f"   Peak Weight: {peak_weight:.2f}")

        if peak_weight >= night_weight:
            print("\n🟢 TEST PASSED: Traffic logic is correctly integrated!")
        else:
            print("\n🔴 TEST FAILED: Traffic logic or weight calculation is inconsistent.")

if __name__ == "__main__":
    run_loader_test()