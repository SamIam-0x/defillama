import pandas as pd
import json
import requests
import time
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings()

print("\n" + "=" * 80)
print("New Chains Lending TVL Growth Analysis - First 180 Days")
print("=" * 80)

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

# Calculate the cutoff date (2 years ago)
two_years_ago = datetime.now() - timedelta(days=730)
print(f"\nAnalyzing chains launched after: {two_years_ago.strftime('%Y-%m-%d')}")

# Read existing chain TVL data to identify recently launched chains
print("\n📊 Loading chain launch data...")
try:
    chain_tvl_df = pd.read_csv('chain_tvl_data.csv')
    chain_tvl_df['DeFi Launch Date'] = pd.to_datetime(chain_tvl_df['DeFi Launch Date'])
    
    # Filter for chains launched in the last 2 years
    recent_chains = chain_tvl_df[chain_tvl_df['DeFi Launch Date'] >= two_years_ago].copy()
    recent_chains = recent_chains.sort_values('DeFi Launch Date', ascending=False)
    
    print(f"Found {len(recent_chains)} chains launched in the last 2 years")
except FileNotFoundError:
    print("❌ chain_tvl_data.csv not found. Please run the main import script first.")
    exit(1)

# Load lending protocols data
print("\n📊 Loading lending protocols data...")
tvl_df = pd.read_csv('tvl_data.csv')
lending_df = tvl_df[tvl_df['category'] == 'Lending'].copy()
print(f"Total lending protocols: {len(lending_df)}")

# Function to safely parse chainTvls
def parse_chain_tvls(chain_tvls_str):
    """Parse the chainTvls column which contains Python dict data"""
    try:
        if pd.isna(chain_tvls_str):
            return {}
        import ast
        return ast.literal_eval(chain_tvls_str)
    except:
        try:
            return json.loads(chain_tvls_str)
        except:
            return {}

lending_df['chainTvls_parsed'] = lending_df['chainTvls'].apply(parse_chain_tvls)

# Filter recent_chains to only those with lending protocols
chains_with_lending = set()
for _, protocol in lending_df.iterrows():
    chain_tvls = protocol['chainTvls_parsed']
    if chain_tvls:
        for chain_name in chain_tvls.keys():
            # Skip metadata keys
            if chain_name not in ['tvl', 'staking', 'pool2', 'borrowed', 'treasury'] and '-' not in chain_name:
                chains_with_lending.add(chain_name)

recent_chains = recent_chains[recent_chains['Chain'].isin(chains_with_lending)].copy()
print(f"Filtered to {len(recent_chains)} chains with lending protocols")

print("\nRecent chains with lending protocols:")
for idx, row in recent_chains.head(15).iterrows():
    print(f"  • {row['Chain']:.<30} launched {row['DeFi Launch Date'].strftime('%Y-%m-%d')}")

# Limit to top chains by current TVL to make analysis faster
# Process top 20 by current TVL
recent_chains = recent_chains.nlargest(20, 'Current TVL')
print(f"\nAnalyzing top {len(recent_chains)} chains by current TVL...")

# For each recent chain, get historical TVL data
all_chain_lending_growth = []

for idx, chain_info in recent_chains.iterrows():
    chain_name = chain_info['Chain']
    launch_date = chain_info['DeFi Launch Date']
    
    print(f"\n{'=' * 80}")
    print(f"Processing: {chain_name}")
    print(f"Launch Date: {launch_date.strftime('%Y-%m-%d')}")
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
        print(f"Fetching data from: {historical_url}")
        
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
        
        print(f"✓ Retrieved {len(chain_historical_data)} historical data points")
        
        # Convert to DataFrame
        chain_hist_df = pd.DataFrame(chain_historical_data)
        chain_hist_df['date'] = pd.to_datetime(chain_hist_df['date'], unit='s')
        
        # Filter for first 180 days after launch
        chain_hist_df = chain_hist_df[
            (chain_hist_df['date'] >= launch_date) &
            (chain_hist_df['date'] <= end_date)
        ].copy()
        
        print(f"✓ Filtered to {len(chain_hist_df)} data points in first 180 days")
        
        if len(chain_hist_df) == 0:
            print(f"⚠️  No data available in the first 180 days")
            continue
        
        # Now get protocol-specific historical data for lending protocols on this chain
        # Find which lending protocols are active on this chain
        lending_protocols_on_chain = []
        for _, protocol in lending_df.iterrows():
            chain_tvls = protocol['chainTvls_parsed']
            if chain_tvls and chain_name in chain_tvls:
                lending_protocols_on_chain.append({
                    'name': protocol['name'],
                    'slug': protocol['slug']
                })
        
        print(f"✓ Found {len(lending_protocols_on_chain)} lending protocols on {chain_name}")
        
        if len(lending_protocols_on_chain) == 0:
            print(f"⚠️  No lending protocols found on {chain_name}")
            # Still record the chain with zero lending TVL
            for _, row in chain_hist_df.iterrows():
                days_since_launch = (row['date'] - launch_date).days
                record = {
                    'chain': chain_name,
                    'launch_date': launch_date,
                    'date': row['date'],
                    'days_since_launch': days_since_launch,
                    'total_chain_tvl': row['tvl'],
                    'lending_tvl': 0,
                    'lending_percentage': 0.0,
                    'num_lending_protocols': 0
                }
                all_chain_lending_growth.append(record)
            continue
        
        # Get historical TVL for each lending protocol
        daily_lending_tvl = {}  # date -> total lending TVL
        
        for protocol_info in lending_protocols_on_chain:
            protocol_slug = protocol_info['slug']
            protocol_name = protocol_info['name']
            
            try:
                # Get historical TVL for this protocol
                protocol_url = f"https://api.llama.fi/protocol/{protocol_slug}"
                print(f"  Fetching {protocol_name}...")
                
                protocol_response = session.get(protocol_url, headers=headers, timeout=30)
                time.sleep(0.5)  # Rate limiting
                
                if protocol_response.status_code != 200:
                    print(f"  ⚠️  Failed to fetch {protocol_name}")
                    continue
                
                protocol_data = protocol_response.json()
                
                # Get chain-specific TVL history
                if 'chainTvls' not in protocol_data:
                    print(f"  ⚠️  No chain TVL data for {protocol_name}")
                    continue
                
                chain_tvl_history = protocol_data['chainTvls'].get(chain_name, {})
                
                if not chain_tvl_history:
                    print(f"  ⚠️  No {chain_name} TVL history for {protocol_name}")
                    continue
                
                # The chain_tvl_history can be:
                # 1. A dict with {timestamp: tvl}
                # 2. A dict with {'tvl': {timestamp: tvl}}
                # 3. A list of {date: timestamp, tvl: value} objects
                
                tvl_data_points = {}
                
                if isinstance(chain_tvl_history, list):
                    # It's a list of data points
                    for data_point in chain_tvl_history:
                        if isinstance(data_point, dict) and 'date' in data_point:
                            timestamp = data_point['date']
                            tvl_value = data_point.get('tvl', 0)
                            try:
                                date = datetime.fromtimestamp(int(timestamp))
                                if launch_date <= date <= end_date:
                                    date_key = date.strftime('%Y-%m-%d')
                                    if date_key not in tvl_data_points:
                                        tvl_data_points[date_key] = 0
                                    tvl_data_points[date_key] += tvl_value
                            except (ValueError, TypeError):
                                continue
                elif isinstance(chain_tvl_history, dict):
                    # Check if it has a 'tvl' key
                    if 'tvl' in chain_tvl_history and isinstance(chain_tvl_history['tvl'], dict):
                        chain_tvl_history = chain_tvl_history['tvl']
                    
                    # Convert timestamps to dates and aggregate
                    for timestamp, tvl_value in chain_tvl_history.items():
                        if timestamp in ['tvl', 'tokensInUsd', 'tokens']:
                            continue
                        try:
                            date = datetime.fromtimestamp(int(timestamp))
                            
                            # Only include dates in our 180-day window
                            if launch_date <= date <= end_date:
                                date_key = date.strftime('%Y-%m-%d')
                                if date_key not in tvl_data_points:
                                    tvl_data_points[date_key] = 0
                                tvl_data_points[date_key] += tvl_value
                        except (ValueError, TypeError):
                            continue
                
                # Merge into daily_lending_tvl
                for date_key, tvl_value in tvl_data_points.items():
                    if date_key not in daily_lending_tvl:
                        daily_lending_tvl[date_key] = 0
                    daily_lending_tvl[date_key] += tvl_value
                
                print(f"  ✓ Added {protocol_name} data")
                
            except Exception as e:
                print(f"  ❌ Error fetching {protocol_name}: {str(e)}")
                continue
        
        print(f"\n✓ Collected lending TVL data for {len(daily_lending_tvl)} days")
        
        # Merge with total chain TVL
        for _, row in chain_hist_df.iterrows():
            date = row['date']
            date_key = date.strftime('%Y-%m-%d')
            days_since_launch = (date - launch_date).days
            
            lending_tvl = daily_lending_tvl.get(date_key, 0)
            total_tvl = row['tvl']
            lending_percentage = (lending_tvl / total_tvl * 100) if total_tvl > 0 else 0
            
            record = {
                'chain': chain_name,
                'launch_date': launch_date,
                'date': date,
                'days_since_launch': days_since_launch,
                'total_chain_tvl': total_tvl,
                'lending_tvl': lending_tvl,
                'lending_percentage': lending_percentage,
                'num_lending_protocols': len(lending_protocols_on_chain)
            }
            all_chain_lending_growth.append(record)
        
        # Print summary for this chain
        if daily_lending_tvl:
            max_lending_tvl = max(daily_lending_tvl.values())
            print(f"\n📊 Summary for {chain_name}:")
            print(f"  • Peak lending TVL in first 180 days: ${max_lending_tvl:,.2f}")
            print(f"  • Number of lending protocols: {len(lending_protocols_on_chain)}")
        
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

print(f"\n✅ Saved data to {output_file}")
print(f"Total records: {len(growth_df)}")
print(f"Chains analyzed: {growth_df['chain'].nunique()}")

# Create summary statistics
print("\n" + "=" * 80)
print("Summary Statistics - First 180 Days")
print("=" * 80)

summary_stats = []
for chain in growth_df['chain'].unique():
    chain_data = growth_df[growth_df['chain'] == chain]
    
    # Get day 0, day 30, day 60, day 90, day 180 (or max available)
    launch_data = chain_data[chain_data['days_since_launch'] == 0].iloc[0] if len(chain_data[chain_data['days_since_launch'] == 0]) > 0 else None
    day_30 = chain_data[chain_data['days_since_launch'] <= 30].tail(1).iloc[0] if len(chain_data[chain_data['days_since_launch'] <= 30]) > 0 else None
    day_60 = chain_data[chain_data['days_since_launch'] <= 60].tail(1).iloc[0] if len(chain_data[chain_data['days_since_launch'] <= 60]) > 0 else None
    day_90 = chain_data[chain_data['days_since_launch'] <= 90].tail(1).iloc[0] if len(chain_data[chain_data['days_since_launch'] <= 90]) > 0 else None
    day_180 = chain_data.tail(1).iloc[0]
    
    max_lending_tvl = chain_data['lending_tvl'].max()
    max_lending_day = chain_data[chain_data['lending_tvl'] == max_lending_tvl].iloc[0]['days_since_launch']
    
    summary_stats.append({
        'chain': chain,
        'launch_date': chain_data.iloc[0]['launch_date'],
        'days_tracked': chain_data['days_since_launch'].max(),
        'num_lending_protocols': chain_data.iloc[0]['num_lending_protocols'],
        'lending_tvl_day_0': launch_data['lending_tvl'] if launch_data is not None else 0,
        'lending_tvl_day_30': day_30['lending_tvl'] if day_30 is not None else 0,
        'lending_tvl_day_60': day_60['lending_tvl'] if day_60 is not None else 0,
        'lending_tvl_day_90': day_90['lending_tvl'] if day_90 is not None else 0,
        'lending_tvl_day_180': day_180['lending_tvl'],
        'peak_lending_tvl': max_lending_tvl,
        'peak_lending_day': max_lending_day,
        'final_lending_percentage': day_180['lending_percentage']
    })

summary_df = pd.DataFrame(summary_stats)
summary_df = summary_df.sort_values('peak_lending_tvl', ascending=False)

# Save summary
summary_file = 'new_chains_lending_growth_summary.csv'
summary_df.to_csv(summary_file, index=False)

print(f"\n✅ Saved summary to {summary_file}")

# Display top performers
print("\n📊 Top 10 Chains by Peak Lending TVL in First 180 Days:")
print("-" * 100)
print(f"{'Chain':<20} {'Launch Date':<12} {'Days':<6} {'Peak TVL':>15} {'Day 30':>15} {'Day 90':>15} {'Day 180':>15}")
print("-" * 100)

for idx, row in summary_df.head(10).iterrows():
    print(f"{row['chain']:<20} {pd.to_datetime(row['launch_date']).strftime('%Y-%m-%d'):<12} {int(row['days_tracked']):<6} "
          f"${row['peak_lending_tvl']:>13,.0f} ${row['lending_tvl_day_30']:>13,.0f} "
          f"${row['lending_tvl_day_90']:>13,.0f} ${row['lending_tvl_day_180']:>13,.0f}")

print("\n" + "=" * 80)
print("✅ Analysis Complete!")
print("=" * 80)
print(f"\nOutput files:")
print(f"  1. {output_file} - Daily lending TVL data")
print(f"  2. {summary_file} - Summary statistics by chain")
