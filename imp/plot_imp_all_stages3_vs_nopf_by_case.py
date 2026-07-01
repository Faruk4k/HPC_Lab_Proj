
import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

STAGE1 = "imp_results.csv"
STAGE2 = "imp_stage2_with_comparison.csv"
STAGE3 = "imp_stage3_with_comparison.csv"
NOPF = "../baseline/nopf_results.csv"

OUTDIR = "plots_imp_all_stages_vs_nopf_by_case"
TOP_N = 30

os.makedirs(OUTDIR, exist_ok=True)

stage1 = pd.read_csv(STAGE1)
stage2 = pd.read_csv(STAGE2)
stage3 = pd.read_csv(STAGE3)
nopf = pd.read_csv(NOPF)

required_cols = [
    "run", "benchmark", "prefetcher", "config", "pf_level", "memory",
    "simSeconds", "ipc",
    "l1d_demand_misses", "l1d_demand_accesses",
    "l2_demand_misses", "l2_demand_accesses",
    "l1d_pf_issued", "l1d_pf_useful", "l1d_pf_unused",
    "l2_pf_issued", "l2_pf_useful", "l2_pf_unused",
]

# Keep the union of all columns from Stage 1, Stage 2, and Stage 3.
# This prevents extra metrics such as pfLate, bandwidth, MSHR pressure,
# DRAM queue length, etc. from being dropped.
all_cols = sorted(set(stage1.columns) | set(stage2.columns) | set(stage3.columns) | set(required_cols))

for df in [stage1, stage2, stage3]:
    for col in all_cols:
        if col not in df.columns:
            df[col] = pd.NA

stage1 = stage1[all_cols].copy()
stage2 = stage2[all_cols].copy()
stage3 = stage3[all_cols].copy()

stage1["stage"] = "stage1"
stage2["stage"] = "stage2"
stage3["stage"] = "stage3"

imp = pd.concat([stage1, stage2, stage3], ignore_index=True)

# Keep only one IMP default. Stage 1 default is the canonical default.
imp = imp[~((imp["stage"] == "stage2") & (imp["config"] == "default"))]
imp = imp[~((imp["stage"] == "stage3") & (imp["config"] == "default"))]

# Remove exact duplicate run names if any.
imp = imp.drop_duplicates(subset=["run"], keep="first")

# Add no-prefetch baseline.
baseline = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

# Remove old baseline columns from Stage 2/Stage 3 files before merging again.
imp = imp.drop(
    columns=[
        "nopf_simSeconds",
        "nopf_simSeconds_x",
        "nopf_simSeconds_y",
    ],
    errors="ignore",
)

imp = imp.merge(baseline, on=["benchmark", "memory"], how="left")

if "nopf_simSeconds" not in imp.columns:
    raise RuntimeError(f"nopf_simSeconds missing after merge. Columns are: {list(imp.columns)}")

imp["speedup_vs_nopf"] = imp["nopf_simSeconds"] / imp["simSeconds"]


# Derived stats.
# Derived stats.
def ensure_col(df, col):
    if col not in df.columns:
        df[col] = pd.NA


def effective_by_level(row, l1d_col, l2_col):
    l1d_val = row.get(l1d_col, pd.NA)
    l2_val = row.get(l2_col, pd.NA)

    if row["pf_level"] == "l1d":
        if pd.notna(l1d_val):
            return l1d_val
        return l2_val

    if row["pf_level"] == "l2":
        if pd.notna(l2_val):
            return l1d_val if pd.isna(l2_val) else l2_val

    return pd.NA


# Make sure the basic columns exist.
for col in [
    "l1d_pf_issued", "l1d_pf_useful", "l1d_pf_unused",
    "l2_pf_issued", "l2_pf_useful", "l2_pf_unused",
    "l1d_demand_misses", "l1d_demand_accesses",
    "l2_demand_misses", "l2_demand_accesses",
]:
    ensure_col(imp, col)


# Use the counters from the cache level where the prefetcher was installed.
imp["pf_issued"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_issued", "l2_pf_issued"),
    axis=1,
)

imp["pf_useful"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_useful", "l2_pf_useful"),
    axis=1,
)

imp["pf_unused"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_unused", "l2_pf_unused"),
    axis=1,
)

imp["pf_accuracy"] = imp["pf_useful"] / imp["pf_issued"].replace(0, pd.NA)
imp["pf_unused_ratio"] = imp["pf_unused"] / imp["pf_issued"].replace(0, pd.NA)


# Miss rates are still useful to compute for both cache levels.
imp["l1d_miss_rate"] = (
    imp["l1d_demand_misses"] / imp["l1d_demand_accesses"].replace(0, pd.NA)
)

imp["l2_miss_rate"] = (
    imp["l2_demand_misses"] / imp["l2_demand_accesses"].replace(0, pd.NA)
)


# Coverage approximation using the active cache level.
def effective_coverage(row):
    useful = row.get("pf_useful", pd.NA)

    if row["pf_level"] == "l1d":
        misses = row.get("l1d_demand_misses", pd.NA)
    elif row["pf_level"] == "l2":
        misses = row.get("l2_demand_misses", pd.NA)
    else:
        return pd.NA

    if pd.isna(useful) or pd.isna(misses) or useful + misses == 0:
        return pd.NA

    return useful / (useful + misses)


imp["pf_coverage"] = imp.apply(effective_coverage, axis=1)


# Optional extra prefetcher counters, if they exist in the extracted CSVs.
for col in [
    "l1d_pf_late", "l2_pf_late",
    "l1d_pf_removed_full", "l2_pf_removed_full",
    "l1d_pf_removed_demand", "l2_pf_removed_demand",
    "l1d_pf_buffer_hit", "l2_pf_buffer_hit",
    "l1d_pf_identified", "l2_pf_identified",
    "l1d_prefetcher_read_rate", "l2_prefetcher_read_rate",
    "l1d_prefetcher_read_bytes", "l2_prefetcher_read_bytes",
]:
    ensure_col(imp, col)


imp["pf_late"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_late", "l2_pf_late"),
    axis=1,
)

imp["pf_late_ratio"] = imp["pf_late"] / imp["pf_issued"].replace(0, pd.NA)

imp["pf_removed_full"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_full", "l2_pf_removed_full"),
    axis=1,
)

imp["pf_removed_demand"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_demand", "l2_pf_removed_demand"),
    axis=1,
)

imp["pf_buffer_hit"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_buffer_hit", "l2_pf_buffer_hit"),
    axis=1,
)

imp["pf_identified"] = imp.apply(
    lambda r: effective_by_level(r, "l1d_pf_identified", "l2_pf_identified"),
    axis=1,
)

imp["pf_removed_full_ratio"] = (
    imp["pf_removed_full"] / imp["pf_identified"].replace(0, pd.NA)
)

imp["pf_removed_demand_ratio"] = (
    imp["pf_removed_demand"] / imp["pf_identified"].replace(0, pd.NA)
)

imp["pf_buffer_hit_ratio"] = (
    imp["pf_buffer_hit"] / imp["pf_identified"].replace(0, pd.NA)
)

imp["prefetcher_read_rate"] = imp.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_rate",
        "l2_prefetcher_read_rate",
    ),
    axis=1,
)

imp["prefetcher_read_bytes"] = imp.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_bytes",
        "l2_prefetcher_read_bytes",
    ),
    axis=1,
)


# DRAM bandwidth utilization, if available.
if "dram_bw_total" in imp.columns and "dram_peak_bw" in imp.columns:
    imp["dram_bw_utilization"] = (
        imp["dram_bw_total"] / (imp["dram_peak_bw"] * 1024 * 1024)
    )

def make_label(row):
    config = str(row["config"])
    stage = str(row["stage"])

    if config == "default":
        return "IMP default"

    return f"{stage}: {config}"


imp["label"] = imp.apply(make_label, axis=1)

imp.to_csv("imp_all_stages_including_stage3_vs_nopf.csv", index=False)

benchmarks = ["simple_triad", "spmv", "bfs", "merge", "quick", "matmult"]
pf_levels = ["l1d", "l2"]
memories = ["ddr4_1x", "ddr4_2x"]


def wrap_labels(labels, width=38):
    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


def add_baseline_row(sub, benchmark, pf_level, memory):
    base = nopf[
        (nopf["benchmark"] == benchmark)
        & (nopf["memory"] == memory)
    ]

    if base.empty:
        return sub

    base = base.iloc[0]

    l1d_miss_rate = pd.NA
    l2_miss_rate = pd.NA

    if "l1d_demand_misses" in nopf.columns and "l1d_demand_accesses" in nopf.columns:
        if pd.notna(base["l1d_demand_accesses"]) and base["l1d_demand_accesses"] != 0:
            l1d_miss_rate = base["l1d_demand_misses"] / base["l1d_demand_accesses"]

    if "l2_demand_misses" in nopf.columns and "l2_demand_accesses" in nopf.columns:
        if pd.notna(base["l2_demand_accesses"]) and base["l2_demand_accesses"] != 0:
            l2_miss_rate = base["l2_demand_misses"] / base["l2_demand_accesses"]

    baseline_row = {
        "run": f"{benchmark}_nopf_{memory}",
        "benchmark": benchmark,
        "prefetcher": "none",
        "config": "none",
        "pf_level": pf_level,
        "memory": memory,
        "simSeconds": float(base["simSeconds"]),
        "stage": "baseline",
        "nopf_simSeconds": float(base["simSeconds"]),
        "speedup_vs_nopf": 1.0,
        "label": "No prefetch baseline",

        # Cache behavior
        "l1d_demand_misses": base.get("l1d_demand_misses", pd.NA),
        "l1d_demand_accesses": base.get("l1d_demand_accesses", pd.NA),
        "l2_demand_misses": base.get("l2_demand_misses", pd.NA),
        "l2_demand_accesses": base.get("l2_demand_accesses", pd.NA),
        "l1d_miss_rate": l1d_miss_rate,
        "l2_miss_rate": l2_miss_rate,

        # No prefetcher exists in baseline
        "pf_issued": 0,
        "pf_useful": 0,
        "pf_unused": 0,
        "pf_accuracy": pd.NA,
        "pf_unused_ratio": pd.NA,
        "pf_late": 0,
        "pf_late_ratio": pd.NA,
        "pf_coverage": 0,

        # Optional memory pressure stats, if nopf_results.csv has them
        "mem_avg_rdq_len": base.get("mem_avg_rdq_len", pd.NA),
        "mem_avg_wrq_len": base.get("mem_avg_wrq_len", pd.NA),
        "dram_bw_total": base.get("dram_bw_total", pd.NA),
        "dram_peak_bw": base.get("dram_peak_bw", pd.NA),
        "dram_avg_q_lat": base.get("dram_avg_q_lat", pd.NA),
        "dram_avg_mem_acc_lat": base.get("dram_avg_mem_acc_lat", pd.NA),

        # No prefetcher memory traffic
        "prefetcher_read_rate": 0,
        "prefetcher_read_bytes": 0,
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
        elif row["stage"] == "stage1":
            colors.append("C0")
        elif row["stage"] == "stage2":
            colors.append("C1")
        elif row["stage"] == "stage3":
            colors.append("C2")
        else:
            colors.append("C0")

    return colors


def plot_horizontal_bar(sub, title, filename, top_only=True):
    if top_only:
        non_ref = sub[
            ~(
                (sub["label"] == "No prefetch baseline")
                | (sub["config"] == "default")
            )
        ]

        plot_df = non_ref.sort_values("speedup_vs_nopf", ascending=False).head(TOP_N)
        plot_df = force_include_reference_rows(plot_df, sub)
    else:
        plot_df = sub.copy()

    plot_df = plot_df.sort_values("speedup_vs_nopf", ascending=True)

    height = max(8, 0.30 * len(plot_df))
    plt.figure(figsize=(14, height))

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

    # Legend.
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="gray", label="No prefetch"),
        plt.Rectangle((0, 0), 1, 1, color="red", label="IMP default"),
        plt.Rectangle((0, 0), 1, 1, color="C0", label="Stage 1"),
        plt.Rectangle((0, 0), 1, 1, color="C1", label="Stage 2"),
        plt.Rectangle((0, 0), 1, 1, color="C2", label="Stage 3"),
    ]

    plt.legend(handles=handles, loc="lower right")

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
                print(f"Skipping empty case: {benchmark}, {pf_level}, {memory}")
                continue

            sub = add_baseline_row(sub, benchmark, pf_level, memory)

            case_csv = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_all_stages_all_configs.csv",
            )

            sub.sort_values("speedup_vs_nopf", ascending=False).to_csv(case_csv, index=False)

            winner = (
                sub[sub["prefetcher"] != "none"]
                .sort_values("speedup_vs_nopf", ascending=False)
                .head(1)
            )

            if not winner.empty:
                winner_rows.append(winner.iloc[0].to_dict())

            title = f"{benchmark}: IMP all stages vs no prefetch ({pf_level.upper()}, {memory})"

            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_top{TOP_N}_all_stages_vs_nopf.png",
            )

            plot_horizontal_bar(sub, title, filename, top_only=True)

            title = f"{benchmark}: all IMP configs from all stages vs no prefetch ({pf_level.upper()}, {memory})"

            filename = os.path.join(
                OUTDIR,
                f"{benchmark}_{pf_level}_{memory}_all_stages_vs_nopf.png",
            )

            plot_horizontal_bar(sub, title, filename, top_only=False)


winners = pd.DataFrame(winner_rows)
winners.to_csv("imp_all_stages_including_stage3_winners_per_case.csv", index=False)

print(f"Wrote plots to: {OUTDIR}")
print("Wrote CSV: imp_all_stages_including_stage3_vs_nopf.csv")
print("Wrote winners CSV: imp_all_stages_including_stage3_winners_per_case.csv")
print(f"Number of plot files: {len([f for f in os.listdir(OUTDIR) if f.endswith('.png')])}")