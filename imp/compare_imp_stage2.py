import pandas as pd

stage1 = pd.read_csv("imp_results_with_speedup.csv")
stage2 = pd.read_csv("imp_stage2_results.csv")

key = ["benchmark", "pf_level", "memory"]

# Stage 1 default baseline
default = (
    stage1[stage1["config"] == "default"][key + ["simSeconds"]]
    .rename(columns={"simSeconds": "imp_default_simSeconds"})
)

# Stage 1 best single-factor baseline
stage1_best = (
    stage1.sort_values("speedup_vs_imp_default", ascending=False)
    .groupby(key)
    .head(1)[key + ["config", "simSeconds", "speedup_vs_imp_default"]]
    .rename(columns={
        "config": "stage1_best_config",
        "simSeconds": "stage1_best_simSeconds",
        "speedup_vs_imp_default": "stage1_best_speedup",
    })
)

out = stage2.merge(default, on=key, how="left")
out = out.merge(stage1_best, on=key, how="left")

out["speedup_vs_imp_default"] = out["imp_default_simSeconds"] / out["simSeconds"]
out["speedup_vs_stage1_best"] = out["stage1_best_simSeconds"] / out["simSeconds"]

# miss rates
out["l1d_miss_rate"] = out["l1d_demand_misses"] / out["l1d_demand_accesses"].replace(0, pd.NA)
out["l2_miss_rate"] = out["l2_demand_misses"] / out["l2_demand_accesses"].replace(0, pd.NA)

# prefetch stats
out["pf_issued"] = out["l1d_pf_issued"].fillna(0) + out["l2_pf_issued"].fillna(0)
out["pf_useful"] = out["l1d_pf_useful"].fillna(0) + out["l2_pf_useful"].fillna(0)
out["pf_unused"] = out["l1d_pf_unused"].fillna(0) + out["l2_pf_unused"].fillna(0)

out["pf_accuracy"] = out["pf_useful"] / out["pf_issued"].replace(0, pd.NA)
out["pf_unused_ratio"] = out["pf_unused"] / out["pf_issued"].replace(0, pd.NA)
out["pf_coverage_l1d"] = out["pf_useful"] / out["l1d_demand_misses"].replace(0, pd.NA)

out.to_csv("imp_stage2_with_comparison.csv", index=False)

best_stage2 = (
    out.sort_values("speedup_vs_imp_default", ascending=False)
    .groupby(key)
    .head(5)
)

best_stage2.to_csv("imp_stage2_best_top5_per_case.csv", index=False)

winners = (
    out.sort_values("speedup_vs_imp_default", ascending=False)
    .groupby(key)
    .head(1)
)

winners.to_csv("imp_stage2_winners_per_case.csv", index=False)

summary = (
    out.groupby("config")[["speedup_vs_imp_default", "speedup_vs_stage1_best", "pf_accuracy", "pf_unused_ratio"]]
    .agg(["count", "mean", "median", "min", "max"])
)

summary.to_csv("imp_stage2_config_summary.csv")

print("Wrote:")
print("  imp_stage2_with_comparison.csv")
print("  imp_stage2_best_top5_per_case.csv")
print("  imp_stage2_winners_per_case.csv")
print("  imp_stage2_config_summary.csv")
print()
print("Stage 2 rows:", len(out))
print("Stage 2 wins over Stage 1 best:", (out["speedup_vs_stage1_best"] > 1.0).sum())
print("Stage 2 wins over Stage 1 best by >1%:", (out["speedup_vs_stage1_best"] > 1.01).sum())
