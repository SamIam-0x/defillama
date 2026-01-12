"""
Comprehensive Chain Analysis Script
Fetches comprehensive metrics for blockchain chains from DeFiLlama API:
- Chain token price, FDV, and Market Cap
- Chain DeFi TVL
- Chain stablecoin market cap
- Chain active addresses
- Chain bridged TVL
"""

import requests
import pandas as pd
import time
import urllib3
from datetime import datetime
import json

# Disable SSL warnings
urllib3.disable_warnings()

# Create a requests session with SSL verification disabled
session = requests.Session()
session.verify = False

def get_comprehensive_chain_metrics(num_chains=100):
    """
    Fetch comprehensive metrics for top chains by TVL
    
    Args:
        num_chains: Number of top chains to analyze (default: 100)
    
    Returns:
        DataFrame with comprehensive chain metrics
    """
    
    print("=" * 60)
    print("Comprehensive Chain Metrics Analysis")
    print("=" * 60)
    print(f"Fetching data for top {num_chains} chains by TVL...")
    print()
    
    comprehensive_chain_data = []
    
    # 1. Get all chains data
    print("Step 1: Fetching chain list...")
    chains_url = "https://api.llama.fi/v2/chains"
    chains_response = session.get(chains_url)
    time.sleep(0.25)
    
    if chains_response.status_code != 200:
        print(f"Error fetching chains: {chains_response.status_code}")
        return pd.DataFrame()
    
    all_chains = chains_response.json()
    
    # Sort by TVL and get top N chains
    all_chains.sort(key=lambda x: x.get('tvl', 0), reverse=True)
    top_chains = all_chains[:num_chains]
    
    print(f"✓ Found {len(all_chains)} total chains")
    print(f"✓ Processing top {len(top_chains)} chains\n")
    
    # 2. Load stablecoin data if available
    stablecoin_df = None
    try:
        stablecoin_df = pd.read_csv('all_stablecoins_chain_distribution.csv')
        stablecoin_df['date'] = pd.to_datetime(stablecoin_df['date'])
        print("✓ Loaded existing stablecoin data\n")
    except FileNotFoundError:
        print("⚠ Stablecoin data file not found. Stablecoin market cap will be 0.")
        print("  Run defillama_import.py first to generate stablecoin data.\n")
    
    # 3. Process each chain
    for i, chain in enumerate(top_chains, 1):
        chain_name = chain['name']
        print(f"[{i}/{len(top_chains)}] Processing: {chain_name}")
        
        chain_metrics = {
            'chain': chain_name,
            'defi_tvl': chain.get('tvl', 0),
            'token_symbol': chain.get('tokenSymbol', ''),
            'chain_id': chain.get('chainId', ''),
            'gecko_id': chain.get('gecko_id', ''),
            'cmc_id': chain.get('cmcId', ''),
        }
        
        # Get token price, FDV, and Market Cap
        if chain_metrics['gecko_id']:
            try:
                # First, get price from DeFiLlama
                coins_url = f"https://coins.llama.fi/prices/current/coingecko:{chain_metrics['gecko_id']}"
                coins_response = session.get(coins_url)
                time.sleep(0.25)
                
                if coins_response.status_code == 200:
                    coins_data = coins_response.json()
                    coin_key = f"coingecko:{chain_metrics['gecko_id']}"
                    
                    if 'coins' in coins_data and coin_key in coins_data['coins']:
                        coin_info = coins_data['coins'][coin_key]
                        chain_metrics['token_price'] = coin_info.get('price', 0)
                        print(f"  ✓ Token: {chain_metrics['token_symbol']}")
                        print(f"  ✓ Price: ${chain_metrics['token_price']:,.4f}")
                    else:
                        chain_metrics['token_price'] = 0
                        print(f"  ✗ No price data available")
                else:
                    chain_metrics['token_price'] = 0
                    print(f"  ✗ Price API error: {coins_response.status_code}")
                
                # Set market cap and FDV to 0 (CoinGecko lookups removed)
                chain_metrics['market_cap'] = 0
                chain_metrics['fdv'] = 0
                    
            except Exception as e:
                print(f"  ✗ Error fetching token data: {str(e)}")
                chain_metrics['token_price'] = 0
                chain_metrics['market_cap'] = 0
                chain_metrics['fdv'] = 0
        else:
            chain_metrics['token_price'] = 0
            chain_metrics['market_cap'] = 0
            chain_metrics['fdv'] = 0
            print(f"  ✗ No gecko_id for price lookup")
        
        # Get stablecoin market cap
        if stablecoin_df is not None:
            try:
                latest_date = stablecoin_df['date'].max()
                chain_stablecoins = stablecoin_df[
                    (stablecoin_df['chain'] == chain_name) & 
                    (stablecoin_df['date'] == latest_date)
                ]
                stable_mcap = chain_stablecoins['circulating'].sum()
                chain_metrics['stablecoin_mcap'] = stable_mcap
                print(f"  ✓ Stablecoin Market Cap: ${stable_mcap:,.0f}")
            except Exception as e:
                print(f"  ✗ Error fetching stablecoin data: {str(e)}")
                chain_metrics['stablecoin_mcap'] = 0
        else:
            chain_metrics['stablecoin_mcap'] = 0
        
        # Get bridged TVL
        try:
            bridges_url = f"https://bridges.llama.fi/bridgevolume/{chain_name}?id=0"
            bridges_response = session.get(bridges_url)
            time.sleep(0.25)
            
            if bridges_response.status_code == 200:
                bridges_data = bridges_response.json()
                if isinstance(bridges_data, list) and len(bridges_data) > 0:
                    latest_bridge_data = bridges_data[-1] if bridges_data else {}
                    chain_metrics['bridged_tvl'] = latest_bridge_data.get('depositUSD', 0)
                    print(f"  ✓ Bridged TVL: ${chain_metrics['bridged_tvl']:,.0f}")
                else:
                    chain_metrics['bridged_tvl'] = 0
                    print(f"  ✗ No bridge data available")
            else:
                chain_metrics['bridged_tvl'] = 0
                print(f"  ✗ Bridge API error: {bridges_response.status_code}")
        except Exception as e:
            print(f"  ✗ Error fetching bridge data: {str(e)}")
            chain_metrics['bridged_tvl'] = 0
        
        # Get active addresses (may require Pro API)
        try:
            overview_url = f"https://api.llama.fi/overview/chains/{chain_name}"
            overview_response = session.get(overview_url)
            time.sleep(0.25)
            
            if overview_response.status_code == 200:
                overview_data = overview_response.json()
                chain_metrics['active_addresses'] = overview_data.get('activeAddresses', 0)
                if chain_metrics['active_addresses'] > 0:
                    print(f"  ✓ Active Addresses: {chain_metrics['active_addresses']:,}")
                else:
                    print(f"  ✗ Active addresses not available")
            else:
                chain_metrics['active_addresses'] = 0
                print(f"  ✗ Overview API error: {overview_response.status_code}")
        except Exception as e:
            print(f"  ✗ Error fetching active addresses: {str(e)}")
            chain_metrics['active_addresses'] = 0
        
        # Calculate some additional metrics
        if chain_metrics['defi_tvl'] > 0:
            chain_metrics['stablecoin_to_tvl_ratio'] = (
                chain_metrics['stablecoin_mcap'] / chain_metrics['defi_tvl']
            ) if chain_metrics['stablecoin_mcap'] > 0 else 0
            
            chain_metrics['market_cap_to_tvl_ratio'] = (
                chain_metrics['market_cap'] / chain_metrics['defi_tvl']
            ) if chain_metrics['market_cap'] > 0 else 0
        else:
            chain_metrics['stablecoin_to_tvl_ratio'] = 0
            chain_metrics['market_cap_to_tvl_ratio'] = 0
        
        comprehensive_chain_data.append(chain_metrics)
        print(f"  ✓ DeFi TVL: ${chain_metrics['defi_tvl']:,.0f}\n")
    
    # Create DataFrame
    df = pd.DataFrame(comprehensive_chain_data)
    
    # Sort by DeFi TVL
    df = df.sort_values('defi_tvl', ascending=False)
    
    # Add timestamp
    df['data_timestamp'] = datetime.now()
    
    return df


def main():
    """Main execution function"""
    
    # Get comprehensive metrics
    df = get_comprehensive_chain_metrics(num_chains=100)
    
    if df.empty:
        print("\n❌ Failed to fetch data")
        return
    
    # Save to CSV
    output_file = 'comprehensive_chain_metrics.csv'
    df.to_csv(output_file, index=False)
    
    # Save to JSON for easier programmatic access
    json_file = 'comprehensive_chain_metrics.json'
    df.to_json(json_file, orient='records', indent=2, date_format='iso')
    
    # Print summary
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"Total chains analyzed: {len(df)}")
    print(f"Data saved to: {output_file}")
    print(f"JSON saved to: {json_file}")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)
    
    print(f"\nTotal DeFi TVL: ${df['defi_tvl'].sum():,.0f}")
    print(f"Total Stablecoin Market Cap: ${df['stablecoin_mcap'].sum():,.0f}")
    print(f"Total Market Cap (chains with tokens): ${df['market_cap'].sum():,.0f}")
    print(f"Chains with token data: {(df['token_price'] > 0).sum()}")
    print(f"Chains with stablecoin data: {(df['stablecoin_mcap'] > 0).sum()}")
    print(f"Chains with bridge data: {(df['bridged_tvl'] > 0).sum()}")
    print(f"Chains with active address data: {(df['active_addresses'] > 0).sum()}")
    
    # Print top 10 chains
    print("\n" + "=" * 60)
    print("Top 10 Chains by DeFi TVL")
    print("=" * 60)
    
    top_10 = df.head(10)
    for idx, row in top_10.iterrows():
        print(f"\n{row['chain']}:")
        print(f"  Token: {row['token_symbol']}")
        print(f"  DeFi TVL: ${row['defi_tvl']:,.0f}")
        print(f"  Token Price: ${row['token_price']:,.4f}")
        print(f"  Market Cap: ${row['market_cap']:,.0f}")
        print(f"  FDV: ${row['fdv']:,.0f}")
        print(f"  Stablecoin Market Cap: ${row['stablecoin_mcap']:,.0f}")
        print(f"  Bridged TVL: ${row['bridged_tvl']:,.0f}")
        print(f"  Active Addresses: {row['active_addresses']:,}")
        if row['stablecoin_to_tvl_ratio'] > 0:
            print(f"  Stablecoin/TVL Ratio: {row['stablecoin_to_tvl_ratio']:.2%}")
        if row['market_cap_to_tvl_ratio'] > 0:
            print(f"  Market Cap/TVL Ratio: {row['market_cap_to_tvl_ratio']:.2f}x")
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

