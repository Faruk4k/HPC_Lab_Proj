from pathlib import Path
import math

import pandas as pd
import matplotlib.pyplot as plt


OUTDIR = Path("plots_prefetcher_metric_dashboard")
OUTDIR.mkdir(exist_ok=True)

NOPF = Path("baseline/nopf_results.csv")

FAMILY_FILES = {
    "Next-line": [
        Path("nextline/nextline_results_vs_nopf.csv"),
    ],
    "Stride": [
        Path("stride/stride_results_vs_nopf.csv"),
    ],
    "IMP": [
        Path("imp/imp_all_stages_including_stage3_vs_nopf.csv"),
    ],
    #"AMPM": [
        #Path("ampm/ampm_results_vs_nopf.csv"),
       # Path("ampm/ampm_stage1_results_vs_nopf.csv"),
        #Path("ampm/ampm_stage1_with_comparison.csv"),
    #],
}

BENCHMARKS = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]

CONDITIONS = [
    ("l1d", "ddr4_1x", "L1D + DDR4 1x"),
    ("l1d", "ddr4_2x", "L1D + DDR4 2x"),
    ("l2", "ddr4_1x", "L2 + DDR4 1x"),
    ("l2", "ddr4_2x", "L2 + DDR4 2x"),
]


def read_existing(files, family):
    dfs = []

    for path in files:
        if path.exists():
            print(f"Reading {family}: {path}")
            df = pd.read_csv(path)
            df["family"] = family
            df["source_file"] = str(path)
            dfs.append(df)

    if not dfs:
        print(f"WARNING: no CSV found for {family}, skipping.")
        return pd.DataFrame()

    out = pd.concat(dfs, ignore_index=True)
    out = out.drop_duplicates()
    return out


def safe_div(num, den):
    try:
        if pd.isna(num) or pd.isna(den) or den == 0:
            return math.nan
        return num / den
    except Exception:
        return math.nan


def ensure_col(df, col, default=math.nan):
    if col not in df.columns:
        df[col] = default


def add_speedup_vs_nopf(df, nopf):
    base = nopf[["benchmark", "memory", "simSeconds"]].rename(
        columns={"simSeconds": "nopf_simSeconds"}
    )

    df = df.drop(columns=["nopf_simSeconds"], errors="ignore")
    df = df.merge(base, on=["benchmark", "memory"], how="left")

    # Always recompute to avoid accidentally using old speedup definitions.
    df["speedup_vs_nopf"] = df["nopf_simSeconds"] / df["simSeconds"]

    return df


def effective_by_level(row, l1d_col, l2_col):
    pf_level = row.get("pf_level", "")

    if pf_level == "l1d":
        return row.get(l1d_col, math.nan)

    if pf_level == "l2":
        return row.get(l2_col, math.nan)

    return math.nan


def add_baseline_metrics(nopf):
    nopf = nopf.copy()

    for col in [
        "l1d_demand_misses",
        "l1d_demand_accesses",
        "l2_demand_misses",
        "l2_demand_accesses",
        "simSeconds",
    ]:
        ensure_col(nopf, col)

    nopf["l1d_miss_rate"] = nopf.apply(
        lambda r: safe_div(r["l1d_demand_misses"], r["l1d_demand_accesses"]),
        axis=1,
    )

    nopf["l2_miss_rate"] = nopf.apply(
        lambda r: safe_div(r["l2_demand_misses"], r["l2_demand_accesses"]),
        axis=1,
    )

    return nopf


def add_prefetch_and_memory_metrics(df):
    df = df.copy()

    # Basic demand counters.
    for col in [
        "l1d_demand_misses",
        "l1d_demand_accesses",
        "l2_demand_misses",
        "l2_demand_accesses",
    ]:
        ensure_col(df, col)

    df["l1d_miss_rate"] = df.apply(
        lambda r: safe_div(r["l1d_demand_misses"], r["l1d_demand_accesses"]),
        axis=1,
    )

    df["l2_miss_rate"] = df.apply(
        lambda r: safe_div(r["l2_demand_misses"], r["l2_demand_accesses"]),
        axis=1,
    )

    # Basic prefetch counters.
    for col in [
        "l1d_pf_issued",
        "l1d_pf_useful",
        "l1d_pf_unused",
        "l2_pf_issued",
        "l2_pf_useful",
        "l2_pf_unused",
    ]:
        ensure_col(df, col)

    df["pf_issued"] = df.apply(
        lambda r: effective_by_level(r, "l1d_pf_issued", "l2_pf_issued"),
        axis=1,
    )

    df["pf_useful"] = df.apply(
        lambda r: effective_by_level(r, "l1d_pf_useful", "l2_pf_useful"),
        axis=1,
    )

    df["pf_unused"] = df.apply(
        lambda r: effective_by_level(r, "l1d_pf_unused", "l2_pf_unused"),
        axis=1,
    )

    df["pf_accuracy_calc"] = df.apply(
        lambda r: safe_div(r["pf_useful"], r["pf_issued"]),
        axis=1,
    )

    def coverage(row):
        if row.get("pf_level") == "l1d":
            misses = row.get("l1d_demand_misses", math.nan)
        elif row.get("pf_level") == "l2":
            misses = row.get("l2_demand_misses", math.nan)
        else:
            misses = math.nan

        useful = row.get("pf_useful", math.nan)
        return safe_div(useful, useful + misses)

    df["pf_coverage_calc"] = df.apply(coverage, axis=1)

    df["pf_unused_ratio"] = df.apply(
        lambda r: safe_div(r["pf_unused"], r["pf_issued"]),
        axis=1,
    )

    def prefetches_per_access(row):
        if row.get("pf_level") == "l1d":
            accesses = row.get("l1d_demand_accesses", math.nan)
        elif row.get("pf_level") == "l2":
            accesses = row.get("l2_demand_accesses", math.nan)
        else:
            accesses = math.nan

        return safe_div(row.get("pf_issued", math.nan), accesses)

    df["pf_per_demand_access"] = df.apply(prefetches_per_access, axis=1)

    # Extra prefetcher counters from gem5 stats.
    extra_pf_cols = [
        "pf_late",
        "pf_hit_in_cache",
        "pf_hit_in_mshr",
        "pf_hit_in_wb",
        "pf_removed_full",
        "pf_removed_demand",
        "pf_buffer_hit",
        "pf_identified",
    ]

    for suffix in [
        "late",
        "hit_in_cache",
        "hit_in_mshr",
        "hit_in_wb",
        "removed_full",
        "removed_demand",
        "buffer_hit",
        "identified",
    ]:
        ensure_col(df, f"l1d_pf_{suffix}")
        ensure_col(df, f"l2_pf_{suffix}")

    for suffix in [
        "late",
        "hit_in_cache",
        "hit_in_mshr",
        "hit_in_wb",
        "removed_full",
        "removed_demand",
        "buffer_hit",
        "identified",
    ]:
        df[f"pf_{suffix}"] = df.apply(
            lambda r, s=suffix: effective_by_level(
                r,
                f"l1d_pf_{s}",
                f"l2_pf_{s}",
            ),
            axis=1,
        )

    df["pf_late_ratio"] = df.apply(
        lambda r: safe_div(r["pf_late"], r["pf_issued"]),
        axis=1,
    )

    df["pf_removed_full_ratio"] = df.apply(
        lambda r: safe_div(r["pf_removed_full"], r["pf_identified"]),
        axis=1,
    )

    df["pf_removed_demand_ratio"] = df.apply(
        lambda r: safe_div(r["pf_removed_demand"], r["pf_identified"]),
        axis=1,
    )

    df["pf_buffer_hit_ratio"] = df.apply(
        lambda r: safe_div(r["pf_buffer_hit"], r["pf_identified"]),
        axis=1,
    )

    # MSHR pressure / cache blocking.
    for col in [
        "l1d_blocked_cycles_no_mshrs",
        "l1d_blocked_causes_no_mshrs",
        "l1d_avg_blocked_no_mshrs",
        "l2_blocked_cycles_no_mshrs",
        "l2_blocked_causes_no_mshrs",
        "l2_avg_blocked_no_mshrs",
    ]:
        ensure_col(df, col)

    df["blocked_cycles_no_mshrs"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_blocked_cycles_no_mshrs",
            "l2_blocked_cycles_no_mshrs",
        ),
        axis=1,
    )

    df["blocked_causes_no_mshrs"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_blocked_causes_no_mshrs",
            "l2_blocked_causes_no_mshrs",
        ),
        axis=1,
    )

    df["avg_blocked_no_mshrs"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_avg_blocked_no_mshrs",
            "l2_avg_blocked_no_mshrs",
        ),
        axis=1,
    )

    # Memory controller / DRAM pressure.
    for col in [
        "mem_avg_rdq_len",
        "mem_avg_wrq_len",
        "mem_num_rd_retry",
        "mem_num_wr_retry",
        "mem_avg_read_bw_sys",
        "mem_avg_write_bw_sys",
        "dram_bw_read_total",
        "dram_bw_write_total",
        "dram_bw_total",
        "dram_peak_bw",
        "dram_avg_q_lat",
        "dram_avg_mem_acc_lat",
        "l1d_prefetcher_read_bytes",
        "l2_prefetcher_read_bytes",
        "l1d_prefetcher_read_rate",
        "l2_prefetcher_read_rate",
    ]:
        ensure_col(df, col)

    df["prefetcher_read_bytes"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_prefetcher_read_bytes",
            "l2_prefetcher_read_bytes",
        ),
        axis=1,
    )

    df["prefetcher_read_rate"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_prefetcher_read_rate",
            "l2_prefetcher_read_rate",
        ),
        axis=1,
    )

    # dram_peak_bw is in MiB/s in gem5 output. dram_bw_total is Byte/s.
    df["dram_bw_utilization"] = df.apply(
        lambda r: safe_div(r["dram_bw_total"], r["dram_peak_bw"] * 1024 * 1024),
        axis=1,
    )

    # Prefer gem5's direct accuracy/coverage if your extractor has them.
    # Otherwise use calculated accuracy/coverage.
    ensure_col(df, "l1d_prefetcher_accuracy")
    ensure_col(df, "l2_prefetcher_accuracy")
    ensure_col(df, "l1d_prefetcher_coverage")
    ensure_col(df, "l2_prefetcher_coverage")

    df["pf_accuracy_direct"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_prefetcher_accuracy",
            "l2_prefetcher_accuracy",
        ),
        axis=1,
    )

    df["pf_coverage_direct"] = df.apply(
        lambda r: effective_by_level(
            r,
            "l1d_prefetcher_coverage",
            "l2_prefetcher_coverage",
        ),
        axis=1,
    )

    df["pf_accuracy"] = df["pf_accuracy_direct"].combine_first(df["pf_accuracy_calc"])
    df["pf_coverage"] = df["pf_coverage_direct"].combine_first(df["pf_coverage_calc"])

    return df


def best_per_case(df):
    return (
        df.sort_values("speedup_vs_nopf", ascending=False)
        .groupby(["benchmark", "pf_level", "memory", "family"], as_index=False)
        .first()
    )


def default_per_case(df):
    if "config" not in df.columns:
        return pd.DataFrame()

    d = df[df["config"] == "default"].copy()

    if d.empty:
        print("WARNING: no default rows found in combined data.")
        return pd.DataFrame()

    return (
        d.sort_values("speedup_vs_nopf", ascending=False)
        .groupby(["benchmark", "pf_level", "memory", "family"], as_index=False)
        .first()
    )


def color_for_family(family):
    if family == "No prefetch":
        return "gray"
    if family == "Next-line":
        return "C0"
    if family == "Stride":
        return "C1"
    if family == "IMP":
        return "C2"
    if family == "AMPM":
        return "C3"
    return "C4"


def baseline_row(nopf, benchmark, pf_level, memory):
    row = nopf[
        (nopf["benchmark"] == benchmark)
        & (nopf["memory"] == memory)
    ]

    if row.empty:
        raise RuntimeError(f"No baseline row for {benchmark}, {memory}")

    row = row.iloc[0]

    return {
        "benchmark": benchmark,
        "pf_level": pf_level,
        "memory": memory,
        "family": "No prefetch",
        "config": "none",
        "speedup_vs_nopf": 1.0,
        "simSeconds": row.get("simSeconds", math.nan),
        "l1d_miss_rate": row.get("l1d_miss_rate", math.nan),
        "l2_miss_rate": row.get("l2_miss_rate", math.nan),
        "pf_issued": 0.0,
        "pf_useful": 0.0,
        "pf_unused": 0.0,
        "pf_accuracy": math.nan,
        "pf_coverage": 0.0,
        "pf_unused_ratio": math.nan,
        "pf_per_demand_access": 0.0,
        "pf_late": 0.0,
        "pf_late_ratio": math.nan,
        "pf_removed_full": 0.0,
        "pf_removed_full_ratio": math.nan,
        "pf_removed_demand": 0.0,
        "pf_removed_demand_ratio": math.nan,
        "pf_buffer_hit": 0.0,
        "pf_buffer_hit_ratio": math.nan,
        "blocked_cycles_no_mshrs": math.nan,
        "blocked_causes_no_mshrs": math.nan,
        "avg_blocked_no_mshrs": math.nan,
        "mem_avg_rdq_len": math.nan,
        "mem_avg_wrq_len": math.nan,
        "mem_num_rd_retry": math.nan,
        "mem_num_wr_retry": math.nan,
        "dram_bw_total": math.nan,
        "dram_bw_utilization": math.nan,
        "dram_avg_q_lat": math.nan,
        "dram_avg_mem_acc_lat": math.nan,
        "prefetcher_read_rate": 0.0,
        "prefetcher_read_bytes": 0.0,
    }


def fmt_value(value):
    if pd.isna(value):
        return ""

    value = float(value)

    if abs(value) >= 1e9:
        return f"{value / 1e9:.1f}G"
    if abs(value) >= 1e6:
        return f"{value / 1e6:.1f}M"
    if abs(value) >= 1e3:
        return f"{value / 1e3:.1f}K"
    if abs(value) < 0.01 and value != 0:
        return f"{value:.2e}"

    return f"{value:.2f}"


def make_grouped_metric_plot(plot_df, defaults, metric, ylabel, suffix):
    default_lookup = {}

    if not defaults.empty and metric in defaults.columns:
        for _, r in defaults.iterrows():
            value = r.get(metric, math.nan)
            if pd.notna(value):
                key = (r["benchmark"], r["pf_level"], r["memory"], r["family"])
                default_lookup[key] = float(value)

    family_order = ["No prefetch", "Next-line", "Stride", "IMP", "AMPM"]
    present_families = [f for f in family_order if f in set(plot_df["family"])]

    for pf_level, memory, condition_label in CONDITIONS:
        cond_df = plot_df[
            (plot_df["pf_level"] == pf_level)
            & (plot_df["memory"] == memory)
        ].copy()

        if cond_df.empty:
            continue

        if metric not in cond_df.columns:
            print(f"Skipping {metric} for {condition_label}: missing column")
            continue

        if cond_df[metric].dropna().empty:
            print(f"Skipping {metric} for {condition_label}: all NaN")
            continue

        fig, ax = plt.subplots(figsize=(22, 8))

        width = 0.15
        x = list(range(len(BENCHMARKS)))

        center = (len(present_families) - 1) / 2
        offsets = {
            family: (i - center) * width
            for i, family in enumerate(present_families)
        }

        for family in present_families:
            values = []

            for benchmark in BENCHMARKS:
                row = cond_df[
                    (cond_df["benchmark"] == benchmark)
                    & (cond_df["family"] == family)
                ]

                if row.empty:
                    values.append(math.nan)
                else:
                    values.append(float(row[metric].iloc[0]))

            positions = [i + offsets[family] for i in x]

            bars = ax.bar(
                positions,
                values,
                width=width,
                label=family,
                color=color_for_family(family),
            )

            for bar, value, benchmark in zip(bars, values, BENCHMARKS):
                if pd.notna(value):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        value,
                        fmt_value(value),
                        ha="center",
                        va="bottom",
                        fontsize=7,
                        rotation=0,
                    )

                if family != "No prefetch":
                    key = (benchmark, pf_level, memory, family)

                    if key in default_lookup:
                        default_value = default_lookup[key]
                        ax.hlines(
                            y=default_value,
                            xmin=bar.get_x(),
                            xmax=bar.get_x() + bar.get_width(),
                            color="red",
                            linewidth=2.0,
                        )

        if metric == "speedup_vs_nopf":
            ax.axhline(1.0, linestyle="--", linewidth=1)

        ax.set_xticks(x)
        ax.set_xticklabels(BENCHMARKS, rotation=20)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} — {condition_label}")

        handles, labels = ax.get_legend_handles_labels()
        if default_lookup:
            handles.append(plt.Line2D([0], [0], color="red", linewidth=2.0))
            labels.append("Default config")
        ax.legend(handles, labels, loc="best")

        plt.tight_layout()

        out = OUTDIR / f"group_{pf_level}_{memory}_{suffix}.png"
        plt.savefig(out, dpi=200)
        plt.close()

        print(f"Wrote {out}")


def make_metric_csv_summary(plot_df):
    summary_cols = [
        "benchmark",
        "pf_level",
        "memory",
        "family",
        "config",
        "speedup_vs_nopf",
        "l1d_miss_rate",
        "l2_miss_rate",
        "pf_issued",
        "pf_useful",
        "pf_unused",
        "pf_accuracy",
        "pf_coverage",
        "pf_unused_ratio",
        "pf_late",
        "pf_late_ratio",
        "pf_removed_full",
        "pf_removed_full_ratio",
        "pf_buffer_hit",
        "pf_buffer_hit_ratio",
        "blocked_cycles_no_mshrs",
        "blocked_causes_no_mshrs",
        "avg_blocked_no_mshrs",
        "mem_avg_rdq_len",
        "mem_avg_wrq_len",
        "dram_bw_total",
        "dram_bw_utilization",
        "dram_avg_q_lat",
        "dram_avg_mem_acc_lat",
        "prefetcher_read_rate",
        "prefetcher_read_bytes",
    ]

    existing = [c for c in summary_cols if c in plot_df.columns]
    plot_df[existing].to_csv(OUTDIR / "prefetcher_metric_summary_for_report.csv", index=False)


def main():
    if not NOPF.exists():
        raise FileNotFoundError(f"Missing baseline file: {NOPF}")

    nopf = pd.read_csv(NOPF)
    nopf = add_baseline_metrics(nopf)

    family_dfs = []

    for family, files in FAMILY_FILES.items():
        df = read_existing(files, family)

        if df.empty:
            continue

        df = add_speedup_vs_nopf(df, nopf)
        df = add_prefetch_and_memory_metrics(df)

        if "prefetcher" in df.columns:
            df = df[df["prefetcher"] != "none"].copy()

        family_dfs.append(df)

    if not family_dfs:
        raise RuntimeError("No prefetcher CSV files found.")

    all_results = pd.concat(family_dfs, ignore_index=True)
    all_results = all_results.drop_duplicates()

    best = best_per_case(all_results)
    defaults = default_per_case(all_results)

    best.to_csv(OUTDIR / "best_prefetcher_metric_rows.csv", index=False)
    defaults.to_csv(OUTDIR / "default_prefetcher_metric_rows.csv", index=False)

    plot_rows = []

    for benchmark in BENCHMARKS:
        for pf_level, memory, _ in CONDITIONS:
            plot_rows.append(baseline_row(nopf, benchmark, pf_level, memory))

            sub = best[
                (best["benchmark"] == benchmark)
                & (best["pf_level"] == pf_level)
                & (best["memory"] == memory)
            ]

            for _, row in sub.iterrows():
                plot_rows.append(row.to_dict())

    plot_df = pd.DataFrame(plot_rows)

    plot_df.to_csv(OUTDIR / "prefetcher_metric_plot_data.csv", index=False)
    make_metric_csv_summary(plot_df)

    metrics_to_plot = [
        ("speedup_vs_nopf", "Speedup vs no-prefetch baseline", "speedup_vs_nopf"),

        ("l1d_miss_rate", "L1D demand miss rate", "l1d_miss_rate"),
        ("l2_miss_rate", "L2 demand miss rate", "l2_miss_rate"),

        ("pf_issued", "Prefetches issued", "pf_issued"),
        ("pf_useful", "Useful prefetches", "pf_useful"),
        ("pf_unused", "Unused prefetches", "pf_unused"),

        ("pf_accuracy", "Prefetch accuracy", "pf_accuracy"),
        ("pf_coverage", "Prefetch coverage", "pf_coverage"),
        ("pf_unused_ratio", "Unused prefetch ratio", "pf_unused_ratio"),

        ("pf_late", "Late prefetches", "pf_late"),
        ("pf_late_ratio", "Late prefetch ratio", "pf_late_ratio"),

        ("pf_removed_full", "Prefetches dropped: queue full", "pf_removed_full"),
        ("pf_removed_full_ratio", "Queue-full drop ratio", "pf_removed_full_ratio"),
        ("pf_removed_demand", "Prefetches removed by demand", "pf_removed_demand"),
        ("pf_removed_demand_ratio", "Demand-removal ratio", "pf_removed_demand_ratio"),
        ("pf_buffer_hit", "Redundant prefetch queue hits", "pf_buffer_hit"),
        ("pf_buffer_hit_ratio", "Prefetch queue-hit ratio", "pf_buffer_hit_ratio"),

        ("blocked_cycles_no_mshrs", "Cache blocked cycles: no MSHRs", "blocked_cycles_no_mshrs"),
        ("blocked_causes_no_mshrs", "Cache blocked events: no MSHRs", "blocked_causes_no_mshrs"),
        ("avg_blocked_no_mshrs", "Average blocked cycles per no-MSHR event", "avg_blocked_no_mshrs"),

        ("mem_avg_rdq_len", "Average memory read queue length", "mem_avg_rdq_len"),
        ("mem_avg_wrq_len", "Average memory write queue length", "mem_avg_wrq_len"),

        ("dram_bw_total", "Total DRAM bandwidth", "dram_bw_total"),
        ("dram_bw_utilization", "DRAM bandwidth utilization", "dram_bw_utilization"),
        ("dram_avg_q_lat", "Average DRAM queue latency", "dram_avg_q_lat"),
        ("dram_avg_mem_acc_lat", "Average DRAM memory access latency", "dram_avg_mem_acc_lat"),

        ("prefetcher_read_rate", "Prefetcher memory read bandwidth", "prefetcher_read_rate"),
        ("prefetcher_read_bytes", "Prefetcher memory read bytes", "prefetcher_read_bytes"),
    ]

    for metric, ylabel, suffix in metrics_to_plot:
        if metric not in plot_df.columns:
            print(f"Skipping {metric}: missing column")
            continue

        if plot_df[metric].dropna().empty:
            print(f"Skipping {metric}: all NaN")
            continue

        make_grouped_metric_plot(plot_df, defaults, metric, ylabel, suffix)

    print()
    print(f"Done. Outputs are in: {OUTDIR}")
    print("Main CSVs:")
    print(OUTDIR / "best_prefetcher_metric_rows.csv")
    print(OUTDIR / "default_prefetcher_metric_rows.csv")
    print(OUTDIR / "prefetcher_metric_plot_data.csv")
    print(OUTDIR / "prefetcher_metric_summary_for_report.csv")


if __name__ == "__main__":
    main()