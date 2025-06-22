from defillama import DefiLlama
import pandas as pd
import json
import subprocess
import requests
from datetime import datetime, timedelta
import time
import urllib3
urllib3.disable_warnings()

# initialize api client with verify=False
llama = DefiLlama()
llama.session.verify = False

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

# get list of stablecoins
response = llama.get_stablecoins(include_prices=True)
time.sleep(1)  # Add sleep after first API call

# saving response to json
with open('stablecoins_list.json', 'w') as f:
    json.dump(response, f)

# Print the response structure
print("Response type:", type(response))
print("Response keys:", response.keys() if isinstance(response, dict) else "Not a dict")
print("Response length:", len(response) if hasattr(response, '__len__') else "No length")

# Create DataFrame from peggedAssets
df = pd.DataFrame(response['peggedAssets'])

# saving to csv
df.to_csv('stablecoins_list.csv', index=False)

# Function to extract peggedUSD value from circulating field
def extract_circulating(value):
    try:
        # Convert string representation of dict to actual dict
        if isinstance(value, str):
            value = eval(value)  # Using eval since the string is a valid Python dict
        return value.get('peggedUSD', 0)
    except:
        return 0

# Extract circulating supply values from existing df
df['circulating_supply'] = df['circulating'].apply(extract_circulating)

# Sort by circulating supply in descending order and get top 100
top_100_stablecoins = df.sort_values('circulating_supply', ascending=False).head(200)

# Save top 100 to a new CSV
top_100_stablecoins.to_csv('top_100_stablecoins.csv', index=False)

print("\nTop 100 stablecoins by circulating supply:")
print(top_100_stablecoins[['name', 'symbol', 'circulating_supply']].to_string())

# List to store all records
all_records = []

# Iterate over top stablecoins
for _, stablecoin in top_100_stablecoins.iterrows():
    stablecoin_id = stablecoin['id']
    print(f"Processing stablecoin: {stablecoin['name']} (ID: {stablecoin_id})")
    
    try:
        # Get historical mcap sum of all stablecoins in a chain
        response = llama.get_stablecoins_historical_mcap_n_chain_distribution(stablecoin_id=stablecoin_id)
        time.sleep(1)  # Add sleep after each stablecoin API call
        
        # Print response structure for debugging
        print(f"Response type for {stablecoin['name']}:", type(response))
        print(f"Response keys for {stablecoin['name']}:", response.keys() if isinstance(response, dict) else "Not a dict")
        
        # Transform the data into records
        for chain, daily_data in response['chainBalances'].items():
            for data_point in daily_data['tokens']:
                try:
                    # Extract circulating amount, defaulting to 0 if not present
                    circulating = data_point.get('circulating', {}).get('peggedUSD', 0)
                    
                    record = {
                        'stablecoin_id': stablecoin_id,
                        'stablecoin_name': response.get('name', 'Unknown'),
                        'stablecoin_symbol': response.get('symbol', 'Unknown'),
                        'date': pd.to_datetime(data_point['date'], unit='s'),
                        'chain': chain,
                        'circulating': circulating
                    }
                    all_records.append(record)
                except Exception as e:
                    print(f"Error processing data point for chain {chain}: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"Error processing stablecoin {stablecoin['name']}: {str(e)}")
        continue

# Create DataFrame from all records
df = pd.DataFrame(all_records)

# Add native_bridged_standard column with blank values
df['native_bridged_standard'] = ''

# Set USDT0 for specific chains
usdt0_chains = [
    'Corn', 
    'Unichain', 
    'Sei', 
    'Berachain', 
    'Ink', 
    'Optimism', 
    'Arbitrum', 
    'Flare', 
    'Hyperliquid L1'
    ]
df.loc[(df['stablecoin_symbol'] == 'USDT') & (df['chain'].isin(usdt0_chains)), 'native_bridged_standard'] = 'USDT0'

# Set USDC as native for specific chains
usdc_native_chains = [
    'Ethereum', 
    'Solana', 
    'Base', 
    'Arbitrum', 
    'Avalanche', 
    'Polygon', 
    'Sui',
    'Noble', 
    'Stellar', 
    'Aptos', 
    'Optimism', 
    'Algorand', 
    'Near', 
    'Hedera',
    'Polkadot', 
    'Tron', 
    'Celo', 
    'Linea', 
    'Unichain', 
    'ZKSync Era', 
    'Sonic', 
    'World Chain', 
    'Ripple'
    ]
df.loc[(df['stablecoin_symbol'] == 'USDC') & (df['chain'].isin(usdc_native_chains)), 'native_bridged_standard'] = 'native'

# Set USDT as native for specific chains
usdt_native_chains = [
    'Bitcoin',  # Omni Protocol Token via Bitcoin Blockchain
    'Ethereum', 
    'Avalanche', 
    'Cosmos', 
    'Celo',  # ERC20 Token via various blockchains
    'Tron',  # TRC20 Token via Tron Blockchain
    'EOS',  # EOSIO.TOKEN via EOS Blockchain
    'Liquid',  # Liquid Asset via Liquid Blockchain
    'Algorand',  # Algorand Asset via Algorand Blockchain
    'Bitcoin Cash',  # SLP Token via Bitcoin Cash Blockchain
    'Solana',  # Solana Token via Solana Blockchain
    'Polkadot',  # Statemint Asset via Polkadot Network
    'Kusama',  # Statemine Asset via Kusama Network
    'Tezos',  # Tezos Token via Tezos Blockchain
    'Ton',  # Ton Jetton via Ton Blockchain
    'Aptos',  # Fungible Asset via Aptos Blockchain
    'Kaia'  # Fungible Asset via Kaia Blockchain
]
df.loc[(df['stablecoin_symbol'] == 'USDT') & (df['chain'].isin(usdt_native_chains)), 'native_bridged_standard'] = 'native'

# Sort by date, stablecoin, and chain
df = df.sort_values(['date', 'stablecoin_id', 'chain'])

# saving to csv
df.to_csv('all_stablecoins_chain_distribution.csv', index=False)

# creating a dataframe of just meta stablecoin in df; dropping date and circulating and grouping by chain and stablecoin symbol
meta_df = df.drop(columns=['date', 'circulating']).groupby(['chain', 'stablecoin_symbol', 'native_bridged_standard', 'stablecoin_id', 'stablecoin_name']).sum().reset_index()

# saving meta df to csv
meta_df.to_csv('meta_stablecoins_chain_distribution.csv', index=False)

# USDC Market Share Analysis
print("\n=== USDC Market Share Analysis ===")

# Filter data for the last 90 days
ninety_days_ago = datetime.now() - timedelta(days=90)
recent_df = df[df['date'] >= ninety_days_ago].copy()

# Get all chains where USDC is present
usdc_chains = recent_df[recent_df['stablecoin_symbol'] == 'USDC']['chain'].unique()
print(f"USDC is present on {len(usdc_chains)} chains")

# Get today's total stablecoin circulating supply for each chain to determine top 10
latest_date = recent_df['date'].max()
today_total_data = recent_df[recent_df['date'] == latest_date].copy()

# Calculate total stablecoin supply per chain today
today_total_stablecoins = today_total_data.groupby('chain')['circulating'].sum().sort_values(ascending=False)

# Get top 10 chains by total stablecoin circulating supply today
top_10_total_chains = today_total_stablecoins.head(10).index.tolist()

print(f"\nTop 10 chains by total stablecoin circulating supply today ({latest_date.strftime('%Y-%m-%d')}):")
for i, chain in enumerate(top_10_total_chains, 1):
    supply = today_total_stablecoins[chain]
    print(f"{i:2d}. {chain}: ${supply:,.2f}")

# Calculate daily market share for top 10 chains only
usdc_market_share_data = []

for chain in top_10_total_chains:
    print(f"\nProcessing USDC market share for chain: {chain}")
    
    # Get data for this specific chain
    chain_data = recent_df[recent_df['chain'] == chain].copy()
    
    # Group by date and calculate total stablecoin supply and USDC supply
    daily_totals = chain_data.groupby('date')['circulating'].sum().reset_index()
    daily_totals.rename(columns={'circulating': 'total_stablecoin_supply'}, inplace=True)
    
    # Get USDC data for this chain
    usdc_data = chain_data[chain_data['stablecoin_symbol'] == 'USDC'].copy()
    
    # Merge USDC data with daily totals
    if not usdc_data.empty:
        usdc_daily = usdc_data.groupby('date')['circulating'].sum().reset_index()
        usdc_daily.rename(columns={'circulating': 'usdc_supply'}, inplace=True)
        
        # Merge with daily totals
        merged_data = pd.merge(daily_totals, usdc_daily, on='date', how='left')
        merged_data['usdc_supply'] = merged_data['usdc_supply'].fillna(0)
        
        # Calculate market share percentage
        merged_data['usdc_market_share_pct'] = (
            merged_data['usdc_supply'] / merged_data['total_stablecoin_supply'] * 100
        )
        
        # Add chain information
        merged_data['chain'] = chain
        
        # Select relevant columns and add to results
        result_data = merged_data[['date', 'chain', 'usdc_supply', 'total_stablecoin_supply', 'usdc_market_share_pct']].copy()
        usdc_market_share_data.append(result_data)
        
        # Print summary statistics
        avg_market_share = merged_data['usdc_market_share_pct'].mean()
        max_market_share = merged_data['usdc_market_share_pct'].max()
        min_market_share = merged_data['usdc_market_share_pct'].min()
        latest_market_share = merged_data['usdc_market_share_pct'].iloc[-1]
        today_total_supply = today_total_stablecoins[chain]
        today_usdc_supply = today_total_data[
            (today_total_data['chain'] == chain) & 
            (today_total_data['stablecoin_symbol'] == 'USDC')
        ]['circulating'].sum()
        
        print(f"  ✓ {chain}: Avg: {avg_market_share:.2f}%, Max: {max_market_share:.2f}%, Min: {min_market_share:.2f}%, Latest: {latest_market_share:.2f}%")
        print(f"     Today's Total Stablecoins: ${today_total_supply:,.2f}")
        print(f"     Today's USDC Supply: ${today_usdc_supply:,.2f}")
    else:
        print(f"  ✗ No USDC data found for {chain}")

# Combine all chain data
if usdc_market_share_data:
    usdc_market_share_df = pd.concat(usdc_market_share_data, ignore_index=True)
    
    # Sort by date and chain
    usdc_market_share_df = usdc_market_share_df.sort_values(['date', 'chain'])
    
    # Save to CSV
    usdc_market_share_df.to_csv('usdc_market_share_90days.csv', index=False)
    
    print(f"\nUSDC market share data saved to usdc_market_share_90days.csv")
    print(f"Total records: {len(usdc_market_share_df)}")
    
    # Print summary statistics across top 10 chains
    print("\n=== USDC Market Share Summary - Top 10 Chains by Total Stablecoins (Last 90 Days) ===")
    summary_stats = usdc_market_share_df.groupby('chain')['usdc_market_share_pct'].agg([
        'mean', 'max', 'min', 'std'
    ]).round(2)
    summary_stats.columns = ['Avg_Market_Share_%', 'Max_Market_Share_%', 'Min_Market_Share_%', 'Std_Dev_%']
    
    # Add today's total stablecoin supply and USDC supply to the summary
    summary_stats['Today_Total_Stablecoins'] = summary_stats.index.map(today_total_stablecoins)
    
    # Calculate today's USDC supply for each chain
    today_usdc_supplies = {}
    for chain in summary_stats.index:
        usdc_supply = today_total_data[
            (today_total_data['chain'] == chain) & 
            (today_total_data['stablecoin_symbol'] == 'USDC')
        ]['circulating'].sum()
        today_usdc_supplies[chain] = usdc_supply
    
    summary_stats['Today_USDC_Supply'] = summary_stats.index.map(today_usdc_supplies)
    summary_stats = summary_stats.sort_values('Today_Total_Stablecoins', ascending=False)
    
    print(summary_stats.to_string())
    
    # Save summary statistics
    summary_stats.to_csv('usdc_market_share_summary.csv')
    print(f"\nSummary statistics saved to usdc_market_share_summary.csv")
    
else:
    print("No USDC market share data available")

# Upload USDC market share data to Google Sheets
try:
    from google_sheets_upload import main as upload_to_sheets
    
    # Define files to upload for USDC market share analysis
    usdc_files_to_upload = [
        ('usdc_market_share_90days.csv', 'USDC Market Share 90 Days'),
        ('usdc_market_share_summary.csv', 'USDC Market Share Summary')
    ]
    
    print("\n=== Uploading USDC Market Share Data to Google Sheets ===")
    upload_to_sheets(usdc_files_to_upload)
    print("✓ USDC market share data successfully uploaded to Google Sheets")
    
except Exception as e:
    print(f"Error uploading USDC market share data to Google Sheets: {e}")
    print("USDC market share data files have been saved locally")

# Get TVL data for all chains
print("\nFetching TVL data for all chains...")
tvl_data = llama.get_all_protocols()
time.sleep(1)  # Add sleep after TVL API call

# Save TVL data to JSON
with open('tvl_data.json', 'w') as f:
    json.dump(tvl_data, f)

# Convert TVL data to DataFrame
tvl_df = pd.DataFrame(tvl_data)

# Save TVL data to CSV
tvl_df.to_csv('tvl_data.csv', index=False)

print("TVL data saved to tvl_data.json and tvl_data.csv")

# Get chain TVL data
print("\nFetching chain TVL data...")
chains_url = "https://api.llama.fi/v2/chains"
response = session.get(chains_url)
time.sleep(1)  # Add sleep after chains API call
chains_data = response.json()

# Sort chains by TVL and get top 200
chains_data.sort(key=lambda x: x['tvl'], reverse=True)
top_chains = chains_data[:500]

print(f"\nProcessing top {len(top_chains)} chains by TVL...")
print(f"First chain example: {top_chains[0]}")  # Debug print first chain data

# Get historical TVL for each chain
chain_tvl_data = []
for i, chain in enumerate(top_chains, 1):
    chain_name = chain['name']
    print(f"\nProcessing chain {i}/{len(top_chains)}: {chain_name}")
    try:
        # Get historical TVL data
        historical_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
        print(f"Fetching data from: {historical_url}")  # Debug print URL
        headers = {'User-Agent': 'curl/7.64.1'}
        hist_response = session.get(historical_url, headers=headers)
        time.sleep(1)  # Add sleep after each historical TVL API call
        print(f"Status code: {hist_response.status_code}")
        print(f"Headers: {hist_response.headers}")
        if hist_response.status_code == 200:
            hist_data = hist_response.json()
            if not hist_data or not isinstance(hist_data, list):
                print(f"✗ Invalid data format for {chain_name}")
                continue
                
            # Convert timestamps to dates and get TVL values
            tvl_history = [(datetime.fromtimestamp(entry['date']), entry['tvl']) 
                         for entry in hist_data]
            
            if not tvl_history:
                print(f"✗ No TVL history found for {chain_name}")
                continue
                
            # Get earliest date with TVL
            earliest_date = min(date for date, _ in tvl_history)
            current_tvl = tvl_history[-1][1]  # Latest TVL
        else:
            print(f"Error fetching data for {chain_name}")
            continue
        
        # Calculate growth rates
        latest_date = tvl_history[-1][0]
        seven_days_ago = latest_date - timedelta(days=7)
        thirty_days_ago = latest_date - timedelta(days=30)
        ninety_days_ago = latest_date - timedelta(days=90)
        
        # Find closest dates for comparison
        def find_closest_date(target_date):
            return min(tvl_history, key=lambda x: abs(x[0] - target_date))
        
        seven_days_ago_tvl = find_closest_date(seven_days_ago)[1]
        thirty_days_ago_tvl = find_closest_date(thirty_days_ago)[1]
        ninety_days_ago_tvl = find_closest_date(ninety_days_ago)[1]
        
        # Calculate growth rates
        growth_7d = (current_tvl - seven_days_ago_tvl) / seven_days_ago_tvl if seven_days_ago_tvl > 0 else None
        growth_30d = (current_tvl - thirty_days_ago_tvl) / thirty_days_ago_tvl if thirty_days_ago_tvl > 0 else None
        growth_90d = (current_tvl - ninety_days_ago_tvl) / ninety_days_ago_tvl if ninety_days_ago_tvl > 0 else None
        
        chain_data = {
            'Chain': chain_name,
            'Current TVL': current_tvl,
            'DeFi Launch Date': earliest_date,
            '7d Growth': growth_7d,
            '30d Growth': growth_30d,
            '90d Growth': growth_90d
        }
        chain_tvl_data.append(chain_data)
        print(f"✓ Successfully processed {chain_name} - TVL: ${current_tvl:,.2f}")
        print(f"  Data collected: {chain_data}")  # Debug print collected data
        
    except Exception as e:
        print(f"✗ Error processing {chain_name}: {str(e)}")
        continue

print(f"\nTotal chains processed successfully: {len(chain_tvl_data)}")

# Create DataFrame from chain TVL data
chain_tvl_df = pd.DataFrame(chain_tvl_data)

# Debug print to verify DataFrame structure
print("\nDataFrame columns:", chain_tvl_df.columns.tolist())
print("Number of rows:", len(chain_tvl_df))
if len(chain_tvl_df) > 0:
    print("\nFirst row of data:")
    print(chain_tvl_df.iloc[0].to_dict())

# Sort by TVL
chain_tvl_df = chain_tvl_df.sort_values('Current TVL', ascending=False)

# Save chain TVL data to CSV
chain_tvl_df.to_csv('chain_tvl_data.csv', index=False)

print("\nChain TVL data saved to chain_tvl_data.csv")

# run stablecoin_analysis.py
subprocess.run(['python', 'src/stablecoin_analysis.py'])