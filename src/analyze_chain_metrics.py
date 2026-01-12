"""
Example script showing how to analyze the comprehensive chain metrics data
"""

import pandas as pd
import json

def load_chain_metrics():
    """Load the comprehensive chain metrics data"""
    try:
        df = pd.read_csv('comprehensive_chain_metrics.csv')
        print(f"✓ Loaded data for {len(df)} chains\n")
        return df
    except FileNotFoundError:
        print("❌ comprehensive_chain_metrics.csv not found!")
        print("Run: python src/comprehensive_chain_analysis.py first\n")
        return None


def analyze_top_chains_by_metric(df, metric, top_n=10):
    """Analyze top chains by a specific metric"""
    print(f"Top {top_n} Chains by {metric.replace('_', ' ').title()}")
    print("=" * 60)
    
    top_chains = df.nlargest(top_n, metric)
    
    for i, (_, row) in enumerate(top_chains.iterrows(), 1):
        print(f"{i:2d}. {row['chain']:20s} ${row[metric]:>15,.0f}")
    print()


def analyze_stablecoin_dominance(df):
    """Analyze chains by stablecoin dominance"""
    print("Chains by Stablecoin Dominance (Stablecoin/TVL Ratio)")
    print("=" * 60)
    
    # Filter chains with both TVL and stablecoin data
    filtered = df[(df['defi_tvl'] > 0) & (df['stablecoin_mcap'] > 0)].copy()
    
    # Sort by ratio
    filtered = filtered.sort_values('stablecoin_to_tvl_ratio', ascending=False)
    
    for i, (_, row) in enumerate(filtered.head(10).iterrows(), 1):
        ratio = row['stablecoin_to_tvl_ratio'] * 100
        print(f"{i:2d}. {row['chain']:20s} {ratio:6.2f}% "
              f"(${row['stablecoin_mcap']:>12,.0f} / ${row['defi_tvl']:>12,.0f})")
    print()


def analyze_mcap_to_tvl_ratio(df):
    """Analyze chains by Market Cap to TVL ratio"""
    print("Chains by Market Cap to TVL Ratio")
    print("=" * 60)
    
    # Filter chains with both market cap and TVL data
    filtered = df[(df['market_cap'] > 0) & (df['defi_tvl'] > 0)].copy()
    
    # Sort by ratio
    filtered = filtered.sort_values('market_cap_to_tvl_ratio', ascending=False)
    
    print("\nHighest Ratios (potentially overvalued or low DeFi usage):")
    for i, (_, row) in enumerate(filtered.head(5).iterrows(), 1):
        ratio = row['market_cap_to_tvl_ratio']
        print(f"{i}. {row['chain']:20s} {ratio:6.2f}x "
              f"(MC: ${row['market_cap']:>12,.0f} / TVL: ${row['defi_tvl']:>12,.0f})")
    
    print("\nLowest Ratios (potentially undervalued or high DeFi usage):")
    for i, (_, row) in enumerate(filtered.tail(5).iterrows(), 1):
        ratio = row['market_cap_to_tvl_ratio']
        print(f"{i}. {row['chain']:20s} {ratio:6.2f}x "
              f"(MC: ${row['market_cap']:>12,.0f} / TVL: ${row['defi_tvl']:>12,.0f})")
    print()


def analyze_bridge_activity(df):
    """Analyze chains by bridge activity"""
    print("Top Chains by Bridged TVL")
    print("=" * 60)
    
    # Filter chains with bridge data
    filtered = df[df['bridged_tvl'] > 0].copy()
    filtered = filtered.sort_values('bridged_tvl', ascending=False)
    
    for i, (_, row) in enumerate(filtered.head(10).iterrows(), 1):
        bridge_pct = (row['bridged_tvl'] / row['defi_tvl'] * 100) if row['defi_tvl'] > 0 else 0
        print(f"{i:2d}. {row['chain']:20s} ${row['bridged_tvl']:>15,.0f} "
              f"({bridge_pct:5.1f}% of TVL)")
    print()


def compare_chains(df, chain_names):
    """Compare specific chains side by side"""
    print("Chain Comparison")
    print("=" * 60)
    
    for chain_name in chain_names:
        chain_data = df[df['chain'] == chain_name]
        
        if chain_data.empty:
            print(f"\n{chain_name}: ❌ Not found in data")
            continue
        
        row = chain_data.iloc[0]
        print(f"\n{chain_name}:")
        print(f"  Token: {row['token_symbol']}")
        print(f"  Token Price: ${row['token_price']:,.4f}")
        print(f"  Market Cap: ${row['market_cap']:,.0f}")
        print(f"  FDV: ${row['fdv']:,.0f}")
        print(f"  DeFi TVL: ${row['defi_tvl']:,.0f}")
        print(f"  Stablecoin Market Cap: ${row['stablecoin_mcap']:,.0f}")
        print(f"  Bridged TVL: ${row['bridged_tvl']:,.0f}")
        print(f"  Active Addresses: {row['active_addresses']:,.0f}")
        
        if row['stablecoin_to_tvl_ratio'] > 0:
            print(f"  Stablecoin/TVL Ratio: {row['stablecoin_to_tvl_ratio']:.2%}")
        if row['market_cap_to_tvl_ratio'] > 0:
            print(f"  Market Cap/TVL Ratio: {row['market_cap_to_tvl_ratio']:.2f}x")
    print()


def summary_statistics(df):
    """Print summary statistics"""
    print("Overall Summary Statistics")
    print("=" * 60)
    
    print(f"Total Chains Analyzed: {len(df)}")
    print(f"\nTotal Metrics:")
    print(f"  Total DeFi TVL: ${df['defi_tvl'].sum():,.0f}")
    print(f"  Total Stablecoin Market Cap: ${df['stablecoin_mcap'].sum():,.0f}")
    print(f"  Total Market Cap (tokens): ${df['market_cap'].sum():,.0f}")
    print(f"  Total Bridged TVL: ${df['bridged_tvl'].sum():,.0f}")
    
    print(f"\nData Availability:")
    print(f"  Chains with token price data: {(df['token_price'] > 0).sum()}")
    print(f"  Chains with market cap data: {(df['market_cap'] > 0).sum()}")
    print(f"  Chains with stablecoin data: {(df['stablecoin_mcap'] > 0).sum()}")
    print(f"  Chains with bridge data: {(df['bridged_tvl'] > 0).sum()}")
    print(f"  Chains with active address data: {(df['active_addresses'] > 0).sum()}")
    
    print(f"\nAverage Metrics (excluding zeros):")
    print(f"  Avg DeFi TVL: ${df[df['defi_tvl'] > 0]['defi_tvl'].mean():,.0f}")
    print(f"  Avg Token Price: ${df[df['token_price'] > 0]['token_price'].mean():,.4f}")
    print(f"  Avg Market Cap: ${df[df['market_cap'] > 0]['market_cap'].mean():,.0f}")
    print(f"  Avg Stablecoin Market Cap: ${df[df['stablecoin_mcap'] > 0]['stablecoin_mcap'].mean():,.0f}")
    print()


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("Comprehensive Chain Metrics Analysis")
    print("=" * 60 + "\n")
    
    # Load data
    df = load_chain_metrics()
    if df is None:
        return
    
    # Run various analyses
    summary_statistics(df)
    
    analyze_top_chains_by_metric(df, 'defi_tvl', top_n=10)
    analyze_top_chains_by_metric(df, 'stablecoin_mcap', top_n=10)
    analyze_top_chains_by_metric(df, 'market_cap', top_n=10)
    
    analyze_stablecoin_dominance(df)
    analyze_mcap_to_tvl_ratio(df)
    analyze_bridge_activity(df)
    
    # Compare specific chains
    chains_to_compare = ['Ethereum', 'Solana', 'Base', 'Arbitrum', 'Polygon']
    compare_chains(df, chains_to_compare)
    
    print("=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

