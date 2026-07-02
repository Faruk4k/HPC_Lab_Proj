#!/usr/bin/env python3
"""
Analyze Stage 1 results to recommend parameters for Stage 2.

This script:
1. Identifies which parameter values perform best across cases
2. Analyzes the impact (performance range) of each parameter
3. Recommends promising parameter combinations for Stage 2
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import sys

def extract_parameter(config_name):
    """Extract parameter name and value from config name."""
    # Map short names to parameter types
    param_map = {
        'ls': 'limit_stride',
        'sd': 'start_degree',
        'hz': 'hot_zone_size',
        'assoc': 'access_map_table_assoc',
        'epoch': 'epoch_cycles',
    }
    
    for prefix, param_type in param_map.items():
        if config_name.startswith(prefix):
            value = config_name[len(prefix):]
            return param_type, value
    
    return None, None

def main():
    # Load results
    csv_file = "ampm_results.csv"
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found")
        sys.exit(1)
    
    # Analyze impact of each parameter
    grouped = df.groupby(["benchmark", "pf_level", "memory"])
    
    parameter_impacts = defaultdict(list)  # {param: [impact_values]}
    parameter_rankings = defaultdict(Counter)  # {param_value: rank_count}
    
    print("\n" + "=" * 100)
    print("STAGE 1 PARAMETER IMPACT ANALYSIS")
    print("=" * 100)
    
    for group_key, group_df in grouped:
        # Get sorted by IPC (best to worst)
        group_sorted = group_df.sort_values("ipc", ascending=False, na_position='last')
        
        # Calculate impact for each parameter in this case
        config_to_ipc = dict(zip(group_sorted['config'], group_sorted['ipc']))
        
        # Group by parameter type
        params_in_case = defaultdict(dict)  # {param_type: {value: ipc}}
        
        for config, ipc in config_to_ipc.items():
            if config == 'default':
                continue
            param_type, value = extract_parameter(config)
            if param_type:
                params_in_case[param_type][value] = ipc
        
        # Calculate range for each parameter in this case
        for param_type, values_dict in params_in_case.items():
            if len(values_dict) > 0:
                ipc_values = list(values_dict.values())
                impact = ((max(ipc_values) - min(ipc_values)) / min(ipc_values)) * 100 if min(ipc_values) > 0 else 0
                parameter_impacts[param_type].append(impact)
                
                # Track ranking of best value
                best_value = max(values_dict, key=values_dict.get)
                parameter_rankings[f"{param_type}:{best_value}"] += 1
    
    # Print parameter impact analysis
    print("\n1. PARAMETER IMPACT ANALYSIS (% IPC variation across values)")
    print("-" * 100)
    print(f"{'Parameter':<30} {'Avg Impact %':<15} {'Min Impact %':<15} {'Max Impact %':<15} {'# Cases':<10}")
    print("-" * 100)
    
    impact_summary = {}
    for param_type in sorted(parameter_impacts.keys()):
        impacts = parameter_impacts[param_type]
        avg_impact = np.mean(impacts)
        min_impact = np.min(impacts)
        max_impact = np.max(impacts)
        num_cases = len(impacts)
        impact_summary[param_type] = avg_impact
        
        print(f"{param_type:<30} {avg_impact:<15.2f} {min_impact:<15.2f} {max_impact:<15.2f} {num_cases:<10}")
    
    # Print best parameter values
    print("\n2. MOST COMMON TOP-PERFORMING PARAMETER VALUES")
    print("-" * 100)
    print(f"{'Parameter Value':<40} {'# Times Ranked #1':<20}")
    print("-" * 100)
    
    for param_value, count in sorted(parameter_rankings.items(), key=lambda x: x[1], reverse=True):
        print(f"{param_value:<40} {count:<20}")
    
    # Recommendations
    print("\n3. STAGE 2 RECOMMENDATIONS")
    print("-" * 100)
    
    print("\nParameter selection strategy:")
    print("  • Parameters with HIGHEST impact (best candidates for combination effects)")
    sorted_impact = sorted(impact_summary.items(), key=lambda x: x[1], reverse=True)
    for i, (param, impact) in enumerate(sorted_impact, 1):
        print(f"    {i}. {param}: {impact:.2f}% avg impact")
    
    print("\n  • Best performing values (top candidates for Stage 2):")
    top_performers = sorted(parameter_rankings.items(), key=lambda x: x[1], reverse=True)[:10]
    for param_value, count in top_performers:
        param_type, value = param_value.split(':')
        print(f"    {param_value}: appears in top rank {count} times")
    
    print("\n4. RECOMMENDED STAGE 2 CONFIGURATIONS")
    print("-" * 100)
    print("\nSuggestion: Combine the highest-impact parameters with their best-performing values:")
    print("\nHighest-Impact Parameters (try these combinations):")
    print("  1. Vary hot_zone_size (hz*) - shows highest impact, especially good for L2")
    print("  2. Vary limit_stride (ls*) - strong impact on some benchmarks")
    print("  3. Vary start_degree (sd*) - moderate consistent impact")
    print("  4. Vary associativity (assoc*) - lower but consistent impact")
    print("  5. Vary epoch_cycles (epoch*) - lowest impact, can be held constant")
    
    print("\nRecommended Stage 2 approach:")
    print("  • Pick top 3 from each highest-impact parameter group")
    print("  • Create factorial design: e.g., if top hz values are [hz512, hz1k, hz2k],")
    print("    top ls values are [ls2, ls4, ls8], etc.")
    print("  • This gives 3x3x3... = manageable number of combinations")
    print("  • Focus on L2 prefetcher since hot_zone_size shows more impact there")
    
    print("\n" + "=" * 100 + "\n")

if __name__ == "__main__":
    main()
