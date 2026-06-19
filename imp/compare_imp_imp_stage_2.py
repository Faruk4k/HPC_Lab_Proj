import pandas as pd

w = pd.read_csv("imp_stage2_winners_per_case.csv")
print("WINNERS PER CASE")
print(w[[
    "benchmark", "pf_level", "memory", "config",
    "speedup_vs_imp_default", "stage1_best_config",
    "stage1_best_speedup", "speedup_vs_stage1_best",
    "pf_accuracy", "pf_unused_ratio"
]].to_string(index=False))

print("\nCONFIG MEAN SPEEDUP")
df = pd.read_csv("imp_stage2_with_comparison.csv")
print(df.groupby("config")["speedup_vs_imp_default"].mean().sort_values(ascending=False).head(15).to_string())

print("\nCONFIG MEAN SPEEDUP VS STAGE1 BEST")
print(df.groupby("config")["speedup_vs_stage1_best"].mean().sort_values(ascending=False).head(15).to_string())
