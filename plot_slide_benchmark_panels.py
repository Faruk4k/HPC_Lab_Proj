import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


OUTDIR = "plot_slide_benchmark_panels"
os.makedirs(OUTDIR, exist_ok=True)

FILES = {
    "Next-line": "nextline/nextline_results_vs_nopf.csv",
    "Stride": "stride/stride_results_vs_nopf.csv",
    "IMP": "imp/imp_all_stages_including_stage3_vs_nopf.csv",
    # Enable once AMPM is ready:
    "AMPM": "ampm/ampm_results_vs_nopf.csv",
}

BENCHMARKS = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]

PANEL_CASES = [
    ("l1d", "ddr4_1x"),
    ("l1d", "ddr4_2x"),
    ("l2", "ddr4_1x"),
    ("l2", "ddr4_2x"),
]

# Each output figure is one benchmark + one metric.
# The 4 panels are the 4 pf_level/memory combinations.
PLOT_METRICS = {
    # Main prefetch quality
    "pf_accuracy": "Prefetch accuracy",
    "pf_coverage": "Prefetch coverage",
    "pf_unused_ratio": "Unused prefetch ratio",
    "pf_late_ratio": "Late prefetch ratio",

}

METRIC_HIGH_IS_GOOD = {
    # Prefetch quality
    "pf_accuracy": True,
    "pf_coverage": True,

    # Lower overhead/waste is better
    "pf_unused_ratio": False,
    "pf_late_ratio": False,

    # Memory/cache pressure metrics: usually lower is better
    "prefetcher_read_rate": False,
    "dram_bw_utilization": False,
    "l1d_miss_rate": False,
    "l2_miss_rate": False,
    "mem_avg_rdq_len": False,
    "dram_avg_q_lat": False,
    "dram_avg_mem_acc_lat": False,
    "load_to_use_mean": False,
}

FAMILY_COLORS = {
    "Next-line": "C0",
    "Stride": "C1",
    "IMP": "C2",
    "AMPM": "C3",
}

REASON_MARKERS = {
    "default": "D",
    "top_speedup": "*",
    "top_coverage": "^",
    "top_accuracy": "s",
    "low_unused": "v",
    "low_late": "X",
}

REASON_LABELS = {
    "default": "Default",
    "top_speedup": "Top 3 speedup",
    "top_coverage": "Top 3 coverage",
    "top_accuracy": "Top 3 accuracy",
    "low_unused": "Lowest 3 unused ratio",
    "low_late": "Lowest 3 late ratio",
}

TOP_K = 3

# Keep these small. They only separate overlapping markers visually.
REASON_OFFSETS = {
    "default": (0.000, 0.000),
    "top_speedup": (0.004, 0.004),
    "top_coverage": (-0.004, 0.004),
    "top_accuracy": (0.004, -0.004),
    "low_unused": (-0.004, -0.004),
    "low_late": (0.000, 0.006),
}

LABEL_POINTS = False


def load_all_results():
    frames = []

    for family, path in FILES.items():
        if not os.path.exists(path):
            print(f"Skipping missing file: {path}")
            continue

        df = pd.read_csv(path)
        df["family"] = family

        if "speedup_vs_nopf" not in df.columns:
            print(f"Skipping {path}: missing speedup_vs_nopf")
            continue

        frames.append(df)

    if not frames:
        raise RuntimeError("No result CSV files found")

    df = pd.concat(frames, ignore_index=True)

    if "prefetcher" in df.columns:
        df = df[df["prefetcher"] != "none"].copy()

    numeric_cols = [
        "speedup_vs_nopf",
        "pf_accuracy",
        "pf_coverage",
        "pf_unused_ratio",
        "pf_late_ratio",
        "prefetcher_read_rate",
        "dram_bw_utilization",
        "l1d_miss_rate",
        "l2_miss_rate",
        "mem_avg_rdq_len",
        "dram_avg_q_lat",
        "dram_avg_mem_acc_lat",
        "load_to_use_mean",
        "pf_issued",
        "pf_useful",
        "pf_unused",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def config_label(row):
    family = str(row.get("family", ""))
    config = str(row.get("config", ""))
    stage = str(row.get("stage", ""))

    if family == "IMP" and stage not in ["", "nan", "None"]:
        return f"{family} {stage}:{config}"

    return f"{family} {config}"


def short_label(row):
    label = config_label(row)
    speedup = row.get("speedup_vs_nopf", pd.NA)

    if len(label) > 34:
        label = label[:31] + "..."

    if pd.notna(speedup):
        label = f"{label}\n{speedup:.3f}x"

    return "\n".join(textwrap.wrap(label, width=22))


def row_key_cols(df):
    if "run" in df.columns:
        return ["family", "run"]
    return ["family", "benchmark", "pf_level", "memory", "config"]


def add_reason(selected_frames, rows, reason):
    if rows.empty:
        return

    rows = rows.copy()
    rows["selection_reason"] = reason
    selected_frames.append(rows)


def top_k_per_family(case_df, metric, k=3, largest=True):
    if metric not in case_df.columns:
        return case_df.iloc[0:0].copy()

    valid = case_df[pd.notna(case_df[metric])].copy()

    if valid.empty:
        return valid

    return (
        valid.sort_values(metric, ascending=not largest)
        .groupby("family", as_index=False)
        .head(k)
    )


def select_interesting_reason_entries_for_case(case_df):
    """
    Important:
    This returns one row per selection reason.
    So if the same config is both top_speedup and top_coverage,
    it appears twice with different selection_reason values.
    That allows marker shape to represent the reason.
    """

    selected = []

    # Default per prefetcher family.
    if "config" in case_df.columns:
        defaults = case_df[case_df["config"].astype(str) == "default"]
        add_reason(selected, defaults, "default")

    # Top 3 by speedup per family.
    add_reason(
        selected,
        top_k_per_family(case_df, "speedup_vs_nopf", TOP_K, largest=True),
        "top_speedup",
    )

    # Top 3 by coverage per family.
    add_reason(
        selected,
        top_k_per_family(case_df, "pf_coverage", TOP_K, largest=True),
        "top_coverage",
    )

    # Top 3 by accuracy per family.
    add_reason(
        selected,
        top_k_per_family(case_df, "pf_accuracy", TOP_K, largest=True),
        "top_accuracy",
    )

    # Lowest 3 unused ratio per family.
    add_reason(
        selected,
        top_k_per_family(case_df, "pf_unused_ratio", TOP_K, largest=False),
        "low_unused",
    )

    # Lowest 3 late ratio per family.
    add_reason(
        selected,
        top_k_per_family(case_df, "pf_late_ratio", TOP_K, largest=False),
        "low_late",
    )

    if not selected:
        return case_df.iloc[0:0].copy()

    out = pd.concat(selected, ignore_index=True)

    # Remove exact duplicate reason entries.
    keys = row_key_cols(out) + ["selection_reason"]
    out = out.drop_duplicates(subset=keys, keep="first")

    return out


def build_selected_dataset(df):
    selected_cases = []

    for benchmark in BENCHMARKS:
        for pf_level, memory in PANEL_CASES:
            case_df = df[
                (df["benchmark"] == benchmark)
                & (df["pf_level"] == pf_level)
                & (df["memory"] == memory)
            ].copy()

            if case_df.empty:
                continue

            selected = select_interesting_reason_entries_for_case(case_df)
            selected_cases.append(selected)

    if not selected_cases:
        raise RuntimeError("No selected rows generated")

    selected_long = pd.concat(selected_cases, ignore_index=True)

    selected_long.to_csv(
        os.path.join(OUTDIR, "selected_reason_entries_for_plots.csv"),
        index=False,
    )

    # Also write a compact unique-row version with combined reasons.
    keys = row_key_cols(selected_long)

    reason_map = (
        selected_long.groupby(keys)["selection_reason"]
        .apply(lambda x: "|".join(sorted(set(x))))
        .reset_index()
    )

    selected_unique = (
        selected_long.drop(columns=["selection_reason"])
        .drop_duplicates(subset=keys, keep="first")
        .merge(reason_map, on=keys, how="left")
    )

    selected_unique.to_csv(
        os.path.join(OUTDIR, "selected_unique_rows_for_plots.csv"),
        index=False,
    )

    return selected_long


def reason_jitter(sub, metric, reason):
    """
    Slight visual jitter so multiple reason markers at the same point are visible.
    The actual CSV values are unchanged.
    """

    x_range = sub["speedup_vs_nopf"].max() - sub["speedup_vs_nopf"].min()
    y_range = sub[metric].max() - sub[metric].min()

    if pd.isna(x_range) or x_range == 0:
        x_range = 1.0

    if pd.isna(y_range) or y_range == 0:
        y_range = 1.0

    dx_frac, dy_frac = REASON_OFFSETS.get(reason, (0.0, 0.0))

    return dx_frac * x_range, dy_frac * y_range


def should_label(row, metric):
    if not LABEL_POINTS:
        return False

    reason = str(row.get("selection_reason", ""))

    # Always label defaults and top speedup points.
    if reason in ["default", "top_speedup"]:
        return True

    # For metric-specific plots, label the points selected because of that metric.
    metric_reason = {
        "pf_coverage": "top_coverage",
        "pf_accuracy": "top_accuracy",
        "pf_unused_ratio": "low_unused",
        "pf_late_ratio": "low_late",
    }

    return metric_reason.get(metric) == reason

def write_panel_ranked_csv(sub, benchmark, pf_level, memory, metric, metric_label):
    """
    Write one ranked CSV for one panel of one image.

    The CSV contains the exact selected rows used for that panel.
    Ranking is based on the y-axis metric:
      - high-is-good metrics: descending
      - low-is-good metrics: ascending

    Speedup is used as a secondary tie-breaker, descending.
    """

    if sub.empty or metric not in sub.columns:
        return

    ranked = sub[
        pd.notna(sub["speedup_vs_nopf"])
        & pd.notna(sub[metric])
        & pd.notna(sub["selection_reason"])
    ].copy()

    if ranked.empty:
        return

    high_is_good = METRIC_HIGH_IS_GOOD.get(metric, True)

    ranked = ranked.sort_values(
        by=[metric, "speedup_vs_nopf"],
        ascending=[not high_is_good, False],
    ).copy()

    ranked.insert(0, "rank", range(1, len(ranked) + 1))

    ranked["ranked_by"] = metric
    ranked["ranked_by_label"] = metric_label
    ranked["rank_direction"] = "high_is_good" if high_is_good else "low_is_good"

    # Nice compact column order.
    preferred_cols = [
        "rank",
        "benchmark",
        "pf_level",
        "memory",
        "family",
        "prefetcher",
        "stage",
        "config",
        "run",
        "selection_reason",
        "ranked_by",
        "ranked_by_label",
        "rank_direction",
        "speedup_vs_nopf",
        metric,

        # Common comparison metrics
        "pf_accuracy",
        "pf_coverage",
        "pf_unused_ratio",
        "pf_late_ratio",
        "prefetcher_read_rate",
        "dram_bw_utilization",
        "l1d_miss_rate",
        "l2_miss_rate",
        "mem_avg_rdq_len",
        "dram_avg_q_lat",
        "dram_avg_mem_acc_lat",
        "load_to_use_mean",

        # Useful raw counters
        "pf_issued",
        "pf_useful",
        "pf_unused",
        "pf_late",
        "prefetcher_read_bytes",
        "simSeconds",
        "nopf_simSeconds",
        "ipc",
    ]

    preferred_cols = [c for c in preferred_cols if c in ranked.columns]

    # Keep any remaining columns too, after the preferred ones.
    remaining_cols = [c for c in ranked.columns if c not in preferred_cols]
    ranked = ranked[preferred_cols + remaining_cols]

    filename = os.path.join(
        OUTDIR,
        f"{benchmark}_{metric}_{pf_level}_{memory}_ranked.csv",
    )

    ranked.to_csv(filename, index=False)
def metric_direction_text(metric):
    high_is_good = METRIC_HIGH_IS_GOOD.get(metric, True)

    if high_is_good:
        return "Y-axis ranking: higher is better"

    return "Y-axis ranking: lower is better"

def plot_benchmark_metric(selected_long, benchmark, metric, metric_label):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=False, sharey=False)
    axes = axes.flatten()

    any_data = False

    for ax, (pf_level, memory) in zip(axes, PANEL_CASES):
        sub = selected_long[
            (selected_long["benchmark"] == benchmark)
            & (selected_long["pf_level"] == pf_level)
            & (selected_long["memory"] == memory)
        ].copy()

        if metric not in sub.columns:
            ax.text(0.5, 0.5, f"Missing metric:\n{metric}", ha="center", va="center")
            ax.set_title(f"{pf_level.upper()}, {memory}")
            continue

        sub = sub[
            pd.notna(sub["speedup_vs_nopf"])
            & pd.notna(sub[metric])
            & pd.notna(sub["selection_reason"])
        ].copy()

        if sub.empty:
            ax.text(0.5, 0.5, "No selected data", ha="center", va="center")
            ax.set_title(f"{pf_level.upper()}, {memory}")
            continue

        
        write_panel_ranked_csv(
            sub,
            benchmark,
            pf_level,
            memory,
            metric,
            metric_label,
        )

        any_data = True

        for reason, reason_group in sub.groupby("selection_reason"):
            marker = REASON_MARKERS.get(reason, "o")
            dx, dy = reason_jitter(sub, metric, reason)

            for family, group in reason_group.groupby("family"):
                ax.scatter(
                    group["speedup_vs_nopf"] + dx,
                    group[metric] + dy,
                    s=80 if reason != "top_speedup" else 120,
                    alpha=0.78,
                    color=FAMILY_COLORS.get(family, "gray"),
                    marker=marker,
                    edgecolors="black",
                    linewidths=0.5,
                    zorder=4 if reason in ["default", "top_speedup"] else 3,
                )

        for _, row in sub.iterrows():
            if should_label(row, metric):
                dx, dy = reason_jitter(sub, metric, row["selection_reason"])

                ax.annotate(
                    short_label(row),
                    xy=(row["speedup_vs_nopf"] + dx, row[metric] + dy),
                    xytext=(6, 6),
                    textcoords="offset points",
                    fontsize=7,
                    ha="left",
                    va="bottom",
                    arrowprops=dict(arrowstyle="-", linewidth=0.4),
                )

        ax.axvline(1.0, linestyle="--", linewidth=1, color="black")
        ax.grid(alpha=0.25)
        ax.set_title(f"{pf_level.upper()}, {memory}")
        ax.set_xlabel("Speedup vs no-prefetch")
        ax.set_ylabel(metric_label)

    if not any_data:
        plt.close(fig)
        return False

    fig.suptitle(
        f"{benchmark}: {metric_label} vs speedup\n"
        f"{metric_direction_text(metric)}. "
        f"Selection is per prefetcher family: default, top 3 speedup, top 3 coverage, "
        f"top 3 accuracy, lowest 3 unused, lowest 3 late",
        fontsize=13,
    )

    family_handles = [
        Line2D(
            [0], [0],
            marker="o",
            color="w",
            label=family,
            markerfacecolor=color,
            markeredgecolor="black",
            markersize=8,
        )
        for family, color in FAMILY_COLORS.items()
        if family in selected_long["family"].unique()
    ]

    reason_handles = [
        Line2D(
            [0], [0],
            marker=marker,
            color="black",
            label=REASON_LABELS.get(reason, reason),
            markerfacecolor="white",
            markersize=8,
            linestyle="None",
        )
        for reason, marker in REASON_MARKERS.items()
    ]

    baseline_handle = Line2D(
        [0], [0],
        color="black",
        linestyle="--",
        label="No prefetch = 1.0x",
    )

    fig.legend(
        handles=family_handles + reason_handles + [baseline_handle],
        loc="lower center",
        ncol=5,
        fontsize=8,
        bbox_to_anchor=(0.5, -0.015),
    )

    plt.tight_layout(rect=[0, 0.08, 1, 0.92])

    filename = os.path.join(
        OUTDIR,
        f"{benchmark}_{metric}_selected_panels_reason_markers.png",
    )

    plt.savefig(filename, dpi=220)
    plt.close(fig)

    return True


def main():
    df = load_all_results()
    selected_long = build_selected_dataset(df)

    written = 0

    for benchmark in BENCHMARKS:
        for metric, metric_label in PLOT_METRICS.items():
            ok = plot_benchmark_metric(selected_long, benchmark, metric, metric_label)
            if ok:
                written += 1

    print(f"Wrote selected benchmark-panel plots to: {OUTDIR}")
    print(f"Wrote selected reason-entry CSV: {os.path.join(OUTDIR, 'selected_reason_entries_for_plots.csv')}")
    print(f"Wrote selected unique-row CSV: {os.path.join(OUTDIR, 'selected_unique_rows_for_plots.csv')}")
    print(f"Number of plot files: {written}")


if __name__ == "__main__":
    main()