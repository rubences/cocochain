#!/usr/bin/env python3
"""
Quick Demo of Hybrid IoV CoCoChain Simulation
Demonstrates key functionality with reduced simulation time
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_iov_simulation import HybridIoVNetwork, log_results

def quick_demo():
    """Run a quick demonstration of the hybrid IoV simulation"""
    print("Hybrid IoV CoCoChain - Quick Demo")
    print("="*50)
    
    print("\n📊 System Configuration:")
    print("  • 3 Domains: Urban, Interurban, Rural")
    print("  • 3-5 RSUs per domain as validator nodes")  
    print("  • 300 vehicles distributed across domains")
    print("  • SAE models for semantic concept exchange")
    print("  • Inter-domain synchronization every 30s")
    
    # Quick simulation with reduced time
    print("\n🚀 Running quick simulation (20 seconds)...")
    
    # WITH CoCoChain
    print("\n1. WITH CoCoChain semantic exchange:")
    network_with = HybridIoVNetwork(enable_cocochain=True)
    results_with = network_with.run_simulation(duration_seconds=20)
    
    # WITHOUT CoCoChain  
    print("\n2. WITHOUT CoCoChain semantic exchange:")
    network_without = HybridIoVNetwork(enable_cocochain=False)
    results_without = network_without.run_simulation(duration_seconds=20)
    
    # Quick summary
    print("\n📈 Key Results Summary:")
    print("-" * 50)
    
    # CDFT comparison
    cdft_with = sum(len(v['values']) for v in results_with['cdft_by_domain'].values())
    cdft_without = sum(len(v['values']) for v in results_without['cdft_by_domain'].values())
    
    avg_cdft_with = sum(sum(v['values']) for v in results_with['cdft_by_domain'].values()) / max(cdft_with, 1)
    avg_cdft_without = sum(sum(v['values']) for v in results_without['cdft_by_domain'].values()) / max(cdft_without, 1)
    
    print(f"Average CDFT:")
    print(f"  • With CoCoChain:    {avg_cdft_with:.3f}s ({cdft_with} transactions)")
    print(f"  • Without CoCoChain: {avg_cdft_without:.3f}s ({cdft_without} transactions)")
    
    # IO Overhead
    io_overhead = results_with['total_io_overhead']
    print(f"\nInteroperability Overhead: {io_overhead:.3f} MB/s")
    
    # Bandwidth summary
    total_bw_with = sum(v['intra'] + v['inter'] for v in results_with['bandwidth_by_domain'].values())
    total_bw_without = sum(v['intra'] + v['inter'] for v in results_without['bandwidth_by_domain'].values())
    
    print(f"\nTotal Bandwidth Usage:")
    print(f"  • With CoCoChain:    {total_bw_with:.1f} MB/s")
    print(f"  • Without CoCoChain: {total_bw_without:.1f} MB/s")
    
    print(f"\n✅ Demo completed! For full analysis, run:")
    print(f"   python3 scripts/hybrid_iov_simulation.py")
    print(f"   python3 scripts/analyze_hybrid_results.py")

if __name__ == "__main__":
    quick_demo()