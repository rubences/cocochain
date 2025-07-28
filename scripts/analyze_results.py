#!/usr/bin/env python3
"""
CoCoChain Simulation Result Analysis Script
Processes simulation results and generates table format for research paper
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from pathlib import Path

def parse_scalar_file(filepath):
    """Parse OMNeT++ scalar result file"""
    results = {}
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('scalar'):
                    parts = line.split()
                    if len(parts) >= 4:
                        module = parts[1]
                        metric = parts[2]
                        value = float(parts[3])
                        
                        if module not in results:
                            results[module] = {}
                        results[module][metric] = value
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return results

def parse_vector_file(filepath):
    """Parse OMNeT++ vector result file"""
    vectors = {}
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('vector'):
                    parts = line.split()
                    if len(parts) >= 5:
                        vector_id = parts[1]
                        module = parts[2]
                        metric = parts[3]
                        
                        if module not in vectors:
                            vectors[module] = {}
                        if metric not in vectors[module]:
                            vectors[module][metric] = []
                        
                elif line and not line.startswith('#'):
                    # Vector data line: vectorId time value
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            value = float(parts[2])
                            # For simplicity, we'll just collect all values
                            # In practice, you'd want to organize by vector_id
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return vectors

def analyze_results():
    """Analyze simulation results and generate summary table"""
    
    # Look for result files
    result_dir = Path("../results")
    if not result_dir.exists():
        print("Results directory not found. Please run simulation first.")
        return
    
    # Find all scalar and vector files
    scalar_files = glob.glob(str(result_dir / "*.sca"))
    vector_files = glob.glob(str(result_dir / "*.vec"))
    
    if not scalar_files and not vector_files:
        print("No result files found. Please run simulation first.")
        return
    
    # Aggregate results across all runs
    all_latencies = []
    all_overhead = []
    all_malformed = []
    
    run_results = []
    
    for scalar_file in scalar_files:
        results = parse_scalar_file(scalar_file)
        
        # Extract key metrics
        latency_values = []
        overhead_total = 0
        malformed_total = 0
        
        for module, metrics in results.items():
            if 'endToEndLatency:mean' in metrics:
                latency_values.append(metrics['endToEndLatency:mean'])
            if 'consensusOverhead:sum' in metrics:
                overhead_total += metrics['consensusOverhead:sum']
            if 'malformedDetected:sum' in metrics:
                malformed_total += metrics['malformedDetected:sum']
        
        if latency_values:
            avg_latency = np.mean(latency_values)
            all_latencies.extend(latency_values)
        else:
            avg_latency = 0
        
        all_overhead.append(overhead_total)
        all_malformed.append(malformed_total)
        
        run_results.append({
            'avg_latency': avg_latency,
            'total_overhead': overhead_total,
            'malformed_detected': malformed_total
        })
    
    # Calculate statistics
    if all_latencies:
        latency_mean = np.mean(all_latencies)
        latency_std = np.std(all_latencies)
    else:
        latency_mean = latency_std = 0
    
    overhead_mean = np.mean(all_overhead) if all_overhead else 0
    overhead_std = np.std(all_overhead) if all_overhead else 0
    
    malformed_mean = np.mean(all_malformed) if all_malformed else 0
    malformed_std = np.std(all_malformed) if all_malformed else 0
    
    # Generate research paper table
    print("\n" + "="*60)
    print("CoCoChain Simulation Results - Scenario 1")
    print("High-density Urban Network (500 vehicles/km²)")
    print("="*60)
    
    print(f"\nNetwork Configuration:")
    print(f"- Topology: 4×4 grid, 5 km²")
    print(f"- Vehicles: 2500 (500/km²)")
    print(f"- Message interval: 1.5s")
    print(f"- Corruption rate: 10%")
    print(f"- Simulation runs: {len(run_results)}")
    
    print(f"\nResults Summary:")
    print(f"{'Metric':<35} {'Mean':<15} {'Std Dev':<15}")
    print("-" * 65)
    print(f"{'End-to-end latency (s)':<35} {latency_mean:<15.4f} {latency_std:<15.4f}")
    print(f"{'Consensus overhead (msgs)':<35} {overhead_mean:<15.2f} {overhead_std:<15.2f}")
    print(f"{'Malformed detected (count)':<35} {malformed_mean:<15.2f} {malformed_std:<15.2f}")
    
    # Generate LaTeX table for research paper
    print(f"\nLaTeX Table Format:")
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{CoCoChain Performance in High-density Urban Network}")
    print("\\begin{tabular}{|l|c|c|}")
    print("\\hline")
    print("\\textbf{Metric} & \\textbf{Mean} & \\textbf{Std Dev} \\\\")
    print("\\hline")
    print(f"End-to-end latency (s) & {latency_mean:.4f} & {latency_std:.4f} \\\\")
    print(f"Consensus overhead (msgs) & {overhead_mean:.0f} & {overhead_std:.0f} \\\\")
    print(f"Malformed detected & {malformed_mean:.0f} & {malformed_std:.0f} \\\\")
    print("\\hline")
    print("\\end{tabular}")
    print("\\label{tab:cocochain_scenario1}")
    print("\\end{table}")
    
    # Save detailed results to CSV
    if run_results:
        df = pd.DataFrame(run_results)
        df.to_csv('cocochain_scenario1_results.csv', index=False)
        print(f"\nDetailed results saved to: cocochain_scenario1_results.csv")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    analyze_results()