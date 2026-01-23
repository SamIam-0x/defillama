import pandas as pd
import json
import requests
import time
import urllib3
from datetime import datetime

urllib3.disable_warnings()

print("\n" + "=" * 80)
print("LST/LRT Total TVL by Chain Analysis")
print("=" * 80)

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

# Define the key LST/LRT tokens to track
lst_lrt_tokens = {
    'WEETH': 'Ether.fi',
    'WSTETH': 'Lido',
    'RSETH': 'KelpDAO',
    'EZETH': 'Renzo',
    'WRSETH': 'KelpDAO',
    'CBETH': 'Coinbase',
    'WSUPEROETHB': 'Superform',
    'RETH': 'Rocket Pool',
    'GTMSETHC': 'Gravita',
    'DETH': 'DineroDAO',
    'FLRETH': 'Flare',
    'STEAKETH': 'Steakhouse',
    'YOETH': 'Yearn',
    'METH': 'Mantle',
    'CSETH': 'Coinshift',
    'BSDETH': 'Based',
    'NWETH': 'Nimbora',
    'TETH': 'Tangible'
}

print(f"\n📊 Tracking {len(lst_lrt_tokens)} LST/LRT tokens:")
for token, protocol in lst_lrt_tokens.items():
    print(f"  • {token} ({protocol})")

# Fetch yield pools data from DeFiLlama
print("\n📊 Fetching yield pools data from DeFiLlama...")
pools_url = "https://yields.llama.fi/pools"

try:
    response = session.get(pools_url)
    time.sleep(0.25)
    
    if response.status_code == 200:
        pools_data = response.json()
        print(f"✓ Successfully fetched {len(pools_data.get('data', []))} pools")
    else:
        print(f"✗ Error fetching pools data: Status code {response.status_code}")
        exit(1)
except Exception as e:
    print(f"✗ Error fetching pools data: {str(e)}")
    exit(1)

# Convert to DataFrame
pools_df = pd.DataFrame(pools_data['data'])

print(f"\nTotal pools: {len(pools_df)}")

# Filter for our LST/LRT tokens (case-insensitive)
lst_lrt_symbols = [token.upper() for token in lst_lrt_tokens.keys()]
lst_lrt_pools = pools_df[pools_df['symbol'].str.upper().isin(lst_lrt_symbols)].copy()

print(f"Total pools with our LST/LRT tokens: {len(lst_lrt_pools)}")

# Aggregate TVL by token and chain
print("\n📈 Aggregating TVL by token and chain...")

# Create a list to store aggregated data
token_chain_breakdown = []

for symbol_upper in lst_lrt_symbols:
    # Get original casing from the data
    token_pools = lst_lrt_pools[lst_lrt_pools['symbol'].str.upper() == symbol_upper]
    
    if len(token_pools) == 0:
        print(f"  ⚠️  No pools found for {symbol_upper}")
        continue
    
    # Get the actual symbol as it appears in the data
    actual_symbol = token_pools['symbol'].iloc[0]
    protocol_name = lst_lrt_tokens.get(symbol_upper, 'Unknown')
    
    print(f"\n  Processing {actual_symbol} ({protocol_name}): {len(token_pools)} pools")
    
    # Group by chain
    for chain in token_pools['chain'].unique():
        chain_pools = token_pools[token_pools['chain'] == chain]
        
        # Sum up TVL for this token on this chain
        total_tvl = chain_pools['tvlUsd'].sum()
        
        # Get unique projects providing this token
        projects = chain_pools['project'].unique()
        num_projects = len(projects)
        
        token_chain_breakdown.append({
            'symbol': actual_symbol,
            'protocol': protocol_name,
            'chain': chain,
            'total_tvl_usd': total_tvl,
            'num_pools': len(chain_pools),
            'num_projects': num_projects,
            'projects': ', '.join(sorted(projects))
        })
        
        if total_tvl > 10_000_000:  # Only print if > $10M
            print(f"    {chain}: ${total_tvl:,.2f} across {num_projects} projects")

# Create DataFrame from aggregated data
if len(token_chain_breakdown) == 0:
    print("\n✗ No data found for the specified tokens")
    exit(1)

lst_lrt_df = pd.DataFrame(token_chain_breakdown)

# Sort by symbol and TVL
lst_lrt_df = lst_lrt_df.sort_values(['symbol', 'total_tvl_usd'], ascending=[True, False])

# Save detailed breakdown
output_file = 'lst_lrt_tvl_by_chain_detailed.csv'
lst_lrt_df.to_csv(output_file, index=False)
print(f"\n✓ Detailed data saved to {output_file}")

# Create summary by token (aggregated across all chains)
token_summary = lst_lrt_df.groupby(['symbol', 'protocol']).agg({
    'total_tvl_usd': 'sum',
    'chain': 'nunique',
    'num_pools': 'sum',
    'num_projects': 'sum'
}).reset_index()
token_summary.columns = ['symbol', 'protocol', 'total_tvl', 'num_chains', 'total_pools', 'total_projects']
token_summary = token_summary.sort_values('total_tvl', ascending=False)

# Save token summary
token_summary.to_csv('lst_lrt_tvl_by_token_summary.csv', index=False)
print(f"✓ Token summary saved to lst_lrt_tvl_by_token_summary.csv")

# Create summary by chain (aggregated across all tokens)
chain_summary = lst_lrt_df.groupby('chain').agg({
    'total_tvl_usd': 'sum',
    'symbol': 'nunique',
    'num_pools': 'sum'
}).reset_index()
chain_summary.columns = ['chain', 'total_tvl', 'num_tokens', 'total_pools']
chain_summary = chain_summary.sort_values('total_tvl', ascending=False)

# Save chain summary
chain_summary.to_csv('lst_lrt_tvl_by_chain_summary.csv', index=False)
print(f"✓ Chain summary saved to lst_lrt_tvl_by_chain_summary.csv")

# Print summary
print("\n" + "=" * 80)
print("Summary: LST/LRT TVL by Token")
print("=" * 80)
print(f"\nTotal LST/LRT tokens tracked: {len(token_summary)}")
print(f"Total chains with LST/LRT activity: {len(chain_summary)}")
print(f"Total TVL in LST/LRTs: ${token_summary['total_tvl'].sum():,.2f}")

print("\n📊 Top 15 LST/LRT Tokens by Total TVL:")
print("-" * 100)
print(f"{'Token':<15} {'Protocol':<20} {'Total TVL':>20} {'# Chains':>12} {'# Pools':>12}")
print("-" * 100)
top_15_tokens = token_summary.head(15)
for idx, row in top_15_tokens.iterrows():
    print(f"{row['symbol']:<15} {row['protocol']:<20} ${row['total_tvl']:>18,.2f} {row['num_chains']:>11} {row['total_pools']:>11}")

print("\n" + "=" * 80)
print("Summary: LST/LRT TVL by Chain")
print("=" * 80)

print("\n📊 Top 20 Chains by LST/LRT TVL:")
print("-" * 100)
print(f"{'Chain':<20} {'Total TVL':>20} {'# Tokens':>12} {'# Pools':>12}")
print("-" * 100)
top_20_chains = chain_summary.head(20)
for idx, row in top_20_chains.iterrows():
    print(f"{row['chain']:<20} ${row['total_tvl']:>18,.2f} {row['num_tokens']:>11} {row['total_pools']:>11}")

# Create a pivot table showing token distribution across chains
print("\n" + "=" * 80)
print("Token Distribution Across Top Chains")
print("=" * 80)

# Get top 10 chains by TVL
top_chains = chain_summary.head(10)['chain'].tolist()

# Create pivot for top tokens and top chains
top_tokens = token_summary.head(10)['symbol'].tolist()
pivot_data = lst_lrt_df[
    (lst_lrt_df['symbol'].isin(top_tokens)) & 
    (lst_lrt_df['chain'].isin(top_chains))
]

if len(pivot_data) > 0:
    pivot = pivot_data.pivot_table(
        index='symbol',
        columns='chain',
        values='total_tvl_usd',
        aggfunc='sum',
        fill_value=0
    )
    
    # Save pivot table
    pivot.to_csv('lst_lrt_token_chain_matrix.csv')
    print(f"\n✓ Token-chain matrix saved to lst_lrt_token_chain_matrix.csv")
    
    print("\nTop 10 Tokens × Top 10 Chains (TVL in millions USD):")
    print("=" * 120)
    
    # Print header
    header = f"{'Token':<12}"
    for chain in pivot.columns:
        header += f" {chain[:10]:>10}"
    header += f" {'Total':>12}"
    print(header)
    print("-" * 120)
    
    # Print data
    for token in pivot.index:
        row_str = f"{token:<12}"
        row_total = 0
        for chain in pivot.columns:
            tvl = pivot.loc[token, chain]
            row_total += tvl
            if tvl > 0:
                row_str += f" ${tvl/1e6:>8.1f}M"
            else:
                row_str += f" {'-':>10}"
        row_str += f" ${row_total/1e6:>10.1f}M"
        print(row_str)

# Detailed breakdown for top tokens
print("\n" + "=" * 80)
print("Detailed Chain Breakdown for Top 5 Tokens")
print("=" * 80)

for token in token_summary.head(5)['symbol']:
    token_data = lst_lrt_df[lst_lrt_df['symbol'] == token].sort_values('total_tvl_usd', ascending=False).head(10)
    protocol = token_data['protocol'].iloc[0]
    total_tvl = token_data['total_tvl_usd'].sum()
    
    print(f"\n{token} ({protocol}) - Total: ${total_tvl:,.2f}")
    print("-" * 100)
    print(f"{'Chain':<20} {'TVL':>20} {'# Pools':>12} {'Top Projects':<40}")
    print("-" * 100)
    
    for idx, row in token_data.iterrows():
        projects = row['projects'].split(', ')[:3]  # Top 3 projects
        projects_str = ', '.join(projects)
        print(f"{row['chain']:<20} ${row['total_tvl_usd']:>18,.2f} {row['num_pools']:>11} {projects_str:<40}")

print("\n" + "=" * 80)
print("✅ Analysis Complete!")
print("=" * 80)
print("\n📁 Output Files:")
print("  1. lst_lrt_tvl_by_chain_detailed.csv - Full breakdown by token and chain")
print("  2. lst_lrt_tvl_by_token_summary.csv - Summary by token (aggregated across chains)")
print("  3. lst_lrt_tvl_by_chain_summary.csv - Summary by chain (aggregated across tokens)")
print("  4. lst_lrt_token_chain_matrix.csv - Pivot table of tokens × chains")
