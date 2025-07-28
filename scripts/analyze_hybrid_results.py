#!/usr/bin/env python3
"""
Hybrid IoV CoCoChain Results Analysis
Advanced analysis and reporting for the hybrid IoV simulation results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for publication quality
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_results():
    """Load simulation results from CSV files"""
    try:
        cdft_df = pd.read_csv('/tmp/cdft_results.csv')
        bandwidth_df = pd.read_csv('/tmp/bandwidth_results.csv')
        return cdft_df, bandwidth_df
    except FileNotFoundError:
        print("Error: Result files not found. Please run hybrid_iov_simulation.py first.")
        return None, None

def create_publication_plots(cdft_df, bandwidth_df):
    """Create publication-quality plots with enhanced styling"""
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. Enhanced Bandwidth Distribution Chart
    ax1 = fig.add_subplot(gs[0, :])
    
    # Prepare bandwidth data
    domains = ['urban', 'interurban', 'rural']
    with_data = bandwidth_df[bandwidth_df['configuration'] == 'with_cocochain']
    without_data = bandwidth_df[bandwidth_df['configuration'] == 'without_cocochain']
    
    x = np.arange(len(domains))
    width = 0.35
    
    # Plot bars
    intra_with = [with_data[with_data['domain'] == d]['intra_domain_bandwidth'].iloc[0] for d in domains]
    inter_with = [with_data[with_data['domain'] == d]['inter_domain_bandwidth'].iloc[0] for d in domains]
    intra_without = [without_data[without_data['domain'] == d]['intra_domain_bandwidth'].iloc[0] for d in domains]
    inter_without = [without_data[without_data['domain'] == d]['inter_domain_bandwidth'].iloc[0] for d in domains]
    
    bars1 = ax1.bar(x - width/2, intra_with, width, label='Intra-domain (With CoCoChain)', 
                    color='#2E86C1', alpha=0.8)
    bars2 = ax1.bar(x - width/2, inter_with, width, bottom=intra_with, 
                    label='Inter-domain (With CoCoChain)', color='#E74C3C', alpha=0.8)
    bars3 = ax1.bar(x + width/2, intra_without, width, label='Intra-domain (Without CoCoChain)', 
                    color='#5DADE2', alpha=0.8)
    bars4 = ax1.bar(x + width/2, inter_without, width, bottom=intra_without, 
                    label='Inter-domain (Without CoCoChain)', color='#F1948A', alpha=0.8)
    
    # Add value labels on bars
    def add_value_labels(bars, values):
        for bar, value in zip(bars, values):
            if value > 0:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_y() + height/2,
                        f'{value:.1f}', ha='center', va='center', fontweight='bold', color='white')
    
    add_value_labels(bars1, intra_with)
    add_value_labels(bars2, inter_with)
    add_value_labels(bars3, intra_without)
    
    ax1.set_xlabel('Domain Type', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Bandwidth Usage (MB/s)', fontsize=14, fontweight='bold')
    ax1.set_title('Bandwidth Distribution: Intra vs Inter-domain Communication', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels([d.capitalize() for d in domains], fontsize=12)
    ax1.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Enhanced CDFT Box Plot
    ax2 = fig.add_subplot(gs[1, 0])
    
    # Prepare CDFT data for box plot
    plot_data = []
    labels = []
    
    for domain in domains:
        # With CoCoChain
        with_cdft = cdft_df[(cdft_df['configuration'] == 'with_cocochain') & 
                           (cdft_df['domain'] == domain)]['cdft_time'].values
        if len(with_cdft) > 0:
            plot_data.append(with_cdft)
            labels.append(f'{domain.capitalize()}\n(With)')
        
        # Without CoCoChain
        without_cdft = cdft_df[(cdft_df['configuration'] == 'without_cocochain') & 
                              (cdft_df['domain'] == domain)]['cdft_time'].values
        if len(without_cdft) > 0:
            plot_data.append(without_cdft)
            labels.append(f'{domain.capitalize()}\n(Without)')
    
    bp = ax2.boxplot(plot_data, tick_labels=labels, patch_artist=True, notch=True)
    
    # Color the boxes alternately
    colors = ['#3498DB', '#E67E22'] * (len(plot_data) // 2 + 1)
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_xlabel('Domain and Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cross-Domain Finality Time (s)', fontsize=12, fontweight='bold')
    ax2.set_title('CDFT Distribution Across Domains', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right', fontsize=10)
    
    # 3. Performance Summary Statistics
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    
    # Calculate summary statistics
    summary_stats = []
    for config in ['with_cocochain', 'without_cocochain']:
        config_data = cdft_df[cdft_df['configuration'] == config]
        avg_cdft = config_data['cdft_time'].mean()
        std_cdft = config_data['cdft_time'].std()
        samples = len(config_data)
        
        # Bandwidth totals
        bandwidth_config = bandwidth_df[bandwidth_df['configuration'] == config]
        total_bandwidth = bandwidth_config['total_bandwidth'].sum()
        inter_bandwidth = bandwidth_config['inter_domain_bandwidth'].sum()
        
        summary_stats.append({
            'Configuration': config.replace('_', ' ').title(),
            'Avg CDFT (s)': f'{avg_cdft:.3f} ± {std_cdft:.3f}',
            'Samples': f'{samples:,}',
            'Total BW (MB/s)': f'{total_bandwidth:.1f}',
            'Inter-domain BW': f'{inter_bandwidth:.1f}',
            'IO Overhead': f'{inter_bandwidth:.3f}' if inter_bandwidth > 0 else '0.000'
        })
    
    # Create table
    table_data = []
    headers = list(summary_stats[0].keys())
    for stat in summary_stats:
        table_data.append(list(stat.values()))
    
    table = ax3.table(cellText=table_data, colLabels=headers, 
                     cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style the table
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#3498DB')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ECF0F1')
    
    ax3.set_title('Performance Summary', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('/home/runner/work/cocochain/cocochain/hybrid_iov_analysis.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Enhanced analysis saved to hybrid_iov_analysis.png")
    
    return fig

def generate_latex_table(cdft_df, bandwidth_df):
    """Generate LaTeX table for publication"""
    
    latex_output = """
\\begin{table}[h]
\\centering
\\caption{Hybrid IoV CoCoChain Performance Comparison}
\\label{tab:hybrid_iov_performance}
\\begin{tabular}{|l|c|c|c|c|}
\\hline
\\textbf{Domain} & \\textbf{Configuration} & \\textbf{CDFT (s)} & \\textbf{Intra BW (MB/s)} & \\textbf{Inter BW (MB/s)} \\\\
\\hline
"""
    
    domains = ['urban', 'interurban', 'rural']
    
    for domain in domains:
        # With CoCoChain
        with_cdft = cdft_df[(cdft_df['configuration'] == 'with_cocochain') & 
                           (cdft_df['domain'] == domain)]['cdft_time']
        with_bw = bandwidth_df[(bandwidth_df['configuration'] == 'with_cocochain') & 
                              (bandwidth_df['domain'] == domain)].iloc[0]
        
        latex_output += f"{domain.capitalize()} & With CoCoChain & {with_cdft.mean():.3f} ± {with_cdft.std():.3f} & {with_bw['intra_domain_bandwidth']:.1f} & {with_bw['inter_domain_bandwidth']:.3f} \\\\\n"
        
        # Without CoCoChain
        without_cdft = cdft_df[(cdft_df['configuration'] == 'without_cocochain') & 
                              (cdft_df['domain'] == domain)]['cdft_time']
        without_bw = bandwidth_df[(bandwidth_df['configuration'] == 'without_cocochain') & 
                                 (bandwidth_df['domain'] == domain)].iloc[0]
        
        latex_output += f" & Without CoCoChain & {without_cdft.mean():.3f} ± {without_cdft.std():.3f} & {without_bw['intra_domain_bandwidth']:.1f} & {without_bw['inter_domain_bandwidth']:.3f} \\\\\n"
        latex_output += "\\hline\n"
    
    latex_output += """\\end{tabular}
\\end{table}
"""
    
    with open('/home/runner/work/cocochain/cocochain/results/performance_table.tex', 'w') as f:
        f.write(latex_output)
    
    print("LaTeX table saved to results/performance_table.tex")
    return latex_output

def print_detailed_analysis(cdft_df, bandwidth_df):
    """Print detailed analysis results"""
    
    print("\n" + "="*100)
    print("DETAILED HYBRID IoV COCOCHAIN ANALYSIS")
    print("="*100)
    
    # Domain-wise analysis
    domains = ['urban', 'interurban', 'rural']
    
    print("\n--- CROSS-DOMAIN FINALITY TIME (CDFT) ANALYSIS ---")
    for domain in domains:
        print(f"\n{domain.upper()} DOMAIN:")
        
        with_cdft = cdft_df[(cdft_df['configuration'] == 'with_cocochain') & 
                           (cdft_df['domain'] == domain)]['cdft_time']
        without_cdft = cdft_df[(cdft_df['configuration'] == 'without_cocochain') & 
                              (cdft_df['domain'] == domain)]['cdft_time']
        
        print(f"  With CoCoChain:    Mean={with_cdft.mean():.4f}s, Std={with_cdft.std():.4f}s, "
              f"Min={with_cdft.min():.4f}s, Max={with_cdft.max():.4f}s")
        print(f"  Without CoCoChain: Mean={without_cdft.mean():.4f}s, Std={without_cdft.std():.4f}s, "
              f"Min={without_cdft.min():.4f}s, Max={without_cdft.max():.4f}s")
        
        # Performance impact
        impact = ((with_cdft.mean() - without_cdft.mean()) / without_cdft.mean()) * 100
        print(f"  Performance Impact: {impact:+.2f}% (positive = slower with CoCoChain)")
    
    print("\n--- BANDWIDTH USAGE ANALYSIS ---")
    for domain in domains:
        print(f"\n{domain.upper()} DOMAIN:")
        
        with_bw = bandwidth_df[(bandwidth_df['configuration'] == 'with_cocochain') & 
                              (bandwidth_df['domain'] == domain)].iloc[0]
        without_bw = bandwidth_df[(bandwidth_df['configuration'] == 'without_cocochain') & 
                                 (bandwidth_df['domain'] == domain)].iloc[0]
        
        print(f"  With CoCoChain:")
        print(f"    Intra-domain: {with_bw['intra_domain_bandwidth']:.2f} MB/s")
        print(f"    Inter-domain: {with_bw['inter_domain_bandwidth']:.2f} MB/s")
        print(f"    Total:        {with_bw['total_bandwidth']:.2f} MB/s")
        
        print(f"  Without CoCoChain:")
        print(f"    Intra-domain: {without_bw['intra_domain_bandwidth']:.2f} MB/s")
        print(f"    Inter-domain: {without_bw['inter_domain_bandwidth']:.2f} MB/s")
        print(f"    Total:        {without_bw['total_bandwidth']:.2f} MB/s")
        
        # Overhead calculation
        overhead = with_bw['inter_domain_bandwidth']
        overhead_pct = (overhead / with_bw['total_bandwidth']) * 100 if with_bw['total_bandwidth'] > 0 else 0
        print(f"  Interoperability Overhead: {overhead:.3f} MB/s ({overhead_pct:.2f}% of total)")
    
    # Overall statistics
    print("\n--- OVERALL SYSTEM PERFORMANCE ---")
    
    total_with_bandwidth = bandwidth_df[bandwidth_df['configuration'] == 'with_cocochain']['total_bandwidth'].sum()
    total_without_bandwidth = bandwidth_df[bandwidth_df['configuration'] == 'without_cocochain']['total_bandwidth'].sum()
    total_inter_bandwidth = bandwidth_df[bandwidth_df['configuration'] == 'with_cocochain']['inter_domain_bandwidth'].sum()
    
    print(f"Total Bandwidth Usage:")
    print(f"  With CoCoChain:    {total_with_bandwidth:.2f} MB/s")
    print(f"  Without CoCoChain: {total_without_bandwidth:.2f} MB/s")
    print(f"  Inter-domain Only: {total_inter_bandwidth:.2f} MB/s")
    print(f"  System IO Overhead: {total_inter_bandwidth:.3f} MB/s "
          f"({(total_inter_bandwidth/total_with_bandwidth)*100:.2f}% of total)")
    
    avg_cdft_with = cdft_df[cdft_df['configuration'] == 'with_cocochain']['cdft_time'].mean()
    avg_cdft_without = cdft_df[cdft_df['configuration'] == 'without_cocochain']['cdft_time'].mean()
    
    print(f"\nAverage CDFT:")
    print(f"  With CoCoChain:    {avg_cdft_with:.4f}s")
    print(f"  Without CoCoChain: {avg_cdft_without:.4f}s")
    print(f"  Latency Overhead:  {avg_cdft_with - avg_cdft_without:+.4f}s "
          f"({((avg_cdft_with - avg_cdft_without)/avg_cdft_without)*100:+.2f}%)")
    
    print("\n" + "="*100)

def main():
    """Main analysis function"""
    print("Hybrid IoV CoCoChain Results Analysis")
    print("="*50)
    
    # Load data
    cdft_df, bandwidth_df = load_results()
    if cdft_df is None or bandwidth_df is None:
        return
    
    print(f"Loaded {len(cdft_df)} CDFT measurements and {len(bandwidth_df)} bandwidth measurements")
    
    # Create enhanced visualizations
    print("\n1. Creating enhanced visualizations...")
    fig = create_publication_plots(cdft_df, bandwidth_df)
    
    # Generate LaTeX table
    print("\n2. Generating LaTeX table...")
    latex_table = generate_latex_table(cdft_df, bandwidth_df)
    
    # Print detailed analysis
    print("\n3. Performing detailed analysis...")
    print_detailed_analysis(cdft_df, bandwidth_df)
    
    print("\nAnalysis completed successfully!")
    print("Generated files:")
    print("  - hybrid_iov_analysis.png (Enhanced visualization)")
    print("  - results/performance_table.tex (LaTeX table)")

if __name__ == "__main__":
    main()