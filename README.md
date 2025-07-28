# CoCoChain - OMNeT++/Veins Simulation

This repository implements an OMNeT++/Veins simulation for CoCoChain, a Byzantine Fault Tolerant blockchain protocol designed for vehicular networks with semantic concept verification.

## Overview

CoCoChain addresses the challenge of concept corruption in V2V communications by implementing:
- **Semantic Digest Verification**: Hash-based integrity checking of concept vectors
- **Byzantine Fault Tolerance**: Consensus mechanism resilient to adversarial nodes
- **Adversarial Detection**: Identification and rejection of malformed transactions

## Simulation Scenario

**Scenario 1: High-density Urban Network**
- **Topology**: 4×4 grid covering 5 km²
- **Vehicle Density**: 500 vehicles/km² (2500 total vehicles)
- **Communication**: V2V messages every 1.5 seconds
- **Adversarial Nodes**: 10% simulate concept corruption
- **Consensus**: BFT with 67% threshold

## Quick Start

### Prerequisites
- OMNeT++ 6.0+ with INET framework (for full simulation)
- Python 3.x with numpy and pandas (for analysis)
- C++17 compatible compiler

### Running Tests
```bash
# Test core algorithms (no OMNeT++ required)
cd scripts
python3 test_cocochain.py

# View sample results
python3 demo_results.py
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

## Key Metrics

The simulation measures:
- **End-to-end confirmation latency**: Time from transaction creation to consensus
- **Consensus message overhead**: Total messages exchanged during consensus
- **Malformed transaction detection**: Number of corrupted transactions identified

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