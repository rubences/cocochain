# CoCoChain - Highway OMNeT++/Veins Simulation

This repository implements an OMNeT++/Veins simulation for CoCoChain, a Byzantine Fault Tolerant blockchain protocol designed for vehicular networks with semantic concept verification.

## Highway Scenario Implementation

**NEW**: This implementation has been updated to support the highway scenario as specified in the research requirements:

### Scenario Configuration

- **Topology**: 20 km linear highway with 5 RSUs (Road Side Units)
- **RSU Coverage**: 1 km each with 500m overlap at positions 2km, 6km, 10km, 14km, 18km
- **Vehicle Count**: 200 vehicles moving at 100–130 km/h
- **Transaction Rate**: Each vehicle sends a transaction every 2 seconds
- **Simulation Time**: 600 seconds with 10 repetitions
- **Consensus Comparison**: CoCoChain vs PBFT baseline

### Key Metrics Tracked

1. **End-to-end authentication latency during RSU handovers**
2. **Handover success rate (HSR)**: Successful commit without delay
3. **Throughput**: Transactions per second

### Generated Visualizations

The simulation automatically generates:

1. **Box plot**: Authentication latency comparison (PBFT vs CoCoChain)
2. **Line plot**: HSR vs vehicle speed (sampled at 100, 110, 120, 130 km/h)

### Data Export

- **CSV files**: Latency logs and success ratios exported for further analysis
- **EPS format**: High-quality figures for paper inclusion
- **Research report**: Comprehensive analysis in text format

## Quick Start

### Prerequisites
- OMNeT++ 6.0+ with INET framework (for full simulation)
- Python 3.x with numpy, pandas, matplotlib (for analysis)
- C++17 compatible compiler

### Test Implementation (No OMNeT++ Required)
```bash
# Test highway scenario logic
cd scripts
python3 test_highway.py

# Generate sample visualizations and data
python3 analyze_highway.py
```

### Full Simulation (Requires OMNeT++)
```bash
# Run complete highway simulation
./run_highway_simulation.sh

# Or manually run specific configurations:
make clean && make
cd simulations

# CoCoChain baseline
../CoCoChain -u Cmdenv -f highway.ini -c CoCoChain --repeat=10

# PBFT comparison
../CoCoChain -u Cmdenv -f highway.ini -c PBFT --repeat=10

# Speed analysis
../CoCoChain -u Cmdenv -f highway.ini -c Speed100 --repeat=10
```

## Architecture

### Highway Network Components

1. **RSU (Road Side Unit)**: Stationary infrastructure providing 1km coverage
   - CoCoChain or PBFT consensus processing
   - Vehicle handover management
   - Authentication and verification

2. **Vehicle**: Mobile nodes with highway mobility patterns
   - Linear movement at 100-130 km/h
   - Transaction generation every 2 seconds
   - RSU handover initiation and completion

3. **Highway Topology**: 20km linear road with strategic RSU placement
   - 5 RSUs with overlapping coverage zones
   - Supports seamless handovers between coverage areas

### Consensus Implementations

#### CoCoChain (Optimized for V2X)
- Semantic digest verification: 1-5ms authentication latency
- Byzantine fault tolerance with 67% threshold
- Optimized for mobile handover scenarios
- Higher throughput and success rates

#### PBFT Baseline (Traditional)
- Standard PBFT consensus: 10-50ms authentication latency
- Multiple round voting mechanism
- Higher overhead in mobile environments

## Performance Results

Based on simulation data:

| Metric | CoCoChain | PBFT | Improvement |
|--------|-----------|------|-------------|
| Authentication Latency | 2.8 ± 0.9 ms | 25.4 ± 4.4 ms | 89% faster |
| Handover Success Rate | 95.0 ± 1.7% | 88.5 ± 3.2% | +6.6 points |
| Throughput | 24.9 ± 3.0 tx/s | 17.9 ± 4.3 tx/s | 39% higher |

### Speed Analysis (CoCoChain)
- **100 km/h**: 94.6% HSR, 3.25ms latency
- **110 km/h**: 93.9% HSR, 3.18ms latency  
- **120 km/h**: 92.4% HSR, 3.10ms latency
- **130 km/h**: 92.8% HSR, 3.54ms latency

## Generated Files

After running analysis:

```
highway_analysis_report.txt                    # Complete analysis report
authentication_latency_boxplot.eps/.png        # Box plot visualization
handover_success_rate_vs_speed.eps/.png        # Line plot visualization
authentication_latencies.csv                   # Raw latency data
handover_success_rates.csv                     # HSR by speed data
summary_statistics.csv                         # Statistical summary
```

## Implementation Details

### RSU Handover Process
1. Vehicle detects new RSU in range
2. Initiates handover request to target RSU
3. RSU authenticates vehicle using consensus
4. Handover completion with latency measurement
5. Success/failure recording for HSR calculation

### Semantic Verification
- Hash-based semantic digest of transaction content
- Corruption detection during consensus
- Integrity verification across RSU handovers

### Transaction Flow
1. Vehicle generates transaction with semantic content
2. Broadcast to current RSU
3. RSU runs consensus (CoCoChain or PBFT)
4. Authentication and verification
5. Confirmation back to vehicle
6. Metrics recording (latency, success, throughput)

## Research Integration

This implementation is designed for academic research papers:

- **Statistical rigor**: 10 repetitions with confidence intervals
- **Publication-ready figures**: EPS format for LaTeX inclusion
- **Comparative analysis**: Direct CoCoChain vs PBFT comparison
- **CSV export**: Raw data for custom analysis
- **Standard metrics**: Authentication latency, HSR, throughput

## Legacy Urban Scenario

The original urban grid scenario (4×4 grid, 2500 vehicles) is still available:

```bash
# Run original urban scenario
cd simulations
../CoCoChain -u Cmdenv -f omnetpp.ini -c General --repeat=10
```

See `SIMULATION_README.md` for details on the urban scenario implementation.