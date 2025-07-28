#!/usr/bin/env python3
"""
Hybrid IoV CoCoChain Simulation
Models a 3-domain setup (urban, interurban, rural) with inter-domain semantic alignment
"""

import random
import time
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import seaborn as sns

# Set matplotlib backend for non-interactive environments
plt.switch_backend('Agg')

class DomainType(Enum):
    URBAN = "urban"
    INTERURBAN = "interurban" 
    RURAL = "rural"

@dataclass
class ConceptVector:
    data: List[float]
    timestamp: float
    node_id: int
    domain: DomainType
    is_corrupted: bool = False

@dataclass 
class SAEModel:
    """Semantic Autoencoder Model for concept encoding/decoding"""
    domain: DomainType
    encoding_matrix: np.ndarray
    decoding_matrix: np.ndarray
    
    def encode(self, concept_vector: List[float]) -> List[float]:
        """Encode concept vector using SAE"""
        encoded = np.dot(self.encoding_matrix, concept_vector)
        return encoded.tolist()
    
    def decode(self, encoded_vector: List[float]) -> List[float]:
        """Decode concept vector using SAE"""
        decoded = np.dot(self.decoding_matrix, encoded_vector)
        return decoded.tolist()

@dataclass
class Transaction:
    id: int
    concept_vector: ConceptVector
    semantic_digest: str
    timestamp: float
    originator: int
    domain: DomainType
    verified: bool = False
    cross_domain: bool = False

@dataclass
class RSU:
    """Road Side Unit - Validator node"""
    id: int
    domain: DomainType
    position: Tuple[float, float]
    connected_vehicles: Set[int] = field(default_factory=set)
    
@dataclass
class EdgeServer:
    """Edge Server - Domain-level validator"""
    id: int
    domain: DomainType
    connected_rsus: List[int] = field(default_factory=list)
    
@dataclass
class InterDomainMessage:
    """Message for cross-domain semantic exchange"""
    source_domain: DomainType
    target_domain: DomainType
    semantic_concepts: List[float]
    timestamp: float
    size_bytes: int

class Vehicle:
    def __init__(self, vehicle_id: int, domain: DomainType, rsu_id: int):
        self.id = vehicle_id
        self.domain = domain
        self.rsu_id = rsu_id
        self.transaction_times: Dict[int, float] = {}
        self.events_generated = 0
        
    def generate_event(self) -> ConceptVector:
        """Generate vehicle event with concept vector"""
        cv = ConceptVector(
            data=[random.gauss(0, 1) for _ in range(10)],
            timestamp=time.time(),
            node_id=self.id,
            domain=self.domain
        )
        self.events_generated += 1
        return cv

class Domain:
    def __init__(self, domain_type: DomainType, num_rsus: int = 4):
        self.type = domain_type
        self.rsus = []
        self.edge_server = EdgeServer(id=random.randint(1000, 9999), domain=domain_type)
        self.vehicles = []
        self.sae_model = None
        self.bandwidth_usage = {"intra": 0.0, "inter": 0.0}  # MB/s
        
        # Create RSUs for this domain
        for i in range(num_rsus):
            rsu = RSU(
                id=i + (domain_type.value.upper().encode()[0] * 100),
                domain=domain_type,
                position=(random.uniform(0, 1000), random.uniform(0, 1000))
            )
            self.rsus.append(rsu)
            self.edge_server.connected_rsus.append(rsu.id)
    
    def initialize_sae_model(self):
        """Initialize SAE model for this domain"""
        # Create encoding/decoding matrices (simplified SAE)
        encoding_matrix = np.random.normal(0, 0.1, (8, 10))  # 10->8 compression
        decoding_matrix = np.random.normal(0, 0.1, (10, 8))  # 8->10 decompression
        
        self.sae_model = SAEModel(
            domain=self.type,
            encoding_matrix=encoding_matrix,
            decoding_matrix=decoding_matrix
        )

class HybridIoVNetwork:
    def __init__(self, enable_cocochain: bool = True):
        self.domains = {}
        self.enable_cocochain = enable_cocochain
        self.shared_sae_models = {}
        self.sync_interval = 30.0  # seconds
        self.last_sync_time = 0.0
        
        # Metrics
        self.cdft_measurements = defaultdict(list)  # Cross-Domain Finality Time
        self.io_measurements = defaultdict(float)   # Interoperability Overhead
        self.bandwidth_logs = defaultdict(list)
        self.total_messages = 0
        
        # Initialize domains
        self._initialize_domains()
        self._distribute_vehicles()
        self._initialize_shared_sae_models()
    
    def _initialize_domains(self):
        """Initialize the 3 domains with RSUs"""
        for domain_type in DomainType:
            num_rsus = random.randint(3, 5)  # 3-5 RSUs per domain
            domain = Domain(domain_type, num_rsus)
            domain.initialize_sae_model()
            self.domains[domain_type] = domain
            print(f"Created {domain_type.value} domain with {num_rsus} RSUs")
    
    def _distribute_vehicles(self):
        """Distribute 300 vehicles across domains"""
        total_vehicles = 300
        
        # Distribution weights: urban (40%), interurban (35%), rural (25%)
        distributions = {
            DomainType.URBAN: 0.40,
            DomainType.INTERURBAN: 0.35,
            DomainType.RURAL: 0.25
        }
        
        vehicle_id = 0
        for domain_type, ratio in distributions.items():
            num_vehicles = int(total_vehicles * ratio)
            domain = self.domains[domain_type]
            
            for i in range(num_vehicles):
                # Assign to random RSU in domain
                rsu = random.choice(domain.rsus)
                vehicle = Vehicle(vehicle_id, domain_type, rsu.id)
                domain.vehicles.append(vehicle)
                rsu.connected_vehicles.add(vehicle_id)
                vehicle_id += 1
                
        print(f"Distributed 300 vehicles: Urban({len(self.domains[DomainType.URBAN].vehicles)}), "
              f"Interurban({len(self.domains[DomainType.INTERURBAN].vehicles)}), "
              f"Rural({len(self.domains[DomainType.RURAL].vehicles)})")
    
    def _initialize_shared_sae_models(self):
        """Initialize shared SAE models across domains"""
        for domain_type in DomainType:
            self.shared_sae_models[domain_type] = self.domains[domain_type].sae_model
        print("Initialized shared SAE models across domains")
    
    def simulate_intra_domain_consensus(self, domain: Domain, transaction: Transaction) -> float:
        """Simulate PBFT consensus within a domain"""
        start_time = time.time()
        
        # Simulate PBFT phases: propose, prepare, commit
        num_nodes = len(domain.rsus) + 1  # RSUs + edge server
        consensus_messages = num_nodes * 3  # 3 phases
        
        # Add to intra-domain bandwidth
        message_size_kb = 2.0  # Average message size
        bandwidth_mb = (consensus_messages * message_size_kb) / 1024
        domain.bandwidth_usage["intra"] += bandwidth_mb
        
        # Simulate consensus delay based on domain type
        base_delay = {
            DomainType.URBAN: 0.5,     # Fast urban network
            DomainType.INTERURBAN: 1.0, # Medium interurban
            DomainType.RURAL: 1.5      # Slower rural network
        }
        
        consensus_time = base_delay[domain.type] + random.uniform(0, 0.5)
        time.sleep(0.001)  # Small actual delay for simulation
        
        self.total_messages += consensus_messages
        return consensus_time
    
    def simulate_inter_domain_sync(self, source_domain: DomainType, target_domain: DomainType) -> float:
        """Simulate inter-domain semantic alignment"""
        if not self.enable_cocochain:
            return 0.0
            
        start_time = time.time()
        
        # Generate semantic concepts for exchange
        source_sae = self.shared_sae_models[source_domain]
        target_sae = self.shared_sae_models[target_domain]
        
        # Create sample concepts to exchange
        concepts = [random.gauss(0, 1) for _ in range(10)]
        encoded_concepts = source_sae.encode(concepts)
        decoded_concepts = target_sae.decode(encoded_concepts)
        
        # Calculate message size
        concept_size = len(encoded_concepts) * 8  # 8 bytes per float
        message = InterDomainMessage(
            source_domain=source_domain,
            target_domain=target_domain,
            semantic_concepts=encoded_concepts,
            timestamp=time.time(),
            size_bytes=concept_size
        )
        
        # Add to inter-domain bandwidth
        bandwidth_mb = concept_size / (1024 * 1024)
        self.domains[source_domain].bandwidth_usage["inter"] += bandwidth_mb
        self.domains[target_domain].bandwidth_usage["inter"] += bandwidth_mb
        
        # Add to interoperability overhead
        self.io_measurements[source_domain] += bandwidth_mb
        self.io_measurements[target_domain] += bandwidth_mb
        
        sync_time = random.uniform(0.1, 0.3)  # Inter-domain sync delay
        time.sleep(0.001)
        
        return sync_time
    
    def simulate_cross_domain_transaction(self, transaction: Transaction) -> float:
        """Simulate cross-domain transaction processing"""
        start_time = time.time()
        
        source_domain = self.domains[transaction.domain]
        
        # Step 1: Intra-domain consensus in source domain
        intra_consensus_time = self.simulate_intra_domain_consensus(source_domain, transaction)
        
        # Step 2: Inter-domain semantic alignment (if enabled)
        inter_domain_time = 0.0
        if self.enable_cocochain:
            for target_domain_type in DomainType:
                if target_domain_type != transaction.domain:
                    sync_time = self.simulate_inter_domain_sync(transaction.domain, target_domain_type)
                    inter_domain_time += sync_time
        
        # Step 3: Consensus in other domains
        cross_domain_consensus_time = 0.0
        for domain_type, domain in self.domains.items():
            if domain_type != transaction.domain:
                consensus_time = self.simulate_intra_domain_consensus(domain, transaction)
                cross_domain_consensus_time += consensus_time
        
        total_cdft = intra_consensus_time + inter_domain_time + cross_domain_consensus_time
        return total_cdft
    
    def simulate_events_round(self):
        """Simulate one round of asynchronous vehicle events"""
        events_generated = 0
        
        for domain_type, domain in self.domains.items():
            for vehicle in domain.vehicles:
                # Asynchronous event generation (10% chance per round per vehicle)
                if random.random() < 0.1:
                    concept_vector = vehicle.generate_event()
                    
                    # Create transaction
                    transaction = Transaction(
                        id=random.randint(1000000, 9999999),
                        concept_vector=concept_vector,
                        semantic_digest=hashlib.sha256(str(concept_vector.data).encode()).hexdigest()[:16],
                        timestamp=time.time(),
                        originator=vehicle.id,
                        domain=domain_type,
                        cross_domain=random.random() < 0.3  # 30% are cross-domain
                    )
                    
                    vehicle.transaction_times[transaction.id] = time.time()
                    
                    # Process transaction
                    if transaction.cross_domain:
                        cdft = self.simulate_cross_domain_transaction(transaction)
                        self.cdft_measurements[domain_type].append(cdft)
                    else:
                        # Intra-domain only
                        intra_time = self.simulate_intra_domain_consensus(domain, transaction)
                        self.cdft_measurements[domain_type].append(intra_time)
                    
                    events_generated += 1
        
        return events_generated
    
    def run_simulation(self, duration_seconds: int = 120):
        """Run the complete simulation"""
        print(f"Starting hybrid IoV simulation for {duration_seconds} seconds")
        print(f"CoCoChain semantic exchange: {'ENABLED' if self.enable_cocochain else 'DISABLED'}")
        
        start_time = time.time()
        round_count = 0
        total_events = 0
        
        while (time.time() - start_time) < duration_seconds:
            # Generate events
            events_in_round = self.simulate_events_round()
            total_events += events_in_round
            
            # Inter-domain synchronization every 30s
            current_time = time.time() - start_time
            if current_time - self.last_sync_time >= self.sync_interval:
                if self.enable_cocochain:
                    print(f"Inter-domain sync at {current_time:.1f}s")
                    # Sync between all domain pairs
                    domains_list = list(DomainType)
                    for i, source in enumerate(domains_list):
                        for target in domains_list[i+1:]:
                            self.simulate_inter_domain_sync(source, target)
                            self.simulate_inter_domain_sync(target, source)
                
                self.last_sync_time = current_time
            
            round_count += 1
            time.sleep(0.01)  # Small delay between rounds
        
        print(f"Simulation completed: {round_count} rounds, {total_events} events generated")
        return self.collect_results()
    
    def collect_results(self) -> Dict:
        """Collect simulation results"""
        results = {
            'cdft_by_domain': {},
            'bandwidth_by_domain': {},
            'total_io_overhead': sum(self.io_measurements.values()),
            'enable_cocochain': self.enable_cocochain
        }
        
        # CDFT statistics per domain
        for domain_type in DomainType:
            cdft_times = self.cdft_measurements[domain_type]
            if cdft_times:
                results['cdft_by_domain'][domain_type.value] = {
                    'mean': np.mean(cdft_times),
                    'std': np.std(cdft_times),
                    'values': cdft_times
                }
            else:
                results['cdft_by_domain'][domain_type.value] = {
                    'mean': 0, 'std': 0, 'values': []
                }
        
        # Bandwidth usage per domain
        for domain_type, domain in self.domains.items():
            results['bandwidth_by_domain'][domain_type.value] = domain.bandwidth_usage.copy()
        
        return results

def create_visualizations(results_with_cocochain, results_without_cocochain):
    """Create publishable quality visualizations"""
    
    # Set style for publication quality
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. Stacked bar chart: Bandwidth distribution (intra vs inter-domain)
    domains = ['urban', 'interurban', 'rural']
    
    # Data for with CoCoChain
    intra_with = [results_with_cocochain['bandwidth_by_domain'][d]['intra'] for d in domains]
    inter_with = [results_with_cocochain['bandwidth_by_domain'][d]['inter'] for d in domains]
    
    # Data for without CoCoChain
    intra_without = [results_without_cocochain['bandwidth_by_domain'][d]['intra'] for d in domains]
    inter_without = [results_without_cocochain['bandwidth_by_domain'][d]['inter'] for d in domains]
    
    # Create stacked bars
    x_pos = np.arange(len(domains))
    width = 0.35
    
    # With CoCoChain
    ax1.bar(x_pos - width/2, intra_with, width, label='Intra-domain', alpha=0.8)
    ax1.bar(x_pos - width/2, inter_with, width, bottom=intra_with, label='Inter-domain', alpha=0.8)
    
    # Without CoCoChain
    ax1.bar(x_pos + width/2, intra_without, width, alpha=0.8)
    ax1.bar(x_pos + width/2, inter_without, width, bottom=intra_without, alpha=0.8)
    
    ax1.set_xlabel('Domain Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Bandwidth Usage (MB/s)', fontsize=12, fontweight='bold')
    ax1.set_title('Bandwidth Distribution: Intra vs Inter-domain', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([d.capitalize() for d in domains])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add text labels for CoCoChain status
    ax1.text(-0.4, max(max(intra_with), max(intra_without)) * 1.1, 'With\nCoCoChain', 
             ha='center', va='center', fontweight='bold')
    ax1.text(0.4, max(max(intra_with), max(intra_without)) * 1.1, 'Without\nCoCoChain', 
             ha='center', va='center', fontweight='bold')
    
    # 2. Box plot: CDFT comparison across domains
    cdft_data_with = []
    cdft_data_without = []
    domain_labels = []
    
    for domain in domains:
        cdft_with = results_with_cocochain['cdft_by_domain'][domain]['values']
        cdft_without = results_without_cocochain['cdft_by_domain'][domain]['values']
        
        if cdft_with:
            cdft_data_with.extend(cdft_with)
            domain_labels.extend([f"{domain.capitalize()}\n(With CoCoChain)"] * len(cdft_with))
        
        if cdft_without:
            cdft_data_without.extend(cdft_without)
            domain_labels.extend([f"{domain.capitalize()}\n(Without CoCoChain)"] * len(cdft_without))
    
    # Combine data for box plot
    all_cdft_data = []
    all_labels = []
    
    for i, domain in enumerate(domains):
        cdft_with = results_with_cocochain['cdft_by_domain'][domain]['values']
        cdft_without = results_without_cocochain['cdft_by_domain'][domain]['values']
        
        if cdft_with:
            all_cdft_data.append(cdft_with)
            all_labels.append(f"{domain.capitalize()}\n(With)")
        
        if cdft_without:
            all_cdft_data.append(cdft_without)
            all_labels.append(f"{domain.capitalize()}\n(Without)")
    
    if all_cdft_data:
        box_plot = ax2.boxplot(all_cdft_data, tick_labels=all_labels, patch_artist=True)
        
        # Color the boxes
        colors = ['lightblue', 'lightcoral'] * len(domains)
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    
    ax2.set_xlabel('Domain and Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cross-Domain Finality Time (s)', fontsize=12, fontweight='bold')
    ax2.set_title('CDFT Comparison Across Domains', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('/tmp/hybrid_iov_results.png', dpi=300, bbox_inches='tight')
    print("Saved visualization to /tmp/hybrid_iov_results.png")
    
    return fig

def log_results(results_with, results_without):
    """Log detailed results"""
    print("\n" + "="*80)
    print("HYBRID IoV COCOCHAIN SIMULATION RESULTS")
    print("="*80)
    
    print("\n--- Cross-Domain Finality Time (CDFT) ---")
    for config_name, results in [("WITH CoCoChain", results_with), ("WITHOUT CoCoChain", results_without)]:
        print(f"\n{config_name}:")
        for domain, stats in results['cdft_by_domain'].items():
            print(f"  {domain.capitalize()}: Mean={stats['mean']:.4f}s, Std={stats['std']:.4f}s, "
                  f"Samples={len(stats['values'])}")
    
    print("\n--- Bandwidth Usage (MB/s) per Domain ---")
    for config_name, results in [("WITH CoCoChain", results_with), ("WITHOUT CoCoChain", results_without)]:
        print(f"\n{config_name}:")
        for domain, bandwidth in results['bandwidth_by_domain'].items():
            total = bandwidth['intra'] + bandwidth['inter']
            print(f"  {domain.capitalize()}: Intra={bandwidth['intra']:.4f}, "
                  f"Inter={bandwidth['inter']:.4f}, Total={total:.4f}")
    
    print(f"\n--- Interoperability Overhead (IO) ---")
    print(f"WITH CoCoChain: {results_with['total_io_overhead']:.4f} MB/s")
    print(f"WITHOUT CoCoChain: {results_without['total_io_overhead']:.4f} MB/s")
    
    print("\n" + "="*80)

def main():
    """Main simulation execution"""
    print("Hybrid IoV CoCoChain Simulation")
    print("="*50)
    
    # Run simulation WITH CoCoChain semantic exchange
    print("\n1. Running simulation WITH CoCoChain semantic exchange...")
    network_with = HybridIoVNetwork(enable_cocochain=True)
    results_with = network_with.run_simulation(duration_seconds=60)
    
    # Run simulation WITHOUT CoCoChain semantic exchange  
    print("\n2. Running simulation WITHOUT CoCoChain semantic exchange...")
    network_without = HybridIoVNetwork(enable_cocochain=False)
    results_without = network_without.run_simulation(duration_seconds=60)
    
    # Log detailed results
    log_results(results_with, results_without)
    
    # Create visualizations
    print("\n3. Creating visualizations...")
    fig = create_visualizations(results_with, results_without)
    
    # Save results to CSV for further analysis
    cdft_data = []
    bandwidth_data = []
    
    for config_name, results in [("with_cocochain", results_with), ("without_cocochain", results_without)]:
        for domain, stats in results['cdft_by_domain'].items():
            for cdft_time in stats['values']:
                cdft_data.append({
                    'configuration': config_name,
                    'domain': domain,
                    'cdft_time': cdft_time
                })
        
        for domain, bandwidth in results['bandwidth_by_domain'].items():
            bandwidth_data.append({
                'configuration': config_name,
                'domain': domain,
                'intra_domain_bandwidth': bandwidth['intra'],
                'inter_domain_bandwidth': bandwidth['inter'],
                'total_bandwidth': bandwidth['intra'] + bandwidth['inter']
            })
    
    # Save to CSV
    pd.DataFrame(cdft_data).to_csv('/tmp/cdft_results.csv', index=False)
    pd.DataFrame(bandwidth_data).to_csv('/tmp/bandwidth_results.csv', index=False)
    
    print("Results saved to /tmp/cdft_results.csv and /tmp/bandwidth_results.csv")
    print("\nHybrid IoV simulation completed successfully!")

if __name__ == "__main__":
    main()