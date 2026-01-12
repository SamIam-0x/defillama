import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib3
import json
urllib3.disable_warnings()

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

print("=" * 80)
print("Chain Launch & Growth Analysis")
print("=" * 80)
print("Analyzing chains that reached $100M TVL in their first year after launch")
print("=" * 80)

# Get all chains data
chains_url = "https://api.llama.fi/v2/chains"
chains_response = session.get(chains_url)
time.sleep(0.25)
all_chains = chains_response.json()

# Sort by TVL
all_chains.sort(key=lambda x: x.get('tvl', 0), reverse=True)

print(f"\nFetching historical data for {len(all_chains)} chains...")

# Lists to store chain data
tvl_analysis_data = []
stablecoin_analysis_data = []

# Load stablecoin data
try:
    stablecoins_df = pd.read_csv('all_stablecoins_chain_distribution.csv')
    stablecoins_df['date'] = pd.to_datetime(stablecoins_df['date'])
    print(f"✓ Loaded stablecoin data with {len(stablecoins_df)} records")
except Exception as e:
    print(f"✗ Error loading stablecoin data: {e}")
    stablecoins_df = None

# Process each chain
for i, chain in enumerate(all_chains, 1):
    chain_name = chain['name']
    print(f"\n[{i}/{len(all_chains)}] Processing: {chain_name}")
    
    try:
        # Get historical TVL data
        historical_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
        headers = {'User-Agent': 'curl/7.64.1'}
        hist_response = session.get(historical_url, headers=headers)
        time.sleep(0.25)
        
        if hist_response.status_code != 200:
            print(f"  ✗ Failed to fetch data (status {hist_response.status_code})")
            continue
            
        hist_data = hist_response.json()
        if not hist_data or not isinstance(hist_data, list):
            print(f"  ✗ Invalid data format")
            continue
        
        # Convert to DataFrame for easier analysis
        tvl_history = pd.DataFrame([
            {'date': datetime.fromtimestamp(entry['date']), 'tvl': entry['tvl']}
            for entry in hist_data
        ])
        
        if len(tvl_history) == 0:
            print(f"  ✗ No TVL history found")
            continue
        
        # Get launch date (earliest date with TVL)
        launch_date = tvl_history['date'].min()
        one_year_after_launch = launch_date + timedelta(days=365)
        
        # Filter to first year of data
        first_year_data = tvl_history[tvl_history['date'] <= one_year_after_launch].copy()
        
        # Check if chain reached $100M TVL in first year
        reached_100m = first_year_data[first_year_data['tvl'] >= 100_000_000]
        
        if len(reached_100m) > 0:
            # Get the first date it crossed $100M
            first_100m_date = reached_100m['date'].min()
            days_to_100m = (first_100m_date - launch_date).days
            launch_year = launch_date.year
            
            tvl_analysis_data.append({
                'chain': chain_name,
                'launch_date': launch_date,
                'launch_year': launch_year,
                'date_reached_100m': first_100m_date,
                'days_to_100m': days_to_100m,
                'max_tvl_first_year': first_year_data['tvl'].max(),
                'current_tvl': tvl_history['tvl'].iloc[-1]
            })
            
            print(f"  ✓ TVL: Reached $100M in {days_to_100m} days (launched {launch_date.strftime('%Y-%m-%d')})")
        else:
            max_tvl_first_year = first_year_data['tvl'].max()
            print(f"  ✗ TVL: Did not reach $100M in first year (max: ${max_tvl_first_year:,.0f})")
        
        # Now analyze stablecoin TVL for this chain
        if stablecoins_df is not None:
            chain_stablecoins = stablecoins_df[stablecoins_df['chain'] == chain_name].copy()
            
            if len(chain_stablecoins) > 0:
                # Group by date and sum all stablecoin circulating supply
                stablecoin_daily = chain_stablecoins.groupby('date')['circulating'].sum().reset_index()
                stablecoin_daily = stablecoin_daily.sort_values('date')
                
                # Get stablecoin launch date (earliest date with stablecoin data)
                stable_launch_date = stablecoin_daily['date'].min()
                one_year_after_stable_launch = stable_launch_date + timedelta(days=365)
                
                # Filter to first year of stablecoin data
                first_year_stable = stablecoin_daily[
                    stablecoin_daily['date'] <= one_year_after_stable_launch
                ].copy()
                
                # Check if chain reached $100M stablecoin TVL in first year
                reached_100m_stable = first_year_stable[first_year_stable['circulating'] >= 100_000_000]
                
                if len(reached_100m_stable) > 0:
                    # Get the first date it crossed $100M
                    first_100m_stable_date = reached_100m_stable['date'].min()
                    days_to_100m_stable = (first_100m_stable_date - stable_launch_date).days
                    stable_launch_year = stable_launch_date.year
                    
                    stablecoin_analysis_data.append({
                        'chain': chain_name,
                        'stablecoin_launch_date': stable_launch_date,
                        'launch_year': stable_launch_year,
                        'date_reached_100m_stablecoin': first_100m_stable_date,
                        'days_to_100m_stablecoin': days_to_100m_stable,
                        'max_stablecoin_first_year': first_year_stable['circulating'].max(),
                        'current_stablecoin_tvl': stablecoin_daily['circulating'].iloc[-1]
                    })
                    
                    print(f"  ✓ Stablecoin: Reached $100M in {days_to_100m_stable} days (launched {stable_launch_date.strftime('%Y-%m-%d')})")
                else:
                    max_stable_first_year = first_year_stable['circulating'].max()
                    print(f"  ✗ Stablecoin: Did not reach $100M in first year (max: ${max_stable_first_year:,.0f})")
            else:
                print(f"  ✗ No stablecoin data available for this chain")
        
    except Exception as e:
        print(f"  ✗ Error processing {chain_name}: {str(e)}")
        continue

# Create DataFrames
tvl_analysis_df = pd.DataFrame(tvl_analysis_data)
stablecoin_analysis_df = pd.DataFrame(stablecoin_analysis_data)

# Save detailed data
if len(tvl_analysis_df) > 0:
    tvl_analysis_df.to_csv('chains_reached_100m_tvl.csv', index=False)
    print(f"\n✓ Saved {len(tvl_analysis_df)} chains that reached $100M TVL to chains_reached_100m_tvl.csv")

if len(stablecoin_analysis_df) > 0:
    stablecoin_analysis_df.to_csv('chains_reached_100m_stablecoin.csv', index=False)
    print(f"✓ Saved {len(stablecoin_analysis_df)} chains that reached $100M stablecoin TVL to chains_reached_100m_stablecoin.csv")

# Aggregate by year - TVL
print("\n" + "=" * 80)
print("OVERALL TVL ANALYSIS - Chains Reaching $100M in First Year")
print("=" * 80)

if len(tvl_analysis_df) > 0:
    tvl_yearly = tvl_analysis_df.groupby('launch_year').agg({
        'chain': 'count',  # Count of chains
        'days_to_100m': ['mean', 'median']
    }).round(1)
    
    tvl_yearly.columns = ['count', 'avg_days', 'median_days']
    tvl_yearly = tvl_yearly.sort_index()
    
    print("\nChains by Launch Year:")
    print(tvl_yearly.to_string())
    
    # Save summary
    tvl_yearly.to_csv('tvl_100m_yearly_summary.csv')
    print("\n✓ Saved yearly summary to tvl_100m_yearly_summary.csv")
    
    # Show some examples
    print("\n" + "-" * 80)
    print("Examples of fastest chains to reach $100M TVL:")
    print("-" * 80)
    fastest_chains = tvl_analysis_df.nsmallest(10, 'days_to_100m')[
        ['chain', 'launch_year', 'launch_date', 'days_to_100m', 'max_tvl_first_year']
    ]
    for idx, row in fastest_chains.iterrows():
        print(f"{row['chain']:20s} | {row['launch_year']} | {row['days_to_100m']:3.0f} days | Max 1st year: ${row['max_tvl_first_year']:,.0f}")
else:
    print("\nNo chains found that reached $100M TVL in their first year")

# Aggregate by year - Stablecoin
print("\n" + "=" * 80)
print("STABLECOIN TVL ANALYSIS - Chains Reaching $100M in First Year")
print("=" * 80)

if len(stablecoin_analysis_df) > 0:
    stable_yearly = stablecoin_analysis_df.groupby('launch_year').agg({
        'chain': 'count',  # Count of chains
        'days_to_100m_stablecoin': ['mean', 'median']
    }).round(1)
    
    stable_yearly.columns = ['count', 'avg_days', 'median_days']
    stable_yearly = stable_yearly.sort_index()
    
    print("\nChains by Stablecoin Launch Year:")
    print(stable_yearly.to_string())
    
    # Save summary
    stable_yearly.to_csv('stablecoin_100m_yearly_summary.csv')
    print("\n✓ Saved yearly summary to stablecoin_100m_yearly_summary.csv")
    
    # Show some examples
    print("\n" + "-" * 80)
    print("Examples of fastest chains to reach $100M stablecoin TVL:")
    print("-" * 80)
    fastest_stable_chains = stablecoin_analysis_df.nsmallest(10, 'days_to_100m_stablecoin')[
        ['chain', 'launch_year', 'stablecoin_launch_date', 'days_to_100m_stablecoin', 'max_stablecoin_first_year']
    ]
    for idx, row in fastest_stable_chains.iterrows():
        print(f"{row['chain']:20s} | {row['launch_year']} | {row['days_to_100m_stablecoin']:3.0f} days | Max 1st year: ${row['max_stablecoin_first_year']:,.0f}")
else:
    print("\nNo chains found that reached $100M stablecoin TVL in their first year")

print("\n" + "=" * 80)
print("Analysis Complete!")
print("=" * 80)





