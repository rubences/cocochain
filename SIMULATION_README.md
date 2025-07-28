# CoCoChain OMNeT++/Veins Simulation

This project implements an OMNeT++/Veins simulation scenario for CoCoChain under a high-density urban network environment.

## Scenario Configuration

- **Network Type**: High-density urban network (Scenario 1)
- **Topology**: 4×4 grid topology covering 5 km²
- **Vehicle Density**: 500 vehicles/km² (2500 total vehicles)
- **Message Interval**: Each vehicle sends a V2V message every 1.5 seconds
- **Adversarial Nodes**: 10% of nodes simulate concept corruption during transaction encoding
- **Consensus**: Byzantine Fault Tolerance (BFT) with semantic digest verification

## Architecture

### Core Components

1. **CoCoChainApp**: Main application implementing the CoCoChain protocol
   - Transaction generation and processing
   - Concept vector encoding with semantic verification
   - BFT consensus mechanism
   - Adversarial behavior simulation

2. **Vehicle Node**: Network node representing a vehicle with mobility
   - IEEE 802.11p communication interface
   - Random waypoint mobility model
   - UDP-based message exchange

3. **Network Topology**: 4×4 grid layout for urban scenario simulation

### Key Features

#### Concept Corruption Simulation
- 10% of nodes are configured as adversarial
- Adversarial nodes inject malformed concept vectors
- Systematic corruption patterns and noise injection

#### BFT Consensus with Semantic Verification
- Byzantine Fault Tolerance threshold of 67% (2/3 majority)
- Semantic digest computation and verification
- Transaction validation based on concept vector integrity
- Consensus voting and confirmation mechanism

#### Metrics Collection
- **End-to-end confirmation latency**: Time from transaction creation to consensus confirmation
- **Total consensus message overhead**: Number of consensus messages exchanged
- **Malformed transaction detection**: Count of corrupted transactions detected and rejected

## Building and Running

### Prerequisites
- OMNeT++ 6.0+ with INET framework
- C++17 compatible compiler
- Python 3 for result analysis

### Build
```bash
make clean
make
```

### Run Simulation
```bash
./run_simulation.sh
```

This will:
1. Build the simulation
2. Run 10 simulation instances with different random seeds
3. Collect and analyze results
4. Generate summary tables in research paper format

### Manual Execution
```bash
# Build
make

# Run single simulation
cd simulations
../CoCoChain -u Cmdenv -c General

# Analyze results
cd scripts
python3 analyze_results.py
```

## Configuration Parameters

Key parameters in `simulations/omnetpp.ini`:

- `numVehicles = 2500`: Total number of vehicles
- `messageInterval = 1.5s`: V2V message transmission interval
- `corruptionProbability = 0.1`: Fraction of adversarial nodes
- `bftThreshold = 0.67`: BFT consensus threshold
- `semanticVerification = true`: Enable semantic integrity checking
- `maxTransactionAge = 10s`: Maximum age for transaction processing

## Output

The simulation generates:

1. **Scalar Results** (`.sca` files): Summary statistics for each run
2. **Vector Results** (`.vec` files): Time-series data for detailed analysis
3. **Analysis Report**: Console output with averaged results
4. **LaTeX Table**: Ready-to-use table format for research papers
5. **CSV Export**: Detailed results for further analysis

### Sample Output Table

| Metric | Mean | Std Dev |
|--------|------|---------|
| End-to-end latency (s) | X.XXXX | X.XXXX |
| Consensus overhead (msgs) | XXXX | XXXX |
| Malformed detected | XXX | XXX |

## Implementation Details

### Transaction Flow
1. Vehicle generates concept vector
2. Adversarial nodes inject corruption (if applicable)
3. Semantic digest computation
4. Transaction broadcast
5. Peer verification and voting
6. BFT consensus resolution
7. Transaction confirmation/rejection

### Semantic Verification
- Hash-based semantic digest of concept vectors
- Variance-based corruption detection
- Integrity verification during consensus

### Adversarial Behavior
- Random selection of 10% nodes as adversarial
- Concept vector corruption with noise injection
- Malformed vector generation with extreme values

## Research Integration

The simulation is designed to provide data for integration into academic research papers. The analysis script generates:

- Statistical summaries with mean and standard deviation
- LaTeX-formatted tables ready for publication
- CSV data for custom analysis and plotting
- Confidence intervals based on multiple simulation runs

This implementation supports the evaluation of CoCoChain's performance under realistic V2V communication scenarios with Byzantine adversaries.