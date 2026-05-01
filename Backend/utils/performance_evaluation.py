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

        # Improvements
        nodes_improvement = 0.0
        if dij_nodes != 0:
            nodes_improvement = (dij_nodes - ast_nodes) / float(dij_nodes) * 100.0

        cost_improvement = 0.0
        if dij_cost not in (0, float('inf')) and ast_cost != float('inf'):
            cost_improvement = (dij_cost - ast_cost) / float(dij_cost) * 100.0

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
            'cost_improvement_pct': cost_improvement
        })

    # End scenarios loop
    if not results:
        _safe_print("\n[WARNING] No successful scenario results were produced.", debug=True)
        _safe_print(f"[DIAGNOSTIC] Graph nodes: {nodes_count}; scenarios provided: {len(scenarios)}", debug=True)
        return [], None, None

    # Aggregation
    avg_nodes_dij = sum(r['dijkstra_nodes'] for r in results) / max(1, len(results))
    avg_nodes_ast = sum(r['astar_nodes'] for r in results) / max(1, len(results))

    cost_vals_dij = [r['dijkstra_cost'] for r in results if r['dijkstra_cost'] != float('inf')]
    count_cost = len(cost_vals_dij)
    avg_cost_dij = sum(cost_vals_dij) / max(1, count_cost) if count_cost > 0 else float('inf')

    cost_vals_ast = [r['astar_cost'] for r in results if r['astar_cost'] != float('inf')]
    avg_cost_ast = sum(cost_vals_ast) / max(1, count_cost) if count_cost > 0 else float('inf')

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

    # Final report
    _safe_print("\n========== FINAL REPORT ==========", debug=debug_mode)
    _safe_print(f"Scenarios evaluated: {len(results)}", debug=debug_mode)
    _safe_print(f"Avg nodes - Dijkstra: {avg_nodes_dij:.2f}, A*: {avg_nodes_ast:.2f}", debug=debug_mode)
    _safe_print(f"Avg cost - Dijkstra: {avg_cost_dij if avg_cost_dij!=float('inf') else 'inf'}, A*: {avg_cost_ast if avg_cost_ast!=float('inf') else 'inf'}", debug=debug_mode)
    if nodes_plot:
        _safe_print(f"Nodes plot: {nodes_plot}", debug=debug_mode)
    if cost_plot:
        _safe_print(f"Cost plot: {cost_plot}", debug=debug_mode)

    for r in results:
        _safe_print(
            f"{r['start']}->{r['end']} | D_nodes={r['dijkstra_nodes']} A_nodes={r['astar_nodes']} | D_cost={r['dijkstra_cost']} A_cost={r['astar_cost']}",
            debug=debug_mode
        )

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