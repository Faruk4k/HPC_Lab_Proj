import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


OUTDIR = Path("plots_prefetcher_family_comparison_vs_nopf")
OUTDIR.mkdir(exist_ok=True)

NOPF = Path("baseline/nopf_results.csv")

NEXTLINE = Path("nextline/nextline_results_vs_nopf.csv")
STRIDE = Path("stride/stride_results_vs_nopf.csv")

# Prefer the final IMP file including Stage 3. Fall back to older files if needed.
IMP_CANDIDATES = [
    Path("imp/imp_all_stages_including_stage3_vs_nopf.csv"),
    Path("imp/imp_all_stages_vs_nopf.csv"),
    Path("imp/imp_results_with_speedup.csv"),
]

BENCHMARKS = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]

CONDITIONS = [
    ("l1d", "ddr4_1x", "L1D + DDR4 1x"),
    ("l1d", "ddr4_2x", "L1D + DDR4 2x"),
    ("l2", "ddr4_1x", "L2 + DDR4 1x"),
    ("l2", "ddr4_2x", "L2 + DDR4 2x"),
]


def find_existing(paths):
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError(f"None of these files exist: {paths}")


def require_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")


require_file(NOPF)
require_file(NEXTLINE)
require_file(STRIDE)
IMP = find_existing(IMP_CANDIDATES)

print(f"Using IMP file: {IMP}")

nopf = pd.read_csv(NOPF)
nextline = pd.read_csv(NEXTLINE)
stride = pd.read_csv(STRIDE)
imp = pd.read_csv(IMP)


def ensure_speedup_vs_nopf(df, name):
    if "speedup_vs_nopf" in df.columns:
        return df

    base = nopf[["benchmark", "memory", "simSeconds"]].rename(
        columns={"simSeconds": "nopf_simSeconds"}
    )

    df = df.merge(base, on=["benchmark", "memory"], how="left")
    df["speedup_vs_nopf"] = df["nopf_simSeconds"] / df["simSeconds"]

    print(f"Computed speedup_vs_nopf for {name}")
    return df


nextline = ensure_speedup_vs_nopf(nextline, "nextline")
stride = ensure_speedup_vs_nopf(stride, "stride")
imp = ensure_speedup_vs_nopf(imp, "imp")


def best_per_case(df, family_name):
    """
    Return best config per benchmark × pf_level × memory.
    """
    needed = ["benchmark", "pf_level", "memory", "config", "speedup_vs_nopf", "simSeconds"]
    for col in needed:
        if col not in df.columns:
            df[col] = pd.NA

    out = (
        df.sort_values("speedup_vs_nopf", ascending=False)
        .groupby(["benchmark", "pf_level", "memory"], as_index=False)
        .first()
    )

    out = out[
        ["benchmark", "pf_level", "memory", "config", "speedup_vs_nopf", "simSeconds"]
    ].copy()

    out["family"] = family_name

    return out


best_nextline = best_per_case(nextline, "Next-line")
best_stride = best_per_case(stride, "Stride")
best_imp = best_per_case(imp[imp["prefetcher"] != "none"].copy(), "IMP")

family_best = pd.concat(
    [best_nextline, best_stride, best_imp],
    ignore_index=True,
)

family_best.to_csv(
    OUTDIR / "prefetcher_family_best_configs_vs_nopf.csv",
    index=False,
)


def baseline_speedup_row(benchmark, pf_level, memory):
    base = nopf[
        (nopf["benchmark"] == benchmark)
        & (nopf["memory"] == memory)
    ]

    if base.empty:
        raise RuntimeError(f"No baseline row for {benchmark}, {memory}")

    return {
        "benchmark": benchmark,
        "pf_level": pf_level,
        "memory": memory,
        "family": "No prefetch",
        "config": "none",
        "speedup_vs_nopf": 1.0,
        "simSeconds": float(base["simSeconds"].iloc[0]),
    }


all_plot_rows = []

for benchmark in BENCHMARKS:
    for pf_level, memory, condition_label in CONDITIONS:
        all_plot_rows.append(baseline_speedup_row(benchmark, pf_level, memory))

        sub = family_best[
            (family_best["benchmark"] == benchmark)
            & (family_best["pf_level"] == pf_level)
            & (family_best["memory"] == memory)
        ]

        for _, row in sub.iterrows():
            all_plot_rows.append(row.to_dict())

plot_df_all = pd.DataFrame(all_plot_rows)
plot_df_all.to_csv(
    OUTDIR / "prefetcher_family_plot_data_vs_nopf.csv",
    index=False,
)


def label_for_bar(row):
    family = row["family"]
    config = row["config"]

    if family == "No prefetch":
        return "No prefetch"

    return f"{family}\n{config}"


def color_for_family(family):
    if family == "No prefetch":
        return "gray"
    if family == "Next-line":
        return "C0"
    if family == "Stride":
        return "C1"
    if family == "IMP":
        return "C2"
    return "C3"


for benchmark in BENCHMARKS:
    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(18, 12),
        sharey=True,
    )

    axes = axes.flatten()

    bench_df = plot_df_all[plot_df_all["benchmark"] == benchmark].copy()

    x_max = max(1.05, bench_df["speedup_vs_nopf"].max() * 1.08)
    x_min = min(0.95, bench_df["speedup_vs_nopf"].min() * 0.98)

    for ax, (pf_level, memory, condition_label) in zip(axes, CONDITIONS):
        sub = bench_df[
            (bench_df["pf_level"] == pf_level)
            & (bench_df["memory"] == memory)
        ].copy()

        family_order = ["No prefetch", "Next-line", "Stride", "IMP"]
        sub["family_order"] = sub["family"].apply(lambda x: family_order.index(x))
        sub = sub.sort_values("family_order")

        labels = [label_for_bar(row) for _, row in sub.iterrows()]
        values = sub["speedup_vs_nopf"].astype(float).tolist()
        colors = [color_for_family(f) for f in sub["family"]]

        bars = ax.bar(labels, values, color=colors)

        ax.axhline(1.0, linestyle="--", linewidth=1)
        ax.set_title(condition_label)
        ax.set_ylim(x_min, x_max)
        ax.set_ylabel("Speedup vs no-prefetch baseline")
        ax.tick_params(axis="x", labelrotation=20, labelsize=8)

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.3f}x",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    fig.suptitle(
        f"Best prefetcher-family comparison vs no-prefetch baseline — {benchmark}",
        fontsize=18,
    )

    handles = [
        plt.Rectangle((0, 0), 1, 1, color="gray", label="No prefetch"),
        plt.Rectangle((0, 0), 1, 1, color="C0", label="Best Next-line"),
        plt.Rectangle((0, 0), 1, 1, color="C1", label="Best Stride"),
        plt.Rectangle((0, 0), 1, 1, color="C2", label="Best IMP"),
    ]

    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=12)

    plt.tight_layout(rect=[0.02, 0.06, 1.0, 0.94])

    out = OUTDIR / f"{benchmark}_prefetcher_family_comparison_vs_nopf.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print(f"Wrote {out}")


# Also make condition-grouped plots:
# one PNG per condition, with all benchmarks on the x-axis.
for pf_level, memory, condition_label in CONDITIONS:
    cond_df = plot_df_all[
        (plot_df_all["pf_level"] == pf_level)
        & (plot_df_all["memory"] == memory)
    ].copy()

    fig, ax = plt.subplots(figsize=(20, 8))

    families = ["No prefetch", "Next-line", "Stride", "IMP"]
    width = 0.20
    x = list(range(len(BENCHMARKS)))

    offsets = {
        "No prefetch": -1.5 * width,
        "Next-line": -0.5 * width,
        "Stride": 0.5 * width,
        "IMP": 1.5 * width,
    }

    for family in families:
        values = []
        labels = []

        for benchmark in BENCHMARKS:
            row = cond_df[
                (cond_df["benchmark"] == benchmark)
                & (cond_df["family"] == family)
            ]

            if row.empty:
                values.append(float("nan"))
                labels.append("")
            else:
                values.append(float(row["speedup_vs_nopf"].iloc[0]))
                labels.append(str(row["config"].iloc[0]))

        positions = [i + offsets[family] for i in x]

        bars = ax.bar(
            positions,
            values,
            width=width,
            label=family,
            color=color_for_family(family),
        )

        for bar, value in zip(bars, values):
            if pd.notna(value):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    ax.axhline(1.0, linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(BENCHMARKS, rotation=20)
    ax.set_ylabel("Speedup vs no-prefetch baseline")
    ax.set_title(f"Best prefetcher-family comparison — {condition_label}")
    ax.legend()

    plt.tight_layout()

    out = OUTDIR / f"group_{pf_level}_{memory}_prefetcher_family_comparison_vs_nopf.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print(f"Wrote {out}")


print()
print(f"Done. Plots and CSVs are in: {OUTDIR}")
print("Main CSV:")
print(OUTDIR / "prefetcher_family_best_configs_vs_nopf.csv")