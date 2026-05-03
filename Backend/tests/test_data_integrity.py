from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import os

def run_data_integrity_test():
    print("📂 Starting Raw Data Integrity Check...\n")
    
    # Get the directory of this script and build the path to data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, "..", "data", "processed")
    
    required_files = [
        "neighborhoods_districts.csv", "facilities.csv", "existing_roads.csv",
        "traffic_flow.csv", "bus_routes.csv", "metro_lines.csv",
        "potential_roads.csv", "transport_demand.csv"
    ]

    try:
        # 1. Check if all files exist
        for file in required_files:
            path = os.path.join(base_path, file)
            if not os.path.exists(path):
                print(f"❌ Missing File: {file}")
            else:
                print(f"✅ Found: {file}")

        print("\n🔍 Checking for Nulls and Logical Errors...")

        # 2. Validate Districts & Facilities (The Nodes)
        districts = pd.read_csv(os.path.join(base_path, "neighborhoods_districts.csv"))
        facilities = pd.read_csv(os.path.join(base_path, "facilities.csv"))
        
        # Combine all valid IDs
        all_node_ids = set(districts['ID'].astype(str)) | set(facilities['ID'].astype(str))

        if districts.isnull().values.any():
            print("⚠️ Warning: Found null values in districts data!")
        
        # 3. Validate Roads (The Edges)
        roads = pd.read_csv(os.path.join(base_path, "existing_roads.csv"))
        
        # Check if every road connects to a valid node ID
        invalid_roads = []
        for idx, row in roads.iterrows():
            if str(row['FromID']) not in all_node_ids or str(row['TOID']) not in all_node_ids:
                invalid_roads.append(f"Row {idx}: {row['FromID']} -> {row['TOID']}")

        if not invalid_roads:
            print(f"✅ Road Integrity: All {len(roads)} roads connect valid nodes.")
        else:
            print(f"❌ Found {len(invalid_roads)} orphaned roads! Check IDs: {invalid_roads[:5]}")

        # 4. Check Traffic Flow matching
        traffic = pd.read_csv(os.path.join(base_path, "traffic_flow.csv"))
        if len(traffic) != len(roads):
            print(f"⚠️ Warning: Traffic entries ({len(traffic)}) don't match Road entries ({len(roads)}).")
        else:
            print("✅ Traffic Coverage: Perfect match with existing roads.")

        print("\n🏆 DATA INTEGRITY CHECK COMPLETE.")

    except Exception as e:
        print(f"❌ Error during data test: {e}")

if __name__ == "__main__":
    run_data_integrity_test()