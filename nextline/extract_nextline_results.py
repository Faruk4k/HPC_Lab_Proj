import os
import re
import csv
import math

ROOT = "results_nextline_multisim"
OUT = "nextline_results.csv"


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

    if "_nextline_" not in run_name:
        continue

    benchmark, rest = run_name.split("_nextline_", 1)

    if rest.endswith("_l1d_ddr4_1x"):
        pf_level = "l1d"
        memory = "ddr4_1x"
        config = rest[: -len("_l1d_ddr4_1x")]
    elif rest.endswith("_l1d_ddr4_2x"):
        pf_level = "l1d"
        memory = "ddr4_2x"
        config = rest[: -len("_l1d_ddr4_2x")]
    elif rest.endswith("_l2_ddr4_1x"):
        pf_level = "l2"
        memory = "ddr4_1x"
        config = rest[: -len("_l2_ddr4_1x")]
    elif rest.endswith("_l2_ddr4_2x"):
        pf_level = "l2"
        memory = "ddr4_2x"
        config = rest[: -len("_l2_ddr4_2x")]
    else:
        print(f"Skipping unrecognized run name: {run_name}")
        continue

    text = open(stats_path, errors="ignore").read()

    rows.append({
        "run": run_name,
        "benchmark": benchmark,
        "prefetcher": "nextline",
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


if not rows:
    raise RuntimeError("No Next-line rows extracted")

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {OUT} with {len(rows)} rows")