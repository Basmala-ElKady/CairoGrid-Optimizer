import os
import csv
import statistics
import matplotlib.pyplot as plt


def read_results(csv_path):
    rows = []

    print(f"\n[INFO] Reading CSV: {csv_path}")

    if not os.path.exists(csv_path):
        print("[ERROR] CSV file not found!")
        return []

    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)

        for r in reader:
            try:
                non = float(r['non_cost']) if r['non_cost'] not in ('', 'inf') else float('inf')
            except:
                non = float('inf')

            try:
                em = float(r['em_cost']) if r['em_cost'] not in ('', 'inf') else float('inf')
            except:
                em = float('inf')

            reduction = None
            if non != float('inf') and em != float('inf'):
                reduction = non - em

            rows.append({
                'start_node': r['start_node'],
                'non_cost': non,
                'em_cost': em,
                'reduction': reduction
            })

    print(f"[INFO] Rows loaded: {len(rows)}")
    return rows


def plot_histogram(reductions, out_png):
    print(f"[INFO] Saving histogram -> {out_png}")

    plt.figure(figsize=(6, 4))
    plt.hist(reductions, bins=20)
    plt.xlabel('Cost reduction (non - emergency)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()


def plot_scatter(rows, out_png):
    print(f"[INFO] Saving scatter plot -> {out_png}")

    xs = list(range(len(rows)))
    ys = [r['reduction'] if r['reduction'] is not None else 0 for r in rows]

    plt.figure(figsize=(8, 4))
    plt.scatter(xs, ys, alpha=0.7)
    plt.xlabel('Sample index')
    plt.ylabel('Cost reduction')
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()


def generate_markdown(csv_path, out_md, png_hist, png_scatter):
    rows = read_results(csv_path)

    reductions = [r['reduction'] for r in rows if r['reduction'] is not None]

    print(f"[INFO] Valid reductions: {reductions}")

    if reductions:
        avg = statistics.mean(reductions)
        med = statistics.median(reductions)
        count = len(reductions)
    else:
        avg = med = 0
        count = 0

    print(f"[INFO] Avg reduction: {avg}, Median: {med}")

    with open(out_md, 'w') as f:
        f.write('# Emergency Routing Analysis\n\n')
        f.write(f'- Samples (valid reduction): {count}\n')
        f.write(f'- Average reduction: {avg:.3f}\n')
        f.write(f'- Median reduction: {med:.3f}\n\n')
        f.write('## Plots\n\n')
        f.write(f'![]({os.path.basename(png_hist)})\n\n')
        f.write(f'![]({os.path.basename(png_scatter)})\n')

    print(f"[INFO] Markdown saved -> {out_md}")


if __name__ == '__main__':

    base = os.path.join(os.getcwd(), 'Backend', 'simulation', 'output')
    csv_path = os.path.join(base, 'response_time_comparison.csv')

    out_hist = os.path.join(base, 'hist_reduction.png')
    out_scatter = os.path.join(base, 'scatter_reduction.png')
    out_md = os.path.join(base, 'analysis_report.md')

    print("\n========== EMERGENCY ANALYSIS START ==========")

    rows = read_results(csv_path)

    if not rows:
        print("[STOP] No data to process.")
        exit()

    reductions = [r['reduction'] for r in rows if r['reduction'] is not None]

    print(f"[INFO] Reductions extracted: {reductions}")

    if reductions:
        plot_histogram(reductions, out_hist)
        plot_scatter(rows, out_scatter)

    generate_markdown(csv_path, out_md, out_hist, out_scatter)

    print("\n========== DONE ==========")