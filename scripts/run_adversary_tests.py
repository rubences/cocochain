#!/usr/bin/env python3
"""
CoCoChain Adversary Variation Test Script
Tests DMC and FPR performance across different adversary percentages (0% to 20%)
"""

import subprocess
import os
import sys
from pathlib import Path
import shutil

def run_adversary_variation_tests():
    """Run simulation tests with varying adversary percentages"""
    
    # Adversary percentages to test
    adversary_percentages = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    
    print("CoCoChain Adversary Variation Testing")
    print("=" * 50)
    print(f"Testing adversary percentages: {adversary_percentages}")
    
    # Create results directory structure
    base_results_dir = Path("../results/adversary_variation")
    base_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Original config file path
    original_config = Path("../simulations/omnetpp.ini")
    
    for adv_pct in adversary_percentages:
        print(f"\n--- Testing with {adv_pct}% adversaries ---")
        
        # Create specific results directory for this adversary percentage
        results_dir = base_results_dir / f"adv_{adv_pct}pct"
        results_dir.mkdir(exist_ok=True)
        
        # Update configuration for this adversary percentage
        update_config_for_adversary_percentage(original_config, adv_pct / 100.0)
        
        # Run simulation with multiple seeds
        try:
            print(f"Running simulation with {adv_pct}% adversaries...")
            
            # Build first if needed
            os.chdir("../")
            if not Path("CoCoChain").exists():
                print("Building simulation...")
                result = subprocess.run(["make", "clean"], capture_output=True, text=True)
                result = subprocess.run(["make"], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Build failed: {result.stderr}")
                    continue
            
            # Run simulation with 10 seeds
            os.chdir("simulations")
            for seed in range(10):
                print(f"  Running seed {seed}...")
                cmd = [
                    "../CoCoChain", 
                    "-u", "Cmdenv", 
                    "-c", "General",
                    f"--seed-set={seed}",
                    f"--result-dir={results_dir}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Simulation failed for seed {seed}: {result.stderr}")
                    continue
                    
            print(f"Completed simulation for {adv_pct}% adversaries")
            
        except Exception as e:
            print(f"Error running simulation for {adv_pct}% adversaries: {e}")
            continue
        finally:
            # Change back to scripts directory
            os.chdir("../scripts")
    
    # Restore original configuration
    print("\nRestoring original configuration...")
    restore_original_config(original_config)
    
    # Analyze all results
    print("\nAnalyzing adversary variation results...")
    analyze_adversary_variation_results(base_results_dir, adversary_percentages)
    
    print("\nAdversary variation testing complete!")

def update_config_for_adversary_percentage(config_file, adversary_rate):
    """Update configuration file with specific adversary percentage"""
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Update corruption probability
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '**.vehicle.app[0].corruptionProbability' in line:
            lines[i] = f'**.vehicle.app[0].corruptionProbability = {adversary_rate}  # {adversary_rate*100}% corruption rate'
            break
    
    # Write updated config
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))

def restore_original_config(config_file):
    """Restore original configuration with 10% adversaries"""
    update_config_for_adversary_percentage(config_file, 0.1)

def analyze_adversary_variation_results(base_results_dir, adversary_percentages):
    """Analyze results across all adversary percentages"""
    
    import pandas as pd
    import numpy as np
    
    all_results = []
    
    for adv_pct in adversary_percentages:
        results_dir = base_results_dir / f"adv_{adv_pct}pct"
        
        if not results_dir.exists():
            continue
        
        # Parse scalar files in this directory
        scalar_files = list(results_dir.glob("*.sca"))
        
        for scalar_file in scalar_files:
            result = parse_scalar_file_simple(scalar_file)
            if result:
                result['adversary_pct'] = adv_pct
                all_results.append(result)
    
    if not all_results:
        print("No results found for analysis")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    
    # Group by adversary percentage and calculate statistics
    summary = df.groupby('adversary_pct').agg({
        'latency': ['mean', 'std'],
        'throughput': ['mean', 'std'],
        'dmc': ['mean', 'std'],
        'fpr': ['mean', 'std']
    }).round(4)
    
    print("\nAdversary Variation Results Summary:")
    print("=" * 80)
    print(summary)
    
    # Save detailed results
    output_file = base_results_dir / "adversary_variation_summary.csv"
    summary.to_csv(output_file)
    
    # Save raw data
    raw_output_file = base_results_dir / "adversary_variation_raw_data.csv"
    df.to_csv(raw_output_file, index=False)
    
    print(f"\nResults saved to:")
    print(f"- Summary: {output_file}")
    print(f"- Raw data: {raw_output_file}")

def parse_scalar_file_simple(filepath):
    """Simple scalar file parser for adversary variation analysis"""
    
    result = {
        'latency': 0,
        'throughput': 0,
        'dmc': 0,
        'fpr': 0
    }
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('scalar'):
                    parts = line.split()
                    if len(parts) >= 4:
                        metric = parts[2]
                        value = float(parts[3])
                        
                        if 'endToEndLatency:mean' in metric:
                            result['latency'] = value
                        elif 'throughput:mean' in metric:
                            result['throughput'] = value
                        elif 'malformedDetected:sum' in metric:
                            result['dmc'] = value
                        elif 'falsePositiveRate:mean' in metric:
                            result['fpr'] = value
                            
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    
    return result

if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("../simulations/omnetpp.ini").exists():
        print("Error: Please run this script from the scripts/ directory")
        sys.exit(1)
    
    run_adversary_variation_tests()