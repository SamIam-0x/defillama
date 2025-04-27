import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the chain distribution data
df = pd.read_csv('all_stablecoins_chain_distribution.csv')

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Get the latest date in the dataset
latest_date = df['date'].max()
# Calculate the date 30 days before the latest date
thirty_days_ago = latest_date - timedelta(days=30)

# Calculate total stablecoin growth per chain
chain_growth = []
for chain in df['chain'].unique():
    chain_data = df[df['chain'] == chain]
    
    # Get data for latest date and 30 days ago
    latest_data = chain_data[chain_data['date'] == latest_date]
    thirty_days_ago_data = chain_data[chain_data['date'] == thirty_days_ago]
    
    # Calculate total stablecoin supply at both dates
    latest_total = latest_data['circulating'].sum()
    thirty_days_ago_total = thirty_days_ago_data['circulating'].sum()
    
    # Calculate growth percentage and raw growth
    growth_pct = ((latest_total - thirty_days_ago_total) / thirty_days_ago_total) if thirty_days_ago_total > 0 else np.nan
    raw_growth = latest_total - thirty_days_ago_total
    
    # Calculate USDC growth if USDC exists on this chain
    usdc_data = chain_data[chain_data['stablecoin_symbol'] == 'USDC']
    usdc_growth_pct = np.nan
    usdc_raw_growth = np.nan
    
    if not usdc_data.empty:
        latest_usdc = usdc_data[usdc_data['date'] == latest_date]['circulating'].sum()
        thirty_days_ago_usdc = usdc_data[usdc_data['date'] == thirty_days_ago]['circulating'].sum()
        usdc_growth_pct = ((latest_usdc - thirty_days_ago_usdc) / thirty_days_ago_usdc) if thirty_days_ago_usdc > 0 else np.nan
        usdc_raw_growth = latest_usdc - thirty_days_ago_usdc
    
    chain_growth.append({
        'chain': chain,
        'latest_date': latest_date,
        'thirty_days_ago': thirty_days_ago,
        'thirty_days_ago_supply': thirty_days_ago_total,
        'latest_supply': latest_total,
        'raw_growth': raw_growth,
        'growth_pct': growth_pct,
        'usdc_raw_growth': usdc_raw_growth,
        'usdc_growth_pct': usdc_growth_pct
    })

# Create DataFrame from results
growth_df = pd.DataFrame(chain_growth)

# Sort by raw growth in descending order
growth_df = growth_df.sort_values('raw_growth', ascending=False)

# Format the numbers for better readability
growth_df['thirty_days_ago_supply'] = growth_df['thirty_days_ago_supply']
growth_df['latest_supply'] = growth_df['latest_supply']
growth_df['raw_growth'] = growth_df['raw_growth']
growth_df['growth_pct'] = growth_df['growth_pct']
growth_df['usdc_raw_growth'] = growth_df['usdc_raw_growth']
growth_df['usdc_growth_pct'] = growth_df['usdc_growth_pct']

# Save results to CSV
growth_df.to_csv('chain_stablecoin_growth.csv', index=False)

# Print summary
print("\nChain Stablecoin Growth Analysis (Last 30 Days):")
print("===============================================")
print(f"\nAnalysis period: {thirty_days_ago.date()} to {latest_date.date()}")
print("\nTop 10 chains by raw stablecoin growth:")
print(growth_df[['chain', 'raw_growth', 'growth_pct', 'usdc_raw_growth', 'usdc_growth_pct']].head(10).to_string())

print("\nChains with highest USDC growth:")
usdc_growth = growth_df.dropna(subset=['usdc_growth_pct']).sort_values('usdc_growth_pct', ascending=False)
print(usdc_growth[['chain', 'usdc_raw_growth', 'usdc_growth_pct']].head(10).to_string()) 