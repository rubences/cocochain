# CoCoChain - Hybrid IoV Simulation

This repository implements a hybrid Internet of Vehicles (IoV) simulation for CoCoChain, a Byzantine Fault Tolerant blockchain protocol designed for vehicular networks with semantic concept verification and cross-domain interoperability.

## Overview

CoCoChain addresses the challenge of concept corruption in V2V communications by implementing:
- **Semantic Digest Verification**: Hash-based integrity checking of concept vectors
- **Byzantine Fault Tolerance**: Consensus mechanism resilient to adversarial nodes
- **Adversarial Detection**: Identification and rejection of malformed transactions
- **Multi-Domain Architecture**: Support for urban, interurban, and rural domains
- **Inter-Domain Semantic Alignment**: Cross-domain concept exchange with SAE models
- **Cross-Domain Finality**: Transaction confirmation across multiple domains

## Simulation Scenarios

### Hybrid IoV Setup (Primary Implementation)
- **Domains**: 3 domains (urban, interurban, rural)
- **RSUs**: 3-5 Road Side Units per domain acting as validator nodes
- **Vehicles**: 300 vehicles distributed across domains generating events asynchronously
- **Consensus**: Intra-domain PBFT consensus with inter-domain semantic alignment
- **SAE Models**: Shared Semantic Autoencoder models for concept exchange
- **Synchronization**: Inter-domain sync every 30 seconds

### Legacy OMNeT++/Veins Scenario
- **Scenario 1**: High-density Urban Network
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

# Quick hybrid IoV demo (20 seconds)
python3 demo_hybrid_iov.py

# Full hybrid IoV simulation (2 minutes)
python3 hybrid_iov_simulation.py

# Enhanced analysis and visualization
python3 analyze_hybrid_results.py

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

### Hybrid IoV Metrics
- **Cross-Domain Finality Time (CDFT)**: Time for transaction to be confirmed across domains
- **Interoperability Overhead (IO)**: Extra bandwidth from inter-domain concept exchange
- **Intra-domain vs Inter-domain bandwidth**: Communication overhead breakdown
- **Domain-specific performance**: Urban, interurban, and rural network characteristics

### Legacy Metrics  
- **End-to-end confirmation latency**: Time from transaction creation to consensus
- **Consensus message overhead**: Total messages exchanged during consensus
- **Malformed transaction detection**: Number of corrupted transactions identified

## Implementation Details

### Hybrid IoV Architecture
- **Multi-Domain Support**: Urban (high-density), Interurban (medium), Rural (sparse)
- **RSU Network**: 3-5 Road Side Units per domain as validator nodes
- **Edge Servers**: Domain-level coordinators for consensus and semantic alignment
- **SAE Models**: Semantic Autoencoder models for cross-domain concept translation
- **Vehicle Distribution**: 300 vehicles (Urban: 40%, Interurban: 35%, Rural: 25%)
- **Asynchronous Events**: Vehicles generate events probabilistically

### Core Protocol Components
- **ConceptVector**: 10-dimensional semantic representation with corruption detection
- **Transaction**: Includes concept vector, semantic digest, and consensus metadata  
- **BFT Consensus**: Voting-based agreement with Byzantine fault tolerance
- **Adversarial Behavior**: Systematic corruption and malformed vector injection
- **Inter-Domain Sync**: Semantic alignment every 30 seconds between domains

## Output

The simulation generates:

### Hybrid IoV Results
1. **Cross-Domain Finality Time Analysis**: Statistics per domain and configuration
2. **Bandwidth Usage Reports**: Intra vs inter-domain communication breakdown  
3. **Interoperability Overhead Metrics**: Cost of cross-domain semantic exchange
4. **Publication-Quality Visualizations**: 
   - Stacked bar chart (bandwidth distribution)
   - Box plot (CDFT comparison across domains)
5. **LaTeX Tables**: Ready-to-use research paper format
6. **CSV Data**: Detailed results for further analysis (pandas-compatible)

### Legacy Results
- Statistical summaries with mean and standard deviation
- LaTeX-formatted tables ready for publication
- CSV export for further analysis
- Confidence intervals from multiple simulation runs

### Sample Output Table

| Configuration | Domain | CDFT (s) | Intra BW (MB/s) | Inter BW (MB/s) |
|---------------|--------|----------|-----------------|-----------------|
| With CoCoChain | Urban | 1.778 ± 1.567 | 374.4 | 0.569 |
| Without CoCoChain | Urban | 1.639 ± 1.380 | 397.0 | 0.000 |
| With CoCoChain | Interurban | 2.111 ± 1.332 | 284.3 | 0.548 |
| Without CoCoChain | Interurban | 2.009 ± 1.163 | 555.8 | 0.000 |

See `SIMULATION_README.md` for detailed OMNeT++/Veins implementation documentation.