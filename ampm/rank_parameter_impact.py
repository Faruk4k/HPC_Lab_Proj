#!/usr/bin/env python3
"""
Rank the impact of AMPM parameter values on performance.

For each combination of (benchmark, pf_level, memory), this script:
1. Extracts the different parameter configurations tested
2. Calculates performance metrics for each configuration
3. Ranks them by performance impact (IPC and simSeconds)
4. Outputs a detailed report showing the rankings
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import sys

def main():
    # Load the results CSV
    csv_file = "ampm_results_stage1_stage2.csv"
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found")
        sys.exit(1)
    
    # Performance metrics to track (higher IPC is better, lower simSeconds is better)
    ipc_col = "ipc"
    simseconds_col = "simSeconds"
    
    # Group by (benchmark, pf_level, memory)
    grouped = df.groupby(["benchmark", "pf_level", "memory"])

    with open(f"{csv_file}_ranked.txt", "w") as report_file:
    
        total_cases = len(grouped)
        print(f"Found {total_cases} unique cases (benchmark, pf_level, memory combinations)\n")
        print("=" * 100)
        report_file.write(f"Found {total_cases} unique cases (benchmark, pf_level, memory combinations)\n\n")
        report_file.write("=" * 100 + "\n")
        
        for case_num, (group_key, group_df) in enumerate(grouped, 1):
            benchmark, pf_level, memory = group_key
            print(f"\n[Case {case_num}/{total_cases}] Benchmark: {benchmark}, Prefetcher Level: {pf_level}, Memory: {memory}")
            print("-" * 100)
            report_file.write(f"\n[Case {case_num}/{total_cases}] Benchmark: {benchmark}, Prefetcher Level: {pf_level}, Memory: {memory}\n")
            report_file.write("-" * 100 + "\n")
            
            # Sort by IPC (descending - higher is better)
            group_sorted = group_df.sort_values(ipc_col, ascending=False, na_position='last')
            
            # Calculate baseline (default config if it exists, otherwise the best config)
            baseline_config = None
            baseline_ipc = None
            baseline_simseconds = None
            
            default_row = group_df[group_df["config"] == "default"]
            if not default_row.empty:
                baseline_config = "default"
                baseline_ipc = default_row[ipc_col].values[0]
                baseline_simseconds = default_row[simseconds_col].values[0]
            
            print(f"\n{'Rank':<6} {'Config':<20} {'IPC':<12} {'Speedup vs Baseline':<20} {'simSeconds':<15}")
            print("-" * 100)
            report_file.write(f"\n{'Rank':<6} {'Config':<20} {'IPC':<12} {'Speedup vs Baseline':<20} {'simSeconds':<15}\n")
            report_file.write("-" * 100 + "\n")
            
            for rank, (idx, row) in enumerate(group_sorted.iterrows(), 1):
                config = row["config"]
                ipc = row[ipc_col]
                simseconds = row[simseconds_col]
                
                # Calculate speedup relative to baseline
                if baseline_ipc is not None and not np.isnan(baseline_ipc):
                    speedup = ipc / baseline_ipc if not np.isnan(ipc) else np.nan
                else:
                    speedup = np.nan
                
                # Format speedup string
                if np.isnan(speedup):
                    speedup_str = "N/A"
                else:
                    speedup_pct = (speedup - 1) * 100
                    speedup_str = f"{speedup:.4f}x ({speedup_pct:+.2f}%)"
                
                # Mark if this is the baseline
                baseline_marker = " [BASELINE]" if config == baseline_config else ""
                
                print(f"{rank:<6} {config:<20} {ipc:<12.6f} {speedup_str:<20} {simseconds:<15.6e}{baseline_marker}")
                report_file.write(f"{rank:<6} {config:<20} {ipc:<12.6f} {speedup_str:<20} {simseconds:<15.6e}{baseline_marker}\n")
            
            # Summary statistics
            print(f"\n{'Summary:'}")
            print(f"  Best IPC: {group_sorted[ipc_col].max():.6f} (config: {group_sorted[ipc_col].idxmax()})")
            print(f"  Worst IPC: {group_sorted[ipc_col].min():.6f}")
            print(f"  IPC Std Dev: {group_sorted[ipc_col].std():.6f}")
            print(f"  Best simSeconds: {group_sorted[simseconds_col].min():.6e}")
            print(f"  Worst simSeconds: {group_sorted[simseconds_col].max():.6e}")

            report_file.write(f"\n{'Summary:'}\n")
            report_file.write(f"  Best IPC: {group_sorted[ipc_col].max():.6f} (config: {group_sorted[ipc_col].idxmax()})\n")
            report_file.write(f"  Worst IPC: {group_sorted[ipc_col].min():.6f}\n")
            report_file.write(f"  IPC Std Dev: {group_sorted[ipc_col].std  ():.6f}\n")
            report_file.write(f"  Best simSeconds: {group_sorted[simseconds_col].min():.6e}\n")
            report_file.write(f"  Worst simSeconds: {group_sorted[simseconds_col].max():.6e}\n")
            
            # Calculate the impact range
            ipc_impact = ((group_sorted[ipc_col].max() - group_sorted[ipc_col].min()) / group_sorted[ipc_col].min()) * 100
            simseconds_impact = ((group_sorted[simseconds_col].max() - group_sorted[simseconds_col].min()) / group_sorted[simseconds_col].min()) * 100
            
            print(f"  IPC improvement range: {ipc_impact:.2f}%")
            print(f"  simSeconds reduction range: {simseconds_impact:.2f}%")
            print()

            report_file.write(f"  IPC improvement range: {ipc_impact:.2f}%\n")
            report_file.write(f"  simSeconds reduction range: {simseconds_impact:.2f}%\n")


if __name__ == "__main__":
    main()
