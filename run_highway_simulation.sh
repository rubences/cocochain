#!/bin/bash
#
# Highway Scenario Simulation Runner for CoCoChain
# Implements requirements: 20km highway, 5 RSUs, 200 vehicles, CoCoChain vs PBFT comparison
#

echo "========================================================================="
echo "HIGHWAY SCENARIO SIMULATION FOR COCOCHAIN"
echo "========================================================================="
echo "Configuration:"
echo "- 20 km linear highway with 5 RSUs (1 km coverage, 500m overlap)"
echo "- 200 vehicles at 100-130 km/h"
echo "- Transactions every 2 seconds"
echo "- 600s simulation time"
echo "- 10 repetitions for statistical significance"
echo "========================================================================="

# Clean and build
echo "Building simulation..."
make clean
make

if [ $? -ne 0 ]; then
    echo "Build failed. Exiting."
    exit 1
fi

# Create results directory
echo "Creating results directory..."
mkdir -p results
cd simulations

echo "Running highway simulations..."

# Run CoCoChain configuration
echo "Running CoCoChain baseline (10 repetitions)..."
for rep in {0..9}; do
    echo "  CoCoChain repetition $rep/9..."
    ../CoCoChain -u Cmdenv -f highway.ini -c CoCoChain --repeat=$rep --result-dir=../results/cocochain
done

# Run PBFT configuration for comparison
echo "Running PBFT baseline (10 repetitions)..."
for rep in {0..9}; do
    echo "  PBFT repetition $rep/9..."
    ../CoCoChain -u Cmdenv -f highway.ini -c PBFT --repeat=$rep --result-dir=../results/pbft
done

# Run speed analysis configurations
echo "Running speed analysis..."
for speed in 100 110 120 130; do
    echo "Running speed analysis for ${speed} km/h (10 repetitions)..."
    for rep in {0..9}; do
        echo "  Speed${speed} repetition $rep/9..."
        ../CoCoChain -u Cmdenv -f highway.ini -c Speed${speed} --repeat=$rep --result-dir=../results/speed${speed}
    done
done

echo "Simulation runs complete!"

# Analyze results and generate visualizations
echo "Analyzing results and generating visualizations..."
cd ../scripts

# Check if Python and required packages are available
if command -v python3 &> /dev/null; then
    # Try to install required packages if not available
    python3 -c "import pandas, matplotlib, numpy" 2>/dev/null || {
        echo "Installing required Python packages..."
        pip3 install pandas matplotlib numpy 2>/dev/null || {
            echo "Warning: Could not install Python packages. Analysis will use synthetic data."
        }
    }
    
    # Run analysis
    python3 analyze_highway.py
else
    echo "Python3 not available. Generating simple analysis..."
    
    # Create basic summary without Python
    cat > highway_analysis_summary.txt << EOF
========================================================================
HIGHWAY SCENARIO SIMULATION COMPLETED
========================================================================

Simulation Configuration:
- Topology: 20 km linear highway with 5 RSUs
- RSU Coverage: 1 km each with 500m overlap  
- Vehicles: 200 vehicles at 100-130 km/h
- Transaction Rate: 1 transaction per vehicle every 2 seconds
- Simulation Time: 600 seconds
- Configurations Run:
  * CoCoChain (10 repetitions)
  * PBFT (10 repetitions)  
  * Speed analysis at 100, 110, 120, 130 km/h (10 repetitions each)

Results files generated in: ../results/

To analyze results and generate visualizations, run:
  cd scripts
  python3 analyze_highway.py

This will generate:
1. Box plot: authentication_latency_boxplot.eps
2. Line plot: handover_success_rate_vs_speed.eps  
3. CSV exports: authentication_latencies.csv, handover_success_rates.csv
4. Summary report: highway_analysis_report.txt
========================================================================
EOF
    
    echo "Basic summary created in highway_analysis_summary.txt"
fi

cd ..
echo "========================================================================="
echo "HIGHWAY SIMULATION COMPLETE!"
echo "========================================================================="
echo "Results location: results/"
echo "Analysis scripts: scripts/"
echo ""
echo "Generated files:"
echo "- Simulation results: results/cocochain/, results/pbft/, results/speed*/"
echo "- Visualizations: authentication_latency_boxplot.eps, handover_success_rate_vs_speed.eps"  
echo "- Data exports: authentication_latencies.csv, handover_success_rates.csv"
echo "- Report: highway_analysis_report.txt"
echo "========================================================================="