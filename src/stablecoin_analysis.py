import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests

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

# Get USDT native/bridged status from metadata
usdt_status = meta_df[meta_df['stablecoin_symbol'] == 'USDT'].groupby('chain')['native_bridged_standard'].apply(
    lambda x: (
        'USDT0' if any(val == 'USDT0' for val in x.values)
        else 'native' if any(val == 'native' for val in x.values)
        else 'Bridged'
    )
)

# Save USDT launch dates data
usdt_launch_dates_df = pd.DataFrame({
    'Chain': usdt_launch_dates.index,
    'Launch Date': usdt_launch_dates['date'].dt.strftime('%Y-%m-%d'),
    'Current Amount': usdt_launch_dates['circulating'],
    'USDT Status': usdt_status.reindex(usdt_launch_dates.index, fill_value='Bridged'),
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

# 4. Rolling 7-Day USDC Growth Analysis
print("\n4. Creating Rolling 7-Day USDC Growth Analysis...")

# Create rolling 7-day analysis
rolling_data = []

# Get all dates in the dataset
all_dates = df['date'].unique()
all_dates = sorted(all_dates)

# Only process the latest date
current_date = all_dates[-1]
if current_date >= all_dates[96]:  # Ensure we have enough data for 90d + 7d rolling window (97 days total)
        
    # Calculate rolling 7-day averages for current period (last 7 days: days 0-6)
    current_7d_dates = [current_date - timedelta(days=i) for i in range(7)]
    current_7d_data = df[df['date'].isin(current_7d_dates)]
    
    # Calculate rolling 7-day averages for 7 days ago period (days 7-13 ago)
    past_7d_dates = [current_date - timedelta(days=i) for i in range(7, 14)]
    past_7d_data = df[df['date'].isin(past_7d_dates)]
    
    # Calculate rolling 7-day averages for 30 days ago period (days 30-36 ago)
    past_30d_dates = [current_date - timedelta(days=i) for i in range(30, 37)]
    past_30d_data = df[df['date'].isin(past_30d_dates)]
    
    # Calculate rolling 7-day averages for 90 days ago period (days 90-96 ago)
    past_90d_dates = [current_date - timedelta(days=i) for i in range(90, 97)]
    past_90d_data = df[df['date'].isin(past_90d_dates)]
    
    # Calculate current rolling 7-day averages
    current_usdc = current_7d_data[current_7d_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].mean()
    current_total = current_7d_data.groupby(['chain', 'date'])['circulating'].sum().groupby('chain').mean()
    current_usdc_pct = current_usdc / current_total
    
    # Calculate past rolling 7-day averages (7d ago)
    past_usdc = past_7d_data[past_7d_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].mean()
    past_total = past_7d_data.groupby(['chain', 'date'])['circulating'].sum().groupby('chain').mean()
    past_usdc_pct = past_usdc / past_total
    
    # Calculate past rolling 7-day averages (30d ago)
    thirty_days_ago_usdc = past_30d_data[past_30d_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].mean()
    thirty_days_ago_total = past_30d_data.groupby(['chain', 'date'])['circulating'].sum().groupby('chain').mean()
    thirty_days_ago_usdc_pct = thirty_days_ago_usdc / thirty_days_ago_total
    
    # Calculate past rolling 7-day averages (90d ago)
    ninety_days_ago_usdc = past_90d_data[past_90d_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].mean()
    ninety_days_ago_total = past_90d_data.groupby(['chain', 'date'])['circulating'].sum().groupby('chain').mean()
    ninety_days_ago_usdc_pct = ninety_days_ago_usdc / ninety_days_ago_total
    
    # Calculate growth metrics (7d)
    usdc_growth_7d = current_usdc - past_usdc
    total_growth_7d = current_total - past_total
    usdc_growth_rate_7d = (usdc_growth_7d / past_usdc).fillna(0)
    total_growth_rate_7d = (total_growth_7d / past_total).fillna(0)
    usdc_pct_change_7d = current_usdc_pct - past_usdc_pct
    
    # Calculate growth metrics (30d)
    usdc_growth_30d = current_usdc - thirty_days_ago_usdc
    total_growth_30d = current_total - thirty_days_ago_total
    usdc_growth_rate_30d = (usdc_growth_30d / thirty_days_ago_usdc).fillna(0)
    total_growth_rate_30d = (total_growth_30d / thirty_days_ago_total).fillna(0)
    usdc_pct_change_30d = current_usdc_pct - thirty_days_ago_usdc_pct
    
    # Calculate growth metrics (90d)
    usdc_growth_90d = current_usdc - ninety_days_ago_usdc
    total_growth_90d = current_total - ninety_days_ago_total
    usdc_growth_rate_90d = (usdc_growth_90d / ninety_days_ago_usdc).fillna(0)
    total_growth_rate_90d = (total_growth_90d / ninety_days_ago_total).fillna(0)
    usdc_pct_change_90d = current_usdc_pct - ninety_days_ago_usdc_pct
    
    # Get USDC and USDT status from metadata (using current 7-day data)
    current_meta = current_7d_data.drop(columns=['date', 'circulating']).drop_duplicates()
    usdc_status = current_meta[current_meta['stablecoin_symbol'] == 'USDC'].groupby('chain')['native_bridged_standard'].apply(
        lambda x: (
            'USDT0' if any(val == 'USDT0' for val in x.values)
            else 'native' if any(val == 'native' for val in x.values)
            else 'Bridged'
        )
    )
    
    usdt_status = current_meta[current_meta['stablecoin_symbol'] == 'USDT'].groupby('chain')['native_bridged_standard'].apply(
        lambda x: (
            'USDT0' if any(val == 'USDT0' for val in x.values)
            else 'native' if any(val == 'native' for val in x.values)
            else 'Bridged'
        )
    )
    
    # Get dominant stablecoin (using average of current 7-day period)
    dominant_stablecoins = current_7d_data.groupby(['chain', 'stablecoin_symbol'])['circulating'].mean().reset_index()
    dominant_stablecoins = dominant_stablecoins.groupby('chain').apply(
        lambda x: x.loc[x['circulating'].idxmax(), 'stablecoin_symbol']
    )
    
    # Get chain launch dates
    chain_launch_dates = df[df['date'] <= current_date].groupby('chain')['date'].min()
    
    # Create records for each chain
    for chain in current_total.index:
        if chain in current_usdc.index:
            rolling_data.append({
                'Chain': chain,
                'USDC Status': usdc_status.get(chain, 'Bridged'),
                'USDT Status': usdt_status.get(chain, 'Bridged'),
                'Chain Launch Date': chain_launch_dates.get(chain, pd.NaT).strftime('%Y-%m-%d') if pd.notnull(chain_launch_dates.get(chain, pd.NaT)) else 'N/A',
                'Dominant Stablecoin': dominant_stablecoins.get(chain, 'Unknown'),
                'Current USDC Amount': current_usdc.get(chain, 0),
                'Total Circulating Stables': current_total.get(chain, 0),
                'USDC % of Total': current_usdc_pct.get(chain, 0),
                'USDC Growth (7d)': usdc_growth_7d.get(chain, 0),
                'USDC % Change (7d)': usdc_growth_rate_7d.get(chain, 0),
                'USDC % of Total Change (7d)': usdc_pct_change_7d.get(chain, 0),
                'Total Growth (7d)': total_growth_7d.get(chain, 0),
                'Total % Change (7d)': total_growth_rate_7d.get(chain, 0),
                'USDC Growth (30d)': usdc_growth_30d.get(chain, 0),
                'USDC % Change (30d)': usdc_growth_rate_30d.get(chain, 0),
                'USDC % of Total Change (30d)': usdc_pct_change_30d.get(chain, 0),
                'Total Growth (30d)': total_growth_30d.get(chain, 0),
                'Total % Change (30d)': total_growth_rate_30d.get(chain, 0),
                'USDC Growth (90d)': usdc_growth_90d.get(chain, 0),
                'USDC % Change (90d)': usdc_growth_rate_90d.get(chain, 0),
                'USDC % of Total Change (90d)': usdc_pct_change_90d.get(chain, 0),
                'Total Growth (90d)': total_growth_90d.get(chain, 0),
                'Total % Change (90d)': total_growth_rate_90d.get(chain, 0)
            })

# Create DataFrame from rolling data (only latest date)
rolling_df = pd.DataFrame(rolling_data)

# Sort by USDC Growth (7d) in descending order
rolling_df = rolling_df.sort_values('USDC Growth (7d)', ascending=False)

# Get only the latest date's data (since we're only keeping latest, all data is from latest date)
latest_rolling = rolling_df.copy()

# Save only the latest data to CSV
latest_rolling.to_csv('usdc_rolling_7d_analysis.csv', index=False)

# Format for printing
latest_rolling_print = latest_rolling.copy()

# Format values for printing
latest_rolling_print['Current USDC Amount'] = latest_rolling_print['Current USDC Amount'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['Total Circulating Stables'] = latest_rolling_print['Total Circulating Stables'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['USDC % of Total'] = latest_rolling_print['USDC % of Total'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC Growth (7d)'] = latest_rolling_print['USDC Growth (7d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['USDC % Change (7d)'] = latest_rolling_print['USDC % Change (7d)'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC % of Total Change (7d)'] = latest_rolling_print['USDC % of Total Change (7d)'].apply(lambda x: f"{x:+.2%}")
latest_rolling_print['Total Growth (7d)'] = latest_rolling_print['Total Growth (7d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['Total % Change (7d)'] = latest_rolling_print['Total % Change (7d)'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC Growth (30d)'] = latest_rolling_print['USDC Growth (30d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['USDC % Change (30d)'] = latest_rolling_print['USDC % Change (30d)'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC % of Total Change (30d)'] = latest_rolling_print['USDC % of Total Change (30d)'].apply(lambda x: f"{x:+.2%}")
latest_rolling_print['Total Growth (30d)'] = latest_rolling_print['Total Growth (30d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['Total % Change (30d)'] = latest_rolling_print['Total % Change (30d)'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC Growth (90d)'] = latest_rolling_print['USDC Growth (90d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['USDC % Change (90d)'] = latest_rolling_print['USDC % Change (90d)'].apply(lambda x: f"{x:.2%}")
latest_rolling_print['USDC % of Total Change (90d)'] = latest_rolling_print['USDC % of Total Change (90d)'].apply(lambda x: f"{x:+.2%}")
latest_rolling_print['Total Growth (90d)'] = latest_rolling_print['Total Growth (90d)'].apply(lambda x: f"${x:,.2f}")
latest_rolling_print['Total % Change (90d)'] = latest_rolling_print['Total % Change (90d)'].apply(lambda x: f"{x:.2%}")

print(f"\n4. Rolling 7-Day USDC Growth Analysis (Latest Date: {all_dates[-1].strftime('%Y-%m-%d')}):")
print(latest_rolling_print.to_string())

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

# sort table by descending launch date
usdt0_performance_df = usdt0_performance_df.sort_values('Launch Date', ascending=False)

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

# Get USDC native/bridged status from metadata
usdc_status = meta_df[meta_df['stablecoin_symbol'] == 'USDC'].groupby('chain')['native_bridged_standard'].apply(
    lambda x: (
        'USDT0' if any(val == 'USDT0' for val in x.values)
        else 'native' if any(val == 'native' for val in x.values)
        else 'Bridged'
    )
)

# Save USDC launch dates data
usdc_launch_dates_df = pd.DataFrame({
    'Chain': usdc_launch_dates.index,
    'Launch Date': usdc_launch_dates['date'].dt.strftime('%Y-%m-%d'),
    'Current Amount': usdc_launch_dates['circulating'],
    'USDC Status': usdc_status.reindex(usdc_launch_dates.index, fill_value='Bridged'),
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

# Get current circulating amounts and historical data
current_amounts = df[df['date'] == latest_date].groupby(['chain', 'stablecoin_symbol'])['circulating'].sum().reset_index()
seven_days_ago = latest_date - timedelta(days=7)
thirty_days_ago = latest_date - timedelta(days=30)

# Get historical amounts
seven_days_ago_amounts = df[df['date'] == seven_days_ago].groupby(['chain', 'stablecoin_symbol'])['circulating'].sum().reset_index()
thirty_days_ago_amounts = df[df['date'] == thirty_days_ago].groupby(['chain', 'stablecoin_symbol'])['circulating'].sum().reset_index()

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

# Add historical data
stablecoin_analysis = pd.merge(
    stablecoin_analysis,
    seven_days_ago_amounts[['chain', 'stablecoin_symbol', 'circulating']].rename(columns={'circulating': 'seven_days_ago_amount'}),
    on=['chain', 'stablecoin_symbol'],
    how='left'
)

stablecoin_analysis = pd.merge(
    stablecoin_analysis,
    thirty_days_ago_amounts[['chain', 'stablecoin_symbol', 'circulating']].rename(columns={'circulating': 'thirty_days_ago_amount'}),
    on=['chain', 'stablecoin_symbol'],
    how='left'
)

# Calculate changes
stablecoin_analysis['7d_change'] = stablecoin_analysis['circulating'] - stablecoin_analysis['seven_days_ago_amount']
stablecoin_analysis['30d_change'] = stablecoin_analysis['circulating'] - stablecoin_analysis['thirty_days_ago_amount']

# Calculate percentage changes
stablecoin_analysis['7d_pct_change'] = stablecoin_analysis.apply(
    lambda x: (x['7d_change'] / x['seven_days_ago_amount']) if x['seven_days_ago_amount'] > 0 else np.nan,
    axis=1
)

stablecoin_analysis['30d_pct_change'] = stablecoin_analysis.apply(
    lambda x: (x['30d_change'] / x['thirty_days_ago_amount']) if x['thirty_days_ago_amount'] > 0 else np.nan,
    axis=1
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
stablecoin_analysis_print['7d_change'] = stablecoin_analysis_print['7d_change'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
stablecoin_analysis_print['30d_change'] = stablecoin_analysis_print['30d_change'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
stablecoin_analysis_print['7d_pct_change'] = stablecoin_analysis_print['7d_pct_change'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
stablecoin_analysis_print['30d_pct_change'] = stablecoin_analysis_print['30d_pct_change'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")

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

# 9. Largest growth in USDT over past 30 days
usdt_data = df[df['stablecoin_symbol'] == 'USDT']

# Get current circulating amounts
usdt_current = usdt_data[usdt_data['date'] == latest_date].groupby('chain')['circulating'].sum()

# Get growth over different periods
usdt_30d_ago = usdt_data[usdt_data['date'] == thirty_days_ago].groupby('chain')['circulating'].sum()
usdt_7d_ago = usdt_data[usdt_data['date'] == seven_days_ago].groupby('chain')['circulating'].sum()
usdt_90d_ago = usdt_data[usdt_data['date'] == ninety_days_ago].groupby('chain')['circulating'].sum()

# Calculate growth amounts
usdt_growth_30d = (usdt_current - usdt_30d_ago)
usdt_growth_7d = (usdt_current - usdt_7d_ago)
usdt_growth_90d = (usdt_current - usdt_90d_ago)

# Calculate percentage changes
usdt_pct_change_30d = usdt_growth_30d / usdt_30d_ago
usdt_pct_change_7d = usdt_growth_7d / usdt_7d_ago
usdt_pct_change_90d = usdt_growth_90d / usdt_90d_ago

# Calculate USDT percentage of total stablecoins for each period
usdt_pct_current = usdt_current / total_current
usdt_pct_7d_ago = usdt_7d_ago / total_7d_ago
usdt_pct_30d_ago = usdt_30d_ago / total_30d_ago
usdt_pct_90d_ago = usdt_90d_ago / total_90d_ago

# Calculate change in USDT percentage of total
usdt_pct_of_total_change_7d = (usdt_pct_current - usdt_pct_7d_ago)
usdt_pct_of_total_change_30d = (usdt_pct_current - usdt_pct_30d_ago)
usdt_pct_of_total_change_90d = (usdt_pct_current - usdt_pct_90d_ago)

# Get USDT native status from metadata
usdt_native = meta_df[meta_df['stablecoin_symbol'] == 'USDT']
usdt_native = usdt_native.groupby('chain')['native_bridged_standard'].apply(
    lambda x: (
        'USDT0' if any(val == 'USDT0' for val in x.values)
        else 'native' if any(val == 'native' for val in x.values)
        else 'Bridged'
    )
)

# Get common chains that have both USDT and total stablecoin data
usdt_chains = usdt_current.index
common_chains = usdt_chains.intersection(total_current.index)

# Create a DataFrame with numeric values only for common chains
usdt_growth_df = pd.DataFrame({
    'Chain': common_chains,
    'USDT Status': usdt_native[usdt_chains].reindex(common_chains, fill_value='Bridged'),
    'Chain Launch Date': chain_launch_dates[common_chains].dt.strftime('%Y-%m-%d'),
    'Dominant Stablecoin': dominant_stablecoins[common_chains],
    'Current USDT Amount': usdt_current[common_chains],
    'Total Circulating Stables': total_current[common_chains],
    'USDT % of Total': usdt_pct_current[common_chains],
    # 7d metrics
    'USDT Growth (7d)': usdt_growth_7d[common_chains],
    'USDT % Change (7d)': usdt_pct_change_7d[common_chains],
    'USDT % of Total Change (7d)': usdt_pct_of_total_change_7d[common_chains],
    'Total Growth (7d)': total_growth_7d[common_chains],
    'Total % Change (7d)': total_pct_change_7d[common_chains],
    # 30d metrics
    'USDT Growth (30d)': usdt_growth_30d[common_chains],
    'USDT % Change (30d)': usdt_pct_change_30d[common_chains],
    'USDT % of Total Change (30d)': usdt_pct_of_total_change_30d[common_chains],
    'Total Growth (30d)': total_growth_30d[common_chains],
    'Total % Change (30d)': total_pct_change_30d[common_chains],
    # 90d metrics
    'USDT Growth (90d)': usdt_growth_90d[common_chains],
    'USDT % Change (90d)': usdt_pct_change_90d[common_chains],
    'USDT % of Total Change (90d)': usdt_pct_of_total_change_90d[common_chains],
    'Total Growth (90d)': total_growth_90d[common_chains],
    'Total % Change (90d)': total_pct_change_90d[common_chains],
})

# Sort by USDT Growth in descending order
usdt_growth_df = usdt_growth_df.sort_values('USDT Growth (30d)', ascending=False)
usdt_growth_df.to_csv('usdt_growth_analysis.csv', index=False)

# Format values for printing
usdt_growth_df_print = usdt_growth_df.copy()
usdt_growth_df_print['Current USDT Amount'] = usdt_growth_df_print['Current USDT Amount'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['Total Circulating Stables'] = usdt_growth_df_print['Total Circulating Stables'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['USDT % of Total'] = usdt_growth_df_print['USDT % of Total'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT Growth (7d)'] = usdt_growth_df_print['USDT Growth (7d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['USDT % Change (7d)'] = usdt_growth_df_print['USDT % Change (7d)'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT % of Total Change (7d)'] = usdt_growth_df_print['USDT % of Total Change (7d)'].apply(lambda x: f"{x:+.2%}")
usdt_growth_df_print['Total Growth (7d)'] = usdt_growth_df_print['Total Growth (7d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['Total % Change (7d)'] = usdt_growth_df_print['Total % Change (7d)'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT Growth (30d)'] = usdt_growth_df_print['USDT Growth (30d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['USDT % Change (30d)'] = usdt_growth_df_print['USDT % Change (30d)'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT % of Total Change (30d)'] = usdt_growth_df_print['USDT % of Total Change (30d)'].apply(lambda x: f"{x:+.2%}")
usdt_growth_df_print['Total Growth (30d)'] = usdt_growth_df_print['Total Growth (30d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['Total % Change (30d)'] = usdt_growth_df_print['Total % Change (30d)'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT Growth (90d)'] = usdt_growth_df_print['USDT Growth (90d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['USDT % Change (90d)'] = usdt_growth_df_print['USDT % Change (90d)'].apply(lambda x: f"{x:.2%}")
usdt_growth_df_print['USDT % of Total Change (90d)'] = usdt_growth_df_print['USDT % of Total Change (90d)'].apply(lambda x: f"{x:+.2%}")
usdt_growth_df_print['Total Growth (90d)'] = usdt_growth_df_print['Total Growth (90d)'].apply(lambda x: f"${x:,.2f}")
usdt_growth_df_print['Total % Change (90d)'] = usdt_growth_df_print['Total % Change (90d)'].apply(lambda x: f"{x:.2%}")

print("\n9. Growth in USDT and Total Stablecoins Over Past 30 Days (Sorted by USDT Growth):")
print(usdt_growth_df_print.to_string())

# Plot USDT growth vs total growth
plot_df = usdt_growth_df.copy()
plot_df = plot_df[(abs(plot_df['USDT Growth (30d)']) >= 100000) | (abs(plot_df['Total Growth (30d)']) >= 100000)]

chains = plot_df['Chain'].tolist()
usdt_growth = plot_df['USDT Growth (30d)'].values
total_growth = plot_df['Total Growth (30d)'].values
x = np.arange(len(chains))
bar_width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
bars1 = ax.bar(x - bar_width/2, usdt_growth, bar_width, label='USDT Growth')
bars2 = ax.bar(x + bar_width/2, total_growth, bar_width, label='Total Growth')

ax.set_xlabel('Chain')
ax.set_ylabel('Growth (USD)')
ax.set_title('USDT vs Total Stablecoin Growth Over Last 30 Days\n(Only showing chains with growth > $100,000)')
ax.set_xticks(x)
ax.set_xticklabels(chains, rotation=45)
ax.legend()
ax.grid(True, axis='y', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('usdt_growth_comparison.png')
plt.close()

# 10. Aggregate Stablecoin Growth Analysis Across All Chains
# Get the earliest date for each stablecoin
earliest_dates = df.groupby('stablecoin_symbol')['date'].min()

# Calculate current and historical totals for each stablecoin
current_totals = df[df['date'] == latest_date].groupby('stablecoin_symbol')['circulating'].sum()
seven_days_ago = latest_date - timedelta(days=7)
thirty_days_ago = latest_date - timedelta(days=30)
ninety_days_ago = latest_date - timedelta(days=90)

seven_days_ago_totals = df[df['date'] == seven_days_ago].groupby('stablecoin_symbol')['circulating'].sum()
thirty_days_ago_totals = df[df['date'] == thirty_days_ago].groupby('stablecoin_symbol')['circulating'].sum()
ninety_days_ago_totals = df[df['date'] == ninety_days_ago].groupby('stablecoin_symbol')['circulating'].sum()

# Calculate growth amounts
growth_7d = current_totals - seven_days_ago_totals
growth_30d = current_totals - thirty_days_ago_totals
growth_90d = current_totals - ninety_days_ago_totals

# Calculate percentage changes
pct_change_7d = growth_7d / seven_days_ago_totals
pct_change_30d = growth_30d / thirty_days_ago_totals
pct_change_90d = growth_90d / ninety_days_ago_totals

# Create DataFrame with all metrics
stablecoin_growth_df = pd.DataFrame({
    'Stablecoin': current_totals.index,
    'First Appearance': earliest_dates,
    'Current Total': current_totals,
    '7d Growth': growth_7d,
    '7d % Change': pct_change_7d,
    '30d Growth': growth_30d,
    '30d % Change': pct_change_30d,
    '90d Growth': growth_90d,
    '90d % Change': pct_change_90d
})

# Sort by current total in descending order
stablecoin_growth_df = stablecoin_growth_df.sort_values('Current Total', ascending=False)

# Save to CSV
stablecoin_growth_df.to_csv('stablecoin_aggregate_growth.csv', index=False)

# Format for printing
stablecoin_growth_print = stablecoin_growth_df.copy()
stablecoin_growth_print['First Appearance'] = stablecoin_growth_print['First Appearance'].dt.strftime('%Y-%m-%d')
stablecoin_growth_print['Current Total'] = stablecoin_growth_print['Current Total'].apply(lambda x: f"${x:,.2f}")
stablecoin_growth_print['7d Growth'] = stablecoin_growth_print['7d Growth'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
stablecoin_growth_print['7d % Change'] = stablecoin_growth_print['7d % Change'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
stablecoin_growth_print['30d Growth'] = stablecoin_growth_print['30d Growth'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
stablecoin_growth_print['30d % Change'] = stablecoin_growth_print['30d % Change'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
stablecoin_growth_print['90d Growth'] = stablecoin_growth_print['90d Growth'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
stablecoin_growth_print['90d % Change'] = stablecoin_growth_print['90d % Change'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")

print("\n10. Aggregate Stablecoin Growth Analysis Across All Chains:")
print(stablecoin_growth_print.to_string())

# 11. New Chain Launch Analysis
# Get earliest date for each chain (first appearance of any stablecoin)
# First, ensure we're using the correct date range
print("\nDebug - Date range in dataset:")
print("Earliest date:", df['date'].min())
print("Latest date:", df['date'].max())

# Get earliest date for each chain where there is actual stablecoin data (circulating > 0)
chain_launch_dates = df[df['circulating'] > 0].groupby('chain')['date'].min().sort_values(ascending=False)

# Get current data for each chain
latest_date = df['date'].max()  # Ensure we're using the actual latest date
latest_data = df[df['date'] == latest_date]
current_totals = latest_data.groupby('chain')['circulating'].sum()

# Calculate USDC and USDT percentages
usdc_amounts = latest_data[latest_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].sum()
usdt_amounts = latest_data[latest_data['stablecoin_symbol'] == 'USDT'].groupby('chain')['circulating'].sum()

# Debug prints
print("\nDebug - Latest Date:", latest_date)
print("\nLatest USDC Totals by Chain:")
print(usdc_amounts.sort_values(ascending=False).apply(lambda x: f"${x:,.2f}"))
print("\nLatest USDT Totals by Chain:")
print(usdt_amounts.sort_values(ascending=False).apply(lambda x: f"${x:,.2f}"))
print("\nLatest Total Stablecoins by Chain:")
print(current_totals.sort_values(ascending=False).apply(lambda x: f"${x:,.2f}"))

# Print some example chain launch dates for verification
print("\nExample Chain Launch Dates:")
for chain in ['Bittorrent', 'Ethereum', 'Tron']:
    if chain in chain_launch_dates.index:
        print(f"{chain}: {chain_launch_dates[chain]}")

usdc_pct = usdc_amounts / current_totals
usdt_pct = usdt_amounts / current_totals

# Calculate growth rates
seven_days_ago = latest_date - timedelta(days=7)
thirty_days_ago = latest_date - timedelta(days=30)
ninety_days_ago = latest_date - timedelta(days=90)

seven_days_ago_totals = df[df['date'] == seven_days_ago].groupby('chain')['circulating'].sum()
thirty_days_ago_totals = df[df['date'] == thirty_days_ago].groupby('chain')['circulating'].sum()
ninety_days_ago_totals = df[df['date'] == ninety_days_ago].groupby('chain')['circulating'].sum()

growth_7d = (current_totals - seven_days_ago_totals) / seven_days_ago_totals
growth_30d = (current_totals - thirty_days_ago_totals) / thirty_days_ago_totals
growth_90d = (current_totals - ninety_days_ago_totals) / ninety_days_ago_totals

# Create DataFrame with all metrics
chain_launch_analysis = pd.DataFrame({
    'Launch Date': chain_launch_dates.dt.strftime('%Y-%m-%d'),
    'Total Stablecoins': current_totals,
    'USDC %': usdc_pct,
    'USDT %': usdt_pct,
    '7d Growth': growth_7d,
    '30d Growth': growth_30d,
    '90d Growth': growth_90d
}, index=chain_launch_dates.index)

# Sort by launch date (most recent first)
chain_launch_analysis = chain_launch_analysis.sort_values('Launch Date', ascending=False)

# Save to CSV
chain_launch_analysis.to_csv('chain_launch_analysis.csv')

# Format for printing
chain_launch_print = chain_launch_analysis.copy()
chain_launch_print['Total Stablecoins'] = chain_launch_print['Total Stablecoins'].apply(lambda x: f"${x:,.2f}")
chain_launch_print['USDC %'] = chain_launch_print['USDC %'].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
chain_launch_print['USDT %'] = chain_launch_print['USDT %'].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
chain_launch_print['7d Growth'] = chain_launch_print['7d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
chain_launch_print['30d Growth'] = chain_launch_print['30d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
chain_launch_print['90d Growth'] = chain_launch_print['90d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")

print("\n11. Chain Launch Analysis (Sorted by Launch Date):")
print(chain_launch_print.to_string())

# 12. Chain TVL and Stablecoin Analysis
# Read chain TVL data
tvl_stable = pd.read_csv('chain_tvl_data.csv')

# Read stablecoin data
stable_data = pd.read_csv('all_stablecoins_chain_distribution.csv')
stable_data['date'] = pd.to_datetime(stable_data['date'])

# Get latest date
latest_date = stable_data['date'].max()
seven_days_ago = latest_date - timedelta(days=7)
thirty_days_ago = latest_date - timedelta(days=30)
ninety_days_ago = latest_date - timedelta(days=90)

# Calculate current stablecoin metrics
latest_stable_data = stable_data[stable_data['date'] == latest_date]
chain_stable_totals = latest_stable_data.groupby('chain')['circulating'].sum()
chain_usdc_totals = latest_stable_data[latest_stable_data['stablecoin_symbol'] == 'USDC'].groupby('chain')['circulating'].sum()
chain_usdc_percentage = (chain_usdc_totals / chain_stable_totals).fillna(0)

# Calculate stablecoin growth rates
def get_stable_growth(days_ago):
    past_data = stable_data[stable_data['date'] == days_ago]
    past_totals = past_data.groupby('chain')['circulating'].sum()
    current_totals = latest_stable_data.groupby('chain')['circulating'].sum()
    growth = (current_totals - past_totals) / past_totals
    return growth

stable_growth_7d = get_stable_growth(seven_days_ago)
stable_growth_30d = get_stable_growth(thirty_days_ago)
stable_growth_90d = get_stable_growth(ninety_days_ago)

# Calculate historical stablecoin circulation for ratio calculations
seven_days_ago_stable_data = stable_data[stable_data['date'] == seven_days_ago]
thirty_days_ago_stable_data = stable_data[stable_data['date'] == thirty_days_ago]
ninety_days_ago_stable_data = stable_data[stable_data['date'] == ninety_days_ago]

chain_stable_totals_7d = seven_days_ago_stable_data.groupby('chain')['circulating'].sum()
chain_stable_totals_30d = thirty_days_ago_stable_data.groupby('chain')['circulating'].sum()
chain_stable_totals_90d = ninety_days_ago_stable_data.groupby('chain')['circulating'].sum()

# Create stablecoin metrics DataFrame
stable_metrics = pd.DataFrame({
    'Chain': chain_stable_totals.index,
    'Current Stablecoin Circulation': chain_stable_totals,
    'USDC % of Stables': chain_usdc_percentage,
    'Stablecoin Growth (7d)': stable_growth_7d,
    'Stablecoin Growth (30d)': stable_growth_30d,
    'Stablecoin Growth (90d)': stable_growth_90d,
    'Stablecoin Circulation (7d ago)': chain_stable_totals_7d,
    'Stablecoin Circulation (30d ago)': chain_stable_totals_30d,
    'Stablecoin Circulation (90d ago)': chain_stable_totals_90d
})

# Merge TVL data with stablecoin metrics
tvl_stable = tvl_stable.merge(stable_metrics, on='Chain', how='left')

# Calculate TVL/Stablecoin ratios
tvl_stable['Current TVL/Stablecoin Ratio'] = tvl_stable['Current TVL'] / tvl_stable['Current Stablecoin Circulation']

# Calculate historical TVL amounts for ratio calculations
tvl_stable['TVL 7d ago'] = tvl_stable['Current TVL'] / (1 + tvl_stable['7d Growth'])
tvl_stable['TVL 30d ago'] = tvl_stable['Current TVL'] / (1 + tvl_stable['30d Growth'])
tvl_stable['TVL 90d ago'] = tvl_stable['Current TVL'] / (1 + tvl_stable['90d Growth'])

# Calculate historical TVL/Stablecoin ratios
tvl_stable['TVL/Stablecoin Ratio (7d ago)'] = tvl_stable['TVL 7d ago'] / tvl_stable['Stablecoin Circulation (7d ago)']
tvl_stable['TVL/Stablecoin Ratio (30d ago)'] = tvl_stable['TVL 30d ago'] / tvl_stable['Stablecoin Circulation (30d ago)']
tvl_stable['TVL/Stablecoin Ratio (90d ago)'] = tvl_stable['TVL 90d ago'] / tvl_stable['Stablecoin Circulation (90d ago)']

# Convert DeFi Launch Date to datetime
tvl_stable['DeFi Launch Date'] = pd.to_datetime(tvl_stable['DeFi Launch Date'])

# Format the output
tvl_stable_print = tvl_stable.copy()
tvl_stable_print['Current TVL'] = tvl_stable_print['Current TVL'].apply(lambda x: f"${x:,.2f}")
tvl_stable_print['Current Stablecoin Circulation'] = tvl_stable_print['Current Stablecoin Circulation'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
tvl_stable_print['USDC % of Stables'] = tvl_stable_print['USDC % of Stables'].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['DeFi Launch Date'] = tvl_stable_print['DeFi Launch Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else 'N/A')
tvl_stable_print['7d Growth'] = tvl_stable_print['7d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['30d Growth'] = tvl_stable_print['30d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['90d Growth'] = tvl_stable_print['90d Growth'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['Stablecoin Growth (7d)'] = tvl_stable_print['Stablecoin Growth (7d)'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['Stablecoin Growth (30d)'] = tvl_stable_print['Stablecoin Growth (30d)'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['Stablecoin Growth (90d)'] = tvl_stable_print['Stablecoin Growth (90d)'].apply(lambda x: f"{x:+.2%}" if pd.notnull(x) else "N/A")
tvl_stable_print['Current TVL/Stablecoin Ratio'] = tvl_stable_print['Current TVL/Stablecoin Ratio'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
tvl_stable_print['TVL/Stablecoin Ratio (7d ago)'] = tvl_stable_print['TVL/Stablecoin Ratio (7d ago)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
tvl_stable_print['TVL/Stablecoin Ratio (30d ago)'] = tvl_stable_print['TVL/Stablecoin Ratio (30d ago)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
tvl_stable_print['TVL/Stablecoin Ratio (90d ago)'] = tvl_stable_print['TVL/Stablecoin Ratio (90d ago)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")

# sort table by descending launch date
tvl_stable_print = tvl_stable_print.sort_values('DeFi Launch Date', ascending=False)

# Save to CSV
tvl_stable.to_csv('chain_tvl_stable_analysis.csv', index=False)

print("\n12. Chain TVL and Stablecoin Analysis (Sorted by Current TVL):")
print(tvl_stable_print.to_string())

print("\nAll analysis complete! CSV files have been generated.")
print("Run 'python src/google_sheets_upload.py' to upload the data to Google Sheets.")