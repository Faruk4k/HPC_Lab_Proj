import pandas as pd
import math

AMPM = "ampm_results.csv"
NOPF = "../baseline/nopf_results.csv"

OUT = "ampm_results_vs_nopf.csv"
WINNERS = "ampm_winners_vs_nopf_per_case.csv"

ampm = pd.read_csv(AMPM)
nopf = pd.read_csv(NOPF)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

# Avoid duplicate nopf columns if the script is rerun on already-merged data.
ampm = ampm.drop(
    columns=["nopf_simSeconds", "nopf_simSeconds_x", "nopf_simSeconds_y"],
    errors="ignore",
)

ampm = ampm.merge(base, on=["benchmark", "memory"], how="left")
ampm["speedup_vs_nopf"] = ampm["nopf_simSeconds"] / ampm["simSeconds"]


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
    ensure_col(ampm, col)


# Effective prefetch stats based on placement
ampm["pf_issued"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_issued", "l2_pf_issued"),
    axis=1,
)

ampm["pf_useful"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_useful", "l2_pf_useful"),
    axis=1,
)

ampm["pf_unused"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_unused", "l2_pf_unused"),
    axis=1,
)

ampm["pf_accuracy"] = (
    ampm["pf_useful"] / ampm["pf_issued"].replace(0, pd.NA)
)

ampm["pf_unused_ratio"] = (
    ampm["pf_unused"] / ampm["pf_issued"].replace(0, pd.NA)
)

ampm["l1d_miss_rate"] = (
    ampm["l1d_demand_misses"] / ampm["l1d_demand_accesses"].replace(0, pd.NA)
)

ampm["l2_miss_rate"] = (
    ampm["l2_demand_misses"] / ampm["l2_demand_accesses"].replace(0, pd.NA)
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


ampm["pf_coverage"] = ampm.apply(coverage, axis=1)


# Extra prefetch stats, if extract_ampm_results.py contains them
for col in [
    "l1d_pf_late", "l2_pf_late",
    "l1d_pf_removed_full", "l2_pf_removed_full",
    "l1d_pf_removed_demand", "l2_pf_removed_demand",
    "l1d_pf_buffer_hit", "l2_pf_buffer_hit",
    "l1d_pf_identified", "l2_pf_identified",
    "l1d_prefetcher_read_rate", "l2_prefetcher_read_rate",
    "l1d_prefetcher_read_bytes", "l2_prefetcher_read_bytes",
]:
    ensure_col(ampm, col)


ampm["pf_late"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_late", "l2_pf_late"),
    axis=1,
)

ampm["pf_late_ratio"] = (
    ampm["pf_late"] / ampm["pf_issued"].replace(0, pd.NA)
)

ampm["pf_removed_full"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_full", "l2_pf_removed_full"),
    axis=1,
)

ampm["pf_removed_demand"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_removed_demand", "l2_pf_removed_demand"),
    axis=1,
)

ampm["pf_buffer_hit"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_buffer_hit", "l2_pf_buffer_hit"),
    axis=1,
)

ampm["pf_identified"] = ampm.apply(
    lambda r: effective_by_level(r, "l1d_pf_identified", "l2_pf_identified"),
    axis=1,
)

ampm["pf_removed_full_ratio"] = (
    ampm["pf_removed_full"] / ampm["pf_identified"].replace(0, pd.NA)
)

ampm["pf_removed_demand_ratio"] = (
    ampm["pf_removed_demand"] / ampm["pf_identified"].replace(0, pd.NA)
)

ampm["pf_buffer_hit_ratio"] = (
    ampm["pf_buffer_hit"] / ampm["pf_identified"].replace(0, pd.NA)
)

ampm["prefetcher_read_rate"] = ampm.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_rate",
        "l2_prefetcher_read_rate",
    ),
    axis=1,
)

ampm["prefetcher_read_bytes"] = ampm.apply(
    lambda r: effective_by_level(
        r,
        "l1d_prefetcher_read_bytes",
        "l2_prefetcher_read_bytes",
    ),
    axis=1,
)


# DRAM bandwidth utilization, if available
if "dram_bw_total" in ampm.columns and "dram_peak_bw" in ampm.columns:
    ampm["dram_bw_utilization"] = (
        ampm["dram_bw_total"] / (ampm["dram_peak_bw"] * 1024 * 1024)
    )


ampm.to_csv(OUT, index=False)

winners = (
    ampm.sort_values("speedup_vs_nopf", ascending=False)
    .groupby(["benchmark", "pf_level", "memory"], as_index=False)
    .first()
)

winners.to_csv(WINNERS, index=False)

print(f"Wrote {OUT}")
print(f"Wrote {WINNERS}")
print()
print("AMPM winners vs no-prefetch baseline:")
print(
    winners[
        [
            "benchmark",
            "pf_level",
            "memory",
            "stage",
            "config",
            "speedup_vs_nopf",
            "pf_accuracy",
            "pf_coverage",
            "pf_unused_ratio",
            "pf_late_ratio",
        ]
    ].to_string(index=False)
)