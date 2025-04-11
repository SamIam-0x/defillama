# plot all stablecoins chain distribution

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the data
df = pd.read_csv('all_stablecoins_chain_distribution.csv')

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Set the style
sns.set_style("whitegrid")
plt.figure(figsize=(20, 10))

# Group by date and stablecoin to get total circulating supply per stablecoin
stablecoin_totals = df.groupby(['date', 'stablecoin_symbol'])['circulating'].sum().unstack()

# Create a color palette with enough distinct colors
n_colors = len(stablecoin_totals.columns)
colors = sns.color_palette("husl", n_colors)

# Plot each stablecoin's total circulating supply over time
for idx, column in enumerate(stablecoin_totals.columns):
    plt.plot(stablecoin_totals.index, stablecoin_totals[column], 
             label=column, linewidth=1.5, alpha=0.7, color=colors[idx])

plt.title('Total Stablecoin Supply Over Time', fontsize=14, pad=20)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Circulating Supply (USD)', fontsize=12)

# Adjust legend
plt.legend(bbox_to_anchor=(1.05, 1), 
          loc='upper left', 
          ncol=2, 
          fontsize=8)

# Format y-axis to billions
current_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['${:.1f}B'.format(x/1e9) for x in current_values])

plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the plot with extra space for the legend
plt.savefig('stablecoin_supply_over_time.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a second plot showing distribution by chain for the most recent date
latest_date = df['date'].max()
latest_data = df[df['date'] == latest_date]

# Get top 10 chains by total circulating supply
top_chains = latest_data.groupby('chain')['circulating'].sum().nlargest(10).index

# Filter data for top chains
latest_data_top_chains = latest_data[latest_data['chain'].isin(top_chains)]

# Create a stacked bar plot
plt.figure(figsize=(20, 10))
pivot_data = latest_data_top_chains.pivot_table(
    index='chain',
    columns='stablecoin_symbol',
    values='circulating',
    aggfunc='sum'
).fillna(0)

# Plot stacked bars
pivot_data.plot(kind='bar', stacked=True, figsize=(20, 10))

plt.title(f'Stablecoin Distribution by Chain ({latest_date.strftime("%Y-%m-%d")})', fontsize=14, pad=20)
plt.xlabel('Chain', fontsize=12)
plt.ylabel('Circulating Supply (USD)', fontsize=12)

# Format y-axis to billions
current_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['${:.1f}B'.format(x/1e9) for x in current_values])

plt.legend(bbox_to_anchor=(1.05, 1), 
          loc='upper left', 
          ncol=2, 
          fontsize=8)

plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the plot with extra space for the legend
plt.savefig('stablecoin_chain_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
