import pandas as pd
import json
import ast

print("\n" + "=" * 60)
print("Lending TVL by Chain Analysis")
print("=" * 60)

# Read the TVL data
print("\n📊 Loading TVL data...")
tvl_df = pd.read_csv('tvl_data.csv')

print(f"Total protocols loaded: {len(tvl_df)}")
print(f"Total columns: {len(tvl_df.columns)}")

# Filter for lending protocols only
lending_df = tvl_df[tvl_df['category'] == 'Lending'].copy()

print(f"\n🏦 Total lending protocols: {len(lending_df)}")
print(f"Total TVL in lending: ${lending_df['tvl'].sum():,.2f}")

# Function to safely parse chainTvls string (Python dict format)
def parse_chain_tvls(chain_tvls_str):
    """Parse the chainTvls column which contains Python dict data"""
    try:
        if pd.isna(chain_tvls_str):
            return {}
        # The chainTvls column contains Python dict format (single quotes)
        # Try ast.literal_eval first for Python dict format
        return ast.literal_eval(chain_tvls_str)
    except:
        try:
            # Fallback to JSON parsing if it's in JSON format
            return json.loads(chain_tvls_str)
        except:
            return {}

# Parse chainTvls for each lending protocol
lending_df['chainTvls_parsed'] = lending_df['chainTvls'].apply(parse_chain_tvls)

# Create lists to store chain-level TVL and borrowed data
chain_tvl_records = []
chain_borrowed_records = []

# Process each lending protocol
for idx, protocol in lending_df.iterrows():
    protocol_name = protocol['name']
    protocol_slug = protocol['slug']
    total_tvl = protocol['tvl']
    chain_tvls = protocol['chainTvls_parsed']
    
    print(f"\nProcessing: {protocol_name}")
    print(f"  Total TVL: ${total_tvl:,.2f}")
    
    # If we have chain-specific TVL data
    if chain_tvls:
        # Look for chain-specific TVL values
        # The chainTvls dict typically has keys like "Ethereum", "Arbitrum", etc.
        # Some protocols also have "-borrowed", "-staking" suffixes
        for chain_key, value in chain_tvls.items():
            # Skip certain metadata keys that aren't chains
            if chain_key in ['tvl', 'staking', 'pool2', 'borrowed', 'treasury']:
                continue
            
            # Handle borrowed amounts (e.g., "Ethereum-borrowed")
            if '-borrowed' in chain_key.lower():
                chain = chain_key.replace('-borrowed', '').replace('-Borrowed', '')
                
                # Parse the borrowed value
                if isinstance(value, dict):
                    borrowed_amount = value.get('tvl', 0) if value else 0
                else:
                    borrowed_amount = value if value else 0
                
                if borrowed_amount > 0:
                    borrowed_record = {
                        'protocol': protocol_name,
                        'protocol_slug': protocol_slug,
                        'chain': chain,
                        'borrowed': borrowed_amount
                    }
                    chain_borrowed_records.append(borrowed_record)
                    print(f"    {chain} (borrowed): ${borrowed_amount:,.2f}")
                continue
            
            # Skip other suffixes like '-staking', '-pool2', etc.
            if '-' in chain_key and any(suffix in chain_key.lower() for suffix in ['staking', 'pool2', 'treasury', 'offers', 'vesting']):
                continue
            
            # The actual chain name for TVL
            chain = chain_key
            
            # Parse the TVL value
            if isinstance(value, dict):
                # Look for the TVL value in the dict
                if 'tvl' in value:
                    chain_tvl = value['tvl']
                else:
                    # Some dicts just have the raw value as the latest entry
                    chain_tvl = value.get(max(value.keys()), 0) if value else 0
            else:
                chain_tvl = value if value else 0
            
            if chain_tvl > 0:
                record = {
                    'protocol': protocol_name,
                    'protocol_slug': protocol_slug,
                    'chain': chain,
                    'tvl': chain_tvl
                }
                chain_tvl_records.append(record)
                print(f"    {chain} (TVL): ${chain_tvl:,.2f}")
    else:
        # If no chain-specific data, try to use the 'chain' column
        chain = protocol['chain']
        if chain and chain != 'Multi-Chain':
            record = {
                'protocol': protocol_name,
                'protocol_slug': protocol_slug,
                'chain': chain,
                'tvl': total_tvl
            }
            chain_tvl_records.append(record)
            print(f"    {chain} (TVL): ${total_tvl:,.2f}")

# Create DataFrames from records
lending_chain_df = pd.DataFrame(chain_tvl_records)
lending_borrowed_df = pd.DataFrame(chain_borrowed_records)

print(f"\n\n📈 Total TVL chain-level records: {len(lending_chain_df)}")
print(f"📈 Total borrowed chain-level records: {len(lending_borrowed_df)}")

# Group by chain and sum TVL
lending_by_chain = lending_chain_df.groupby('chain').agg({
    'tvl': 'sum',
    'protocol': 'count'
}).reset_index()
lending_by_chain.columns = ['chain', 'total_lending_tvl', 'num_lending_protocols']

# Group by chain and sum borrowed amounts
if not lending_borrowed_df.empty:
    borrowed_by_chain = lending_borrowed_df.groupby('chain').agg({
        'borrowed': 'sum',
        'protocol': 'count'
    }).reset_index()
    borrowed_by_chain.columns = ['chain', 'total_borrowed', 'num_protocols_with_borrowed']
    
    # Merge TVL and borrowed data
    lending_by_chain = lending_by_chain.merge(borrowed_by_chain, on='chain', how='left')
    lending_by_chain['total_borrowed'] = lending_by_chain['total_borrowed'].fillna(0)
    lending_by_chain['num_protocols_with_borrowed'] = lending_by_chain['num_protocols_with_borrowed'].fillna(0).astype(int)
    
    # Calculate utilization rate (borrowed / TVL)
    lending_by_chain['utilization_rate'] = (lending_by_chain['total_borrowed'] / lending_by_chain['total_lending_tvl'] * 100).round(2)
else:
    lending_by_chain['total_borrowed'] = 0
    lending_by_chain['num_protocols_with_borrowed'] = 0
    lending_by_chain['utilization_rate'] = 0

# Sort by TVL descending
lending_by_chain = lending_by_chain.sort_values('total_lending_tvl', ascending=False)

# Save detailed protocol-level data
lending_chain_df_sorted = lending_chain_df.sort_values(['chain', 'tvl'], ascending=[True, False])
lending_chain_df_sorted.to_csv('lending_tvl_by_chain_detailed.csv', index=False)

if not lending_borrowed_df.empty:
    lending_borrowed_df_sorted = lending_borrowed_df.sort_values(['chain', 'borrowed'], ascending=[True, False])
    lending_borrowed_df_sorted.to_csv('lending_borrowed_by_chain_detailed.csv', index=False)

# Save aggregated chain-level data
lending_by_chain.to_csv('lending_tvl_by_chain.csv', index=False)

print("\n" + "=" * 60)
print("Lending TVL & Borrowed Amounts by Chain - Summary")
print("=" * 60)
print(f"\nTotal chains with lending protocols: {len(lending_by_chain)}")
print(f"Total lending TVL across all chains: ${lending_by_chain['total_lending_tvl'].sum():,.2f}")
print(f"Total borrowed across all chains: ${lending_by_chain['total_borrowed'].sum():,.2f}")
overall_utilization = (lending_by_chain['total_borrowed'].sum() / lending_by_chain['total_lending_tvl'].sum() * 100)
print(f"Overall utilization rate: {overall_utilization:.2f}%")

print("\n📊 Top 20 Chains by Lending TVL:")
print("-" * 100)
print(f"{'Chain':<20} {'TVL':>18} {'Borrowed':>18} {'Util %':>8} {'# Protocols':>12}")
print("-" * 100)
top_20 = lending_by_chain.head(20)
for idx, row in top_20.iterrows():
    print(f"{row['chain']:<20} ${row['total_lending_tvl']:>16,.2f} ${row['total_borrowed']:>16,.2f} {row['utilization_rate']:>7.2f}% {row['num_lending_protocols']:>11}")

print("\n" + "=" * 60)
print("Top 10 Chains by Borrowed Amount:")
print("-" * 100)
print(f"{'Chain':<20} {'Borrowed':>18} {'TVL':>18} {'Util %':>8} {'# Protocols':>12}")
print("-" * 100)
top_borrowed = lending_by_chain.sort_values('total_borrowed', ascending=False).head(10)
for idx, row in top_borrowed.iterrows():
    print(f"{row['chain']:<20} ${row['total_borrowed']:>16,.2f} ${row['total_lending_tvl']:>16,.2f} {row['utilization_rate']:>7.2f}% {row['num_lending_protocols']:>11}")

print("\n✅ Analysis complete!")
print(f"📄 TVL detailed data saved to: lending_tvl_by_chain_detailed.csv")
if not lending_borrowed_df.empty:
    print(f"📄 Borrowed detailed data saved to: lending_borrowed_by_chain_detailed.csv")
print(f"📄 Summary data saved to: lending_tvl_by_chain.csv")
