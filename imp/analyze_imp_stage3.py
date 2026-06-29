import pandas as pd

STAGE3 = "imp_stage3_results.csv"
NOPF = "../baseline/nopf_results.csv"
STAGE2 = "imp_stage2_with_comparison.csv"

OUT_ALL = "imp_stage3_with_comparison.csv"
OUT_WINNERS = "imp_stage3_winners_per_case.csv"
OUT_STAGE3_BEATS_STAGE2 = "imp_stage3_beats_stage2_best.csv"

s3 = pd.read_csv(STAGE3)
nopf = pd.read_csv(NOPF)
s2 = pd.read_csv(STAGE2)

base = nopf[["benchmark", "memory", "simSeconds"]].rename(
    columns={"simSeconds": "nopf_simSeconds"}
)

s3 = s3.merge(base, on=["benchmark", "memory"], how="left")
s3["speedup_vs_nopf"] = s3["nopf_simSeconds"] / s3["simSeconds"]

s3["pf_issued"] = s3["l1d_pf_issued"].fillna(0) + s3["l2_pf_issued"].fillna(0)
s3["pf_useful"] = s3["l1d_pf_useful"].fillna(0) + s3["l2_pf_useful"].fillna(0)
s3["pf_unused"] = s3["l1d_pf_unused"].fillna(0) + s3["l2_pf_unused"].fillna(0)

s3["pf_accuracy"] = s3["pf_useful"] / s3["pf_issued"].replace(0, pd.NA)
s3["pf_unused_ratio"] = s3["pf_unused"] / s3["pf_issued"].replace(0, pd.NA)

s3["l1d_miss_rate"] = s3["l1d_demand_misses"] / s3["l1d_demand_accesses"].replace(0, pd.NA)
s3["l2_miss_rate"] = s3["l2_demand_misses"] / s3["l2_demand_accesses"].replace(0, pd.NA)

if "speedup_vs_nopf" not in s2.columns:
    s2 = s2.merge(base, on=["benchmark", "memory"], how="left")
    s2["speedup_vs_nopf"] = s2["nopf_simSeconds"] / s2["simSeconds"]

s2_best = (
    s2[s2["config"] != "default"]
    .sort_values("speedup_vs_nopf", ascending=False)
    .groupby(["benchmark", "pf_level", "memory"], as_index=False)
    .first()
)

s2_best = s2_best[
    ["benchmark", "pf_level", "memory", "config", "simSeconds", "speedup_vs_nopf"]
].rename(
    columns={
        "config": "stage2_best_config",
        "simSeconds": "stage2_best_simSeconds",
        "speedup_vs_nopf": "stage2_best_speedup_vs_nopf",
    }
)

s3 = s3.merge(s2_best, on=["benchmark", "pf_level", "memory"], how="left")
s3["speedup_vs_stage2_best"] = s3["stage2_best_simSeconds"] / s3["simSeconds"]
s3["improvement_over_stage2_best_pct"] = (s3["speedup_vs_stage2_best"] - 1.0) * 100.0

s3.to_csv(OUT_ALL, index=False)

winners = (
    s3.sort_values("speedup_vs_nopf", ascending=False)
    .groupby(["benchmark", "pf_level", "memory"], as_index=False)
    .first()
)

winners.to_csv(OUT_WINNERS, index=False)

beats = winners[winners["speedup_vs_stage2_best"] > 1.01].copy()
beats.to_csv(OUT_STAGE3_BEATS_STAGE2, index=False)

print(f"Wrote {OUT_ALL}")
print(f"Wrote {OUT_WINNERS}")
print(f"Wrote {OUT_STAGE3_BEATS_STAGE2}")
print("Cases where Stage 3 beats Stage 2 best by >1%:", len(beats))