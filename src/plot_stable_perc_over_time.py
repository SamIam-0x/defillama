import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('all_stablecoins_chain_distribution.csv')
# Ensure 'date' column is datetime
df['date'] = pd.to_datetime(df['date'])

# Define the 26-week window
latest_date = df['date'].max()
start_date = latest_date - pd.Timedelta(weeks=26)

# Filter to last 26 weeks
recent_data = df[df['date'] >= start_date]

# Get chains with >$10M USDC on latest date
latest_usdc = df[(df['date'] == latest_date) & (df['stablecoin_symbol'] == 'USDC')]
chains_over_10m = latest_usdc.groupby('chain')['circulating'].sum()
chains_over_10m = chains_over_10m[chains_over_10m > 10_000_000].index.tolist()

# Filter recent data to only those chains
recent_data = recent_data[recent_data['chain'].isin(chains_over_10m)]

# Add week column
recent_data['week'] = recent_data['date'].dt.to_period('W').apply(lambda r: r.start_time)

# Group by week/chain/token and sum
grouped = recent_data.groupby(['week', 'chain', 'stablecoin_symbol'])['circulating'].sum().reset_index()

# Total stablecoins by week/chain
total = grouped.groupby(['week', 'chain'])['circulating'].sum().reset_index(name='total')

# USDC only
usdc = grouped[grouped['stablecoin_symbol'] == 'USDC'][['week', 'chain', 'circulating']]
usdc = usdc.rename(columns={'circulating': 'usdc'})

# Merge
merged = pd.merge(total, usdc, on=['week', 'chain'], how='left')
merged['usdc'] = merged['usdc'].fillna(0)
merged['usdc_pct'] = merged['usdc'] / merged['total']

# Pivot to plot
pivot = merged.pivot(index='week', columns='chain', values='usdc_pct')

# Plot
plt.figure(figsize=(14, 7))
for chain in pivot.columns:
    plt.plot(pivot.index, pivot[chain], label=chain)

plt.title('USDC Share of Stablecoins by Chain (Weekly Avg, Last 26 Weeks)')
plt.xlabel('Week')
plt.ylabel('USDC Share (%)')
plt.legend(title='Chain', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()
