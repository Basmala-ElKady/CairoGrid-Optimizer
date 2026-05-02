import time
import os
import traceback
from typing import List, Dict, Tuple, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from Backend.algorithms.shortest_path.astar import AStarAlgorithm
from Backend.algorithms.shortest_path.dijkstra import DijkstraAlgorithm


def _safe_print(*args, debug=False, **kwargs):
    # Always flush to avoid buffered output hiding logs
    if debug:
        print(*args, **kwargs, flush=True)
    else:
        print(*args, **kwargs, flush=True)


def evaluate_algorithms(
    graph,
    scenarios: List[Tuple[str, str, float]],
    output_dir: str,
    mode: str = 'benchmark',
    benchmark_cost_model: str = 'static',
    debug_mode: bool = False
) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Evaluate A* vs Dijkstra across scenarios.

    - `mode`: 'benchmark' | 'realistic'
    - `benchmark_cost_model`: 'static' | 'dynamic' (when mode=='benchmark')
    - `debug_mode`: when True prints internal states and full tracebacks

    Returns: (results_list, nodes_plot_path or None, cost_plot_path or None)
    """

    _safe_print("\n[INFO] ===== Evaluation Started =====", debug=debug_mode)

    # Defensive checks
    if graph is None:
        raise ValueError('graph is None')

    # Graph must expose nodes mapping or get_all_nodes
    nodes_count = 0
    if hasattr(graph, 'nodes'):
        try:
            nodes_count = len(graph.nodes)
        except Exception:
            nodes_count = 0
    elif hasattr(graph, 'get_all_nodes'):
        try:
            nodes_count = len(graph.get_all_nodes())
        except Exception:
            nodes_count = 0

    if nodes_count == 0:
        raise ValueError('graph has no nodes; ensure graph is built and contains nodes')

    _safe_print(f"[DEBUG] Graph nodes: {nodes_count}", debug=debug_mode)
    _safe_print(f"[DEBUG] Scenarios: {scenarios}", debug=debug_mode)

    os.makedirs(output_dir, exist_ok=True)

    astar = AStarAlgorithm()
    dijkstra = DijkstraAlgorithm()

    results: List[Dict] = []

    for idx, sc in enumerate(scenarios):
        try:
            start, end, t0 = sc
        except Exception as e:
            _safe_print(f"[ERROR] Invalid scenario format at index {idx}: {sc} - {e}", debug=True)
            continue

        _safe_print(f"\n[INFO] Running scenario #{idx+1}: {start} -> {end} @ {t0}", debug=debug_mode)

        # Validate start/end
        start_exists = (hasattr(graph, 'get_node') and graph.get_node(start) is not None) or (hasattr(graph, 'nodes') and str(start) in graph.nodes)
        end_exists = (hasattr(graph, 'get_node') and graph.get_node(end) is not None) or (hasattr(graph, 'nodes') and str(end) in graph.nodes)

        if not start_exists or not end_exists:
            _safe_print(f"[WARNING] Skipping scenario {start}->{end}: start_exists={start_exists}, end_exists={end_exists}", debug=debug_mode)
            continue

        try:
            # Dijkstra
            t_start = time.perf_counter()
            dij = dijkstra.run(
                graph,
                start_node=start,
                end_node=end,
                initial_time=t0,
                mode=mode,
                benchmark_cost_model=benchmark_cost_model,
                benchmark_enable_emergency=False
            )
            dij_time = time.perf_counter() - t_start
            _safe_print(f"[DEBUG] Dijkstra result: {dij}", debug=debug_mode)

        except Exception as e:
            _safe_print(f"[ERROR] Dijkstra failed for {start}->{end}: {e}", debug=True)
            if debug_mode:
                traceback.print_exc()
            continue

        try:
            # A*
            t_start = time.perf_counter()
            ast = astar.run(
                graph,
                start,
                end_node=end,
                initial_time=t0,
                mode=mode,
                benchmark_cost_model=benchmark_cost_model,
                benchmark_enable_emergency=False,
                is_emergency=False
            )
            ast_time = time.perf_counter() - t_start
            _safe_print(f"[DEBUG] A* result: {ast}", debug=debug_mode)

        except Exception as e:
            _safe_print(f"[ERROR] A* failed for {start}->{end}: {e}", debug=True)
            if debug_mode:
                traceback.print_exc()
            continue

        # Normalize result fields safely
        dij_nodes = dij.get('nodes_explored') if isinstance(dij, dict) else None
        dij_cost = dij.get('cost') if isinstance(dij, dict) else None

        ast_nodes = ast.get('nodes_explored') if isinstance(ast, dict) else None
        ast_cost = ast.get('cost') if isinstance(ast, dict) else None

        dij_nodes = int(dij_nodes) if dij_nodes not in (None, float('inf')) else 0
        dij_cost = float(dij_cost) if dij_cost not in (None,) else float('inf')

        ast_nodes = int(ast_nodes) if ast_nodes not in (None, float('inf')) else 0
        ast_cost = float(ast_cost) if ast_cost not in (None,) else float('inf')

        # Improvements with proper handling of edge cases
        nodes_improvement = 0.0
        if dij_nodes > 0:
            nodes_improvement = ((dij_nodes - ast_nodes) / float(dij_nodes)) * 100.0

        # Fixed formula: use max() to avoid division by zero
        cost_improvement = 0.0
        if dij_cost != float('inf') and ast_cost != float('inf'):
            cost_improvement = ((dij_cost - ast_cost) / max(dij_cost, 1e-9)) * 100.0

        # Speedup metric: time comparison (% faster)
        speedup_pct = 0.0
        if dij_time > 1e-6:  # Avoid division by very small times
            speedup_pct = ((dij_time - ast_time) / dij_time) * 100.0

        # Efficiency score: combined metric (cost reduction is primary)
        # If costs are nearly equal, prefer algorithm with fewer node expansions
        efficiency_score = 0.0
        if abs(dij_cost - ast_cost) < 1e-6:  # Costs essentially equal
            efficiency_score = ((dij_nodes - ast_nodes) / max(dij_nodes, 1)) * 100.0
            is_tie_cost = True
        else:
            efficiency_score = cost_improvement
            is_tie_cost = False

        # Detect if algorithms behaved identically
        is_identical = (dij_nodes == ast_nodes and 
                       abs(dij_cost - ast_cost) < 1e-6 and
                       dij['path'] == ast['path'] if 'path' in dij and 'path' in ast else False)

        reason_identical = ""
        if is_identical:
            if dij_nodes == ast_nodes == 1:
                reason_identical = "Direct connection (no choice)"
            elif dij_nodes == ast_nodes > 2:
                reason_identical = "Heuristic ineffective on this graph"
            else:
                reason_identical = "Both found same optimal path"

        results.append({
            'start': start,
            'end': end,
            'time_of_day': t0,
            'dijkstra_nodes': dij_nodes,
            'astar_nodes': ast_nodes,
            'dijkstra_cost': dij_cost,
            'astar_cost': ast_cost,
            'dijkstra_time': dij_time,
            'astar_time': ast_time,
            'nodes_improvement_pct': nodes_improvement,
            'cost_improvement_pct': cost_improvement,
            'speedup_pct': speedup_pct,
            'efficiency_score': efficiency_score,
            'is_tie_cost': is_tie_cost,
            'is_identical': is_identical,
            'identical_reason': reason_identical
        })

        # Debug output for this scenario
        if is_identical:
            _safe_print(f"[DEBUG] Identical results: {reason_identical}", debug=debug_mode)
        else:
            _safe_print(f"[DEBUG] Cost improvement: {cost_improvement:.2f}%, Nodes: {nodes_improvement:.2f}%, Speedup: {speedup_pct:.2f}%", debug=debug_mode)

    # End scenarios loop
    if not results:
        _safe_print("\n[WARNING] No successful scenario results were produced.", debug=True)
        _safe_print(f"[DIAGNOSTIC] Graph nodes: {nodes_count}; scenarios provided: {len(scenarios)}", debug=True)
        return [], None, None

    # Aggregation with proper handling
    avg_nodes_dij = sum(r['dijkstra_nodes'] for r in results) / max(1, len(results))
    avg_nodes_ast = sum(r['astar_nodes'] for r in results) / max(1, len(results))
    avg_nodes_improvement = sum(r['nodes_improvement_pct'] for r in results) / max(1, len(results))

    cost_vals_dij = [r['dijkstra_cost'] for r in results if r['dijkstra_cost'] != float('inf')]
    cost_vals_ast = [r['astar_cost'] for r in results if r['astar_cost'] != float('inf')]
    count_cost = len(cost_vals_dij)
    
    avg_cost_dij = sum(cost_vals_dij) / max(1, count_cost) if count_cost > 0 else float('inf')
    avg_cost_ast = sum(cost_vals_ast) / max(1, count_cost) if count_cost > 0 else float('inf')
    
    avg_cost_improvement = 0.0
    if avg_cost_dij != float('inf') and avg_cost_ast != float('inf'):
        avg_cost_improvement = ((avg_cost_dij - avg_cost_ast) / max(avg_cost_dij, 1e-9)) * 100.0

    time_vals_dij = [r['dijkstra_time'] for r in results]
    time_vals_ast = [r['astar_time'] for r in results]
    avg_time_dij = sum(time_vals_dij) / max(1, len(results))
    avg_time_ast = sum(time_vals_ast) / max(1, len(results))
    
    avg_speedup = 0.0
    if avg_time_dij > 1e-6:
        avg_speedup = ((avg_time_dij - avg_time_ast) / avg_time_dij) * 100.0

    # Detect identical cases
    identical_count = sum(1 for r in results if r['is_identical'])
    ties_count = sum(1 for r in results if r['is_tie_cost'])

    # Count which algorithm wins more often
    astar_better = sum(1 for r in results if r['efficiency_score'] > 0.5)
    dijkstra_better = sum(1 for r in results if r['efficiency_score'] < -0.5)
    ties = len(results) - astar_better - dijkstra_better

    # Plots (only when results exist)
    nodes_plot = None
    cost_plot = None

    try:
        labels = [f"{r['start']}→{r['end']}@{r['time_of_day']}" for r in results]
        x = range(len(results))

        plt.figure(figsize=(10, 4))
        plt.bar([i - 0.2 for i in x], [r['dijkstra_nodes'] for r in results], width=0.4, label='Dijkstra')
        plt.bar([i + 0.2 for i in x], [r['astar_nodes'] for r in results], width=0.4, label='A*')
        plt.xticks(x, labels, rotation=45, ha='right')
        plt.ylabel('Nodes explored')
        plt.legend()
        plt.tight_layout()
        nodes_plot = os.path.join(output_dir, 'nodes.png')
        plt.savefig(nodes_plot)
        plt.close()

        plt.figure(figsize=(10, 4))
        plt.plot(x, [r['dijkstra_cost'] for r in results], 'o-', label='Dijkstra')
        plt.plot(x, [r['astar_cost'] for r in results], 's-', label='A*')
        plt.xticks(x, labels, rotation=45, ha='right')
        plt.ylabel('Cost')
        plt.legend()
        plt.tight_layout()
        cost_plot = os.path.join(output_dir, 'cost.png')
        plt.savefig(cost_plot)
        plt.close()
    except Exception as e:
        _safe_print(f"[WARNING] Plotting failed: {e}", debug=True)
        if debug_mode:
            traceback.print_exc()

    # Final report with improved formatting
    _safe_print("\n" + "="*80, debug=debug_mode)
    _safe_print("PERFORMANCE EVALUATION REPORT", debug=debug_mode)
    _safe_print("="*80, debug=debug_mode)
    _safe_print(f"Scenarios evaluated: {len(results)}", debug=debug_mode)
    _safe_print(f"A* won on efficiency: {astar_better} scenarios", debug=debug_mode)
    _safe_print(f"Dijkstra won: {dijkstra_better} scenarios", debug=debug_mode)
    _safe_print(f"Ties (similar efficiency): {ties} scenarios", debug=debug_mode)
    if identical_count > 0:
        _safe_print(f"[WARNING] Identical results: {identical_count} scenarios", debug=debug_mode)

    _safe_print("\n" + "-"*80, debug=debug_mode)
    _safe_print("AGGREGATED METRICS (Averages)", debug=debug_mode)
    _safe_print("-"*80, debug=debug_mode)
    _safe_print(f"Nodes explored:    Dijkstra {avg_nodes_dij:.1f}, A* {avg_nodes_ast:.1f} (A* benefit: {avg_nodes_improvement:.2f}%)", debug=debug_mode)
    _safe_print(f"Path cost:         Dijkstra {avg_cost_dij if avg_cost_dij!=float('inf') else 'inf':.2f}, A* {avg_cost_ast if avg_cost_ast!=float('inf') else 'inf':.2f} (A* benefit: {avg_cost_improvement:.2f}%)", debug=debug_mode)
    _safe_print(f"Execution time:    Dijkstra {avg_time_dij*1000:.3f}ms, A* {avg_time_ast*1000:.3f}ms (A* faster: {avg_speedup:.2f}%)", debug=debug_mode)

    _safe_print("\n" + "-"*80, debug=debug_mode)
    _safe_print("PER-SCENARIO COMPARISON", debug=debug_mode)
    _safe_print("-"*80, debug=debug_mode)
    _safe_print(f"{'Route':<20} {'Nodes (D/A)':<15} {'Cost (D/A)':<20} {'Time (ms)':<15} {'Status':<15}", debug=debug_mode)
    _safe_print("-"*80, debug=debug_mode)

    for r in results:
        route_label = f"{r['start']}→{r['end']}@{r['time_of_day']}"
        nodes_label = f"{r['dijkstra_nodes']}/{r['astar_nodes']}"
        cost_label = f"{r['dijkstra_cost']:.2f}/{r['astar_cost']:.2f}"
        time_label = f"{r['dijkstra_time']*1000:.2f}/{r['astar_time']*1000:.2f}"
        
        if r['is_identical']:
            status = f"IDENTICAL ({r['identical_reason'][:20]})"
        elif r['efficiency_score'] > 0.5:
            status = f"A* WINS ({r['efficiency_score']:.1f}%)"
        elif r['efficiency_score'] < -0.5:
            status = f"D WINS ({abs(r['efficiency_score']):.1f}%)"
        else:
            status = "SIMILAR"
        
        _safe_print(f"{route_label:<20} {nodes_label:<15} {cost_label:<20} {time_label:<15} {status:<15}", debug=debug_mode)

    _safe_print("\n" + "="*80, debug=debug_mode)
    if nodes_plot:
        _safe_print(f"[PLOT] Nodes comparison saved: {nodes_plot}", debug=debug_mode)
    if cost_plot:
        _safe_print(f"[PLOT] Cost comparison saved: {cost_plot}", debug=debug_mode)

    return results, nodes_plot, cost_plot


if __name__ == '__main__':
    # When invoked directly, run a minimal example
    try:
        # Build a tiny sample graph
        from Backend.graph.transport_graph import TransportGraph
        from Backend.models.node import Node
        from Backend.models.edge import Edge
        from Backend.models.enums import LocationType, TimePeriod

        g = TransportGraph()
        nA = Node('A', 'A', LocationType.DISTRICT, 0, 0)
        nB = Node('B', 'B', LocationType.DISTRICT, 1, 0)
        nC = Node('C', 'C', LocationType.FACILITY, 2, 0)
        g.add_node(nA); g.add_node(nB); g.add_node(nC)

        prof = {TimePeriod.MORNING_PEAK: 900.0, TimePeriod.AFTERNOON: 100.0, TimePeriod.EVENING_PEAK: 400.0, TimePeriod.NIGHT: 10.0}
        g.add_edge(Edge('A', 'B', distance=1.0, capacity=100, condition=8, traffic_profile=prof))
        g.add_edge(Edge('B', 'C', distance=1.0, capacity=100, condition=8, traffic_profile=prof))

        scenarios = [('A', 'C', 8.0), ('B', 'C', 8.0)]
        out_dir = os.path.join(os.getcwd(), 'Backend', 'simulation', 'output')

        evaluate_algorithms(g, scenarios, out_dir, mode='benchmark', benchmark_cost_model='dynamic', debug_mode=True)
    except Exception as e:
        print('[FATAL] Example run failed:', e)
        import traceback
        traceback.print_exc()