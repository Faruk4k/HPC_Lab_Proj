import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


OUTDIR = Path("plots_prefetcher_family_comparison_vs_nopf")
OUTDIR.mkdir(exist_ok=True)

NOPF = Path("baseline/nopf_results.csv")

NEXTLINE = Path("nextline/nextline_results_vs_nopf.csv")
STRIDE = Path("stride/stride_results_vs_nopf.csv")
AMPM = Path("ampm/ampm_results_vs_nopf.csv")

# Prefer the final IMP file including Stage 3. Fall back to older files if needed.
IMP_CANDIDATES = [
    Path("imp/imp_all_stages_including_stage3_vs_nopf.csv"),
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
require_file(AMPM)
IMP = find_existing(IMP_CANDIDATES)

print(f"Using IMP file: {IMP}")

nopf = pd.read_csv(NOPF)
nextline = pd.read_csv(NEXTLINE)
stride = pd.read_csv(STRIDE)
ampm = pd.read_csv(AMPM)
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
ampm = ensure_speedup_vs_nopf(ampm, "ampm")

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
best_ampm = best_per_case(ampm, "AMPM")
best_imp = best_per_case(imp[imp["prefetcher"] != "none"].copy(), "IMP")


def default_per_case(df, family_name):
    """
    Return default config per benchmark × pf_level × memory.
    """
    if "config" not in df.columns:
        return pd.DataFrame()

    default_df = df[df["config"] == "default"].copy()

    if default_df.empty:
        print(f"WARNING: No default rows found for {family_name}")
        return pd.DataFrame()

    out = (
        default_df.sort_values("speedup_vs_nopf", ascending=False)
        .groupby(["benchmark", "pf_level", "memory"], as_index=False)
        .first()
    )

    out = out[
        ["benchmark", "pf_level", "memory", "config", "speedup_vs_nopf", "simSeconds"]
    ].copy()

    out["family"] = family_name
    return out


default_nextline = default_per_case(nextline, "Next-line")
default_stride = default_per_case(stride, "Stride")
default_ampm = default_per_case(ampm, "AMPM")
default_imp = default_per_case(imp[imp["prefetcher"] != "none"].copy(), "IMP")

family_defaults = pd.concat(
    [default_nextline, default_stride, default_ampm, default_imp],
    ignore_index=True,
)

family_defaults.to_csv(
    OUTDIR / "prefetcher_family_default_configs_vs_nopf.csv",
    index=False,
)

default_lookup = {
    (row["benchmark"], row["pf_level"], row["memory"], row["family"]): float(row["speedup_vs_nopf"])
    for _, row in family_defaults.iterrows()
}

family_best = pd.concat(
    [best_nextline, best_stride, best_ampm, best_imp],
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
    if family == "AMPM":
        return "C2"
    if family == "IMP":
        return "C3"
    return "C4"


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

        family_order = ["No prefetch", "Next-line", "Stride", "AMPM", "IMP"]
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

        for bar, value, (_, row) in zip(bars, values, sub.iterrows()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.3f}x",
                ha="center",
                va="bottom",
                fontsize=8,
            )

            if row["family"] != "No prefetch":
                key = (
                    row["benchmark"],
                    row["pf_level"],
                    row["memory"],
                    row["family"],
                )

                if key in default_lookup:
                    default_value = default_lookup[key]

                    ax.hlines(
                        y=default_value,
                        xmin=bar.get_x(),
                        xmax=bar.get_x() + bar.get_width(),
                        color="red",
                        linewidth=2.5,
                    )

                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        default_value,
                        f"default {default_value:.3f}x",
                        ha="center",
                        va="top",
                        fontsize=7,
                        color="red",
                    )

    fig.suptitle(
        f"Best prefetcher-family comparison vs no-prefetch baseline — {benchmark}",
        fontsize=18,
    )

    handles = [
    plt.Rectangle((0, 0), 1, 1, color="gray", label="No prefetch"),
    plt.Rectangle((0, 0), 1, 1, color="C0", label="Best Next-line"),
    plt.Rectangle((0, 0), 1, 1, color="C1", label="Best Stride"),
    plt.Rectangle((0, 0), 1, 1, color="C2", label="Best AMPM"),
    plt.Rectangle((0, 0), 1, 1, color="C3", label="Best IMP"),
    plt.Line2D([0], [0], color="red", linewidth=2.5, label="Default config"),
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

    families = ["No prefetch", "Next-line", "Stride", "AMPM", "IMP"]
    width = 0.16
    x = list(range(len(BENCHMARKS)))

    offsets = {
        "No prefetch": -2.0 * width,
        "Next-line": -1.0 * width,
        "Stride": 0.0 * width,
        "AMPM": 1.0 * width,
        "IMP": 2.0 * width,
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

        for bar, value, benchmark in zip(bars, values, BENCHMARKS):
            if pd.notna(value):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
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
                            linewidth=2.5,
                        )

    ax.axhline(1.0, linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(BENCHMARKS, rotation=20)
    ax.set_ylabel("Speedup vs no-prefetch baseline")
    ax.set_title(f"Best prefetcher-family comparison — {condition_label}")
    ax.legend()
    handles, labels = ax.get_legend_handles_labels()
    handles.append(plt.Line2D([0], [0], color="red", linewidth=2.5))
    labels.append("Default config")
    ax.legend(handles, labels)

    plt.tight_layout()

    out = OUTDIR / f"group_{pf_level}_{memory}_prefetcher_family_comparison_vs_nopf.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print(f"Wrote {out}")


# Combined compact figure: all four conditions as a 2x2 grid in ONE image,
# each panel showing all benchmarks x all families. Meant for the report,
# replacing the per-benchmark and per-condition figures.
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 9), sharey=True)
axes = axes.flatten()

families = ["Next-line", "Stride", "AMPM", "IMP"]
width = 0.19
x = list(range(len(BENCHMARKS)))
offsets = {
    "Next-line": -1.5 * width,
    "Stride": -0.5 * width,
    "AMPM": 0.5 * width,
    "IMP": 1.5 * width,
}

y_max = plot_df_all["speedup_vs_nopf"].max() * 1.14

for ax, (pf_level, memory, condition_label) in zip(axes, CONDITIONS):
    cond_df = plot_df_all[
        (plot_df_all["pf_level"] == pf_level)
        & (plot_df_all["memory"] == memory)
    ]

    for family in families:
        values = []
        for benchmark in BENCHMARKS:
            row = cond_df[
                (cond_df["benchmark"] == benchmark)
                & (cond_df["family"] == family)
            ]
            values.append(
                float(row["speedup_vs_nopf"].iloc[0]) if not row.empty else float("nan")
            )

        positions = [i + offsets[family] for i in x]
        bars = ax.bar(
            positions, values, width=width, color=color_for_family(family)
        )

        for bar, value, benchmark in zip(bars, values, BENCHMARKS):
            if pd.notna(value):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value + 0.005,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                    rotation=90,
                )

                key = (benchmark, pf_level, memory, family)
                if key in default_lookup:
                    ax.hlines(
                        y=default_lookup[key],
                        xmin=bar.get_x(),
                        xmax=bar.get_x() + bar.get_width(),
                        color="red",
                        linewidth=1.8,
                    )

    ax.axhline(1.0, linestyle="--", linewidth=1, color="gray")
    ax.set_xticks(x)
    ax.set_xticklabels(BENCHMARKS, rotation=15, fontsize=9)
    ax.set_ylim(0.9, y_max)
    ax.set_title(condition_label, fontsize=11)
    ax.grid(axis="y", linewidth=0.4, alpha=0.4)
    ax.set_axisbelow(True)

axes[0].set_ylabel("Speedup vs no-prefetch baseline")
axes[2].set_ylabel("Speedup vs no-prefetch baseline")

handles = [
    plt.Rectangle((0, 0), 1, 1, color="C0", label="Best Next-line"),
    plt.Rectangle((0, 0), 1, 1, color="C1", label="Best Stride"),
    plt.Rectangle((0, 0), 1, 1, color="C2", label="Best AMPM"),
    plt.Rectangle((0, 0), 1, 1, color="C3", label="Best IMP"),
    plt.Line2D([0], [0], color="red", linewidth=1.8, label="Default config"),
    plt.Line2D([0], [0], color="gray", linestyle="--", linewidth=1, label="No prefetch = 1.0x"),
]
fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=10)

fig.suptitle(
    "Best prefetcher-family comparison vs no-prefetch baseline (all cases)",
    fontsize=14,
)
plt.tight_layout(rect=[0.0, 0.05, 1.0, 0.96])

out = OUTDIR / "all_conditions_prefetcher_family_comparison_vs_nopf.png"
plt.savefig(out, dpi=150)
plt.close()
print(f"Wrote {out}")


print()
print(f"Done. Plots and CSVs are in: {OUTDIR}")
print("Main CSV:")
print(OUTDIR / "prefetcher_family_best_configs_vs_nopf.csv")