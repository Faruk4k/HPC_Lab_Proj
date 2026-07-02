import csv
import math
import os
import re
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.join(PROJECT_ROOT, "results_ampm_multisim_stage1")
BASELINE_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "baseline", "results_nopf_multisim"))
OUT = os.path.join(PROJECT_ROOT, "ampm_top2_per_parameter.csv")

RUN_RE = re.compile(
    r"^(?P<benchmark>[^_]+)_ampm_(?P<config>[^_]+)_(?P<pf_level>[^_]+)_(?P<memory>ddr4_[12]x)$"
)
BASELINE_RE = re.compile(r"^(?P<benchmark>[^_]+)_nopf_(?P<memory>ddr4_[12]x)$")

PARAMETER_FAMILIES = {
    "amt": "access_map_table_entries",
    "assoc": "access_map_table_assoc",
    "hz": "hot_zone_size",
    "ls": "limit_stride",
    "sd": "start_degree",
    "epoch": "epoch_cycles",
    "default": "default",
}

from ampm_metrics import compute_speedup, extract_prefetcher_metrics


def parameter_family(config_name):
    if config_name == "default":
        return "default"
    for prefix in ("amt", "assoc", "hz", "ls", "sd", "epoch"):
        if config_name.startswith(prefix):
            return prefix
    return "other"


def parse_run_name(run_name):
    match = RUN_RE.match(run_name)
    if not match:
        return None
    return match.groupdict()


def parse_baseline_run_name(run_name):
    match = BASELINE_RE.match(run_name)
    if not match:
        return None
    return match.groupdict()


def load_baseline_results(root_dir):
    baseline = {}

    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Baseline results directory not found: {root_dir}")

    for run_name in sorted(os.listdir(root_dir)):
        run_dir = os.path.join(root_dir, run_name)
        stats_path = os.path.join(run_dir, "stats.txt")

        if not os.path.isdir(run_dir) or not os.path.exists(stats_path):
            continue

        parsed = parse_baseline_run_name(run_name)
        if parsed is None:
            continue

        benchmark = parsed["benchmark"]
        memory = parsed["memory"]
        text = open(stats_path, errors="ignore").read()
        baseline[benchmark, memory] = {
            "baseline_simSeconds": extract_prefetcher_metrics(text)["simSeconds"],
            "baseline_run_name": run_name,
        }

    return baseline


def load_results(root_dir, baseline_map):
    results = []

    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Results directory not found: {root_dir}")

    for run_name in sorted(os.listdir(root_dir)):
        run_dir = os.path.join(root_dir, run_name)
        stats_path = os.path.join(run_dir, "stats.txt")

        if not os.path.isdir(run_dir) or not os.path.exists(stats_path):
            continue

        parsed = parse_run_name(run_name)
        if parsed is None:
            continue

        benchmark = parsed["benchmark"]
        config = parsed["config"]
        pf_level = parsed["pf_level"]
        memory = parsed["memory"]

        text = open(stats_path, errors="ignore").read()


        if pf_level == "l1d":
            cache_name = "l1dcaches"
        elif pf_level == "l2":
            cache_name = "l2cache"
        metrics = extract_prefetcher_metrics(text, cache_name)
        baseline_info = baseline_map.get((benchmark, memory), {})
        baseline_sim_seconds = baseline_info.get("baseline_simSeconds", math.nan)

        results.append({
            "benchmark": benchmark,
            "memory": memory,
            "pf_level": pf_level,
            "config": config,
            "parameter_family": parameter_family(config),
            "parameter_name": PARAMETER_FAMILIES.get(parameter_family(config), parameter_family(config)),
            "simSeconds": metrics["simSeconds"],
            "baseline_simSeconds": baseline_sim_seconds,
            "speedup": compute_speedup(metrics["simSeconds"], baseline_sim_seconds),
            "pfIssued": metrics["pfIssued"],
            "pfUseful": metrics["pfUseful"],
            "pfUnused": metrics["pfUnused"],
            "accuracy": metrics["accuracy"],
            "coverage": metrics["coverage"],
            "pfLate": metrics["pfLate"],
            "pfTimely": metrics["pfTimely"],
            "run_name": run_name,
        })

    return results


def select_top_two(results):
    """Select the top two parameter settings for each case.

    A case is defined by benchmark, cache level, DDR4 memory, and the tuned parameter.
    """
    groups = defaultdict(list)

    for row in results:
        key = (
            row["benchmark"],
            row["memory"],
            row["pf_level"],
            row["parameter_name"],
        )
        groups[key].append(row)

    selected = []
    for key, rows in sorted(groups.items()):
        rows = [r for r in rows if not math.isnan(r["simSeconds"])]
        rows.sort(key=lambda r: r["simSeconds"])
        parameter_name = key[3]
        max_rank = 3 if parameter_name in ("access_map_table_entries", "hot_zone_size") else 2
        for rank, row in enumerate(rows[:max_rank], start=1):
            selected.append({
                "benchmark": row["benchmark"],
                "memory": row["memory"],
                "pf_level": row["pf_level"],
                "parameter_family": row["parameter_family"],
                "parameter_name": row["parameter_name"],
                "rank": rank,
                "config": row["config"],
                "simSeconds": row["simSeconds"],
                "baseline_simSeconds": row["baseline_simSeconds"],
                "speedup": row["speedup"],
                "pfIssued": row["pfIssued"],
                "pfUseful": row["pfUseful"],
                "pfUnused": row["pfUnused"],
                "accuracy": row["accuracy"],
                "coverage": row["coverage"],
                "pfLate": row["pfLate"],
                "pfTimely": row["pfTimely"],
                "run_name": row["run_name"],
            })

    return selected


def write_csv(rows, output_path):
    if not rows:
        print("No results found.")
        return

    fieldnames = [
        "benchmark",
        "memory",
        "pf_level",
        "parameter_family",
        "parameter_name",
        "rank",
        "config",
        "simSeconds",
        "baseline_simSeconds",
        "speedup",
        "pfIssued",
        "pfUseful",
        "pfUnused",
        "accuracy",
        "coverage",
        "pfLate",
        "pfTimely",
        "run_name",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote top-two results to {output_path}")


def main():
    baseline_map = load_baseline_results(BASELINE_ROOT)
    results = load_results(ROOT, baseline_map)
    selected = select_top_two(results)
    write_csv(selected, OUT)

    for row in selected:
        print(
            f"{row['benchmark']} | {row['memory']} | {row['pf_level']} | {row['parameter_family']} | rank={row['rank']} |"
            f" {row['config']} | simSeconds={row['simSeconds']} | speedup={row['speedup']:.4f} |"
            f" accuracy={row['accuracy']:.4f} | coverage={row['coverage']:.4f} | late={row['pfLate']} | timely={row['pfTimely']}"
        )


if __name__ == "__main__":
    main()
