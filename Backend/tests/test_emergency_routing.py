from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import csv

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType
from Backend.services.emergency_service import EmergencyService


def write_facilities_csv(path):
    rows = [
        ["ID", "Name", "Type", "X-coordinate", "Y-coordinate"],
        ["F9", "Qasr El Aini Hospital", "Medical", 31.23, 30.03],
        ["F10", "Maadi Military Hospital", "Medical", 31.25, 29.95]
    ]
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def test_emergency_routing_nearest(tmp_path):
    graph = TransportGraph()

    nA = Node('A', 'Accident', LocationType.DISTRICT, 31.22, 30.02)
    nF9 = Node('F9', 'Qasr El Aini Hospital', LocationType.FACILITY, 31.23, 30.03)
    nF10 = Node('F10', 'Maadi Military Hospital', LocationType.FACILITY, 31.25, 29.95)

    for n in (nA, nF9, nF10):
        graph.add_node(n)

    graph.add_edge(Edge('A', 'F9', distance=1.5, capacity=100, condition=8))
    graph.add_edge(Edge('A', 'F10', distance=5.0, capacity=100, condition=8))

    csv_path = tmp_path / "facilities_test.csv"
    write_facilities_csv(str(csv_path))

    service = EmergencyService(graph, facilities_csv=str(csv_path))
    result = service.get_nearest_hospital_route('A')

    # ================= DEBUG OUTPUT =================
    print("\n========== EMERGENCY ROUTING TEST ==========")
    print("PATH:", result.get("path"))
    print("COST:", result.get("cost"))
    print("METADATA:", result.get("metadata"))
    print("=============================================\n")

    # ================= ASSERTIONS =================
    assert result['path'] != []
    assert result['path'][-1] == 'F9'
    assert result['metadata'].get('hospital_id') == 'F9'
    assert result['metadata'].get('hospital_name') == 'Qasr El Aini Hospital'
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
