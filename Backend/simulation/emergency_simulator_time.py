import os
import sys

# =========================
# FIX IMPORT PATH (IMPORTANT)
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)

from Backend.graph.transport_graph import TransportGraph
from Backend.models.node import Node
from Backend.models.edge import Edge
from Backend.models.enums import LocationType, TimePeriod
from Backend.services.emergency_service import EmergencyService
from Backend.simulation.emergency_simulation_engine import SimulationEngine
from Backend.services.intersection_priority import IntersectionPriority


def build_sample_graph():
    """Builds a small sample graph used for demonstration and testing."""
    g = TransportGraph()

    # Simple sample nodes
    A = Node('A', 'Accident', LocationType.DISTRICT, 31.22, 30.02)
    F9 = Node('F9', 'Qasr El Aini Hospital', LocationType.FACILITY, 31.23, 30.03)
    F10 = Node('F10', 'Maadi Military Hospital', LocationType.FACILITY, 31.25, 29.95)

    for n in (A, F9, F10):
        g.add_node(n)

    # Traffic profiles (vehicle flows)
    profile_morning = {
        TimePeriod.MORNING_PEAK: 300.0,
        TimePeriod.AFTERNOON: 100.0,
        TimePeriod.EVENING_PEAK: 200.0,
        TimePeriod.NIGHT: 50.0
    }

    profile_heavy = {
        TimePeriod.MORNING_PEAK: 800.0,
        TimePeriod.AFTERNOON: 400.0,
        TimePeriod.EVENING_PEAK: 700.0,
        TimePeriod.NIGHT: 100.0
    }

    # Edges with different distances and dynamic traffic
    e1 = Edge('A', 'F9', distance=1.5, capacity=100, condition=8, traffic_profile=profile_heavy)
    e2 = Edge('A', 'F10', distance=5.0, capacity=200, condition=9, traffic_profile=profile_morning)

    g.add_edge(e1)
    g.add_edge(e2)

    return g


def pretty_print_log(title: str, result: dict):
    print('\n' + '=' * 60)
    print(title)
    print('-' * 60)
    print('Path:', result.get('path'))
    print('Cost:', result.get('cost'))
    print('Nodes explored:', result.get('nodes_explored'))
    print('Metadata:', result.get('metadata', {}))
    print('=' * 60 + '\n')


def run_demo():
    graph = build_sample_graph()
    # instantiate simulation engine with default intersection priority
    print('[START] emergency_simulator time-comparison demo', flush=True)
    ip = IntersectionPriority()
    engine = SimulationEngine(graph, intersection_priority=ip)

    # Run scenarios at different times to show time-varying traffic effect
    scenarios = [
        ("A", 8.0, "Morning Peak"),
        ("A", 12.0, "Afternoon"),
        ("A", 17.0, "Evening Peak"),
        ("A", 2.0, "Night"),
    ]

    print("\n" + "="*70, flush=True)
    print("TIME-VARYING TRAFFIC COMPARISON", flush=True)
    print("="*70 + "\n", flush=True)

    results_comparison = []

    for start, time_of_day, label in scenarios:
        print(f"\n[SCENARIO] {label} (time={time_of_day})", flush=True)
        print("-" * 70, flush=True)
        
        res, timeline = engine.run_scenario(start, time_of_day=time_of_day)

        path = res.get('path', [])
        cost = res.get('cost', float('inf'))
        period = res.get('metadata', {}).get('period', 'UNKNOWN')
        final_time = res.get('metadata', {}).get('final_time', 'N/A')
        
        if path and cost < float('inf'):
            print(f"[RESULT] Path: {' -> '.join(path)}", flush=True)
            print(f"[RESULT] Cost: {cost:.3f}", flush=True)
            print(f"[RESULT] Period: {period}", flush=True)
            print(f"[RESULT] Final time: {final_time}", flush=True)
            print(f"[RESULT] Timeline steps: {len(timeline)}", flush=True)
            for t, node in timeline:
                print(f"         time={t:.3f}, node={node}", flush=True)
        else:
            print(f"[WARNING] No valid path found", flush=True)

        results_comparison.append({
            'time': time_of_day,
            'label': label,
            'period': period,
            'cost': cost,
            'path': path
        })

    # Print summary comparison
    print("\n" + "="*70, flush=True)
    print("SUMMARY: COST COMPARISON BY TIME OF DAY", flush=True)
    print("="*70, flush=True)
    print(f"{'Time':<8} {'Label':<20} {'Period':<15} {'Cost':<15}", flush=True)
    print("-"*70, flush=True)
    
    for r in results_comparison:
        cost_str = f"{r['cost']:.3f}" if r['cost'] < float('inf') else "inf"
        print(f"{r['time']:<8.1f} {r['label']:<20} {r['period']:<15} {cost_str:<15}", flush=True)

    # Calculate and show time effect
    valid_costs = [r['cost'] for r in results_comparison if r['cost'] < float('inf')]
    if len(valid_costs) > 1:
        min_cost = min(valid_costs)
        max_cost = max(valid_costs)
        improvement = ((max_cost - min_cost) / max_cost * 100) if max_cost > 0 else 0
        print("\n[TIME EFFECT ANALYSIS]", flush=True)
        print(f"  Min cost (best time): {min_cost:.3f}", flush=True)
        print(f"  Max cost (peak time): {max_cost:.3f}", flush=True)
        print(f"  Time-varying effect: {improvement:.1f}% cost difference", flush=True)

    print("\n[DONE] emergency_simulator", flush=True)


if __name__ == '__main__':
    run_demo()