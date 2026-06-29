import pandas as pd

STRIDE = "stride_results.csv"
NOPF = "../baseline/nopf_results.csv"

OUT = "stride_results_vs_nopf.csv"
WINNERS = "stride_winners_vs_nopf_per_case.csv"

stride = pd.read_csv(STRIDE)
nopf = pd.read_csv(NOPF)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

stride = stride.merge(base, on=["benchmark", "memory"], how="left")

stride["speedup_vs_nopf"] = stride["nopf_simSeconds"] / stride["simSeconds"]

stride["pf_issued"] = stride["l1d_pf_issued"].fillna(0) + stride["l2_pf_issued"].fillna(0)
stride["pf_useful"] = stride["l1d_pf_useful"].fillna(0) + stride["l2_pf_useful"].fillna(0)
stride["pf_unused"] = stride["l1d_pf_unused"].fillna(0) + stride["l2_pf_unused"].fillna(0)

stride["pf_accuracy"] = stride["pf_useful"] / stride["pf_issued"].replace(0, pd.NA)
stride["pf_unused_ratio"] = stride["pf_unused"] / stride["pf_issued"].replace(0, pd.NA)

stride["l1d_miss_rate"] = stride["l1d_demand_misses"] / stride["l1d_demand_accesses"].replace(0, pd.NA)
stride["l2_miss_rate"] = stride["l2_demand_misses"] / stride["l2_demand_accesses"].replace(0, pd.NA)

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
            "pf_unused_ratio",
        ]
    ].to_string(index=False)
)