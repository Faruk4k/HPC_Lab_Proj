import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

STRIDE = "stride_results_vs_nopf.csv"
NOPF = "../baseline/nopf_results.csv"

OUTDIR = "plots_stride_vs_nopf_by_case"
TOP_N = 25

os.makedirs(OUTDIR, exist_ok=True)

stride = pd.read_csv(STRIDE)
nopf = pd.read_csv(NOPF)

benchmarks = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]
pf_levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]

stride["label"] = stride["config"].apply(
    lambda x: "Stride default" if str(x) == "default" else f"stride: {x}"
)


def wrap_labels(labels, width=36):
    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


def add_baseline_row(sub, benchmark, pf_level, memory):
    base = nopf[
        (nopf["benchmark"] == benchmark)
        & (nopf["memory"] == memory)
    ]

    if base.empty:
        return sub

    base_sec = float(base["simSeconds"].iloc[0])

    baseline_row = {
        "run": f"{benchmark}_nopf_{memory}",
        "benchmark": benchmark,
        "prefetcher": "none",
        "config": "none",
        "pf_level": pf_level,
        "memory": memory,
        "simSeconds": base_sec,
        "nopf_simSeconds": base_sec,
        "speedup_vs_nopf": 1.0,
        "label": "No prefetch baseline",
        "pf_accuracy": pd.NA,
        "pf_unused_ratio": pd.NA,
        "l1d_miss_rate": pd.NA,
        "l2_miss_rate": pd.NA,
        "pf_issued": 0,
        "pf_useful": 0,
        "pf_unused": 0,
    }

    return pd.concat([sub, pd.DataFrame([baseline_row])], ignore_index=True)


def force_include_reference_rows(top, full):
    refs = full[
        (full["label"] == "No prefetch baseline")
        | (full["config"] == "default")
    ]

    out = pd.concat([top, refs], ignore_index=True)
    out = out.drop_duplicates(subset=["label"], keep="first")
    return out


def row_colors(plot_df):
    colors = []

    for _, row in plot_df.iterrows():
        if row["prefetcher"] == "none":
            colors.append("gray")
        elif row["config"] == "default":
            colors.append("red")
        else:
            colors.append("C0")

    return colors


def plot_horizontal_bar(sub, title, filename, top_only=True):
    if top_only:
        plot_df = sub.sort_values("speedup_vs_nopf", ascending=False).head(TOP_N)
        plot_df = force_include_reference_rows(plot_df, sub)
    else:
        plot_df = sub.copy()

    plot_df = plot_df.sort_values("speedup_vs_nopf", ascending=True)

    height = max(7, 0.32 * len(plot_df))
    plt.figure(figsize=(13, height))

    plt.barh(
        wrap_labels(plot_df["label"]),
        plot_df["speedup_vs_nopf"],
        color=row_colors(plot_df),
    )

    plt.axvline(1.0, linestyle="--", linewidth=1)

    plt.xlabel("Speedup vs no-prefetch baseline")
    plt.ylabel("Configuration")
    plt.title(title)

    for i, value in enumerate(plot_df["speedup_vs_nopf"]):
        if pd.notna(value):
            plt.text(value, i, f" {value:.3f}x", va="center", fontsize=8)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color="gray", label="No prefetch"),
        plt.Rectangle((0, 0), 1, 1, color="red", label="Stride default"),
        plt.Rectangle((0, 0), 1, 1, color="C0", label="Stride tuned"),
    ]

    plt.legend(handles=handles, loc="lower right")

    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


winner_rows = []

for benchmark in benchmarks:
    for pf_level in pf_levels:
        for memory in memories:
            sub = stride[
                (stride["benchmark"] == benchmark)
                & (stride["pf_level"] == pf_level)
                & (stride["memory"] == memory)
            ].copy()

            if sub.empty:
                print(f"Skipping empty case: {benchmark}, {pf_level}, {memory}")
                continue

            sub = add_baseline_row(sub, benchmark, pf_level, memory)

            case_csv = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_stride_all_configs.csv",
            )

            sub.sort_values("speedup_vs_nopf", ascending=False).to_csv(case_csv, index=False)

            winner = (
                sub[sub["prefetcher"] != "none"]
                .sort_values("speedup_vs_nopf", ascending=False)
                .head(1)
            )

            if not winner.empty:
                winner_rows.append(winner.iloc[0].to_dict())

            title = f"{benchmark}: Stride speedup vs no prefetch ({pf_level.upper()}, {memory})"

            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_top{TOP_N}_stride_vs_nopf.png",
            )

            plot_horizontal_bar(sub, title, filename, top_only=True)

            title = f"{benchmark}: all Stride configs vs no prefetch ({pf_level.upper()}, {memory})"

            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_all_stride_vs_nopf.png",
            )

            plot_horizontal_bar(sub, title, filename, top_only=False)


winners = pd.DataFrame(winner_rows)
winners.to_csv("stride_winners_vs_nopf_per_case_from_plots.csv", index=False)

print(f"Wrote plots to: {OUTDIR}")
print("Wrote winners CSV: stride_winners_vs_nopf_per_case_from_plots.csv")
print(f"Number of plot files: {len([f for f in os.listdir(OUTDIR) if f.endswith('.png')])}")