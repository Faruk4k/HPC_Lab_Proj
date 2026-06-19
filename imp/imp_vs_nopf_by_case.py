import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

STAGE1 = "imp_results_with_speedup.csv"
STAGE2 = "imp_stage2_with_comparison.csv"
NOPF = "../baseline/nopf_results.csv"

OUTDIR = "plots_imp_vs_nopf_by_case"
TOP_N = 25

os.makedirs(OUTDIR, exist_ok=True)

stage1 = pd.read_csv(STAGE1)
stage2 = pd.read_csv(STAGE2)
nopf = pd.read_csv(NOPF)

# We only need raw runtime and metadata. Recompute all speedups against no-prefetch.
common_cols = [
    "run",
    "benchmark",
    "prefetcher",
    "config",
    "pf_level",
    "memory",
    "simSeconds",
    "ipc",
    "l1d_demand_misses",
    "l1d_demand_accesses",
    "l2_demand_misses",
    "l2_demand_accesses",
    "l1d_pf_issued",
    "l1d_pf_useful",
    "l1d_pf_unused",
    "l2_pf_issued",
    "l2_pf_useful",
    "l2_pf_unused",
]

for col in common_cols:
    if col not in stage1.columns:
        stage1[col] = pd.NA
    if col not in stage2.columns:
        stage2[col] = pd.NA

stage1 = stage1[common_cols].copy()
stage2 = stage2[common_cols].copy()

stage1["stage"] = "stage1"
stage2["stage"] = "stage2"

imp = pd.concat([stage1, stage2], ignore_index=True)

# Keep only one IMP default. Stage 1 default is the canonical IMP default.
imp = imp[~((imp["stage"] == "stage2") & (imp["config"] == "default"))]

# Remove exact duplicate run names if any.
imp = imp.drop_duplicates(subset=["run"], keep="first")

# Merge no-prefetch baseline by benchmark + memory.
baseline = (
    nopf[["benchmark", "memory", "simSeconds"]]
    .rename(columns={"simSeconds": "nopf_simSeconds"})
)

imp = imp.merge(baseline, on=["benchmark", "memory"], how="left")
imp["speedup_vs_nopf"] = imp["nopf_simSeconds"] / imp["simSeconds"]

# Prefetch stats.
imp["pf_issued"] = imp["l1d_pf_issued"].fillna(0) + imp["l2_pf_issued"].fillna(0)
imp["pf_useful"] = imp["l1d_pf_useful"].fillna(0) + imp["l2_pf_useful"].fillna(0)
imp["pf_unused"] = imp["l1d_pf_unused"].fillna(0) + imp["l2_pf_unused"].fillna(0)

imp["pf_accuracy"] = imp["pf_useful"] / imp["pf_issued"].replace(0, pd.NA)
imp["pf_unused_ratio"] = imp["pf_unused"] / imp["pf_issued"].replace(0, pd.NA)

imp["l1d_miss_rate"] = imp["l1d_demand_misses"] / imp["l1d_demand_accesses"].replace(0, pd.NA)
imp["l2_miss_rate"] = imp["l2_demand_misses"] / imp["l2_demand_accesses"].replace(0, pd.NA)

# Create readable labels.
def make_label(row):
    config = str(row["config"])
    stage = str(row["stage"])

    if config == "default":
        return f"{stage}: default [IMP default]"

    return f"{stage}: {config}"


imp["label"] = imp.apply(make_label, axis=1)

# Save combined CSV for later report tables.
imp.to_csv("imp_all_stages_vs_nopf.csv", index=False)

benchmarks = sorted(imp["benchmark"].dropna().unique())
pf_levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]


def wrap_labels(labels, width=36):
    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


def add_baseline_row(sub, benchmark, pf_level, memory):
    # Add no-prefetch baseline as speedup = 1.0 for visual reference.
    base = baseline[
        (baseline["benchmark"] == benchmark)
        & (baseline["memory"] == memory)
    ]

    if base.empty:
        return sub

    baseline_row = {
        "run": f"{benchmark}_nopf_{memory}",
        "benchmark": benchmark,
        "prefetcher": "none",
        "config": "none",
        "pf_level": pf_level,
        "memory": memory,
        "simSeconds": float(base["nopf_simSeconds"].iloc[0]),
        "stage": "baseline",
        "nopf_simSeconds": float(base["nopf_simSeconds"].iloc[0]),
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
    # Always include no-prefetch and IMP default rows, even if they are not in top-N.
    refs = full[
        (full["label"] == "No prefetch baseline")
        | (full["config"] == "default")
    ]

    out = pd.concat([top, refs], ignore_index=True)
    out = out.drop_duplicates(subset=["label"], keep="first")
    return out

def plot_horizontal_bar(sub, title, filename, top_only=True):
    if top_only:
        plot_df = sub.sort_values("speedup_vs_nopf", ascending=False).head(TOP_N)
        plot_df = force_include_reference_rows(plot_df, sub)
    else:
        plot_df = sub.copy()

    plot_df = plot_df.sort_values("speedup_vs_nopf", ascending=True)

    colors = []
    for _, row in plot_df.iterrows():
        if row["prefetcher"] == "none":
            colors.append("gray")
        elif row["config"] == "default":
            colors.append("red")
        else:
            colors.append("C0")

    height = max(7, 0.32 * len(plot_df))
    plt.figure(figsize=(13, height))

    plt.barh(wrap_labels(plot_df["label"]), plot_df["speedup_vs_nopf"], color=colors)
    plt.axvline(1.0, linestyle="--", linewidth=1)

    plt.xlabel("Speedup vs no-prefetch baseline")
    plt.ylabel("Configuration")
    plt.title(title)

    for i, value in enumerate(plot_df["speedup_vs_nopf"]):
        if pd.notna(value):
            plt.text(value, i, f" {value:.3f}x", va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()

winner_rows = []

for benchmark in benchmarks:
    for pf_level in pf_levels:
        for memory in memories:
            sub = imp[
                (imp["benchmark"] == benchmark)
                & (imp["pf_level"] == pf_level)
                & (imp["memory"] == memory)
            ].copy()

            if sub.empty:
                continue

            sub = add_baseline_row(sub, benchmark, pf_level, memory)

            # Save per-case CSV.
            case_csv = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_all_configs.csv",
            )
            sub.sort_values("speedup_vs_nopf", ascending=False).to_csv(case_csv, index=False)

            # Winner excluding no-prefetch baseline.
            winner = sub[sub["prefetcher"] != "none"].sort_values(
                "speedup_vs_nopf",
                ascending=False,
            ).head(1)

            if not winner.empty:
                winner_rows.append(winner.iloc[0].to_dict())

            # Top-N readable plot.
            title = f"{benchmark}: IMP speedup vs no prefetch ({pf_level.upper()}, {memory})"
            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_top{TOP_N}_speedup_vs_nopf.png",
            )
            plot_horizontal_bar(sub, title, filename, top_only=True)

            # Full plot with every config.
            title = f"{benchmark}: all IMP configs vs no prefetch ({pf_level.upper()}, {memory})"
            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_all_speedup_vs_nopf.png",
            )
            plot_horizontal_bar(sub, title, filename, top_only=False)

winners = pd.DataFrame(winner_rows)
winners.to_csv("imp_winners_vs_nopf_per_case.csv", index=False)

print(f"Wrote plots to: {OUTDIR}")
print(f"Wrote combined CSV: imp_all_stages_vs_nopf.csv")
print(f"Wrote winners CSV: imp_winners_vs_nopf_per_case.csv")
print(f"Number of plot files: {len([f for f in os.listdir(OUTDIR) if f.endswith('.png')])}")