import pandas as pd

NEXTLINE = "nextline_results.csv"
NOPF = "../baseline/nopf_results.csv"

OUT = "nextline_results_vs_nopf.csv"
WINNERS = "nextline_winners_vs_nopf_per_case.csv"

nextline = pd.read_csv(NEXTLINE)
nopf = pd.read_csv(NOPF)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

nextline = nextline.merge(base, on=["benchmark", "memory"], how="left")

nextline["speedup_vs_nopf"] = nextline["nopf_simSeconds"] / nextline["simSeconds"]

nextline["pf_issued"] = nextline["l1d_pf_issued"].fillna(0) + nextline["l2_pf_issued"].fillna(0)
nextline["pf_useful"] = nextline["l1d_pf_useful"].fillna(0) + nextline["l2_pf_useful"].fillna(0)
nextline["pf_unused"] = nextline["l1d_pf_unused"].fillna(0) + nextline["l2_pf_unused"].fillna(0)

nextline["pf_accuracy"] = nextline["pf_useful"] / nextline["pf_issued"].replace(0, pd.NA)
nextline["pf_unused_ratio"] = nextline["pf_unused"] / nextline["pf_issued"].replace(0, pd.NA)

nextline["l1d_miss_rate"] = nextline["l1d_demand_misses"] / nextline["l1d_demand_accesses"].replace(0, pd.NA)
nextline["l2_miss_rate"] = nextline["l2_demand_misses"] / nextline["l2_demand_accesses"].replace(0, pd.NA)

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
            "pf_unused_ratio",
        ]
    ].to_string(index=False)
)