import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def create_chain_comparison_visualization():
    """Create comprehensive visualization of chain comparison results"""
    
    # Load the results
    df = pd.read_csv('chain_comparison_results.csv')
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. TVL Growth Comparison
    ax1 = plt.subplot(2, 3, 1)
    bars1 = plt.bar(df['Chain'], df['TVL_Change_Percent'], 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('TVL Growth Since Target Date', fontsize=14, fontweight='bold')
    plt.ylabel('Growth (%)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars1, df['TVL_Change_Percent']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 2. USDC Growth Comparison
    ax2 = plt.subplot(2, 3, 2)
    bars2 = plt.bar(df['Chain'], df['USDC_Change_Percent'], 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('USDC Circulation Growth Since Target Date', fontsize=14, fontweight='bold')
    plt.ylabel('Growth (%)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars2, df['USDC_Change_Percent']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 3. Total Stablecoin Growth Comparison
    ax3 = plt.subplot(2, 3, 3)
    bars3 = plt.bar(df['Chain'], df['Total_Stable_Change_Percent'], 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('Total Stablecoin Circulation Growth Since Target Date', fontsize=14, fontweight='bold')
    plt.ylabel('Growth (%)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars3, df['Total_Stable_Change_Percent']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 4. Current TVL Comparison
    ax4 = plt.subplot(2, 3, 4)
    bars4 = plt.bar(df['Chain'], df['Current_TVL'] / 1e6, 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('Current TVL (Millions USD)', fontsize=14, fontweight='bold')
    plt.ylabel('TVL (Millions USD)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars4, df['Current_TVL'] / 1e6):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                f'${value:.0f}M', ha='center', va='bottom', fontweight='bold')
    
    # 5. Current USDC Circulation
    ax5 = plt.subplot(2, 3, 5)
    bars5 = plt.bar(df['Chain'], df['Current_USDC'] / 1e6, 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('Current USDC Circulation (Millions USD)', fontsize=14, fontweight='bold')
    plt.ylabel('USDC (Millions USD)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars5, df['Current_USDC'] / 1e6):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                f'${value:.0f}M', ha='center', va='bottom', fontweight='bold')
    
    # 6. Current Total Stablecoin Circulation
    ax6 = plt.subplot(2, 3, 6)
    bars6 = plt.bar(df['Chain'], df['Current_Total_Stable'] / 1e6, 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title('Current Total Stablecoin Circulation (Millions USD)', fontsize=14, fontweight='bold')
    plt.ylabel('Total Stablecoins (Millions USD)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars6, df['Current_Total_Stable'] / 1e6):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                f'${value:.0f}M', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('chain_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create a summary table
    print("\n" + "="*100)
    print("CHAIN COMPARISON ANALYSIS SUMMARY")
    print("="*100)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    for _, row in df.iterrows():
        print(f"\n{row['Chain']} (Target Date: {row['Target_Date']})")
        print("-" * 60)
        print(f"TVL Growth:          {row['TVL_Change_Percent']:>8.2f}%  (${row['Historical_TVL']:>12,.0f} → ${row['Current_TVL']:>12,.0f})")
        print(f"USDC Growth:         {row['USDC_Change_Percent']:>8.2f}%  (${row['Historical_USDC']:>12,.0f} → ${row['Current_USDC']:>12,.0f})")
        print(f"Total Stable Growth: {row['Total_Stable_Change_Percent']:>8.2f}%  (${row['Historical_Total_Stable']:>12,.0f} → ${row['Current_Total_Stable']:>12,.0f})")
    
    # Create a radar chart for growth comparison
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
    
    # Prepare data for radar chart
    categories = ['TVL Growth', 'USDC Growth', 'Total Stable Growth']
    values = df[['TVL_Change_Percent', 'USDC_Change_Percent', 'Total_Stable_Change_Percent']].values
    
    # Number of variables
    N = len(categories)
    
    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], categories, size=12)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([50, 100, 200, 400, 600, 800], ["50%", "100%", "200%", "400%", "600%", "800%"], 
               color="grey", size=10)
    plt.ylim(0, 800)
    
    # Plot data
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    for i, (chain, color) in enumerate(zip(df['Chain'], colors)):
        values_chain = values[i].tolist()
        values_chain += values_chain[:1]
        ax.plot(angles, values_chain, linewidth=2, linestyle='solid', label=chain, color=color)
        ax.fill(angles, values_chain, alpha=0.1, color=color)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    plt.title('Growth Comparison Radar Chart', size=15, y=1.1)
    
    plt.tight_layout()
    plt.savefig('chain_growth_radar.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nVisualizations saved:")
    print(f"- chain_comparison_analysis.png")
    print(f"- chain_growth_radar.png")

def create_detailed_report():
    """Create a detailed text report with insights"""
    
    df = pd.read_csv('chain_comparison_results.csv')
    
    print("\n" + "="*100)
    print("DETAILED ANALYSIS REPORT")
    print("="*100)
    
    # Find the best performer in each category
    best_tvl = df.loc[df['TVL_Change_Percent'].idxmax()]
    best_usdc = df.loc[df['USDC_Change_Percent'].idxmax()]
    best_total = df.loc[df['Total_Stable_Change_Percent'].idxmax()]
    
    print(f"\n🏆 PERFORMANCE HIGHLIGHTS:")
    print(f"   • Best TVL Growth: {best_tvl['Chain']} ({best_tvl['TVL_Change_Percent']:.1f}%)")
    print(f"   • Best USDC Growth: {best_usdc['Chain']} ({best_usdc['USDC_Change_Percent']:.1f}%)")
    print(f"   • Best Total Stablecoin Growth: {best_total['Chain']} ({best_total['Total_Stable_Change_Percent']:.1f}%)")
    
    print(f"\n📊 CHAIN-SPECIFIC INSIGHTS:")
    
    for _, row in df.iterrows():
        print(f"\n{row['Chain']} Analysis:")
        print(f"   • Time Period: {row['Target_Date']} to {datetime.now().strftime('%Y-%m-%d')}")
        
        # Calculate days between dates
        target_date = datetime.strptime(row['Target_Date'], '%Y-%m-%d')
        days_diff = (datetime.now() - target_date).days
        
        print(f"   • Duration: {days_diff} days")
        
        # Annualized growth rates
        tvl_annual = ((1 + row['TVL_Change_Percent']/100) ** (365/days_diff) - 1) * 100 if days_diff > 0 else 0
        usdc_annual = ((1 + row['USDC_Change_Percent']/100) ** (365/days_diff) - 1) * 100 if days_diff > 0 else 0
        total_annual = ((1 + row['Total_Stable_Change_Percent']/100) ** (365/days_diff) - 1) * 100 if days_diff > 0 else 0
        
        print(f"   • Annualized TVL Growth: {tvl_annual:.1f}%")
        print(f"   • Annualized USDC Growth: {usdc_annual:.1f}%")
        print(f"   • Annualized Total Stablecoin Growth: {total_annual:.1f}%")
        
        # Market share analysis
        total_tvl = df['Current_TVL'].sum()
        total_usdc = df['Current_USDC'].sum()
        total_stable = df['Current_Total_Stable'].sum()
        
        tvl_share = (row['Current_TVL'] / total_tvl) * 100
        usdc_share = (row['Current_USDC'] / total_usdc) * 100
        stable_share = (row['Current_Total_Stable'] / total_stable) * 100
        
        print(f"   • Market Share: {tvl_share:.1f}% of total TVL, {usdc_share:.1f}% of total USDC, {stable_share:.1f}% of total stablecoins")
    
    print(f"\n💡 KEY OBSERVATIONS:")
    print(f"   • All three chains show significant growth across all metrics")
    print(f"   • Aptos shows the most dramatic growth, particularly in stablecoin adoption")
    print(f"   • Sui demonstrates strong balanced growth across all metrics")
    print(f"   • Sonic, being the most recent, shows more modest but still impressive growth")
    print(f"   • USDC adoption is growing faster than TVL in all chains, indicating strong stablecoin ecosystem development")

if __name__ == "__main__":
    create_chain_comparison_visualization()
    create_detailed_report() 