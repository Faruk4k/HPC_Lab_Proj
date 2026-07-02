import pandas as pd
import math

NEXTLINE = "nextline_results.csv"
NOPF = "../baseline/nopf_results.csv"

OUT = "nextline_results_vs_nopf.csv"
WINNERS = "nextline_winners_vs_nopf_per_case.csv"

nextline = pd.read_csv(NEXTLINE)
nopf = pd.read_csv(NOPF)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

# Avoid duplicate nopf columns if the script is rerun on already-merged data.
nextline = nextline.drop(
    columns=["nopf_simSeconds", "nopf_simSeconds_x", "nopf_simSeconds_y"],
    errors="ignore",
)

nextline = nextline.merge(base, on=["benchmark", "memory"], how="left")
nextline["speedup_vs_nopf"] = nextline["nopf_simSeconds"] / nextline["simSeconds"]


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


# Required basic columns
for col in [
    "l1d_pf_issued", "l1d_pf_useful", "l1d_pf_unused",
    "l2_pf_issued", "l2_pf_useful", "l2_pf_unused",
    "l1d_demand_misses", "l1d_demand_accesses",
    "l2_demand_misses", "l2_demand_accesses",
]:
    ensure_col(nextline, col)

# Effective prefetch stats based on placement
nextline["pf_issued"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_issued", "l2_pf_issued"),
    axis=1,
)

nextline["pf_useful"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_useful", "l2_pf_useful"),
    axis=1,
)

nextline["pf_unused"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_unused", "l2_pf_unused"),
    axis=1,
)

nextline["pf_accuracy"] = (
    nextline["pf_useful"] / nextline["pf_issued"].replace(0, pd.NA)
)

nextline["pf_unused_ratio"] = (
    nextline["pf_unused"] / nextline["pf_issued"].replace(0, pd.NA)
)

nextline["l1d_miss_rate"] = (
    nextline["l1d_demand_misses"] / nextline["l1d_demand_accesses"].replace(0, pd.NA)
)

nextline["l2_miss_rate"] = (
    nextline["l2_demand_misses"] / nextline["l2_demand_accesses"].replace(0, pd.NA)
)

# Coverage approximation at the installed prefetcher level
def coverage(row):
    if row["pf_level"] == "l1d":
        misses = row.get("l1d_demand_misses", math.nan)
    elif row["pf_level"] == "l2":
        misses = row.get("l2_demand_misses", math.nan)
    else:
        misses = math.nan

    useful = row.get("pf_useful", math.nan)

    if pd.isna(useful) or pd.isna(misses) or useful + misses == 0:
        return math.nan

    return useful / (useful + misses)


nextline["pf_coverage"] = nextline.apply(coverage, axis=1)

# Extra prefetch stats, if extract_nextline_results.py contains them
for col in [
    "l1d_pf_late", "l2_pf_late",
    "l1d_pf_removed_full", "l2_pf_removed_full",
    "l1d_pf_removed_demand", "l2_pf_removed_demand",
    "l1d_pf_buffer_hit", "l2_pf_buffer_hit",
    "l1d_pf_identified", "l2_pf_identified",
    "l1d_prefetcher_read_rate", "l2_prefetcher_read_rate",
    "l1d_prefetcher_read_bytes", "l2_prefetcher_read_bytes",
]:
    ensure_col(nextline, col)

nextline["pf_late"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_late", "l2_pf_late"),
    axis=1,
)

nextline["pf_late_ratio"] = (
    nextline["pf_late"] / nextline["pf_issued"].replace(0, pd.NA)
)

nextline["pf_removed_full"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_full", "l2_pf_removed_full"),
    axis=1,
)

nextline["pf_removed_demand"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_demand", "l2_pf_removed_demand"),
    axis=1,
)

nextline["pf_buffer_hit"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_buffer_hit", "l2_pf_buffer_hit"),
    axis=1,
)

nextline["pf_identified"] = nextline.apply(
    lambda r: effective_by_level(r, "l1d_pf_identified", "l2_pf_identified"),
    axis=1,
)

nextline["pf_removed_full_ratio"] = (
    nextline["pf_removed_full"] / nextline["pf_identified"].replace(0, pd.NA)
)

nextline["pf_removed_demand_ratio"] = (
    nextline["pf_removed_demand"] / nextline["pf_identified"].replace(0, pd.NA)
)

nextline["pf_buffer_hit_ratio"] = (
    nextline["pf_buffer_hit"] / nextline["pf_identified"].replace(0, pd.NA)
)

nextline["prefetcher_read_rate"] = nextline.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_rate",
        "l2_prefetcher_read_rate",
    ),
    axis=1,
)

nextline["prefetcher_read_bytes"] = nextline.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_bytes",
        "l2_prefetcher_read_bytes",
    ),
    axis=1,
)

# DRAM bandwidth utilization, if available
if "dram_bw_total" in nextline.columns and "dram_peak_bw" in nextline.columns:
    nextline["dram_bw_utilization"] = (
        nextline["dram_bw_total"] / (nextline["dram_peak_bw"] * 1024 * 1024)
    )

nextline.to_csv(OUT, index=False)

winners = (
    nextline.sort_values("speedup_vs_nopf", ascending=False)
    .groupby(["benchmark", "pf_level", "memory"], as_index=False)
    .first()
)

winners.to_csv(WINNERS, index=False)

print(f"Wrote {OUT}")
print(f"Wrote {WINNERS}")
print()
print("Next-line winners vs no-prefetch baseline:")
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