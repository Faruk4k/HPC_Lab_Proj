import pandas as pd
import math

STRIDE = "stride_results.csv"
NOPF = "../baseline/nopf_results.csv"

OUT = "stride_results_vs_nopf.csv"
WINNERS = "stride_winners_vs_nopf_per_case.csv"

stride = pd.read_csv(STRIDE)
nopf = pd.read_csv(NOPF)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

# Avoid duplicated baseline columns if rerun.
stride = stride.drop(
    columns=["nopf_simSeconds", "nopf_simSeconds_x", "nopf_simSeconds_y"],
    errors="ignore",
)

stride = stride.merge(base, on=["benchmark", "memory"], how="left")
stride["speedup_vs_nopf"] = stride["nopf_simSeconds"] / stride["simSeconds"]


def ensure_col(df, col):
    if col not in df.columns:
        df[col] = math.nan


def effective_by_level(row, l1d_col, l2_col):
    l1d_val = row.get(l1d_col, math.nan)
    l2_val = row.get(l2_col, math.nan)

    if row["pf_level"] == "l1d":
        if pd.notna(l1d_val):
            return l1d_val
        return l2_val

    if row["pf_level"] == "l2":
        if pd.notna(l2_val):
            return l2_val
        return l1d_val

    return math.nan


# Required columns
for col in [
    "l1d_pf_issued", "l1d_pf_useful", "l1d_pf_unused",
    "l2_pf_issued", "l2_pf_useful", "l2_pf_unused",
    "l1d_demand_misses", "l1d_demand_accesses",
    "l2_demand_misses", "l2_demand_accesses",
]:
    ensure_col(stride, col)


# Use only the active prefetcher level.
stride["pf_issued"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_issued", "l2_pf_issued"),
    axis=1,
)

stride["pf_useful"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_useful", "l2_pf_useful"),
    axis=1,
)

stride["pf_unused"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_unused", "l2_pf_unused"),
    axis=1,
)

stride["pf_accuracy"] = (
    stride["pf_useful"] / stride["pf_issued"].replace(0, pd.NA)
)

stride["pf_unused_ratio"] = (
    stride["pf_unused"] / stride["pf_issued"].replace(0, pd.NA)
)

stride["l1d_miss_rate"] = (
    stride["l1d_demand_misses"] / stride["l1d_demand_accesses"].replace(0, pd.NA)
)

stride["l2_miss_rate"] = (
    stride["l2_demand_misses"] / stride["l2_demand_accesses"].replace(0, pd.NA)
)


def effective_coverage(row):
    useful = row.get("pf_useful", math.nan)

    if row["pf_level"] == "l1d":
        misses = row.get("l1d_demand_misses", math.nan)
    elif row["pf_level"] == "l2":
        misses = row.get("l2_demand_misses", math.nan)
    else:
        return math.nan

    if pd.isna(useful) or pd.isna(misses) or useful + misses == 0:
        return math.nan

    return useful / (useful + misses)


stride["pf_coverage"] = stride.apply(effective_coverage, axis=1)


# Optional extra prefetch counters
for col in [
    "l1d_pf_late", "l2_pf_late",
    "l1d_pf_removed_full", "l2_pf_removed_full",
    "l1d_pf_removed_demand", "l2_pf_removed_demand",
    "l1d_pf_buffer_hit", "l2_pf_buffer_hit",
    "l1d_pf_identified", "l2_pf_identified",
    "l1d_prefetcher_read_rate", "l2_prefetcher_read_rate",
    "l1d_prefetcher_read_bytes", "l2_prefetcher_read_bytes",
]:
    ensure_col(stride, col)


stride["pf_late"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_late", "l2_pf_late"),
    axis=1,
)

stride["pf_late_ratio"] = (
    stride["pf_late"] / stride["pf_issued"].replace(0, pd.NA)
)

stride["pf_removed_full"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_full", "l2_pf_removed_full"),
    axis=1,
)

stride["pf_removed_demand"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_demand", "l2_pf_removed_demand"),
    axis=1,
)

stride["pf_buffer_hit"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_buffer_hit", "l2_pf_buffer_hit"),
    axis=1,
)

stride["pf_identified"] = stride.apply(
    lambda r: effective_by_level(r, "l1d_pf_identified", "l2_pf_identified"),
    axis=1,
)

stride["pf_removed_full_ratio"] = (
    stride["pf_removed_full"] / stride["pf_identified"].replace(0, pd.NA)
)

stride["pf_removed_demand_ratio"] = (
    stride["pf_removed_demand"] / stride["pf_identified"].replace(0, pd.NA)
)

stride["pf_buffer_hit_ratio"] = (
    stride["pf_buffer_hit"] / stride["pf_identified"].replace(0, pd.NA)
)

stride["prefetcher_read_rate"] = stride.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_rate",
        "l2_prefetcher_read_rate",
    ),
    axis=1,
)

stride["prefetcher_read_bytes"] = stride.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_bytes",
        "l2_prefetcher_read_bytes",
    ),
    axis=1,
)


# DRAM bandwidth utilization, if available.
if "dram_bw_total" in stride.columns and "dram_peak_bw" in stride.columns:
    stride["dram_bw_utilization"] = (
        stride["dram_bw_total"] / (stride["dram_peak_bw"] * 1024 * 1024)
    )


stride.to_csv(OUT, index=False)

winners = (
    stride.sort_values("speedup_vs_nopf", ascending=False)
    .groupby(["benchmark", "pf_level", "memory"], as_index=False)
    .first()
)

winners.to_csv(WINNERS, index=False)

print(f"Wrote {OUT}")
print(f"Wrote {WINNERS}")
print()
print("Stride winners vs no-prefetch baseline:")
print(
    winners[
        [
            "benchmark",
            "pf_level",
            "memory",
            "config",
            "speedup_vs_nopf",
            "pf_accuracy",
            "pf_coverage",
            "pf_unused_ratio",
            "pf_late_ratio",
        ]
    ].to_string(index=False)
)