#!/usr/bin/env python3
"""
September 1, 2024 TVL Analysis
Fetches DeFi TVL and stablecoin TVL data as of September 1, 2024 for all chains,
calculates 30d and 90d growth rates as of that date, and compares with current TVL.
"""

from defillama import DefiLlama
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
import time
import urllib3
import os

urllib3.disable_warnings()

class September2024TVLAnalysis:
    def __init__(self):
        """Initialize the analysis with API clients"""
        # Target date: September 1, 2024
        self.target_date = datetime(2024, 9, 1)
        self.target_timestamp = int(self.target_date.timestamp())
        
        # Initialize API client
        self.llama = DefiLlama()
        self.llama.session.verify = False
        
        # Create requests session
        self.session = requests.Session()
        self.session.verify = False
        
        print(f"🎯 Target analysis date: {self.target_date.strftime('%Y-%m-%d')}")
        print(f"📊 Target timestamp: {self.target_timestamp}")
    
    def fetch_chains_data(self):
        """Fetch all chains data from DeFiLlama"""
        print("\n🔄 Fetching chains data...")
        
        chains_url = "https://api.llama.fi/v2/chains"
        response = self.session.get(chains_url)
        time.sleep(0.5)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch chains data: {response.status_code}")
        
        chains_data = response.json()
        print(f"✅ Found {len(chains_data)} chains")
        
        return chains_data
    
    def get_historical_tvl_for_date(self, chain_name, target_date):
        """Get historical TVL for a specific chain and date"""
        try:
            historical_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
            headers = {'User-Agent': 'curl/7.64.1'}
            response = self.session.get(historical_url, headers=headers)
            time.sleep(0.5)  # Rate limiting
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch historical data for {chain_name}: {response.status_code}")
                return None
            
            hist_data = response.json()
            if not hist_data or not isinstance(hist_data, list):
                print(f"❌ Invalid data format for {chain_name}")
                return None
            
            # Convert to list of (datetime, tvl) tuples
            tvl_history = []
            for entry in hist_data:
                try:
                    date = datetime.fromtimestamp(entry['date'])
                    tvl = entry['tvl']
                    tvl_history.append((date, tvl))
                except (KeyError, ValueError) as e:
                    continue
            
            if not tvl_history:
                print(f"❌ No valid TVL history for {chain_name}")
                return None
            
            # Sort by date
            tvl_history.sort(key=lambda x: x[0])
            
            # Find closest date to target
            target_timestamp = target_date.timestamp()
            closest_entry = min(tvl_history, key=lambda x: abs(x[0].timestamp() - target_timestamp))
            
            return {
                'date': closest_entry[0],
                'tvl': closest_entry[1],
                'full_history': tvl_history
            }
            
        except Exception as e:
            print(f"❌ Error fetching historical TVL for {chain_name}: {str(e)}")
            return None
    
    def calculate_growth_rates(self, tvl_history, target_date):
        """Calculate 30d and 90d growth rates as of the target date"""
        if not tvl_history:
            return None, None
        
        # Find TVL on target date
        target_timestamp = target_date.timestamp()
        target_entry = min(tvl_history, key=lambda x: abs(x[0].timestamp() - target_timestamp))
        target_tvl = target_entry[1]
        
        # Calculate dates for comparison
        thirty_days_before = target_date - timedelta(days=30)
        ninety_days_before = target_date - timedelta(days=90)
        
        # Find closest entries for comparison dates
        thirty_days_entry = min(tvl_history, key=lambda x: abs(x[0].timestamp() - thirty_days_before.timestamp()))
        ninety_days_entry = min(tvl_history, key=lambda x: abs(x[0].timestamp() - ninety_days_before.timestamp()))
        
        # Calculate growth rates
        growth_30d = None
        growth_90d = None
        
        if thirty_days_entry[1] > 0:
            growth_30d = (target_tvl - thirty_days_entry[1]) / thirty_days_entry[1]
        
        if ninety_days_entry[1] > 0:
            growth_90d = (target_tvl - ninety_days_entry[1]) / ninety_days_entry[1]
        
        return growth_30d, growth_90d
    
    def fetch_stablecoin_data_for_date(self, target_date):
        """Fetch stablecoin data for the target date"""
        print(f"\n🪙 Fetching stablecoin data for {target_date.strftime('%Y-%m-%d')}...")
        
        # Get list of stablecoins
        response = self.llama.get_stablecoins(include_prices=True)
        time.sleep(0.5)
        
        if not response or 'peggedAssets' not in response:
            print("❌ Failed to fetch stablecoins list")
            return {}
        
        stablecoins_df = pd.DataFrame(response['peggedAssets'])
        
        # Function to extract circulating supply
        def extract_circulating(value):
            try:
                if isinstance(value, str):
                    value = eval(value)
                return value.get('peggedUSD', 0)
            except:
                return 0
        
        stablecoins_df['circulating_supply'] = stablecoins_df['circulating'].apply(extract_circulating)
        
        # Get top stablecoins by circulating supply
        top_stablecoins = stablecoins_df.sort_values('circulating_supply', ascending=False).head(50)
        
        # Dictionary to store stablecoin TVL by chain
        chain_stablecoin_tvl = {}
        
        print(f"📊 Processing top {len(top_stablecoins)} stablecoins...")
        
        for idx, stablecoin in top_stablecoins.iterrows():
            stablecoin_id = stablecoin['id']
            stablecoin_name = stablecoin['name']
            
            print(f"  Processing: {stablecoin_name} (ID: {stablecoin_id})")
            
            try:
                # Get historical chain distribution
                response = self.llama.get_stablecoins_historical_mcap_n_chain_distribution(stablecoin_id=stablecoin_id)
                time.sleep(0.5)
                
                if not response or 'chainBalances' not in response:
                    print(f"    ❌ No chain balances data for {stablecoin_name}")
                    continue
                
                # Process chain balances
                for chain, daily_data in response['chainBalances'].items():
                    if 'tokens' not in daily_data:
                        continue
                    
                    # Find data closest to target date
                    target_timestamp = target_date.timestamp()
                    closest_data = None
                    min_diff = float('inf')
                    
                    for data_point in daily_data['tokens']:
                        try:
                            point_timestamp = data_point['date']
                            diff = abs(point_timestamp - target_timestamp)
                            if diff < min_diff:
                                min_diff = diff
                                closest_data = data_point
                        except (KeyError, TypeError):
                            continue
                    
                    if closest_data:
                        try:
                            circulating = closest_data.get('circulating', {}).get('peggedUSD', 0)
                            if circulating > 0:
                                if chain not in chain_stablecoin_tvl:
                                    chain_stablecoin_tvl[chain] = 0
                                chain_stablecoin_tvl[chain] += circulating
                        except (TypeError, AttributeError):
                            continue
                            
            except Exception as e:
                print(f"    ❌ Error processing {stablecoin_name}: {str(e)}")
                continue
        
        print(f"✅ Processed stablecoin data for {len(chain_stablecoin_tvl)} chains")
        return chain_stablecoin_tvl
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("🚀 Starting September 1, 2024 TVL Analysis")
        print("=" * 60)
        
        # Fetch chains data
        chains_data = self.fetch_chains_data()
        
        # Process all chains (not just top ones)
        print(f"\n📊 Processing all {len(chains_data)} chains...")
        
        # Fetch stablecoin data for target date
        chain_stablecoin_tvl = self.fetch_stablecoin_data_for_date(self.target_date)
        
        # Process each chain
        results = []
        
        for i, chain_info in enumerate(chains_data, 1):
            chain_name = chain_info['name']
            current_tvl = chain_info.get('tvl', 0)
            
            print(f"\n🔄 Processing chain {i}/{len(chains_data)}: {chain_name}")
            print(f"   Current TVL: ${current_tvl:,.2f}")
            
            # Get historical TVL data
            historical_data = self.get_historical_tvl_for_date(chain_name, self.target_date)
            
            if not historical_data:
                print(f"   ❌ No historical data available for Sept 1, 2024")
                continue
            
            sept_1_tvl = historical_data['tvl']
            tvl_history = historical_data['full_history']
            
            print(f"   Sept 1, 2024 TVL: ${sept_1_tvl:,.2f}")
            
            # Get stablecoin TVL for this chain on Sept 1, 2024
            stablecoin_tvl_sept1 = chain_stablecoin_tvl.get(chain_name, 0)
            
            # Skip chains with no meaningful TVL on Sept 1, 2024
            total_sept1_tvl = sept_1_tvl + stablecoin_tvl_sept1
            if total_sept1_tvl <= 0:
                print(f"   ⏭️  Skipping - no meaningful TVL on Sept 1, 2024")
                continue
            
            # Calculate growth rates as of Sept 1, 2024
            growth_30d, growth_90d = self.calculate_growth_rates(tvl_history, self.target_date)
            
            # Calculate current vs Sept 1 growth
            current_vs_sept1_growth = None
            if sept_1_tvl > 0:
                current_vs_sept1_growth = (current_tvl - sept_1_tvl) / sept_1_tvl
            
            result = {
                'Chain': chain_name,
                'Sept_1_2024_DeFi_TVL': sept_1_tvl,
                'Sept_1_2024_Stablecoin_TVL': stablecoin_tvl_sept1,
                'Sept_1_2024_Total_TVL': total_sept1_tvl,
                'Sept_1_2024_30d_Growth': growth_30d,
                'Sept_1_2024_90d_Growth': growth_90d,
                'Current_DeFi_TVL': current_tvl,
                'Current_vs_Sept1_Growth': current_vs_sept1_growth,
                'Stablecoin_Percentage_Sept1': (stablecoin_tvl_sept1 / total_sept1_tvl * 100) if total_sept1_tvl > 0 else 0
            }
            
            results.append(result)
            
            print(f"   ✅ Processed successfully")
            print(f"      30d Growth (as of Sept 1): {growth_30d*100:.2f}%" if growth_30d else "      30d Growth: N/A")
            print(f"      90d Growth (as of Sept 1): {growth_90d*100:.2f}%" if growth_90d else "      90d Growth: N/A")
            print(f"      Stablecoin TVL (Sept 1): ${stablecoin_tvl_sept1:,.2f}")
            print(f"      Current vs Sept 1 Growth: {current_vs_sept1_growth*100:.2f}%" if current_vs_sept1_growth else "      Current vs Sept 1 Growth: N/A")
        
        # Create DataFrame and save results
        if results:
            df = pd.DataFrame(results)
            
            # Sort by total TVL on Sept 1, 2024
            df = df.sort_values('Sept_1_2024_Total_TVL', ascending=False)
            
            # Format percentage columns
            percentage_cols = ['Sept_1_2024_30d_Growth', 'Sept_1_2024_90d_Growth', 'Current_vs_Sept1_Growth']
            for col in percentage_cols:
                df[col] = df[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
            
            # Format currency columns
            currency_cols = ['Sept_1_2024_DeFi_TVL', 'Sept_1_2024_Stablecoin_TVL', 'Sept_1_2024_Total_TVL', 'Current_DeFi_TVL']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
            
            # Format stablecoin percentage
            df['Stablecoin_Percentage_Sept1'] = df['Stablecoin_Percentage_Sept1'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
            
            # Save to CSV
            output_file = 'september_2024_tvl_analysis_all_chains.csv'
            df.to_csv(output_file, index=False)
            
            print(f"\n✅ Analysis complete!")
            print(f"📁 Results saved to: {output_file}")
            print(f"📊 Total chains analyzed: {len(results)}")
            
            # Print summary statistics
            print(f"\n📈 Summary Statistics:")
            print(f"   Chains with data: {len(results)}")
            print(f"   Average Sept 1 Total TVL: ${df['Sept_1_2024_Total_TVL'].str.replace('$', '').str.replace(',', '').astype(float).mean():,.2f}")
            print(f"   Top chain by Sept 1 Total TVL: {df.iloc[0]['Chain']}")
            
            return df
        else:
            print("❌ No data collected")
            return None

def main():
    """Main function to run the analysis"""
    try:
        analysis = September2024TVLAnalysis()
        results = analysis.run_analysis()
        
        if results is not None:
            print("\n🎉 Analysis completed successfully!")
            print("📊 Check the generated CSV file for detailed results.")
        else:
            print("\n❌ Analysis failed - no results generated")
            
    except Exception as e:
        print(f"\n💥 Analysis failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
