"""
Export comprehensive chain metrics to various formats
"""

import pandas as pd
import json
from datetime import datetime

def export_to_json(df, filename='comprehensive_chain_metrics_formatted.json'):
    """Export to formatted JSON with nested structure"""
    
    chains_dict = {}
    
    for _, row in df.iterrows():
        chain_name = row['chain']
        chains_dict[chain_name] = {
            'token': {
                'symbol': row['token_symbol'],
                'price': float(row['token_price']),
                'market_cap': float(row['market_cap']),
                'fdv': float(row['fdv'])
            },
            'defi': {
                'tvl': float(row['defi_tvl'])
            },
            'stablecoins': {
                'market_cap': float(row['stablecoin_mcap']),
                'tvl_ratio': float(row['stablecoin_to_tvl_ratio'])
            },
            'bridges': {
                'tvl': float(row['bridged_tvl'])
            },
            'activity': {
                'active_addresses': int(row['active_addresses'])
            },
            'ratios': {
                'stablecoin_to_tvl': float(row['stablecoin_to_tvl_ratio']),
                'market_cap_to_tvl': float(row['market_cap_to_tvl_ratio'])
            },
            'identifiers': {
                'chain_id': row['chain_id'],
                'gecko_id': row['gecko_id'],
                'cmc_id': row['cmc_id']
            }
        }
    
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_chains': len(df),
            'data_source': 'DeFiLlama API'
        },
        'chains': chains_dict
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Exported to {filename}")
    return filename


def export_summary_stats(df, filename='chain_metrics_summary.json'):
    """Export summary statistics"""
    
    summary = {
        'generated_at': datetime.now().isoformat(),
        'totals': {
            'chains_analyzed': len(df),
            'total_defi_tvl': float(df['defi_tvl'].sum()),
            'total_stablecoin_mcap': float(df['stablecoin_mcap'].sum()),
            'total_market_cap': float(df['market_cap'].sum()),
            'total_bridged_tvl': float(df['bridged_tvl'].sum())
        },
        'averages': {
            'avg_defi_tvl': float(df[df['defi_tvl'] > 0]['defi_tvl'].mean()),
            'avg_token_price': float(df[df['token_price'] > 0]['token_price'].mean()),
            'avg_market_cap': float(df[df['market_cap'] > 0]['market_cap'].mean()),
            'avg_stablecoin_mcap': float(df[df['stablecoin_mcap'] > 0]['stablecoin_mcap'].mean()),
            'avg_stablecoin_to_tvl_ratio': float(df[df['stablecoin_to_tvl_ratio'] > 0]['stablecoin_to_tvl_ratio'].mean())
        },
        'data_availability': {
            'chains_with_token_price': int((df['token_price'] > 0).sum()),
            'chains_with_market_cap': int((df['market_cap'] > 0).sum()),
            'chains_with_stablecoin_data': int((df['stablecoin_mcap'] > 0).sum()),
            'chains_with_bridge_data': int((df['bridged_tvl'] > 0).sum()),
            'chains_with_active_addresses': int((df['active_addresses'] > 0).sum())
        },
        'top_10_by_tvl': df.nlargest(10, 'defi_tvl')[['chain', 'defi_tvl']].to_dict('records'),
        'top_10_by_stablecoin_mcap': df.nlargest(10, 'stablecoin_mcap')[['chain', 'stablecoin_mcap']].to_dict('records'),
        'top_10_by_market_cap': df.nlargest(10, 'market_cap')[['chain', 'market_cap']].to_dict('records')
    }
    
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Exported summary to {filename}")
    return filename


def export_rankings(df, filename='chain_rankings.csv'):
    """Export rankings by different metrics"""
    
    rankings = pd.DataFrame()
    rankings['chain'] = df['chain']
    
    # Add rankings for each metric
    rankings['tvl_rank'] = df['defi_tvl'].rank(ascending=False, method='min').astype(int)
    rankings['market_cap_rank'] = df['market_cap'].rank(ascending=False, method='min').astype(int)
    rankings['stablecoin_mcap_rank'] = df['stablecoin_mcap'].rank(ascending=False, method='min').astype(int)
    rankings['bridged_tvl_rank'] = df['bridged_tvl'].rank(ascending=False, method='min').astype(int)
    
    # Add the actual values
    rankings['defi_tvl'] = df['defi_tvl']
    rankings['market_cap'] = df['market_cap']
    rankings['stablecoin_mcap'] = df['stablecoin_mcap']
    rankings['bridged_tvl'] = df['bridged_tvl']
    
    # Sort by TVL rank
    rankings = rankings.sort_values('tvl_rank')
    
    rankings.to_csv(filename, index=False)
    print(f"✓ Exported rankings to {filename}")
    return filename


def export_comparison_matrix(df, chains_list, filename='chain_comparison.csv'):
    """Export a comparison matrix for specific chains"""
    
    comparison = df[df['chain'].isin(chains_list)].copy()
    
    if comparison.empty:
        print(f"✗ None of the specified chains found in data")
        return None
    
    # Select key metrics for comparison
    metrics = [
        'chain', 'token_symbol', 'token_price', 'market_cap', 'fdv',
        'defi_tvl', 'stablecoin_mcap', 'bridged_tvl', 'active_addresses',
        'stablecoin_to_tvl_ratio', 'market_cap_to_tvl_ratio'
    ]
    
    comparison = comparison[metrics]
    comparison.to_csv(filename, index=False)
    
    print(f"✓ Exported comparison to {filename}")
    print(f"  Chains included: {', '.join(comparison['chain'].tolist())}")
    return filename


def export_for_excel(df, filename='comprehensive_chain_metrics_excel.csv'):
    """Export with Excel-friendly formatting"""
    
    excel_df = df.copy()
    
    # Format large numbers with thousands separators
    excel_df['defi_tvl_formatted'] = excel_df['defi_tvl'].apply(lambda x: f"${x:,.0f}")
    excel_df['market_cap_formatted'] = excel_df['market_cap'].apply(lambda x: f"${x:,.0f}")
    excel_df['stablecoin_mcap_formatted'] = excel_df['stablecoin_mcap'].apply(lambda x: f"${x:,.0f}")
    excel_df['bridged_tvl_formatted'] = excel_df['bridged_tvl'].apply(lambda x: f"${x:,.0f}")
    
    # Format percentages
    excel_df['stablecoin_to_tvl_pct'] = excel_df['stablecoin_to_tvl_ratio'].apply(lambda x: f"{x*100:.2f}%")
    
    # Reorder columns for better readability
    columns = [
        'chain', 'token_symbol', 'token_price',
        'market_cap_formatted', 'defi_tvl_formatted', 'stablecoin_mcap_formatted',
        'bridged_tvl_formatted', 'active_addresses',
        'stablecoin_to_tvl_pct', 'market_cap_to_tvl_ratio'
    ]
    
    excel_df = excel_df[columns]
    excel_df.to_csv(filename, index=False)
    
    print(f"✓ Exported Excel-friendly format to {filename}")
    return filename


def export_top_chains(df, top_n=20, filename='top_20_chains.csv'):
    """Export just the top N chains with key metrics"""
    
    top_chains = df.nlargest(top_n, 'defi_tvl').copy()
    
    # Select key columns
    columns = [
        'chain', 'token_symbol', 'token_price', 'market_cap', 'defi_tvl',
        'stablecoin_mcap', 'bridged_tvl', 'stablecoin_to_tvl_ratio',
        'market_cap_to_tvl_ratio'
    ]
    
    top_chains = top_chains[columns]
    top_chains.to_csv(filename, index=False)
    
    print(f"✓ Exported top {top_n} chains to {filename}")
    return filename


def main():
    """Main execution"""
    
    print("\n" + "=" * 60)
    print("Exporting Comprehensive Chain Metrics")
    print("=" * 60 + "\n")
    
    # Load data
    try:
        df = pd.read_csv('comprehensive_chain_metrics.csv')
        print(f"✓ Loaded data for {len(df)} chains\n")
    except FileNotFoundError:
        print("❌ comprehensive_chain_metrics.csv not found!")
        print("Run: python src/comprehensive_chain_analysis.py first\n")
        return
    
    print("Exporting to various formats...\n")
    
    # Export to different formats
    export_to_json(df)
    export_summary_stats(df)
    export_rankings(df)
    export_for_excel(df)
    export_top_chains(df, top_n=20)
    
    # Export comparison for specific chains
    l2_chains = ['Arbitrum', 'Optimism', 'Base', 'Polygon', 'ZKsync Era']
    export_comparison_matrix(df, l2_chains, 'l2_comparison.csv')
    
    major_chains = ['Ethereum', 'Solana', 'Tron', 'BSC', 'Avalanche']
    export_comparison_matrix(df, major_chains, 'major_chains_comparison.csv')
    
    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    print("\nFiles created:")
    print("  • comprehensive_chain_metrics_formatted.json - Nested JSON structure")
    print("  • chain_metrics_summary.json - Summary statistics")
    print("  • chain_rankings.csv - Rankings by different metrics")
    print("  • comprehensive_chain_metrics_excel.csv - Excel-friendly format")
    print("  • top_20_chains.csv - Top 20 chains only")
    print("  • l2_comparison.csv - L2 chains comparison")
    print("  • major_chains_comparison.csv - Major chains comparison")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

