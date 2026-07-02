import os
import re
import csv
import math

ROOT = "results_imp_stage3"
OUT = "imp_stage3_results.csv"


def get_stat(text, name):
    matches = re.findall(
        rf"^{re.escape(name)}\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        text,
        re.MULTILINE,
    )
    return float(matches[-1]) if matches else math.nan

def get_stat_values_regex(text, name_regex):
    num = r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    pattern = rf"^({name_regex})\s+{num}"

    values_by_name = {}

    for match in re.finditer(pattern, text, re.MULTILINE):
        stat_name = match.group(1)
        value = float(match.group(2))
        values_by_name[stat_name] = value

    return list(values_by_name.values())


def get_stat_sum_any(text, exact_name, regex_name):
    exact = get_stat(text, exact_name)

    if not math.isnan(exact):
        return exact

    values = get_stat_values_regex(text, regex_name)

    if not values:
        return math.nan

    return sum(values)


def get_stat_mean_any(text, exact_name, regex_name):
    exact = get_stat(text, exact_name)

    if not math.isnan(exact):
        return exact

    values = get_stat_values_regex(text, regex_name)

    if not values:
        return math.nan

    return sum(values) / len(values)

rows = []

for run_name in sorted(os.listdir(ROOT)):
    run_dir = os.path.join(ROOT, run_name)
    stats_path = os.path.join(run_dir, "stats.txt")

    if not os.path.isdir(run_dir) or not os.path.exists(stats_path):
        continue

    # Format:
    # benchmark_imp3_config_pflevel_memory
    if "_imp3_" not in run_name:
        continue

    benchmark, rest = run_name.split("_imp3_", 1)

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
    row = {
        "run": run_name,
        "benchmark": benchmark,
        "prefetcher": "imp",
        "stage": "stage3",
        "config": config,
        "pf_level": pf_level,
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

        # Basic L1D prefetch stats
        "l1d_pf_issued": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfIssued"),
        "l1d_pf_useful": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfUseful"),
        "l1d_pf_unused": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfUnused"),
        "l1d_prefetcher_accuracy": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.accuracy"),
        "l1d_prefetcher_coverage": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.coverage"),

        # Extra L1D prefetch behavior
        "l1d_pf_late": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfLate"),
        "l1d_pf_hit_in_cache": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfHitInCache"),
        "l1d_pf_hit_in_mshr": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfHitInMSHR"),
        "l1d_pf_hit_in_wb": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfHitInWB"),
        "l1d_pf_identified": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfIdentified"),
        "l1d_pf_buffer_hit": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfBufferHit"),
        "l1d_pf_in_cache": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfInCache"),
        "l1d_pf_removed_demand": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfRemovedDemand"),
        "l1d_pf_removed_full": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfRemovedFull"),
        "l1d_pf_span_page": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfSpanPage"),
        "l1d_pf_useful_span_page": get_stat(text, "board.cache_hierarchy.l1dcaches.prefetcher.pfUsefulSpanPage"),

        # Basic L2 prefetch stats
        "l2_pf_issued": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfIssued"),
        "l2_pf_useful": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfUseful"),
        "l2_pf_unused": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfUnused"),
        "l2_prefetcher_accuracy": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.accuracy"),
        "l2_prefetcher_coverage": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.coverage"),

        # Extra L2 prefetch behavior
        "l2_pf_late": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfLate"),
        "l2_pf_hit_in_cache": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfHitInCache"),
        "l2_pf_hit_in_mshr": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfHitInMSHR"),
        "l2_pf_hit_in_wb": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfHitInWB"),
        "l2_pf_identified": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfIdentified"),
        "l2_pf_buffer_hit": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfBufferHit"),
        "l2_pf_in_cache": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfInCache"),
        "l2_pf_removed_demand": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfRemovedDemand"),
        "l2_pf_removed_full": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfRemovedFull"),
        "l2_pf_span_page": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfSpanPage"),
        "l2_pf_useful_span_page": get_stat(text, "board.cache_hierarchy.l2cache.prefetcher.pfUsefulSpanPage"),

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
        "mem_avg_rdq_len": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.avgRdQLen",
            r"board\.memory\.mem_ctrl\d+\.avgRdQLen",
        ),
        "mem_avg_wrq_len": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.avgWrQLen",
            r"board\.memory\.mem_ctrl\d+\.avgWrQLen",
        ),
        "mem_num_rd_retry": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.numRdRetry",
            r"board\.memory\.mem_ctrl\d+\.numRdRetry",
        ),
        "mem_num_wr_retry": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.numWrRetry",
            r"board\.memory\.mem_ctrl\d+\.numWrRetry",
        ),

        # Memory bandwidth
        "mem_avg_read_bw_sys": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.avgRdBWSys",
            r"board\.memory\.mem_ctrl\d+\.avgRdBWSys",
        ),
        "mem_avg_write_bw_sys": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.avgWrBWSys",
            r"board\.memory\.mem_ctrl\d+\.avgWrBWSys",
        ),

        "dram_bw_read_total": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.bwRead::total",
            r"board\.memory\.mem_ctrl\d+\.dram\.bwRead::total",
        ),
        "dram_bw_write_total": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.bwWrite::total",
            r"board\.memory\.mem_ctrl\d+\.dram\.bwWrite::total",
        ),
        "dram_bw_total": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.bwTotal::total",
            r"board\.memory\.mem_ctrl\d+\.dram\.bwTotal::total",
        ),
        "dram_peak_bw": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.peakBW",
            r"board\.memory\.mem_ctrl\d+\.dram\.peakBW",
        ),
        "dram_avg_rd_bw": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.avgRdBW",
            r"board\.memory\.mem_ctrl\d+\.dram\.avgRdBW",
        ),
        "dram_avg_wr_bw": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.dram.avgWrBW",
            r"board\.memory\.mem_ctrl\d+\.dram\.avgWrBW",
        ),

        # Memory latency
        "dram_avg_q_lat": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.dram.avgQLat",
            r"board\.memory\.mem_ctrl\d+\.dram\.avgQLat",
        ),
        "dram_avg_bus_lat": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.dram.avgBusLat",
            r"board\.memory\.mem_ctrl\d+\.dram\.avgBusLat",
        ),
        "dram_avg_mem_acc_lat": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.dram.avgMemAccLat",
            r"board\.memory\.mem_ctrl\d+\.dram\.avgMemAccLat",
        ),

                # Per-requestor prefetcher memory traffic
        "l1d_prefetcher_read_bytes": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadBytes::cache_hierarchy.l1dcaches.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadBytes::cache_hierarchy\.l1dcaches\.prefetcher",
        ),
        "l1d_prefetcher_read_rate": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadRate::cache_hierarchy.l1dcaches.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadRate::cache_hierarchy\.l1dcaches\.prefetcher",
        ),
        "l1d_prefetcher_read_accesses": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadAccesses::cache_hierarchy.l1dcaches.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadAccesses::cache_hierarchy\.l1dcaches\.prefetcher",
        ),
        "l1d_prefetcher_read_avg_lat": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.requestorReadAvgLat::cache_hierarchy.l1dcaches.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadAvgLat::cache_hierarchy\.l1dcaches\.prefetcher",
        ),

        "l2_prefetcher_read_bytes": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadBytes::cache_hierarchy.l2cache.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadBytes::cache_hierarchy\.l2cache\.prefetcher",
        ),
        "l2_prefetcher_read_rate": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadRate::cache_hierarchy.l2cache.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadRate::cache_hierarchy\.l2cache\.prefetcher",
        ),
        "l2_prefetcher_read_accesses": get_stat_sum_any(
            text,
            "board.memory.mem_ctrl.requestorReadAccesses::cache_hierarchy.l2cache.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadAccesses::cache_hierarchy\.l2cache\.prefetcher",
        ),
        "l2_prefetcher_read_avg_lat": get_stat_mean_any(
            text,
            "board.memory.mem_ctrl.requestorReadAvgLat::cache_hierarchy.l2cache.prefetcher",
            r"board\.memory\.mem_ctrl\d+\.requestorReadAvgLat::cache_hierarchy\.l2cache\.prefetcher",
        ),
        
        # Core-side load latency distribution summary
        "load_to_use_samples": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::samples"),
        "load_to_use_mean": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::mean"),
        "load_to_use_stdev": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::stdev"),
        "load_to_use_overflows": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::overflows"),
        "load_to_use_min": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::min_value"),
        "load_to_use_max": get_stat(text, "board.processor.cores.core.lsq0.loadToUse::max_value"),

        # LSQ pressure
        "added_loads_and_stores": get_stat(text, "board.processor.cores.core.lsq0.addedLoadsAndStores"),
    }

    rows.append(row)


if not rows:
    raise RuntimeError("No Stage 3 rows extracted")

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {OUT} with {len(rows)} rows")