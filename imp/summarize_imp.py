import pandas as pd

df = pd.read_csv("imp_results.csv")

key = ["benchmark", "pf_level", "memory"]

default = (
    df[df["config"] == "default"][key + ["simSeconds"]]
    .rename(columns={"simSeconds": "default_simSeconds"})
)

out = df.merge(default, on=key, how="left")
out["speedup_vs_imp_default"] = out["default_simSeconds"] / out["simSeconds"]

# miss rates
out["l1d_miss_rate"] = out["l1d_demand_misses"] / out["l1d_demand_accesses"]
out["l2_miss_rate"] = out["l2_demand_misses"] / out["l2_demand_accesses"]

# prefetch accuracy
out["pf_issued"] = out["l1d_pf_issued"].fillna(0) + out["l2_pf_issued"].fillna(0)
out["pf_useful"] = out["l1d_pf_useful"].fillna(0) + out["l2_pf_useful"].fillna(0)
out["pf_unused"] = out["l1d_pf_unused"].fillna(0) + out["l2_pf_unused"].fillna(0)
out["pf_accuracy"] = out["pf_useful"] / out["pf_issued"].replace(0, pd.NA)
out["pf_coverage_l1d"] = out["pf_useful"] / out["l1d_demand_misses"].replace(0, pd.NA)
out["pf_unused_ratio"] = out["pf_unused"] / out["pf_issued"].replace(0, pd.NA)

out.to_csv("imp_results_with_speedup.csv", index=False)

best = (
    out.sort_values("speedup_vs_imp_default", ascending=False)
    .groupby(key)
    .head(5)
)

best.to_csv("imp_best_top5_per_case.csv", index=False)

summary = (
    out.groupby(["config", "pf_level", "memory"])["speedup_vs_imp_default"]
    .agg(["count", "mean", "median", "min", "max"])
    .reset_index()
    .sort_values("mean", ascending=False)
)

summary.to_csv("imp_config_summary.csv", index=False)

print("Wrote:")
print("  imp_results_with_speedup.csv")
print("  imp_best_top5_per_case.csv")
print("  imp_config_summary.csv")
