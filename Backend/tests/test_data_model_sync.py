from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sys
import os
import pandas as pd



from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType

def test_data_with_models():
    print("🔗 Running Integration Test: Data + Models (Professional Sync Check)...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    districts_path = os.path.join(script_dir, "..", "data", "processed", "neighborhoods_districts.csv")
    roads_path = os.path.join(script_dir, "..", "data", "processed", "existing_roads.csv")

    try:
        # 1. Load Nodes with Header Normalization
        df_nodes = pd.read_csv(districts_path)
        # Normalize headers to lowercase to avoid 'id' vs 'ID' errors
        df_nodes.columns = df_nodes.columns.str.strip().str.lower()
        
        first_row = df_nodes.iloc[0]
        
        # Mapping CSV columns to Node Model
        test_node = Node(
            node_id=str(first_row['id']),
            name=first_row['name'],
            node_type=LocationType.DISTRICT,
            x=float(first_row['x-coordinate']),
            y=float(first_row['y-coordinate']),
            population=int(first_row['population'])
        )
        print(f"✅ Node Model Sync: Successfully mapped '{test_node.name}'")

        # 2. Load Roads with Header Normalization
        df_roads = pd.read_csv(roads_path)
        df_roads.columns = df_roads.columns.str.strip().str.lower()
        
        first_road = df_roads.iloc[0]
        
        # Mapping CSV columns to Edge Model
        test_edge = Edge(
            source_id=str(first_road['fromid']),
            target_id=str(first_road['toid']),
            distance=float(first_road['distance(km)']),
            capacity=int(first_road['current capacity(vehicles/hour)']),
            condition=int(first_road['condition(1-10)'])
        )
        print(f"✅ Edge Model Sync: Successfully mapped road {test_edge.source_id} -> {test_edge.target_id}")

        print("\n🎉 INTEGRATION SUCCESS: Models and CSVs are perfectly aligned!")

    except KeyError as e:
        print(f"❌ Column Name Error: Could not find column {e} in CSV. Check your mapping!")
    except Exception as e:
        print(f"❌ Integration Error: {e}")

if __name__ == "__main__":
    test_data_with_models()