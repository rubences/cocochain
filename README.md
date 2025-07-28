# CoCoChain - OMNeT++/Veins VANET Simulation

This repository implements an OMNeT++/Veins simulation for CoCoChain, a Byzantine Fault Tolerant blockchain protocol designed for vehicular networks with semantic concept verification and top-k concept manipulation detection.

## Overview

CoCoChain addresses the challenge of concept corruption in V2V communications by implementing:
- **Semantic Digest Verification**: Hash-based integrity checking of concept vectors with cosine similarity threshold (θ = 0.2)
- **Byzantine Fault Tolerance**: PBFT consensus mechanism resilient to adversarial nodes
- **Top-k Concept Detection**: Identification and rejection of manipulated top-k concept vectors
- **Adversarial Detection**: Comprehensive detection of malformed transactions with FPR tracking

## Simulation Scenario

**High-density Urban VANET Simulation**
- **Topology**: 4×4 grid covering 5 km²
- **Vehicle Density**: 500 vehicles/km² (2500 total vehicles)
- **Simulation Time**: 600s total (100s warm-up period)
- **Communication**: V2V messages every 1.5 seconds
- **Adversarial Nodes**: Configurable from 0% to 20% (default 10%)
- **Consensus**: PBFT with CoCoChain semantic verification comparison
- **Cosine Similarity Threshold**: θ = 0.2 for top-k concept validation

## Key Metrics

The simulation measures and compares:
- **End-to-end confirmation latency**: Time from transaction creation to consensus (with 95% CI)
- **Throughput**: Transactions per second (tx/s)
- **Consensus message overhead**: Total messages exchanged during consensus
- **Detected Malformed Concepts (DMC)**: Number of corrupted transactions identified
- **False Positive Rate (FPR)**: Percentage of valid transactions incorrectly rejected

## Visualizations

The system generates two required plots:
1. **Bar chart**: PBFT vs CoCoChain comparison across 4 metrics (latency, throughput, DMC, FPR)
2. **Line plot**: DMC and FPR vs % adversaries (0% to 20%)

Both plots are exported in PDF and PNG formats for publication.

## Quick Start

### Prerequisites
- OMNeT++ 6.0+ with INET framework (for full simulation)
- Python 3.x with numpy, pandas, matplotlib, seaborn (for analysis and plotting)
- C++17 compatible compiler

### Running Tests
```bash
# Test core algorithms (no OMNeT++ required)
cd scripts
python3 test_cocochain.py

# Generate sample plots and data
python3 generate_plots.py

# Run adversary variation tests
python3 run_adversary_tests.py
```

### Full Simulation (requires OMNeT++)
```bash
# Build and run
./run_simulation.sh

# Or manually:
make
cd simulations
../CoCoChain -u Cmdenv -c General --repeat=10
```

### Generate Visualizations
```bash
cd scripts
python3 generate_plots.py    # Creates PDF/PNG plots
python3 analyze_results.py   # Analyzes simulation results
```

## Implementation Details

- **ConceptVector**: 10-dimensional semantic representation with corruption detection
- **Transaction**: Includes concept vector, semantic digest, and consensus metadata  
- **BFT Consensus**: Voting-based agreement with Byzantine fault tolerance
- **Adversarial Behavior**: Systematic corruption and malformed vector injection

## Output

Results are generated in research paper format including:
- Statistical summaries with mean and standard deviation
- LaTeX-formatted tables ready for publication
- CSV export for further analysis
- Confidence intervals from multiple simulation runs

See `SIMULATION_README.md` for detailed implementation documentation.