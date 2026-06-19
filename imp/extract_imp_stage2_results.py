import os
import re
import csv
import math

ROOT = "results_imp_stage2"
OUT = "imp_stage2_results.csv"

def get_stat(text, name):
    matches = re.findall(
        rf"^{re.escape(name)}\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        text,
        re.MULTILINE,
    )
    return float(matches[-1]) if matches else math.nan
rows = []

for run_name in sorted(os.listdir(ROOT)):
    run_dir = os.path.join(ROOT, run_name)
    stats_path = os.path.join(run_dir, "stats.txt")

    if not os.path.isdir(run_dir) or not os.path.exists(stats_path):
        continue

    # expected format:
    # benchmark_imp_stage2_config_level_memory
    parts = run_name.split("_imp_stage2_")
    if len(parts) != 2:
        continue

    benchmark = parts[0]
    rest = parts[1]

    # memory is always ddr4_1x or ddr4_2x
    if rest.endswith("_ddr4_1x"):
        memory = "ddr4_1x"
        rest = rest[:-len("_ddr4_1x")]
    elif rest.endswith("_ddr4_2x"):
        memory = "ddr4_2x"
        rest = rest[:-len("_ddr4_2x")]
    else:
        continue

    if rest.endswith("_l1d"):
        pf_level = "l1d"
        config = rest[:-len("_l1d")]
    elif rest.endswith("_l2"):
        pf_level = "l2"
        config = rest[:-len("_l2")]
    else:
        continue

    text = open(stats_path, errors="ignore").read()

    rows.append({
        "run": run_name,
        "benchmark": benchmark,
        "prefetcher": "imp",
        "config": config,
        "pf_level": pf_level,
        "memory": memory,

        "simSeconds": get_stat(text, "simSeconds"),
        "simTicks": get_stat(text, "simTicks"),
        "simInsts": get_stat(text, "simInsts"),
        "numCycles": get_stat(text, "board.processor.cores.core.numCycles"),
        "ipc": get_stat(text, "board.processor.cores.core.ipc"),

        "l1d_demand_misses": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMisses::total"),
        "l1d_demand_accesses": get_stat(text, "board.cache_hierarchy.l1dcaches.demandAccesses::total"),
        "l2_demand_misses": get_stat(text, "board.cache_hierarchy.l2cache.demandMisses::total"),
        "l2_demand_accesses": get_stat(text, "board.cache_hierarchy.l2cache.demandAccesses::total"),

                
        "l1d_pf_issued": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfIssued"),
        "l1d_pf_useful": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfUseful"),
        "l1d_pf_unused": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfUnused"),

        "l2_pf_issued": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfIssued"),
        "l2_pf_useful": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfUseful"),
        "l2_pf_unused": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfUnused"),
    })

fieldnames = list(rows[0].keys()) if rows else []

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {OUT} with {len(rows)} rows")
