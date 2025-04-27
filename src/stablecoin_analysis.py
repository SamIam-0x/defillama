import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Read the data
df = pd.read_csv('all_stablecoins_chain_distribution.csv')

# Create metadata DataFrame
meta_df = df.drop(columns=['date', 'circulating']).drop_duplicates()
meta_df = meta_df.sort_values(['chain', 'stablecoin_symbol'])
meta_df.to_csv('stablecoin_metadata.csv', index=False)

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Get the latest date
latest_date = df['date'].max()
thirty_days_ago = latest_date - timedelta(days=30)

# 2. USDT launch dates and current amounts by chain
usdt_data = df[df['stablecoin_symbol'] == 'USDT']
usdt_launch_dates = usdt_data.groupby('chain').agg({
    'date': 'min',
    'circulating': 'last'
}).sort_values('date', ascending=False)

# Get current total stablecoins per chain
latest_data = df[df['date'] == latest_date]
chain_totals = latest_data.groupby('chain')['circulating'].sum()

# Calculate USDC percentage of all stablecoins for each chain
chain_totals = latest_data.groupby('chain')['circulating'].sum()
usdc_by_chain = latest_data[latest_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].sum()
usdc_share = usdc_by_chain / chain_totals

# Get dominant stablecoin for each chain
dominant_stablecoins = latest_data.groupby('chain').apply(
    lambda x: x.loc[x['circulating'].idxmax(), 'stablecoin_symbol']
)

# Add USDC share and dominant stablecoin to the DataFrame
usdt_launch_dates['USDC % of Chain Stables'] = usdc_share
usdt_launch_dates['Dominant Stablecoin'] = dominant_stablecoins

# Save USDT launch dates data
usdt_launch_dates_df = pd.DataFrame({
    'Chain': usdt_launch_dates.index,
    'Launch Date': usdt_launch_dates['date'].dt.strftime('%Y-%m-%d'),
    'Current Amount': usdt_launch_dates['circulating'],
    'USDC % of Chain Stables': usdt_launch_dates['USDC % of Chain Stables'],
    'Dominant Stablecoin': usdt_launch_dates['Dominant Stablecoin']
})
usdt_launch_dates_df.to_csv('usdt_launch_dates.csv', index=False)

# Format circulating values as dollars for printing
usdt_launch_dates_print = usdt_launch_dates.copy()
usdt_launch_dates_print['circulating'] = usdt_launch_dates_print['circulating'].apply(lambda x: f"${x:,.2f}")
usdt_launch_dates_print['USDC % of Chain Stables'] = usdt_launch_dates_print['USDC % of Chain Stables'].apply(lambda x: f"{x:.2f}%")

print("\n2. USDT Launch Dates, Current Amounts, and USDC Share by Chain:")
print(usdt_launch_dates_print.to_string())

# 3. Largest growth in USDC over past 30 days
usdc_data = df[df['stablecoin_symbol'] == 'USDC']
# usdc_data = df

latest_data = df[df['date'] == latest_date]
thirty_days_ago = latest_date - timedelta(days=30)
seven_days_ago = latest_date - timedelta(days=7)
ninety_days_ago = latest_date - timedelta(days=90)

# Get current circulating amounts
usdc_current = usdc_data[usdc_data['date'] == latest_date].groupby('chain')['circulating'].sum()

# Get growth over different periods
usdc_30d_ago = usdc_data[usdc_data['date'] == thirty_days_ago].groupby('chain')['circulating'].sum()
usdc_7d_ago = usdc_data[usdc_data['date'] == seven_days_ago].groupby('chain')['circulating'].sum()
usdc_90d_ago = usdc_data[usdc_data['date'] == ninety_days_ago].groupby('chain')['circulating'].sum()

# Calculate growth amounts
usdc_growth_30d = (usdc_current - usdc_30d_ago)
usdc_growth_7d = (usdc_current - usdc_7d_ago)
usdc_growth_90d = (usdc_current - usdc_90d_ago)

# Calculate total stablecoin growth
total_30d_ago = df[df['date'] == thirty_days_ago].groupby('chain')['circulating'].sum()
total_7d_ago = df[df['date'] == seven_days_ago].groupby('chain')['circulating'].sum()
total_90d_ago = df[df['date'] == ninety_days_ago].groupby('chain')['circulating'].sum()
total_current = df[df['date'] == latest_date].groupby('chain')['circulating'].sum()

total_growth_30d = (total_current - total_30d_ago)
total_growth_7d = (total_current - total_7d_ago)
total_growth_90d = (total_current - total_90d_ago)

# Calculate percentage changes
total_pct_change_30d = total_growth_30d / total_30d_ago
total_pct_change_7d = total_growth_7d / total_7d_ago
total_pct_change_90d = total_growth_90d / total_90d_ago

usdc_pct_change_30d = usdc_growth_30d / usdc_30d_ago
usdc_pct_change_7d = usdc_growth_7d / usdc_7d_ago
usdc_pct_change_90d = usdc_growth_90d / usdc_90d_ago

# Get USDC native status from metadata
usdc_native = meta_df[meta_df['stablecoin_symbol'] == 'USDC']
usdc_native = usdc_native.groupby('chain')['native_bridged_standard'].apply(
    lambda x: (
        'USDT0' if any(val == 'USDT0' for val in x.values)
        else 'native' if any(val == 'native' for val in x.values)
        else 'Bridged'
    )
)

# Get USDT status from metadata
usdt_meta = meta_df[meta_df['stablecoin_symbol'] == 'USDT']
usdt_status = usdt_meta.groupby('chain')['native_bridged_standard'].apply(
    lambda x: (
        'USDT0' if any(val == 'USDT0' for val in x.values)
        else 'native' if any(val == 'native' for val in x.values)
        else 'Bridged'
    )
)

# Get common chains that have data for all metrics
common_chains = usdc_current.index.intersection(total_current.index)

# Create a Series with 'Bridged' for all common chains
all_chains_status = pd.Series('Bridged', index=common_chains)
# Update with actual USDT status where available
all_chains_status.update(usdt_status[usdt_status.index.isin(common_chains)])

# Calculate USDC percentage of total stablecoins for each period
usdc_pct_current = usdc_current / total_current
usdc_pct_7d_ago = usdc_7d_ago / total_7d_ago
usdc_pct_30d_ago = usdc_30d_ago / total_30d_ago
usdc_pct_90d_ago = usdc_90d_ago / total_90d_ago

# Calculate change in USDC percentage of total
usdc_pct_of_total_change_7d = (usdc_pct_current - usdc_pct_7d_ago)
usdc_pct_of_total_change_30d = (usdc_pct_current - usdc_pct_30d_ago)
usdc_pct_of_total_change_90d = (usdc_pct_current - usdc_pct_90d_ago)

# Calculate USDC growth rates (percentage change in USDC amount)
usdc_growth_rate_7d = (usdc_growth_7d / usdc_7d_ago)  # Already in decimal form
usdc_growth_rate_30d = (usdc_growth_30d / usdc_30d_ago)  # Already in decimal form
usdc_growth_rate_90d = (usdc_growth_90d / usdc_90d_ago)  # Already in decimal form

# Get chain launch dates (earliest date with any stablecoin value)
chain_launch_dates = df.groupby('chain')['date'].min()

# Get dominant stablecoin for each chain
latest_data = df[df['date'] == latest_date]
dominant_stablecoins = latest_data.groupby('chain').apply(
    lambda x: x.loc[x['circulating'].idxmax(), 'stablecoin_symbol']
)

# Create a DataFrame with numeric values only for common chains
growth_df = pd.DataFrame({
    'Chain': common_chains,
    'USDC Status': usdc_native[common_chains],
    'USDT Status': all_chains_status,
    'Chain Launch Date': chain_launch_dates[common_chains].dt.strftime('%Y-%m-%d'),
    'Dominant Stablecoin': dominant_stablecoins[common_chains],
    'Current USDC Amount': usdc_current[common_chains],
    'Total Circulating Stables': total_current[common_chains],
    'USDC % of Total': usdc_pct_current[common_chains],
    # 7d metrics
    'USDC Growth (7d)': usdc_growth_7d[common_chains],
    'USDC % Change (7d)': usdc_growth_rate_7d[common_chains],  # Growth rate of USDC amount
    'USDC % of Total Change (7d)': usdc_pct_of_total_change_7d[common_chains],  # Change in USDC's share
    'Total Growth (7d)': total_growth_7d[common_chains],
    'Total % Change (7d)': total_pct_change_7d[common_chains],
    # 30d metrics
    'USDC Growth (30d)': usdc_growth_30d[common_chains],
    'USDC % Change (30d)': usdc_growth_rate_30d[common_chains],  # Growth rate of USDC amount
    'USDC % of Total Change (30d)': usdc_pct_of_total_change_30d[common_chains],  # Change in USDC's share
    'Total Growth (30d)': total_growth_30d[common_chains],
    'Total % Change (30d)': total_pct_change_30d[common_chains],
    # 90d metrics
    'USDC Growth (90d)': usdc_growth_90d[common_chains],
    'USDC % Change (90d)': usdc_growth_rate_90d[common_chains],  # Growth rate of USDC amount
    'USDC % of Total Change (90d)': usdc_pct_of_total_change_90d[common_chains],  # Change in USDC's share
    'Total Growth (90d)': total_growth_90d[common_chains],
    'Total % Change (90d)': total_pct_change_90d[common_chains],
})

# Sort by USDC Growth in descending order
growth_df = growth_df.sort_values('USDC Growth (30d)', ascending=False)
growth_df.to_csv('usdc_growth_analysis.csv', index=False)

# Format values for printing
growth_df_print = growth_df.copy()
growth_df_print['Current USDC Amount'] = growth_df_print['Current USDC Amount'].apply(lambda x: f"${x:,.2f}")
growth_df_print['Total Circulating Stables'] = growth_df_print['Total Circulating Stables'].apply(lambda x: f"${x:,.2f}")
growth_df_print['USDC % of Total'] = growth_df_print['USDC % of Total'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC Growth (7d)'] = growth_df_print['USDC Growth (7d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['USDC % Change (7d)'] = growth_df_print['USDC % Change (7d)'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC % of Total Change (7d)'] = growth_df_print['USDC % of Total Change (7d)'].apply(lambda x: f"{x:+.2%}")
growth_df_print['Total Growth (7d)'] = growth_df_print['Total Growth (7d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['Total % Change (7d)'] = growth_df_print['Total % Change (7d)'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC Growth (30d)'] = growth_df_print['USDC Growth (30d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['USDC % Change (30d)'] = growth_df_print['USDC % Change (30d)'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC % of Total Change (30d)'] = growth_df_print['USDC % of Total Change (30d)'].apply(lambda x: f"{x:+.2%}")
growth_df_print['Total Growth (30d)'] = growth_df_print['Total Growth (30d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['Total % Change (30d)'] = growth_df_print['Total % Change (30d)'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC Growth (90d)'] = growth_df_print['USDC Growth (90d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['USDC % Change (90d)'] = growth_df_print['USDC % Change (90d)'].apply(lambda x: f"{x:.2%}")
growth_df_print['USDC % of Total Change (90d)'] = growth_df_print['USDC % of Total Change (90d)'].apply(lambda x: f"{x:+.2%}")
growth_df_print['Total Growth (90d)'] = growth_df_print['Total Growth (90d)'].apply(lambda x: f"${x:,.2f}")
growth_df_print['Total % Change (90d)'] = growth_df_print['Total % Change (90d)'].apply(lambda x: f"{x:.2%}")

print("\n3. Growth in USDC and Total Stablecoins Over Past 30 Days (Sorted by USDC Growth):")
print(growth_df_print.to_string())

# 5. USDT0 Performance Analysis
usdt0_data = df[df['native_bridged_standard'] == 'USDT0']
latest_usdt0 = usdt0_data[usdt0_data['date'] == latest_date]
usdt0_supply = latest_usdt0.groupby('chain')['circulating'].sum()
usdt0_supply = usdt0_supply[usdt0_supply > 0]

total_chain_supply = latest_data[latest_data['chain'].isin(usdt0_supply.index)].groupby('chain')['circulating'].sum()
usdt0_share = usdt0_supply / total_chain_supply

usdt0_30d_ago = usdt0_data[usdt0_data['date'] == thirty_days_ago].groupby('chain')['circulating'].sum()
usdt0_growth = (usdt0_supply - usdt0_30d_ago).round(2)

usdt0_launch_dates = usdt0_data[usdt0_data['chain'].isin(usdt0_supply.index)].groupby('chain')['date'].min()
days_since_launch = (latest_date - usdt0_launch_dates).dt.days

# Save USDT0 performance data
usdt0_performance_df = pd.DataFrame({
    'Chain': usdt0_supply.index,
    'Current Supply': usdt0_supply,
    '% of Chain Stablecoins': usdt0_share,
    '30d Growth': usdt0_growth,
    'Launch Date': usdt0_launch_dates.dt.strftime('%Y-%m-%d'),
    'Days Since Launch': days_since_launch
})
usdt0_performance_df.to_csv('usdt0_performance.csv', index=False)

# Format values for printing
usdt0_performance_print = usdt0_performance_df.copy()
usdt0_performance_print['Current Supply'] = usdt0_performance_print['Current Supply'].apply(lambda x: f"${x:,.2f}")
usdt0_performance_print['% of Chain Stablecoins'] = usdt0_performance_print['% of Chain Stablecoins'].apply(lambda x: f"{x:.2f}%")
usdt0_performance_print['30d Growth'] = usdt0_performance_print['30d Growth'].apply(lambda x: f"${x:,.2f}")

print("\n5. USDT0 Performance Analysis:")
print(usdt0_performance_print.to_string())

# 6. USDC launch dates and current amounts by chain
usdc_data = df[df['stablecoin_symbol'] == 'USDC']
usdc_launch_dates = usdc_data.groupby('chain').agg({
    'date': 'min',
    'circulating': 'last'
}).sort_values('date', ascending=False)

# Get current total stablecoins per chain
latest_data = df[df['date'] == latest_date]
chain_totals = latest_data.groupby('chain')['circulating'].sum()

# Calculate USDC market share
usdc_launch_dates['USDC % of Total'] = usdc_launch_dates['circulating'] / chain_totals

# Get dominant stablecoin for each chain
dominant_stablecoins = latest_data.groupby('chain').apply(
    lambda x: x.loc[x['circulating'].idxmax(), 'stablecoin_symbol']
)
usdc_launch_dates['Dominant Stablecoin'] = dominant_stablecoins

# Save USDC launch dates data
usdc_launch_dates_df = pd.DataFrame({
    'Chain': usdc_launch_dates.index,
    'Launch Date': usdc_launch_dates['date'].dt.strftime('%Y-%m-%d'),
    'Current Amount': usdc_launch_dates['circulating'],
    'USDC % of Total': usdc_launch_dates['USDC % of Total'],
    'Dominant Stablecoin': usdc_launch_dates['Dominant Stablecoin']
})
usdc_launch_dates_df.to_csv('usdc_launch_dates.csv', index=False)

# Format values for printing
usdc_launch_dates_print = usdc_launch_dates.copy()
usdc_launch_dates_print['circulating'] = usdc_launch_dates_print['circulating'].apply(lambda x: f"${x:,.2f}")
usdc_launch_dates_print['USDC % of Total'] = usdc_launch_dates_print['USDC % of Total'].apply(lambda x: f"{x:.2f}%")

print("\n6. USDC Launch Dates and Current Amounts by Chain:")
print(usdc_launch_dates_print.to_string())

# Plot USDC growth vs total growth
plot_df = growth_df.copy()
plot_df = plot_df[(abs(plot_df['USDC Growth (30d)']) >= 100000) | (abs(plot_df['Total Growth (30d)']) >= 100000)]

chains = plot_df['Chain'].tolist()
usdc_growth = plot_df['USDC Growth (30d)'].values
total_growth = plot_df['Total Growth (30d)'].values
x = np.arange(len(chains))
bar_width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
bars1 = ax.bar(x - bar_width/2, usdc_growth, bar_width, label='USDC Growth')
bars2 = ax.bar(x + bar_width/2, total_growth, bar_width, label='Total Growth')

ax.set_xlabel('Chain')
ax.set_ylabel('Growth (USD)')
ax.set_title('USDC vs Total Stablecoin Growth Over Last 30 Days\n(Only showing chains with growth > $100,000)')
ax.set_xticks(x)
ax.set_xticklabels(chains, rotation=45)
ax.legend()
ax.grid(True, axis='y', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('usdc_growth_comparison.png')
plt.close()

# 7. Stablecoin Launch Dates and Current Market Share Analysis
# Get first appearance date for each stablecoin on each chain
launch_dates = df.groupby(['chain', 'stablecoin_symbol'])['date'].min().reset_index()

# Get current circulating amounts
current_amounts = df[df['date'] == latest_date].groupby(['chain', 'stablecoin_symbol'])['circulating'].sum().reset_index()

# Get total stablecoins per chain
chain_totals = current_amounts.groupby('chain')['circulating'].sum()

# Calculate market share
current_amounts['market_share'] = current_amounts.apply(
    lambda x: x['circulating'] / chain_totals[x['chain']] if x['circulating'] > 0 else 0, 
    axis=1
)

# Merge launch dates with current amounts
stablecoin_analysis = pd.merge(
    launch_dates,
    current_amounts[['chain', 'stablecoin_symbol', 'circulating', 'market_share']],
    on=['chain', 'stablecoin_symbol'],
    how='left'
)

# Add metadata
stablecoin_analysis = pd.merge(
    stablecoin_analysis,
    meta_df[['chain', 'stablecoin_symbol', 'native_bridged_standard']],
    on=['chain', 'stablecoin_symbol'],
    how='left'
)

# Sort by launch date (most recent first)
stablecoin_analysis = stablecoin_analysis.sort_values('date', ascending=False)

# Save to CSV
stablecoin_analysis.to_csv('stablecoin_launch_analysis.csv', index=False)

# Format for printing
stablecoin_analysis_print = stablecoin_analysis.copy()
stablecoin_analysis_print['date'] = stablecoin_analysis_print['date'].dt.strftime('%Y-%m-%d')
stablecoin_analysis_print['circulating'] = stablecoin_analysis_print['circulating'].apply(lambda x: f"${x:,.2f}")
stablecoin_analysis_print['market_share'] = stablecoin_analysis_print['market_share'].apply(lambda x: f"{x:.2%}")

print("\n7. Stablecoin Launch Dates and Current Market Share:")
print(stablecoin_analysis_print.to_string())

# 8. 30-Day Growth Analysis
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
        'latest_supply': latest_total,
        'thirty_days_ago_supply': thirty_days_ago_total,
        'raw_growth': raw_growth,
        'growth_pct': growth_pct,
        'usdc_raw_growth': usdc_raw_growth,
        'usdc_growth_pct': usdc_growth_pct
    })

# Create DataFrame from results
growth_df = pd.DataFrame(chain_growth)

# Sort by raw growth in descending order
growth_df = growth_df.sort_values('raw_growth', ascending=False)

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

# After all CSV files are generated, upload to Google Sheets
try:
    from google_sheets_upload import main as upload_to_sheets
    upload_to_sheets()
except Exception as e:
    print(f"Error uploading to Google Sheets: {e}")
    print("Please make sure you have set up the Google Sheets API credentials")