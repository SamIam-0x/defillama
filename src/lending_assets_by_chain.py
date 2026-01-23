import pandas as pd
import json
import requests
import time
import urllib3
from datetime import datetime

urllib3.disable_warnings()

print("\n" + "=" * 80)
print("Lending Protocol Supplied Assets Breakdown by Chain")
print("=" * 80)

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

# Fetch yield pools data from DeFiLlama
print("\n📊 Fetching yield pools data from DeFiLlama...")
pools_url = "https://yields.llama.fi/pools"

try:
    response = session.get(pools_url)
    time.sleep(0.25)
    
    if response.status_code == 200:
        pools_data = response.json()
        print(f"✓ Successfully fetched {len(pools_data.get('data', []))} pools")
        
        # Save raw data for debugging
        with open('yield_pools_raw.json', 'w') as f:
            json.dump(pools_data, f, indent=2)
        print(f"✓ Raw data saved to yield_pools_raw.json")
    else:
        print(f"✗ Error fetching pools data: Status code {response.status_code}")
        exit(1)
except Exception as e:
    print(f"✗ Error fetching pools data: {str(e)}")
    exit(1)

# Convert to DataFrame
pools_df = pd.DataFrame(pools_data['data'])

print(f"\nTotal pools: {len(pools_df)}")
print(f"Columns available: {list(pools_df.columns)}")

# Get list of lending protocols from TVL data
print("\n🏦 Loading lending protocols list...")
tvl_df = pd.read_csv('tvl_data.csv')
lending_protocols = tvl_df[tvl_df['category'] == 'Lending']['slug'].unique().tolist()
print(f"Found {len(lending_protocols)} lending protocols")

# Filter pools for lending protocols only
print("\n🏦 Filtering pools for lending protocols...")
lending_pools = pools_df[pools_df['project'].isin(lending_protocols)].copy()
print(f"Total lending pools: {len(lending_pools)}")

# Define EVM chains (common EVM-compatible chains)
evm_chains = [
    'Ethereum', 'Arbitrum', 'Optimism', 'Polygon', 'Base', 'Avalanche', 
    'BSC', 'Fantom', 'Gnosis', 'Celo', 'Moonbeam', 'Moonriver', 
    'Cronos', 'Kava', 'Aurora', 'Harmony', 'Metis', 'Boba', 
    'Linea', 'Scroll', 'zkSync Era', 'Polygon zkEVM', 'Mantle',
    'Manta', 'Blast', 'Mode', 'OP Mainnet', 'Arbitrum Nova',
    'Rootstock', 'Kroma', 'Taiko', 'Fraxtal', 'Sei', 'Worldchain',
    'Sonic', 'Ink', 'Unichain', 'Berachain', 'X Layer', 'Zircuit',
    'zkLink Nova', 'BOB', 'Corn', 'Lisk', 'World Chain', 'Monad',
    'opBNB', 'Gravity', 'Plume Mainnet', 'Flare', 'Conflux', 'Plasma'
]

# Filter for EVM chains
print("\n⛓️  Filtering for EVM chains...")
evm_lending_pools = lending_pools[lending_pools['chain'].isin(evm_chains)].copy()
print(f"Total lending pools on EVM chains: {len(evm_lending_pools)}")

# Check if we have the necessary columns
print("\n🔍 Checking available data fields...")
sample_pool = evm_lending_pools.iloc[0] if len(evm_lending_pools) > 0 else None
if sample_pool is not None:
    print("\nSample pool data:")
    print(f"  Project: {sample_pool.get('project', 'N/A')}")
    print(f"  Symbol: {sample_pool.get('symbol', 'N/A')}")
    print(f"  Chain: {sample_pool.get('chain', 'N/A')}")
    print(f"  TVL: ${sample_pool.get('tvlUsd', 0):,.2f}")
    print(f"  Available keys: {list(sample_pool.keys())}")

# Group by chain and asset symbol
print("\n📈 Aggregating TVL by chain and asset...")

# Create a list to store aggregated data
asset_breakdown = []

for chain in evm_lending_pools['chain'].unique():
    chain_pools = evm_lending_pools[evm_lending_pools['chain'] == chain]
    
    print(f"\n  Processing {chain}: {len(chain_pools)} pools")
    
    # Group by symbol (asset)
    for symbol in chain_pools['symbol'].unique():
        symbol_pools = chain_pools[chain_pools['symbol'] == symbol]
        
        # Sum up TVL for this asset on this chain
        total_tvl = symbol_pools['tvlUsd'].sum()
        
        # Get unique protocols providing this asset
        protocols = symbol_pools['project'].unique()
        num_protocols = len(protocols)
        
        # Get the underlying tokens if available
        underlyingTokens = symbol_pools['underlyingTokens'].iloc[0] if 'underlyingTokens' in symbol_pools.columns else []
        
        asset_breakdown.append({
            'chain': chain,
            'symbol': symbol,
            'total_tvl_usd': total_tvl,
            'num_protocols': num_protocols,
            'protocols': ', '.join(protocols),
            'underlyingTokens': underlyingTokens
        })
        
        if total_tvl > 1000000:  # Only print assets with > $1M TVL
            print(f"    {symbol}: ${total_tvl:,.2f} across {num_protocols} protocols")

# Create DataFrame from aggregated data
asset_breakdown_df = pd.DataFrame(asset_breakdown)

# Define asset type classifications
def classify_asset(symbol):
    """Classify assets into categories based on symbol"""
    symbol_upper = symbol.upper()
    
    # BTC tokens
    btc_tokens = [
        'WBTC', 'CBBTC', 'BTCB', 'LBTC', 'BTC.B', 'TBTC', 'SOLVBTC', 
        'VBGTWBTC', 'XSOLVBTC', 'EBTC', 'FBTC', 'ENZOBTC', 'UBTC', 
        'STBTC', 'M-BTC', 'HYPERCBBTCD', 'GTWBTCC', 'MHYPERBTC',
        'NWBTC', 'YBTC.B', 'BTC', 'CDCBTC', 'FIABTC', 'MWCBBTC',
        'SMCBBTC', 'HGBTC'
    ]
    if symbol_upper in btc_tokens:
        return 'BTC Tokens'
    
    # ETH LSTs (Liquid Staking Tokens)
    eth_lsts = [
        'WEETH', 'WSTETH', 'STETH', 'RSETH', 'RETH', 'TETH', 
        'EZETH', 'OSETH', 'WRSETH', 'ETH+', 'WSTETH-ETH-25X',
        'WEETHS', 'WSUPEROETHB', 'CBETH', 'SFRXETH', 'FRXETH',
        'EETH', 'PUFETH', 'AGETH', 'SAVETH', 'OETH', 'SVETH',
        'ETHX', 'METH', 'DETH', 'BSDETH', 'CSETH', 'HGETH',
        'YNETHX', 'GTMSETHC', 'STEAKETH', 'AVGWETHCORE', 'NWETH',
        'AWETH', 'MHYETH', 'HYPERETHD', 'MHYPERETH', 'YOETH',
        'GTMSUSDC', 'FLRETH', 'STHETH'
    ]
    if symbol_upper in eth_lsts:
        return 'ETH LSTs'
    
    # ETH - all other ETH variants
    if 'ETH' in symbol_upper and symbol_upper not in ['BETH', 'SETH']:
        # Already classified as LST above, so this catches remaining ETH tokens
        return 'ETH'
    
    # Stablecoins - anything containing USD or EUR
    if 'USD' in symbol_upper or 'EUR' in symbol_upper or 'DAI' in symbol_upper:
        return 'Stablecoins'
    
    # All other assets
    return 'Other Assets'

# Add asset type classification
asset_breakdown_df['asset_type'] = asset_breakdown_df['symbol'].apply(classify_asset)

# Sort by chain and TVL
asset_breakdown_df = asset_breakdown_df.sort_values(['chain', 'total_tvl_usd'], ascending=[True, False])

# Save detailed breakdown
output_file = 'lending_assets_by_chain_detailed.csv'
asset_breakdown_df.to_csv(output_file, index=False)
print(f"\n✓ Detailed data saved to {output_file}")

# Create summary by chain
chain_summary = asset_breakdown_df.groupby('chain').agg({
    'total_tvl_usd': 'sum',
    'symbol': 'count',
    'num_protocols': 'sum'
}).reset_index()
chain_summary.columns = ['chain', 'total_tvl', 'num_unique_assets', 'total_protocol_count']
chain_summary = chain_summary.sort_values('total_tvl', ascending=False)

# Save chain summary
chain_summary.to_csv('lending_assets_by_chain_summary.csv', index=False)
print(f"✓ Chain summary saved to lending_assets_by_chain_summary.csv")

# Print summary
print("\n" + "=" * 80)
print("Summary: Lending Assets by Chain (EVM only)")
print("=" * 80)
print(f"\nTotal EVM chains analyzed: {len(chain_summary)}")
print(f"Total unique assets: {asset_breakdown_df['symbol'].nunique()}")
print(f"Total TVL in lending on EVM chains: ${chain_summary['total_tvl'].sum():,.2f}")

print("\n📊 Top 20 Chains by Total Lending TVL:")
print("-" * 100)
print(f"{'Chain':<20} {'Total TVL':>20} {'# Assets':>12} {'# Protocols':>15}")
print("-" * 100)
top_20_chains = chain_summary.head(20)
for idx, row in top_20_chains.iterrows():
    print(f"{row['chain']:<20} ${row['total_tvl']:>18,.2f} {row['num_unique_assets']:>11} {row['total_protocol_count']:>14}")

# Print top assets across all EVM chains
print("\n" + "=" * 80)
print("Top 30 Supplied Assets Across All EVM Chains (Aggregated)")
print("=" * 80)
print("-" * 100)
print(f"{'Asset':<15} {'Total TVL':>20} {'# Chains':>12} {'# Protocols':>15}")
print("-" * 100)

asset_totals = asset_breakdown_df.groupby('symbol').agg({
    'total_tvl_usd': 'sum',
    'chain': 'nunique',
    'num_protocols': 'sum'
}).reset_index()
asset_totals.columns = ['symbol', 'total_tvl', 'num_chains', 'total_protocols']
asset_totals = asset_totals.sort_values('total_tvl', ascending=False)

# Save asset totals
asset_totals.to_csv('lending_assets_total_across_chains.csv', index=False)
print(f"✓ Asset totals saved to lending_assets_total_across_chains.csv")

print()
top_30_assets = asset_totals.head(30)
for idx, row in top_30_assets.iterrows():
    print(f"{row['symbol']:<15} ${row['total_tvl']:>18,.2f} {row['num_chains']:>11} {row['total_protocols']:>14}")

# Create asset type summary
print("\n" + "=" * 80)
print("Asset Type Summary (Aggregated Across All Chains)")
print("=" * 80)

asset_type_summary = asset_breakdown_df.groupby('asset_type').agg({
    'total_tvl_usd': 'sum',
    'symbol': 'nunique',
    'chain': 'nunique'
}).reset_index()
asset_type_summary.columns = ['asset_type', 'total_tvl', 'num_unique_assets', 'num_chains']
asset_type_summary = asset_type_summary.sort_values('total_tvl', ascending=False)

print(f"\n{'Asset Type':<20} {'Total TVL':>20} {'# Unique Assets':>18} {'# Chains':>12}")
print("-" * 80)
for idx, row in asset_type_summary.iterrows():
    print(f"{row['asset_type']:<20} ${row['total_tvl']:>18,.2f} {row['num_unique_assets']:>17} {row['num_chains']:>11}")

# Save asset type summary
asset_type_summary.to_csv('lending_assets_by_type_summary.csv', index=False)
print(f"\n✓ Asset type summary saved to lending_assets_by_type_summary.csv")

# Create detailed breakdown by asset type and chain
print("\n" + "=" * 80)
print("Asset Type Breakdown by Chain")
print("=" * 80)

asset_type_by_chain = asset_breakdown_df.groupby(['chain', 'asset_type']).agg({
    'total_tvl_usd': 'sum',
    'symbol': 'nunique'
}).reset_index()
asset_type_by_chain.columns = ['chain', 'asset_type', 'total_tvl', 'num_assets']
asset_type_by_chain = asset_type_by_chain.sort_values(['chain', 'total_tvl'], ascending=[True, False])

# Save asset type by chain
asset_type_by_chain.to_csv('lending_assets_by_type_and_chain.csv', index=False)
print(f"✓ Asset type by chain saved to lending_assets_by_type_and_chain.csv")

# Print top chains for each asset type
for asset_type in ['BTC Tokens', 'ETH LSTs', 'ETH', 'Stablecoins', 'Other Assets']:
    print(f"\n{asset_type} - Top 10 Chains:")
    print("-" * 80)
    type_data = asset_type_by_chain[asset_type_by_chain['asset_type'] == asset_type]
    type_data_sorted = type_data.sort_values('total_tvl', ascending=False).head(10)
    
    if len(type_data_sorted) > 0:
        print(f"{'Chain':<20} {'Total TVL':>20} {'# Assets':>12}")
        print("-" * 80)
        for idx, row in type_data_sorted.iterrows():
            print(f"{row['chain']:<20} ${row['total_tvl']:>18,.2f} {row['num_assets']:>11}")
    else:
        print("  No data available")

# Create detailed breakdown for each asset type
print("\n" + "=" * 80)
print("Top Assets by Type")
print("=" * 80)

for asset_type in ['BTC Tokens', 'ETH LSTs', 'ETH', 'Stablecoins', 'Other Assets']:
    print(f"\n{asset_type} - Top 10 Assets (Aggregated Across All Chains):")
    print("-" * 80)
    
    type_assets = asset_breakdown_df[asset_breakdown_df['asset_type'] == asset_type]
    type_totals = type_assets.groupby('symbol').agg({
        'total_tvl_usd': 'sum',
        'chain': 'nunique',
        'num_protocols': 'sum'
    }).reset_index()
    type_totals.columns = ['symbol', 'total_tvl', 'num_chains', 'total_protocols']
    type_totals = type_totals.sort_values('total_tvl', ascending=False).head(10)
    
    if len(type_totals) > 0:
        print(f"{'Asset':<15} {'Total TVL':>20} {'# Chains':>12} {'# Protocols':>15}")
        print("-" * 80)
        for idx, row in type_totals.iterrows():
            print(f"{row['symbol']:<15} ${row['total_tvl']:>18,.2f} {row['num_chains']:>11} {row['total_protocols']:>14}")
    else:
        print("  No data available")

print("\n" + "=" * 80)
print("✅ Analysis Complete!")
print("=" * 80)
print("\n📁 Output Files:")
print("  1. lending_assets_by_chain_detailed.csv - Full breakdown by chain and asset (with asset_type)")
print("  2. lending_assets_by_chain_summary.csv - Summary by chain")
print("  3. lending_assets_total_across_chains.csv - Assets aggregated across all chains")
print("  4. lending_assets_by_type_summary.csv - Summary by asset type (BTC, ETH LSTs, etc.)")
print("  5. lending_assets_by_type_and_chain.csv - Asset type breakdown by chain")
print("  6. yield_pools_raw.json - Raw API response for debugging")
print("\n📊 Asset Types:")
print("  • BTC Tokens - WBTC, CBBTC, BTCB, LBTC, TBTC, etc.")
print("  • ETH LSTs - WEETH, WSTETH, RSETH, RETH, EZETH, etc.")
print("  • ETH - All other ETH variants (WETH, ETH, etc.)")
print("  • Stablecoins - Assets containing USD or EUR in name")
print("  • Other Assets - All remaining assets")
