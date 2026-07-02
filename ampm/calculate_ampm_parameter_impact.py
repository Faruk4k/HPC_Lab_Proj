import argparse
import csv
import math
import os
import re
from collections import defaultdict

from ampm_metrics import compute_speedup, extract_prefetcher_metrics

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.join(PROJECT_ROOT, "results_ampm_multisim_stage1")
BASELINE_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "baseline", "results_nopf_multisim"))

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
        baseline[benchmark, memory] = extract_prefetcher_metrics(text)["simSeconds"]

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

        if pf_level not in {"l1d", "l2"}:
            continue

        cache_name = "l1dcaches" if pf_level == "l1d" else "l2cache"
        text = open(stats_path, errors="ignore").read()
        metrics = extract_prefetcher_metrics(text, cache_name)
        baseline_sim_seconds = baseline_map.get((benchmark, memory), math.nan)
        speedup = compute_speedup(metrics["simSeconds"], baseline_sim_seconds)

        results.append({
            "benchmark": benchmark,
            "memory": memory,
            "pf_level": pf_level,
            "config": config,
            "parameter_family": parameter_family(config),
            "parameter_name": PARAMETER_FAMILIES.get(parameter_family(config), parameter_family(config)),
            "simSeconds": metrics["simSeconds"],
            "baseline_simSeconds": baseline_sim_seconds,
            "speedup": speedup,
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


def compute_parameter_impact(results):
    impact = defaultdict(lambda: {
        "speeds": [],
        "configs": set(),
        "rows": [],
    })

    for row in results:
        key = (row["benchmark"], row["pf_level"], row["memory"], row["parameter_name"])
        if not math.isnan(row["speedup"]):
            impact[key]["speeds"].append(row["speedup"])
            impact[key]["configs"].add(row["config"])
            impact[key]["rows"].append(row)

    summary = []
    for (benchmark, pf_level, memory, parameter_name), values in impact.items():
        speeds = values["speeds"]
        if not speeds:
            continue
        best = max(speeds)
        worst = min(speeds)
        summary.append({
            "benchmark": benchmark,
            "pf_level": pf_level,
            "memory": memory,
            "parameter_name": parameter_name,
            "count": len(speeds),
            "config_count": len(values["configs"]),
            "speedup_min": worst,
            "speedup_max": best,
            "speedup_delta": best - worst,
            "mean_speedup": sum(speeds) / len(speeds),
            "best_config": sorted(values["rows"], key=lambda r: r["speedup"], reverse=True)[0]["config"],
            "best_speedup": best,
            "worst_config": sorted(values["rows"], key=lambda r: r["speedup"])[0]["config"],
            "worst_speedup": worst,
        })

    return sorted(summary, key=lambda x: (x["benchmark"], x["pf_level"], x["memory"], -x["speedup_delta"]))


def write_summary_csv(summary, output_path):
    fieldnames = [
        "benchmark",
        "pf_level",
        "memory",
        "parameter_name",
        "count",
        "config_count",
        "speedup_min",
        "speedup_max",
        "speedup_delta",
        "mean_speedup",
        "best_config",
        "best_speedup",
        "worst_config",
        "worst_speedup",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def format_summary(summary):
    lines = []
    for row in summary:
        lines.append(
            f"{row['benchmark']:<8} | {row['pf_level']:>3} | {row['memory']:<8} | {row['parameter_name']:<24} | delta={row['speedup_delta']:.6f} "
            f"[{row['speedup_min']:.6f}, {row['speedup_max']:.6f}] | mean={row['mean_speedup']:.6f} "
            f"best={row['best_config']} ({row['best_speedup']:.6f}) "
            f"worst={row['worst_config']} ({row['worst_speedup']:.6f})"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calculate AMPM parameter impact for L1D and L2.")
    parser.add_argument("--results-dir", default=ROOT, help="AMPM results directory")
    parser.add_argument("--baseline-dir", default=BASELINE_ROOT, help="Baseline no-prefetch results directory")
    parser.add_argument("--output-csv", help="Save impact summary to a CSV file")
    args = parser.parse_args()

    baseline_map = load_baseline_results(args.baseline_dir)
    results = load_results(args.results_dir, baseline_map)
    summary = compute_parameter_impact(results)

    print(format_summary(summary))
    if args.output_csv:
        write_summary_csv(summary, args.output_csv)
        print(f"Saved impact summary to {args.output_csv}")


if __name__ == "__main__":
    main()
