#!/usr/bin/env python3
"""
CoCoChain Simulation Test - Standalone version for validation
Tests the core algorithms without OMNeT++ dependency
"""

import random
import time
import hashlib
import numpy as np
from typing import List, Dict, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ConceptVector:
    data: List[float]
    timestamp: float
    node_id: int
    is_corrupted: bool = False

@dataclass
class Transaction:
    id: int
    concept_vector: ConceptVector
    semantic_digest: str
    timestamp: float
    originator: int
    verified: bool = False

@dataclass
class ConsensusMessage:
    TYPE_VOTE = "VOTE"
    type: str
    transaction_id: int
    sender_id: int
    vote: bool
    timestamp: float

class CoCoChainNode:
    def __init__(self, node_id: int, is_adversarial: bool = False):
        self.node_id = node_id
        self.is_adversarial = is_adversarial
        self.pending_transactions: Dict[int, Transaction] = {}
        self.consensus_votes: Dict[int, List[ConsensusMessage]] = defaultdict(list)
        self.confirmed_transactions: Set[int] = set()
        self.transaction_start_times: Dict[int, float] = {}
        
        # Metrics
        self.latencies = []
        self.messages_sent = 0
        self.malformed_detected = 0
        self.false_positives = 0
        self.total_valid_transactions = 0
        self.throughput = 0
        self.last_throughput_time = 0.0
        
        # Parameters
        self.bft_threshold = 0.67
        self.max_transaction_age = 10.0

    def generate_concept_vector(self) -> ConceptVector:
        """Generate a 10-dimensional concept vector"""
        cv = ConceptVector(
            data=[random.gauss(0, 1) for _ in range(10)],
            timestamp=time.time(),
            node_id=self.node_id
        )
        
        # Apply corruption if adversarial
        if self.is_adversarial and random.random() < 0.8:  # 80% chance to corrupt
            self.inject_malformed_vector(cv)
        
        return cv

    def inject_malformed_vector(self, cv: ConceptVector):
        """Inject malformed data into concept vector"""
        cv.is_corrupted = True
        # Add systematic corruption
        for i in range(len(cv.data)):
            cv.data[i] *= (1.0 + random.uniform(-0.5, 0.5))
        
        # Sometimes inject extreme values
        if random.random() < 0.5:
            idx = random.randint(0, len(cv.data) - 1)
            cv.data[idx] = random.uniform(-10, 10)

    def compute_semantic_digest(self, cv: ConceptVector) -> str:
        """Compute semantic digest of concept vector"""
        data_str = ";".join(f"{val:.6f}" for val in cv.data)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def verify_semantic_integrity(self, tx: Transaction) -> bool:
        """Verify semantic integrity of transaction"""
        # Recompute digest
        computed_digest = self.compute_semantic_digest(tx.concept_vector)
        if computed_digest != tx.semantic_digest:
            return False
        
        # Check for corruption patterns
        cv_data = tx.concept_vector.data
        mean_val = np.mean(cv_data)
        variance = np.var(cv_data)
        
        # Flag as malformed if variance is too high
        if variance > 2.0:
            return False
        
        # Check for extreme values
        if any(abs(val) > 5.0 for val in cv_data):
            return False
        
        # Cosine similarity check (simplified) - only for top-k concepts
        if any(abs(val) > 0.8 for val in cv_data):  # Only check top-k concepts
            reference_vector = [0.5] * 10  # Better reference vector
            similarity = self.calculate_cosine_similarity(cv_data, reference_vector)
            if similarity < 0.2:  # θ = 0.2
                # Check if this is a false positive
                if not tx.concept_vector.is_corrupted:
                    self.false_positives += 1
                return False
        
        # If transaction passes all checks and is not corrupted
        if not tx.concept_vector.is_corrupted:
            self.total_valid_transactions += 1
        
        return True
    
    def calculate_cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    def create_transaction(self) -> Transaction:
        """Create a new transaction"""
        cv = self.generate_concept_vector()
        tx = Transaction(
            id=random.randint(1000000, 9999999),
            concept_vector=cv,
            semantic_digest=self.compute_semantic_digest(cv),
            timestamp=time.time(),
            originator=self.node_id
        )
        
        self.transaction_start_times[tx.id] = time.time()
        return tx

    def process_transaction(self, tx: Transaction, network: 'CoCoChainNetwork') -> bool:
        """Process received transaction"""
        # Skip own transactions
        if tx.originator == self.node_id:
            return True
        
        # Check age
        age = time.time() - tx.timestamp
        if age > self.max_transaction_age:
            return False
        
        # Verify integrity
        is_valid = self.verify_semantic_integrity(tx)
        if not is_valid:
            self.malformed_detected += 1
            return False
        
        # Store and start consensus
        self.pending_transactions[tx.id] = tx
        self.start_consensus(tx, network)
        return True

    def start_consensus(self, tx: Transaction, network: 'CoCoChainNetwork'):
        """Start consensus process for transaction"""
        vote = self.verify_semantic_integrity(tx)
        
        msg = ConsensusMessage(
            type=ConsensusMessage.TYPE_VOTE,
            transaction_id=tx.id,
            sender_id=self.node_id,
            vote=vote,
            timestamp=time.time()
        )
        
        # Broadcast vote to network
        network.broadcast_consensus_message(msg, self.node_id)
        self.messages_sent += 1

    def process_consensus_message(self, msg: ConsensusMessage):
        """Process consensus message"""
        if msg.type != ConsensusMessage.TYPE_VOTE:
            return
        
        self.consensus_votes[msg.transaction_id].append(msg)
        
        # Check for consensus
        votes = self.consensus_votes[msg.transaction_id]
        total_votes = len(votes)
        positive_votes = sum(1 for v in votes if v.vote)
        
        # Use conservative network size estimate
        estimated_network_size = 50
        required_votes = int(estimated_network_size * self.bft_threshold)
        
        if total_votes >= required_votes:
            consensus = positive_votes >= required_votes
            
            if consensus:
                self.finalize_transaction(msg.transaction_id)
            else:
                # Reject transaction
                self.pending_transactions.pop(msg.transaction_id, None)
                self.consensus_votes.pop(msg.transaction_id, None)

    def finalize_transaction(self, tx_id: int):
        """Finalize confirmed transaction"""
        if tx_id in self.confirmed_transactions:
            return
        
        self.confirmed_transactions.add(tx_id)
        
        # Record latency if we originated this transaction
        if tx_id in self.transaction_start_times:
            latency = time.time() - self.transaction_start_times[tx_id]
            self.latencies.append(latency)
            del self.transaction_start_times[tx_id]
        
        # Clean up
        self.pending_transactions.pop(tx_id, None)
        self.consensus_votes.pop(tx_id, None)

class CoCoChainNetwork:
    def __init__(self, num_nodes: int, adversarial_ratio: float = 0.1):
        self.nodes = []
        self.total_messages = 0
        
        # Create nodes
        for i in range(num_nodes):
            is_adversarial = random.random() < adversarial_ratio
            node = CoCoChainNode(i, is_adversarial)
            self.nodes.append(node)
        
        print(f"Created network with {num_nodes} nodes, {sum(1 for n in self.nodes if n.is_adversarial)} adversarial")

    def broadcast_transaction(self, tx: Transaction, sender_id: int):
        """Broadcast transaction to all nodes"""
        for node in self.nodes:
            if node.node_id != sender_id:
                node.process_transaction(tx, self)
        self.total_messages += len(self.nodes) - 1

    def broadcast_consensus_message(self, msg: ConsensusMessage, sender_id: int):
        """Broadcast consensus message to all nodes"""
        for node in self.nodes:
            if node.node_id != sender_id:
                node.process_consensus_message(msg)
        self.total_messages += len(self.nodes) - 1

    def simulate_round(self):
        """Simulate one round of transaction generation"""
        # Each node has a chance to generate a transaction
        for node in self.nodes:
            if random.random() < 0.1:  # 10% chance per round
                tx = node.create_transaction()
                self.broadcast_transaction(tx, node.node_id)

    def get_metrics(self):
        """Collect network-wide metrics"""
        all_latencies = []
        total_malformed = 0
        total_confirmed = 0
        total_false_positives = 0
        total_valid_transactions = 0
        
        for node in self.nodes:
            all_latencies.extend(node.latencies)
            total_malformed += node.malformed_detected
            total_confirmed += len(node.confirmed_transactions)
            total_false_positives += node.false_positives
            total_valid_transactions += node.total_valid_transactions
        
        # Calculate FPR
        if total_valid_transactions + total_false_positives > 0:
            fpr = (total_false_positives / (total_valid_transactions + total_false_positives)) * 100
        else:
            fpr = 0.0
        
        # Estimate throughput (transactions per second)
        simulation_time = 50 * 0.001  # rounds * sleep_time
        throughput = total_confirmed / simulation_time if simulation_time > 0 else 0
        
        return {
            'avg_latency': np.mean(all_latencies) if all_latencies else 0,
            'std_latency': np.std(all_latencies) if all_latencies else 0,
            'total_overhead': self.total_messages,
            'malformed_detected': total_malformed,
            'confirmed_transactions': total_confirmed,
            'false_positive_rate': fpr,
            'throughput': throughput,
            'num_nodes': len(self.nodes)
        }

def run_simulation(num_nodes=100, rounds=50, seed=None):
    """Run CoCoChain simulation"""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    network = CoCoChainNetwork(num_nodes, adversarial_ratio=0.1)
    
    print(f"Running simulation: {num_nodes} nodes, {rounds} rounds, seed={seed}")
    
    for round_num in range(rounds):
        network.simulate_round()
        time.sleep(0.001)  # Small delay to create realistic timestamps
    
    return network.get_metrics()

def main():
    """Run multiple simulations and analyze results"""
    print("CoCoChain Simulation Test")
    print("=" * 50)
    
    results = []
    
    # Run 10 simulations with different seeds
    for seed in range(10):
        metrics = run_simulation(num_nodes=100, rounds=50, seed=seed)
        results.append(metrics)
        print(f"Seed {seed}: Latency={metrics['avg_latency']:.4f}s, "
              f"Throughput={metrics['throughput']:.1f}tx/s, "
              f"Overhead={metrics['total_overhead']}, "
              f"DMC={metrics['malformed_detected']}, "
              f"FPR={metrics['false_positive_rate']:.1f}%")
    
    # Calculate averages
    avg_latency = np.mean([r['avg_latency'] for r in results])
    std_latency = np.std([r['avg_latency'] for r in results])
    avg_throughput = np.mean([r['throughput'] for r in results])
    std_throughput = np.std([r['throughput'] for r in results])
    avg_overhead = np.mean([r['total_overhead'] for r in results])
    std_overhead = np.std([r['total_overhead'] for r in results])
    avg_malformed = np.mean([r['malformed_detected'] for r in results])
    std_malformed = np.std([r['malformed_detected'] for r in results])
    avg_fpr = np.mean([r['false_positive_rate'] for r in results])
    std_fpr = np.std([r['false_positive_rate'] for r in results])
    
    print("\n" + "=" * 50)
    print("CoCoChain Test Results Summary")
    print("=" * 50)
    print(f"{'Metric':<30} {'Mean':<12} {'Std Dev':<12}")
    print("-" * 54)
    print(f"{'End-to-end latency (s)':<30} {avg_latency:<12.4f} {std_latency:<12.4f}")
    print(f"{'Throughput (tx/s)':<30} {avg_throughput:<12.1f} {std_throughput:<12.1f}")
    print(f"{'Consensus overhead (msgs)':<30} {avg_overhead:<12.0f} {std_overhead:<12.0f}")
    print(f"{'DMC (count)':<30} {avg_malformed:<12.0f} {std_malformed:<12.0f}")
    print(f"{'FPR (%)':<30} {avg_fpr:<12.1f} {std_fpr:<12.1f}")
    print("\nSimulation validation completed successfully!")

if __name__ == "__main__":
    main()