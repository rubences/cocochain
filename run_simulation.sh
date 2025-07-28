#!/bin/bash
#
# CoCoChain Simulation Runner
#

echo "Building CoCoChain simulation..."
make clean
make

if [ $? -ne 0 ]; then
    echo "Build failed. Exiting."
    exit 1
fi

echo "Creating results directory..."
mkdir -p results

echo "Running simulation with 10 random seeds..."
cd simulations

for seed in {0..9}; do
    echo "Running simulation with seed $seed..."
    ../CoCoChain -u Cmdenv -c General --seed-set=$seed --result-dir=../results
done

echo "Analyzing results..."
cd ../scripts
python3 analyze_results.py

echo "Simulation complete. Check results directory for output files."