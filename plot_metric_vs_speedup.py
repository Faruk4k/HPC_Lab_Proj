import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = "plots_metric_vs_speedup_scatter"
os.makedirs(OUTDIR, exist_ok=True)

TOP_N = 5

FILES = {
    "Next-line": "nextline/nextline_results_vs_nopf.csv",
    "Stride": "stride/stride_results_vs_nopf.csv",
    "IMP": "imp/imp_all_stages_including_stage3_vs_nopf.csv",
    # Enable when ready:
    # "AMPM": "ampm/ampm_results_vs_nopf.csv",
}

benchmarks = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]
pf_levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]

family_colors = {
    "Next-line": "C0",
    "Stride": "C1",
    "IMP": "C2",
    "AMPM": "C3",
}

METRICS = {
    "pf_accuracy": "Prefetch accuracy",
    "pf_coverage": "Prefetch coverage",
    "pf_unused_ratio": "Unused prefetch ratio",
    "pf_late_ratio": "Late prefetch ratio",
    "pf_issued": "Prefetches issued",
    "pf_useful": "Useful prefetches",
    "pf_unused": "Unused prefetches",
    "l1d_miss_rate": "L1D miss rate",
    "l2_miss_rate": "L2 miss rate",
    "dram_bw_utilization": "DRAM bandwidth utilization",
    "dram_bw_total": "DRAM total bandwidth",
    "dram_avg_q_lat": "DRAM queue latency",
    "dram_avg_mem_acc_lat": "DRAM memory access latency",
    "mem_avg_rdq_len": "Memory read queue length",
    "mem_avg_wrq_len": "Memory write queue length",
    "prefetcher_read_rate": "Prefetcher read rate",
    "prefetcher_read_bytes": "Prefetcher read bytes",
    "pf_removed_full": "Prefetches dropped: queue full",
    "pf_removed_demand": "Prefetches removed by demand",
    "pf_buffer_hit": "Prefetch buffer hits",
    "l1d_blocked_cycles_no_mshrs": "L1D blocked cycles: no MSHRs",
    "l2_blocked_cycles_no_mshrs": "L2 blocked cycles: no MSHRs",
    "load_to_use_mean": "Mean load-to-use latency",
}


def load_all():
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
        raise RuntimeError("No valid input CSV files found")

    out = pd.concat(frames, ignore_index=True)

    if "prefetcher" in out.columns:
        out = out[out["prefetcher"] != "none"].copy()

    return out


def make_label(row):
    family = str(row.get("family", ""))
    config = str(row.get("config", ""))
    stage = str(row.get("stage", ""))

    if family == "IMP" and stage not in ["", "nan", "None"]:
        return f"{family} {stage}:{config}"

    return f"{family} {config}"


def short_label(row):
    label = make_label(row)
    speedup = row.get("speedup_vs_nopf", pd.NA)

    if pd.notna(speedup):
        label += f"\n{speedup:.3f}x"

    return "\n".join(textwrap.wrap(label, width=24))


def clean_numeric(df, col):
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def plot_metric_case(df, benchmark, pf_level, memory, metric, metric_label):
    sub = df[
        (df["benchmark"] == benchmark)
        & (df["pf_level"] == pf_level)
        & (df["memory"] == memory)
    ].copy()

    if sub.empty:
        return

    if metric not in sub.columns:
        return

    sub = clean_numeric(sub, "speedup_vs_nopf")
    sub = clean_numeric(sub, metric)

    sub = sub[
        pd.notna(sub["speedup_vs_nopf"])
        & pd.notna(sub[metric])
    ].copy()

    if sub.empty:
        return

    # Remove impossible / meaningless infinities.
    sub = sub.replace([float("inf"), -float("inf")], pd.NA)
    sub = sub[
        pd.notna(sub["speedup_vs_nopf"])
        & pd.notna(sub[metric])
    ].copy()

    if sub.empty:
        return

    top = (
        sub.sort_values("speedup_vs_nopf", ascending=False)
        .head(TOP_N)
        .copy()
    )

    plt.figure(figsize=(12, 7))

    # All dots by family.
    for family, group in sub.groupby("family"):
        plt.scatter(
            group["speedup_vs_nopf"],
            group[metric],
            s=35,
            alpha=0.35,
            color=family_colors.get(family, "gray"),
            label=family,
        )

    # Highlight top speedup runs.
    for family, group in top.groupby("family"):
        plt.scatter(
            group["speedup_vs_nopf"],
            group[metric],
            s=130,
            color=family_colors.get(family, "gray"),
            edgecolors="black",
            linewidths=0.8,
            zorder=4,
        )

    # Mark default configs.
    if "config" in sub.columns:
        defaults = sub[sub["config"].astype(str) == "default"]
        if not defaults.empty:
            plt.scatter(
                defaults["speedup_vs_nopf"],
                defaults[metric],
                s=100,
                marker="D",
                facecolors="none",
                edgecolors="black",
                linewidths=1.2,
                label="Default config",
                zorder=5,
            )

    # Label top N speedup runs.
    for _, row in top.iterrows():
        plt.annotate(
            short_label(row),
            xy=(row["speedup_vs_nopf"], row[metric]),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=8,
            ha="left",
            va="bottom",
            arrowprops=dict(arrowstyle="-", linewidth=0.5),
        )

    plt.axvline(
        1.0,
        linestyle="--",
        linewidth=1,
        color="black",
        label="No prefetch = 1.0x",
    )

    plt.xlabel("Speedup vs no-prefetch baseline")
    plt.ylabel(metric_label)

    plt.title(
        f"{metric_label} vs speedup\n"
        f"{benchmark}, {pf_level.upper()}, {memory}"
    )

    plt.grid(alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()

    filename = os.path.join(
        OUTDIR,
        f"{benchmark}_{pf_level}_{memory}_{metric}_vs_speedup.png",
    )

    plt.savefig(filename, dpi=200)
    plt.close()


def main():
    df = load_all()

    written = 0

    for benchmark in benchmarks:
        for pf_level in pf_levels:
            for memory in memories:
                for metric, metric_label in METRICS.items():
                    before = len(os.listdir(OUTDIR))
                    plot_metric_case(
                        df,
                        benchmark,
                        pf_level,
                        memory,
                        metric,
                        metric_label,
                    )
                    after = len(os.listdir(OUTDIR))
                    if after > before:
                        written += 1

    print(f"Wrote metric-vs-speedup scatter plots to: {OUTDIR}")
    print(f"Number of plot files: {len([f for f in os.listdir(OUTDIR) if f.endswith('.png')])}")


if __name__ == "__main__":
    main()