import os

benchmarks = ["simple_triad", "matmult", "spmv", "merge", "quick", "bfs"]

stride_configs = [
    "deg1_dist1", "deg1_dist4", "deg1_dist8", "deg1_dist16", "deg1_dist32",
    "deg4_dist1", "deg4_dist4", "deg4_dist8", "deg4_dist16", "deg4_dist32",
    "deg8_dist1", "deg8_dist4", "deg8_dist8", "deg8_dist16", "deg8_dist32",
    "deg16_dist1", "deg16_dist4", "deg16_dist8", "deg16_dist16", "deg16_dist32",
    "deg32_dist1", "deg32_dist4", "deg32_dist8", "deg32_dist16", "deg32_dist32",
]

levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]

root = r"HPC_Lab_Proj\stride\results_stride_multisim"

missing = []

for bench in benchmarks:
    for cfg in stride_configs:
        for level in levels:
            for mem in memories:
                sim_id = f"{bench}_stride_{cfg}_{level}_{mem}"
                stats_path = os.path.join(root, sim_id, "stats.txt")
                if not os.path.exists(stats_path):
                    missing.append((bench, cfg, level, mem, sim_id))

print(f"Expected: {len(benchmarks) * len(stride_configs) * len(levels) * len(memories)}")
print(f"Missing : {len(missing)}")

with open("missing_stride_runs.txt", "w") as f:
    for bench, cfg, level, mem, sim_id in missing:
        f.write(f"{bench} {cfg} {level} {mem} {sim_id}\n")

print("Wrote missing_stride_runs.txt")