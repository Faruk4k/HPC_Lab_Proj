import os
import re
import csv
import math

ROOT = "results_nopf_multisim"
OUT = "nopf_results.csv"


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

    if "_nopf_" not in run_name:
        continue

    benchmark, memory = run_name.split("_nopf_")

    text = open(stats_path, errors="ignore").read()
    row = {
        "run": run_name,
        "benchmark": benchmark,
        "prefetcher": "none",
        "config": "none",
        "memory": memory,

        # Main simulation stats
        "simSeconds": get_stat(text, "simSeconds"),
        "simTicks": get_stat(text, "simTicks"),
        "simInsts": get_stat(text, "simInsts"),
        "simOps": get_stat(text, "simOps"),
        "numCycles": get_stat(text, "board.processor.cores.core.numCycles"),
        "ipc": get_stat(text, "board.processor.cores.core.ipc"),

        # Demand cache behavior
        "l1d_demand_misses": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMisses::total"),
        "l1d_demand_accesses": get_stat(text, "board.cache_hierarchy.l1dcaches.demandAccesses::total"),
        "l2_demand_misses": get_stat(text, "board.cache_hierarchy.l2cache.demandMisses::total"),
        "l2_demand_accesses": get_stat(text, "board.cache_hierarchy.l2cache.demandAccesses::total"),

        # Demand miss latency
        "l1d_demand_miss_latency": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMissLatency::total"),
        "l1d_demand_avg_miss_latency": get_stat(text, "board.cache_hierarchy.l1dcaches.demandAvgMissLatency::total"),
        "l2_demand_miss_latency": get_stat(text, "board.cache_hierarchy.l2cache.demandMissLatency::total"),
        "l2_demand_avg_miss_latency": get_stat(text, "board.cache_hierarchy.l2cache.demandAvgMissLatency::total"),

        # MSHR / cache blocking pressure
        "l1d_blocked_cycles_no_mshrs": get_stat(text, "board.cache_hierarchy.l1dcaches.blockedCycles::no_mshrs"),
        "l1d_blocked_causes_no_mshrs": get_stat(text, "board.cache_hierarchy.l1dcaches.blockedCauses::no_mshrs"),
        "l1d_avg_blocked_no_mshrs": get_stat(text, "board.cache_hierarchy.l1dcaches.avgBlocked::no_mshrs"),

        "l2_blocked_cycles_no_mshrs": get_stat(text, "board.cache_hierarchy.l2cache.blockedCycles::no_mshrs"),
        "l2_blocked_causes_no_mshrs": get_stat(text, "board.cache_hierarchy.l2cache.blockedCauses::no_mshrs"),
        "l2_avg_blocked_no_mshrs": get_stat(text, "board.cache_hierarchy.l2cache.avgBlocked::no_mshrs"),

        # MSHR miss behavior
        "l1d_demand_mshr_hits": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMshrHits::total"),
        "l1d_demand_mshr_misses": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMshrMisses::total"),
        "l1d_demand_mshr_miss_rate": get_stat(text, "board.cache_hierarchy.l1dcaches.demandMshrMissRate::total"),
        "l1d_demand_avg_mshr_miss_latency": get_stat(text, "board.cache_hierarchy.l1dcaches.demandAvgMshrMissLatency::total"),

        "l2_demand_mshr_hits": get_stat(text, "board.cache_hierarchy.l2cache.demandMshrHits::total"),
        "l2_demand_mshr_misses": get_stat(text, "board.cache_hierarchy.l2cache.demandMshrMisses::total"),
        "l2_demand_mshr_miss_rate": get_stat(text, "board.cache_hierarchy.l2cache.demandMshrMissRate::total"),
        "l2_demand_avg_mshr_miss_latency": get_stat(text, "board.cache_hierarchy.l2cache.demandAvgMshrMissLatency::total"),

        # Memory-controller queue pressure
        "mem_avg_rdq_len": get_stat(text, "board.memory.mem_ctrl.avgRdQLen"),
        "mem_avg_wrq_len": get_stat(text, "board.memory.mem_ctrl.avgWrQLen"),
        "mem_num_rd_retry": get_stat(text, "board.memory.mem_ctrl.numRdRetry"),
        "mem_num_wr_retry": get_stat(text, "board.memory.mem_ctrl.numWrRetry"),

        # Memory bandwidth
        "mem_avg_read_bw_sys": get_stat(text, "board.memory.mem_ctrl.avgRdBWSys"),
        "mem_avg_write_bw_sys": get_stat(text, "board.memory.mem_ctrl.avgWrBWSys"),

        "dram_bw_read_total": get_stat(text, "board.memory.mem_ctrl.dram.bwRead::total"),
        "dram_bw_write_total": get_stat(text, "board.memory.mem_ctrl.dram.bwWrite::total"),
        "dram_bw_total": get_stat(text, "board.memory.mem_ctrl.dram.bwTotal::total"),
        "dram_peak_bw": get_stat(text, "board.memory.mem_ctrl.dram.peakBW"),
        "dram_avg_rd_bw": get_stat(text, "board.memory.mem_ctrl.dram.avgRdBW"),
        "dram_avg_wr_bw": get_stat(text, "board.memory.mem_ctrl.dram.avgWrBW"),

        # Memory latency
        "dram_avg_q_lat": get_stat(text, "board.memory.mem_ctrl.dram.avgQLat"),
        "dram_avg_bus_lat": get_stat(text, "board.memory.mem_ctrl.dram.avgBusLat"),
        "dram_avg_mem_acc_lat": get_stat(text, "board.memory.mem_ctrl.dram.avgMemAccLat"),

        # Core-side load latency distribution summary
        "load_to_use_samples": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::samples"),
        "load_to_use_mean": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::mean"),
        "load_to_use_stdev": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::stdev"),
        "load_to_use_overflows": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::overflows"),
        "load_to_use_min": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::min_value"),
        "load_to_use_max": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::max_value"),

        # LSQ pressure
        "added_loads_and_stores": get_stat(text, "board.processor.cores.core.lsq0.addedLoadsAndStores"),

        # No-prefetch derived placeholders
        "pf_issued": 0,
        "pf_useful": 0,
        "pf_unused": 0,
        "pf_late": 0,
        "pf_accuracy": math.nan,
        "pf_coverage": 0,
        "pf_unused_ratio": math.nan,
        "prefetcher_read_rate": 0,
        "prefetcher_read_bytes": 0,
    }

    rows.append(row)


with open(OUT, "w", newline="") as f:
    fieldnames = list(rows[0].keys()) if rows else []
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {OUT} with {len(rows)} rows")
