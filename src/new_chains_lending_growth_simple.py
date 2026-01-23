import pandas as pd
import json
import requests
import time
from datetime import datetime, timedelta
import ast
import urllib3

urllib3.disable_warnings()

print("\n" + "=" * 80)
print("New Chains Lending TVL Growth Analysis - First 180 Days")
print("(Using current lending % applied to historical total TVL)")
print("=" * 80)

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

# Calculate the cutoff date (2 years ago)
two_years_ago = datetime.now() - timedelta(days=730)
print(f"\nAnalyzing chains launched after: {two_years_ago.strftime('%Y-%m-%d')}")

# Read existing chain TVL data to identify recently launched chains
print("\n📊 Loading chain launch data...")
chain_tvl_df = pd.read_csv('chain_tvl_data.csv')
chain_tvl_df['DeFi Launch Date'] = pd.to_datetime(chain_tvl_df['DeFi Launch Date'])

# Filter for chains launched in the last 2 years
recent_chains = chain_tvl_df[chain_tvl_df['DeFi Launch Date'] >= two_years_ago].copy()
recent_chains = recent_chains.sort_values('DeFi Launch Date', ascending=False)

print(f"Found {len(recent_chains)} chains launched in the last 2 years")

# Load lending protocols data and calculate current lending TVL by chain
print("\n📊 Loading lending protocols data...")
tvl_df = pd.read_csv('tvl_data.csv')
lending_df = tvl_df[tvl_df['category'] == 'Lending'].copy()

def parse_chain_tvls(chain_tvls_str):
    """Parse the chainTvls column"""
    try:
        if pd.isna(chain_tvls_str):
            return {}
        return ast.literal_eval(chain_tvls_str)
    except:
        try:
            return json.loads(chain_tvls_str)
        except:
            return {}

lending_df['chainTvls_parsed'] = lending_df['chainTvls'].apply(parse_chain_tvls)

# Calculate current lending TVL by chain
current_lending_by_chain = {}
for _, protocol in lending_df.iterrows():
    chain_tvls = protocol['chainTvls_parsed']
    if chain_tvls:
        for chain_key, tvl_value in chain_tvls.items():
            # Skip metadata keys and borrowed amounts
            if chain_key in ['tvl', 'staking', 'pool2', 'borrowed', 'treasury']:
                continue
            if '-' in chain_key and any(suffix in chain_key.lower() for suffix in ['borrowed', 'staking', 'pool2', 'treasury']):
                continue
            
            chain = chain_key
            
            # Parse TVL value
            if isinstance(tvl_value, dict):
                tvl = tvl_value.get('tvl', 0) if tvl_value else 0
            else:
                tvl = tvl_value if tvl_value else 0
            
            if tvl > 0:
                if chain not in current_lending_by_chain:
                    current_lending_by_chain[chain] = 0
                current_lending_by_chain[chain] += tvl

print(f"Calculated current lending TVL for {len(current_lending_by_chain)} chains")

# Filter recent_chains to only those with lending protocols
recent_chains = recent_chains[recent_chains['Chain'].isin(current_lending_by_chain.keys())].copy()
print(f"Filtered to {len(recent_chains)} recent chains with lending protocols")

# Calculate lending percentage for each chain
recent_chains['current_lending_tvl'] = recent_chains['Chain'].map(current_lending_by_chain)
recent_chains['lending_percentage'] = (recent_chains['current_lending_tvl'] / recent_chains['Current TVL'] * 100).round(2)

print("\nRecent chains with lending activity:")
print("-" * 80)
print(f"{'Chain':<25} {'Launch Date':<12} {'Current TVL':>15} {'Lending TVL':>15} {'Lending %':>10}")
print("-" * 80)
for idx, row in recent_chains.nlargest(20, 'Current TVL').iterrows():
    print(f"{row['Chain']:<25} {row['DeFi Launch Date'].strftime('%Y-%m-%d'):<12} "
          f"${row['Current TVL']:>13,.0f} ${row['current_lending_tvl']:>13,.0f} {row['lending_percentage']:>9.1f}%")

# Select top chains by current TVL for detailed analysis
chains_to_analyze = recent_chains.nlargest(15, 'Current TVL')
print(f"\n\nAnalyzing detailed growth for top {len(chains_to_analyze)} chains...")

all_chain_lending_growth = []

for idx, chain_info in chains_to_analyze.iterrows():
    chain_name = chain_info['Chain']
    launch_date = chain_info['DeFi Launch Date']
    lending_pct = chain_info['lending_percentage'] / 100
    current_lending_tvl = chain_info['current_lending_tvl']
    
    print(f"\n{'=' * 80}")
    print(f"Processing: {chain_name}")
    print(f"Launch Date: {launch_date.strftime('%Y-%m-%d')}")
    print(f"Current Lending %: {lending_pct * 100:.2f}%")
    print(f"{'=' * 80}")
    
    # Calculate the date range for first 180 days
    end_date = launch_date + timedelta(days=180)
    if end_date > datetime.now():
        end_date = datetime.now()
    
    days_available = (end_date - launch_date).days
    print(f"Analyzing {days_available} days of data (up to 180 days)")
    
    try:
        # Get historical TVL data for this chain
        historical_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
        headers = {'User-Agent': 'curl/7.64.1'}
        hist_response = session.get(historical_url, headers=headers, timeout=30)
        time.sleep(0.5)  # Rate limiting
        
        if hist_response.status_code != 200:
            print(f"❌ Failed to fetch data: Status {hist_response.status_code}")
            continue
        
        chain_historical_data = hist_response.json()
        
        if not chain_historical_data or not isinstance(chain_historical_data, list):
            print(f"❌ Invalid data format")
            continue
        
        # Convert to DataFrame
        chain_hist_df = pd.DataFrame(chain_historical_data)
        chain_hist_df['date'] = pd.to_datetime(chain_hist_df['date'], unit='s')
        
        # Filter for first 180 days after launch
        chain_hist_df = chain_hist_df[
            (chain_hist_df['date'] >= launch_date) &
            (chain_hist_df['date'] <= end_date)
        ].copy()
        
        print(f"✓ Retrieved {len(chain_hist_df)} data points in first 180 days")
        
        if len(chain_hist_df) == 0:
            print(f"⚠️  No data available in the first 180 days")
            continue
        
        # Calculate estimated lending TVL by applying current lending percentage
        chain_hist_df['estimated_lending_tvl'] = chain_hist_df['tvl'] * lending_pct
        chain_hist_df['days_since_launch'] = (chain_hist_df['date'] - launch_date).dt.days
        chain_hist_df['chain'] = chain_name
        chain_hist_df['launch_date'] = launch_date
        chain_hist_df['lending_percentage'] = lending_pct * 100
        
        # Add to results
        for _, row in chain_hist_df.iterrows():
            record = {
                'chain': chain_name,
                'launch_date': launch_date,
                'date': row['date'],
                'days_since_launch': row['days_since_launch'],
                'total_chain_tvl': row['tvl'],
                'estimated_lending_tvl': row['estimated_lending_tvl'],
                'lending_percentage': row['lending_percentage']
            }
            all_chain_lending_growth.append(record)
        
        # Print summary
        print(f"\n📊 Growth Summary:")
        print(f"  • Day 0 TVL: ${chain_hist_df.iloc[0]['tvl']:,.0f} (est. lending: ${chain_hist_df.iloc[0]['estimated_lending_tvl']:,.0f})")
        if len(chain_hist_df) >= 30:
            day_30 = chain_hist_df[chain_hist_df['days_since_launch'] <= 30].iloc[-1]
            print(f"  • Day 30 TVL: ${day_30['tvl']:,.0f} (est. lending: ${day_30['estimated_lending_tvl']:,.0f})")
        if len(chain_hist_df) >= 90:
            day_90 = chain_hist_df[chain_hist_df['days_since_launch'] <= 90].iloc[-1]
            print(f"  • Day 90 TVL: ${day_90['tvl']:,.0f} (est. lending: ${day_90['estimated_lending_tvl']:,.0f})")
        final_day = chain_hist_df.iloc[-1]
        print(f"  • Day {int(final_day['days_since_launch'])} TVL: ${final_day['tvl']:,.0f} (est. lending: ${final_day['estimated_lending_tvl']:,.0f})")
        
    except Exception as e:
        print(f"❌ Error processing {chain_name}: {str(e)}")
        continue

# Create DataFrame from all collected data
print("\n" + "=" * 80)
print("Creating final dataset...")
print("=" * 80)

if not all_chain_lending_growth:
    print("❌ No data collected. Exiting.")
    exit(1)

growth_df = pd.DataFrame(all_chain_lending_growth)
growth_df = growth_df.sort_values(['chain', 'days_since_launch'])

# Save to CSV
output_file = 'new_chains_lending_growth_180days.csv'
growth_df.to_csv(output_file, index=False)

print(f"\n✅ Saved detailed data to {output_file}")
print(f"Total records: {len(growth_df)}")
print(f"Chains analyzed: {growth_df['chain'].nunique()}")

# Create summary statistics
print("\n" + "=" * 80)
print("Summary Statistics - First 180 Days")
print("=" * 80)

summary_stats = []
for chain in growth_df['chain'].unique():
    chain_data = growth_df[growth_df['chain'] == chain].sort_values('days_since_launch')
    
    day_0 = chain_data.iloc[0]
    day_30 = chain_data[chain_data['days_since_launch'] <= 30].iloc[-1] if len(chain_data[chain_data['days_since_launch'] <= 30]) > 0 else day_0
    day_60 = chain_data[chain_data['days_since_launch'] <= 60].iloc[-1] if len(chain_data[chain_data['days_since_launch'] <= 60]) > 0 else day_30
    day_90 = chain_data[chain_data['days_since_launch'] <= 90].iloc[-1] if len(chain_data[chain_data['days_since_launch'] <= 90]) > 0 else day_60
    day_180 = chain_data.iloc[-1]
    
    max_lending = chain_data['estimated_lending_tvl'].max()
    max_day = chain_data[chain_data['estimated_lending_tvl'] == max_lending].iloc[0]['days_since_launch']
    
    summary_stats.append({
        'chain': chain,
        'launch_date': day_0['launch_date'],
        'days_tracked': int(day_180['days_since_launch']),
        'lending_tvl_day_0': day_0['estimated_lending_tvl'],
        'lending_tvl_day_30': day_30['estimated_lending_tvl'],
        'lending_tvl_day_60': day_60['estimated_lending_tvl'],
        'lending_tvl_day_90': day_90['estimated_lending_tvl'],
        'lending_tvl_day_180': day_180['estimated_lending_tvl'],
        'peak_lending_tvl': max_lending,
        'peak_lending_day': int(max_day),
        'lending_percentage': day_0['lending_percentage'],
        'growth_0_to_30': ((day_30['estimated_lending_tvl'] - day_0['estimated_lending_tvl']) / day_0['estimated_lending_tvl'] * 100) if day_0['estimated_lending_tvl'] > 0 else 0,
        'growth_0_to_90': ((day_90['estimated_lending_tvl'] - day_0['estimated_lending_tvl']) / day_0['estimated_lending_tvl'] * 100) if day_0['estimated_lending_tvl'] > 0 else 0,
        'growth_0_to_180': ((day_180['estimated_lending_tvl'] - day_0['estimated_lending_tvl']) / day_0['estimated_lending_tvl'] * 100) if day_0['estimated_lending_tvl'] > 0 else 0
    })

summary_df = pd.DataFrame(summary_stats)
summary_df = summary_df.sort_values('peak_lending_tvl', ascending=False)

# Save summary
summary_file = 'new_chains_lending_growth_summary.csv'
summary_df.to_csv(summary_file, index=False)

print(f"\n✅ Saved summary to {summary_file}")

# Display top performers
print("\n📊 Top Chains by Peak Lending TVL in First 180 Days:")
print("-" * 120)
print(f"{'Chain':<20} {'Launch':<12} {'Days':<6} {'Day 0 TVL':>15} {'Day 30':>15} {'Day 90':>15} {'Peak TVL':>15} {'Grow 0-180':>12}")
print("-" * 120)

for idx, row in summary_df.head(15).iterrows():
    print(f"{row['chain']:<20} {pd.to_datetime(row['launch_date']).strftime('%Y-%m-%d'):<12} {row['days_tracked']:<6} "
          f"${row['lending_tvl_day_0']:>13,.0f} ${row['lending_tvl_day_30']:>13,.0f} "
          f"${row['lending_tvl_day_90']:>13,.0f} ${row['peak_lending_tvl']:>13,.0f} {row['growth_0_to_180']:>10.0f}%")

print("\n" + "=" * 80)
print("✅ Analysis Complete!")
print("=" * 80)
print(f"\nOutput files:")
print(f"  1. {output_file} - Daily lending TVL data (estimated)")
print(f"  2. {summary_file} - Summary statistics by chain")
print(f"\nNote: Lending TVL is estimated by applying current lending percentage")
print(f"      to historical total chain TVL.")
