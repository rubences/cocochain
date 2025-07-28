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
    all_fpr = []
    all_throughput = []
    
    run_results = []
    
    for scalar_file in scalar_files:
        results = parse_scalar_file(scalar_file)
        
        # Extract key metrics
        latency_values = []
        overhead_total = 0
        malformed_total = 0
        fpr_values = []
        throughput_values = []
        
        for module, metrics in results.items():
            if 'endToEndLatency:mean' in metrics:
                latency_values.append(metrics['endToEndLatency:mean'])
            if 'consensusOverhead:sum' in metrics:
                overhead_total += metrics['consensusOverhead:sum']
            if 'malformedDetected:sum' in metrics:
                malformed_total += metrics['malformedDetected:sum']
            if 'falsePositiveRate:mean' in metrics:
                fpr_values.append(metrics['falsePositiveRate:mean'])
            if 'throughput:mean' in metrics:
                throughput_values.append(metrics['throughput:mean'])
        
        # Calculate averages
        avg_latency = np.mean(latency_values) if latency_values else 0
        avg_fpr = np.mean(fpr_values) if fpr_values else 0
        avg_throughput = np.mean(throughput_values) if throughput_values else 0
        
        all_latencies.extend(latency_values)
        all_overhead.append(overhead_total)
        all_malformed.append(malformed_total)
        all_fpr.extend(fpr_values)
        all_throughput.extend(throughput_values)
        
        run_results.append({
            'avg_latency': avg_latency,
            'total_overhead': overhead_total,
            'malformed_detected': malformed_total,
            'false_positive_rate': avg_fpr,
            'throughput': avg_throughput
        })
    
    # Calculate statistics with 95% confidence intervals
    def calc_stats_with_ci(data):
        if not data:
            return 0, 0, 0, 0
        mean = np.mean(data)
        std = np.std(data)
        n = len(data)
        # 95% CI using t-distribution approximation
        ci_margin = 1.96 * std / np.sqrt(n) if n > 1 else 0
        ci_lower = mean - ci_margin
        ci_upper = mean + ci_margin
        return mean, std, ci_lower, ci_upper
    
    latency_mean, latency_std, lat_ci_low, lat_ci_high = calc_stats_with_ci(all_latencies)
    overhead_mean, overhead_std, oh_ci_low, oh_ci_high = calc_stats_with_ci(all_overhead)
    malformed_mean, malformed_std, mal_ci_low, mal_ci_high = calc_stats_with_ci(all_malformed)
    fpr_mean, fpr_std, fpr_ci_low, fpr_ci_high = calc_stats_with_ci(all_fpr)
    throughput_mean, throughput_std, tp_ci_low, tp_ci_high = calc_stats_with_ci(all_throughput)
    
    # Generate research paper table
    print("\n" + "="*80)
    print("CoCoChain Simulation Results - High-density Urban VANET")
    print("4×4 Grid Topology, 500 vehicles/km², 600s simulation (100s warm-up)")
    print("="*80)
    
    print(f"\nNetwork Configuration:")
    print(f"- Topology: 4×4 grid, 5 km²")
    print(f"- Vehicles: 2500 (500/km²)")
    print(f"- Message interval: 1.5s")
    print(f"- Corruption rate: 10%")
    print(f"- Cosine similarity threshold: θ = 0.2")
    print(f"- Simulation runs: {len(run_results)}")
    
    print(f"\nResults Summary:")
    print(f"{'Metric':<35} {'Mean':<12} {'Std Dev':<12} {'95% CI':<20}")
    print("-" * 79)
    print(f"{'End-to-end latency (s)':<35} {latency_mean:<12.4f} {latency_std:<12.4f} [{lat_ci_low:.4f}, {lat_ci_high:.4f}]")
    print(f"{'Throughput (tx/s)':<35} {throughput_mean:<12.2f} {throughput_std:<12.2f} [{tp_ci_low:.2f}, {tp_ci_high:.2f}]")
    print(f"{'Consensus overhead (msgs)':<35} {overhead_mean:<12.0f} {overhead_std:<12.0f} [{oh_ci_low:.0f}, {oh_ci_high:.0f}]")
    print(f"{'Detected Malformed Concepts':<35} {malformed_mean:<12.0f} {malformed_std:<12.0f} [{mal_ci_low:.0f}, {mal_ci_high:.0f}]")
    print(f"{'False Positive Rate (%)':<35} {fpr_mean:<12.2f} {fpr_std:<12.2f} [{fpr_ci_low:.2f}, {fpr_ci_high:.2f}]")
    
    # Generate LaTeX table for research paper
    print(f"\nLaTeX Table Format:")
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{CoCoChain Performance in High-density Urban VANET}")
    print("\\begin{tabular}{|l|c|c|c|}")
    print("\\hline")
    print("\\textbf{Metric} & \\textbf{Mean} & \\textbf{Std Dev} & \\textbf{95\\% CI} \\\\")
    print("\\hline")
    print(f"End-to-end latency (s) & {latency_mean:.4f} & {latency_std:.4f} & [{lat_ci_low:.4f}, {lat_ci_high:.4f}] \\\\")
    print(f"Throughput (tx/s) & {throughput_mean:.2f} & {throughput_std:.2f} & [{tp_ci_low:.2f}, {tp_ci_high:.2f}] \\\\")
    print(f"Consensus overhead (msgs) & {overhead_mean:.0f} & {overhead_std:.0f} & [{oh_ci_low:.0f}, {oh_ci_high:.0f}] \\\\")
    print(f"DMC (count) & {malformed_mean:.0f} & {malformed_std:.0f} & [{mal_ci_low:.0f}, {mal_ci_high:.0f}] \\\\")
    print(f"FPR (\\%) & {fpr_mean:.2f} & {fpr_std:.2f} & [{fpr_ci_low:.2f}, {fpr_ci_high:.2f}] \\\\")
    print("\\hline")
    print("\\end{tabular}")
    print("\\label{tab:cocochain_vanet}")
    print("\\end{table}")
    
    # Save detailed results to CSV with all metrics
    if run_results:
        df = pd.DataFrame(run_results)
        csv_filename = 'cocochain_detailed_results.csv'
        df.to_csv(csv_filename, index=False)
        print(f"\nDetailed results saved to: {csv_filename}")
        
        # Save summary statistics
        summary_data = {
            'metric': ['latency', 'throughput', 'consensus_overhead', 'dmc', 'fpr'],
            'mean': [latency_mean, throughput_mean, overhead_mean, malformed_mean, fpr_mean],
            'std_dev': [latency_std, throughput_std, overhead_std, malformed_std, fpr_std],
            'ci_lower': [lat_ci_low, tp_ci_low, oh_ci_low, mal_ci_low, fpr_ci_low],
            'ci_upper': [lat_ci_high, tp_ci_high, oh_ci_high, mal_ci_high, fpr_ci_high]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('cocochain_summary_stats.csv', index=False)
        print(f"Summary statistics saved to: cocochain_summary_stats.csv")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_results()