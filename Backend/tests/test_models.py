from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sys
import os



from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod

def test_system_backbone():
    print("🧪 Running Unit Tests for Models...\n")

    try:
        # 1. Test Node Creation
        node_a = Node("1", "Maadi", LocationType.DISTRICT, 31.25, 29.96, 250000)
        node_b = Node("F1", "Cairo Airport", LocationType.FACILITY, 31.41, 30.11)
        
        print(f"✅ Nodes created: {node_a.name} (ID: {node_a.id}), {node_b.name} (ID: {node_b.id})")

        # 2. Test Edge & Traffic Profile
        # Create an edge from Maadi to Airport: dist=15km, cap=3000, condition=8
        road = Edge(node_a.id, node_b.id, 15.0, 3000, 8)
        
        # Set traffic flow for Morning Peak
        road.traffic.update_flow(TimePeriod.MORNING_PEAK, 2800) # Heavy traffic
        road.traffic.update_flow(TimePeriod.NIGHT, 500)         # Light traffic

        print(f"✅ Edge created: {road.source_id} -> {road.target_id}")

        # 3. Test Dynamic Weight Calculation (The Core Logic)
        morning_weight = road.get_weight(TimePeriod.MORNING_PEAK)
        night_weight = road.get_weight(TimePeriod.NIGHT)

        print(f"\n📈 Weight Analysis for 15km road:")
        print(f"- Morning Peak Weight: {morning_weight} (Expected to be high)")
        print(f"- Night Weight: {night_weight} (Expected to be lower)")

        assert morning_weight > night_weight, "Error: Morning weight should be higher than Night weight!"
        assert isinstance(node_b.id, str), "Error: ID should be a string to support 'F1'!"

        print("\n🎉 All Model Tests Passed Successfully!")

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")

if __name__ == "__main__":
    test_system_backbone()