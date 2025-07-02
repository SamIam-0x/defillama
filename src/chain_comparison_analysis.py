import pandas as pd
import numpy as np
import requests
import json
import sqlite3
from datetime import datetime, timedelta
import time
import os
from pathlib import Path
import urllib3
import warnings

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChainComparisonAnalysis:
    def __init__(self, db_path='chain_data.db'):
        """Initialize the analysis with database connection"""
        self.db_path = db_path
        self.session = requests.Session()
        self.session.verify = False
        self.setup_database()
        
    def setup_database(self):
        """Set up SQLite database with tables for historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for historical TVL data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_tvl (
                chain_name TEXT,
                date TEXT,
                tvl REAL,
                PRIMARY KEY (chain_name, date)
            )
        ''')
        
        # Create table for historical stablecoin data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_stablecoins (
                chain_name TEXT,
                stablecoin_symbol TEXT,
                date TEXT,
                circulating REAL,
                PRIMARY KEY (chain_name, stablecoin_symbol, date)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_existing_data(self):
        """Load existing CSV data into the database"""
        print("Loading existing data into database...")
        
        # Load chain TVL data
        if os.path.exists('chain_tvl_data.csv'):
            tvl_df = pd.read_csv('chain_tvl_data.csv')
            conn = sqlite3.connect(self.db_path)
            
            # Store current TVL data (we'll need to fetch historical data separately)
            for _, row in tvl_df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_tvl (chain_name, date, tvl)
                    VALUES (?, ?, ?)
                ''', (row['Chain'], datetime.now().strftime('%Y-%m-%d'), row['Current TVL']))
            
            conn.commit()
            conn.close()
            print(f"Loaded current TVL data for {len(tvl_df)} chains")
        
        # Load stablecoin distribution data
        if os.path.exists('all_stablecoins_chain_distribution.csv'):
            print("Loading stablecoin data (this may take a while for large files)...")
            # Read in chunks to handle large files
            chunk_size = 10000
            conn = sqlite3.connect(self.db_path)
            
            for chunk in pd.read_csv('all_stablecoins_chain_distribution.csv', chunksize=chunk_size):
                for _, row in chunk.iterrows():
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO historical_stablecoins 
                        (chain_name, stablecoin_symbol, date, circulating)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        row['chain'], 
                        row['stablecoin_symbol'], 
                        row['date'], 
                        row['circulating']
                    ))
            
            conn.commit()
            conn.close()
            print("Loaded stablecoin distribution data")
    
    def fetch_historical_tvl(self, chain_name, target_date):
        """Fetch historical TVL data for a specific chain and date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we already have this data
        cursor.execute('''
            SELECT tvl FROM historical_tvl 
            WHERE chain_name = ? AND date = ?
        ''', (chain_name, target_date.strftime('%Y-%m-%d')))
        
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        
        # Fetch from API if not in database
        print(f"Fetching historical TVL for {chain_name} on {target_date.strftime('%Y-%m-%d')}")
        
        try:
            historical_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
            headers = {'User-Agent': 'curl/7.64.1'}
            response = self.session.get(historical_url, headers=headers)
            time.sleep(1)  # Rate limiting
            
            if response.status_code == 200:
                hist_data = response.json()
                
                # Validate that hist_data is a list and contains the expected structure
                if not isinstance(hist_data, list) or len(hist_data) == 0:
                    print(f"No historical data available for {chain_name}")
                    conn.close()
                    return None
                
                # Validate the first entry has the expected structure
                if not isinstance(hist_data[0], dict) or 'date' not in hist_data[0] or 'tvl' not in hist_data[0]:
                    print(f"Unexpected data format for {chain_name}")
                    conn.close()
                    return None
                
                # Find the closest date to our target
                target_timestamp = int(target_date.timestamp())
                closest_entry = min(hist_data, key=lambda x: abs(x['date'] - target_timestamp))
                
                # Store in database
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_tvl (chain_name, date, tvl)
                    VALUES (?, ?, ?)
                ''', (chain_name, target_date.strftime('%Y-%m-%d'), closest_entry['tvl']))
                
                conn.commit()
                conn.close()
                return closest_entry['tvl']
            else:
                print(f"Error fetching TVL for {chain_name}: {response.status_code}")
                conn.close()
                return None
                
        except Exception as e:
            print(f"Error processing {chain_name}: {str(e)}")
            conn.close()
            return None
    
    def get_stablecoin_data(self, chain_name, stablecoin_symbol, target_date):
        """Get stablecoin circulating supply for a specific chain, symbol, and date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have this data
        cursor.execute('''
            SELECT circulating FROM historical_stablecoins 
            WHERE chain_name = ? AND stablecoin_symbol = ? AND date = ?
        ''', (chain_name, stablecoin_symbol, target_date.strftime('%Y-%m-%d')))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Try to find the closest date
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, circulating FROM historical_stablecoins 
                WHERE chain_name = ? AND stablecoin_symbol = ?
                ORDER BY ABS(JULIANDAY(date) - JULIANDAY(?))
                LIMIT 1
            ''', (chain_name, stablecoin_symbol, target_date.strftime('%Y-%m-%d')))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[1]
            else:
                return 0
    
    def get_total_stablecoin_circulation(self, chain_name, target_date):
        """Get total stablecoin circulation for a chain on a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(circulating) FROM historical_stablecoins 
            WHERE chain_name = ? AND date = ?
        ''', (chain_name, target_date.strftime('%Y-%m-%d')))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        else:
            # Try to find the closest date
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, SUM(circulating) as total FROM historical_stablecoins 
                WHERE chain_name = ?
                GROUP BY date
                ORDER BY ABS(JULIANDAY(date) - JULIANDAY(?))
                LIMIT 1
            ''', (chain_name, target_date.strftime('%Y-%m-%d')))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1]:
                return result[1]
            else:
                return 0
    
    def fetch_current_stablecoin_data(self, chain_name, stablecoin_symbol='USDC'):
        """Fetch current stablecoin data from DeFiLlama API"""
        try:
            # DeFiLlama stablecoin API endpoint
            url = f"https://api.llama.fi/stablecoins"
            headers = {'User-Agent': 'curl/7.64.1'}
            response = self.session.get(url, headers=headers)
            time.sleep(0.5)  # Rate limiting
            
            if response.status_code == 200:
                stablecoins_data = response.json()
                
                # Find the specific stablecoin and chain
                for stablecoin in stablecoins_data:
                    if stablecoin.get('symbol', '').upper() == stablecoin_symbol.upper():
                        # Look for the specific chain in the stablecoin's chains
                        for chain_data in stablecoin.get('chains', []):
                            if chain_data.get('name', '').lower() == chain_name.lower():
                                return chain_data.get('circulating', 0)
                
                print(f"No {stablecoin_symbol} data found for {chain_name}")
                return 0
            else:
                print(f"Error fetching stablecoin data for {chain_name}: {response.status_code}")
                return 0
                
        except Exception as e:
            print(f"Error fetching stablecoin data for {chain_name}: {str(e)}")
            return 0
    
    def fetch_current_total_stablecoin_circulation(self, chain_name):
        """Fetch current total stablecoin circulation for a chain from DeFiLlama API"""
        try:
            # DeFiLlama stablecoin API endpoint
            url = f"https://api.llama.fi/stablecoins"
            headers = {'User-Agent': 'curl/7.64.1'}
            response = self.session.get(url, headers=headers)
            time.sleep(0.5)  # Rate limiting
            
            if response.status_code == 200:
                stablecoins_data = response.json()
                total_circulation = 0
                
                # Sum up all stablecoins for the specific chain
                for stablecoin in stablecoins_data:
                    for chain_data in stablecoin.get('chains', []):
                        if chain_data.get('name', '').lower() == chain_name.lower():
                            total_circulation += chain_data.get('circulating', 0)
                
                return total_circulation
            else:
                print(f"Error fetching total stablecoin data for {chain_name}: {response.status_code}")
                return 0
                
        except Exception as e:
            print(f"Error fetching total stablecoin data for {chain_name}: {str(e)}")
            return 0
    
    def run_comparison_analysis(self):
        """Run the main comparison analysis"""
        # Define the chains and their target dates
        chains_to_analyze = {
            'Aptos': datetime(2024, 7, 23),
            'Sui': datetime(2024, 10, 6),
            'Sonic': datetime(2025, 3, 4)
        }
        
        today = datetime.now()
        results = []
        
        print("Starting chain comparison analysis...")
        print(f"Comparing data from target dates to today ({today.strftime('%Y-%m-%d')})")
        
        for chain_name, target_date in chains_to_analyze.items():
            print(f"\nAnalyzing {chain_name}...")
            
            # Get historical data
            historical_tvl = self.fetch_historical_tvl(chain_name, target_date)
            historical_usdc = self.get_stablecoin_data(chain_name, 'USDC', target_date)
            historical_total_stable = self.get_total_stablecoin_circulation(chain_name, target_date)
            
            # Get current data
            current_tvl = self.fetch_historical_tvl(chain_name, today)
            current_usdc = self.get_stablecoin_data(chain_name, 'USDC', today)
            current_total_stable = self.get_total_stablecoin_circulation(chain_name, today)
            
            # Calculate percentage changes
            tvl_change = ((current_tvl - historical_tvl) / historical_tvl * 100) if historical_tvl and historical_tvl > 0 else None
            usdc_change = ((current_usdc - historical_usdc) / historical_usdc * 100) if historical_usdc and historical_usdc > 0 else None
            total_stable_change = ((current_total_stable - historical_total_stable) / historical_total_stable * 100) if historical_total_stable and historical_total_stable > 0 else None
            
            result = {
                'Chain': chain_name,
                'Target_Date': target_date.strftime('%Y-%m-%d'),
                'Historical_TVL': historical_tvl,
                'Current_TVL': current_tvl,
                'TVL_Change_Percent': tvl_change,
                'Historical_USDC': historical_usdc,
                'Current_USDC': current_usdc,
                'USDC_Change_Percent': usdc_change,
                'Historical_Total_Stable': historical_total_stable,
                'Current_Total_Stable': current_total_stable,
                'Total_Stable_Change_Percent': total_stable_change
            }
            
            results.append(result)
            
            print(f"  Target Date: {target_date.strftime('%Y-%m-%d')}")
            print(f"  TVL: ${historical_tvl:,.2f} → ${current_tvl:,.2f} ({tvl_change:+.2f}%)" if tvl_change is not None else f"  TVL: ${historical_tvl:,.2f} → ${current_tvl:,.2f} (N/A)")
            print(f"  USDC: ${historical_usdc:,.2f} → ${current_usdc:,.2f} ({usdc_change:+.2f}%)" if usdc_change is not None else f"  USDC: ${historical_usdc:,.2f} → ${current_usdc:,.2f} (N/A)")
            print(f"  Total Stable: ${historical_total_stable:,.2f} → ${current_total_stable:,.2f} ({total_stable_change:+.2f}%)" if total_stable_change is not None else f"  Total Stable: ${historical_total_stable:,.2f} → ${current_total_stable:,.2f} (N/A)")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        results_df.to_csv('chain_comparison_results.csv', index=False)
        
        # Create summary
        print("\n" + "="*80)
        print("SUMMARY OF CHAIN COMPARISON ANALYSIS")
        print("="*80)
        
        for _, row in results_df.iterrows():
            print(f"\n{row['Chain']} (Target Date: {row['Target_Date']})")
            print("-" * 50)
            
            if row['TVL_Change_Percent'] is not None:
                print(f"TVL Growth: {row['TVL_Change_Percent']:+.2f}%")
            else:
                print("TVL Growth: N/A")
                
            if row['USDC_Change_Percent'] is not None:
                print(f"USDC Growth: {row['USDC_Change_Percent']:+.2f}%")
            else:
                print("USDC Growth: N/A")
                
            if row['Total_Stable_Change_Percent'] is not None:
                print(f"Total Stablecoin Growth: {row['Total_Stable_Change_Percent']:+.2f}%")
            else:
                print("Total Stablecoin Growth: N/A")
        
        print(f"\nResults saved to: chain_comparison_results.csv")
        print(f"Database saved to: {self.db_path}")
        
        return results_df

    def run_launch_vs_current_analysis(self):
        """Run analysis comparing launch metrics of launched chains vs current metrics of to-be-launched chains"""
        # Define the launched chains and their launch dates
        launched_chains = {
            'Aptos': datetime(2024, 7, 23),
            'Sui': datetime(2024, 10, 6),
            'Sonic': datetime(2025, 3, 4),
            'Linea': datetime(2025, 3, 25),
            'World Chain': datetime(2025, 6, 11),
            'Ripple': datetime(2025, 6, 12)
        }
        
        # Define the to-be-launched chains
        to_be_launched_chains = [
            'XDC', 'Ink', 'Plume Mainnet', 'Core', 'Soneium', 'Mantle', 
            'MegaETH', 'Abstract', 'Gravity', 'Etherlink', 'Gnosis'
        ]
        
        # Chain name mappings for API compatibility (some chains might have different names in DeFiLlama)
        chain_name_mappings = {
            'XDC': 'xdc',
            'Ink': 'ink',
            'Plume Mainnet': 'plume mainnet',
            'Core': 'core',
            'Soneium': 'soneium',
            'Mantle': 'mantle',
            'MegaETH': 'megaeth',
            'Abstract': 'abstract',
            'Gravity': 'gravity',
            'Etherlink': 'etherlink',
            'Gnosis': 'gnosis'
        }
        
        today = datetime.now()
        results = []
        
        print("Starting Launch vs Current Analysis...")
        print("=" * 80)
        print("Comparing launch metrics of launched chains with current metrics of to-be-launched chains")
        print(f"Analysis date: {today.strftime('%Y-%m-%d')}")
        print("=" * 80)
        
        # First, get launch metrics for launched chains
        print("\n1. COLLECTING LAUNCH METRICS FOR LAUNCHED CHAINS")
        print("-" * 60)
        launch_metrics = {}
        
        for chain_name, launch_date in launched_chains.items():
            print(f"\nAnalyzing {chain_name} (Launch: {launch_date.strftime('%Y-%m-%d')})...")
            
            # Get launch date metrics
            launch_tvl = self.fetch_historical_tvl(chain_name, launch_date)
            launch_usdc = self.get_stablecoin_data(chain_name, 'USDC', launch_date)
            launch_total_stable = self.get_total_stablecoin_circulation(chain_name, launch_date)
            
            launch_metrics[chain_name] = {
                'launch_date': launch_date,
                'launch_tvl': launch_tvl,
                'launch_usdc': launch_usdc,
                'launch_total_stable': launch_total_stable
            }
            
            print(f"  Launch TVL: ${launch_tvl:,.2f}" if launch_tvl else "  Launch TVL: N/A")
            print(f"  Launch USDC: ${launch_usdc:,.2f}" if launch_usdc else "  Launch USDC: N/A")
            print(f"  Launch Total Stable: ${launch_total_stable:,.2f}" if launch_total_stable else "  Launch Total Stable: N/A")
        
        # Calculate average launch metrics
        valid_launch_tvls = [m['launch_tvl'] for m in launch_metrics.values() if m['launch_tvl'] and m['launch_tvl'] > 0]
        valid_launch_stables = [m['launch_total_stable'] for m in launch_metrics.values() if m['launch_total_stable'] and m['launch_total_stable'] > 0]
        
        avg_launch_tvl = np.mean(valid_launch_tvls) if valid_launch_tvls else 0
        avg_launch_stable = np.mean(valid_launch_stables) if valid_launch_stables else 0
        
        print(f"\nAverage Launch Metrics:")
        print(f"  Average Launch TVL: ${avg_launch_tvl:,.2f}")
        print(f"  Average Launch Total Stable: ${avg_launch_stable:,.2f}")
        
        # Now get current metrics for to-be-launched chains
        print("\n\n2. COLLECTING CURRENT METRICS FOR TO-BE-LAUNCHED CHAINS")
        print("-" * 60)
        
        for chain_name in to_be_launched_chains:
            print(f"\nAnalyzing {chain_name} (Current metrics)...")
            
            # Use mapped chain name for API calls
            api_chain_name = chain_name_mappings.get(chain_name, chain_name)
            
            # Get current metrics
            current_tvl = self.fetch_historical_tvl(api_chain_name, today)
            current_usdc = self.fetch_current_stablecoin_data(api_chain_name, 'USDC')
            current_total_stable = self.fetch_current_total_stablecoin_circulation(api_chain_name)
            
            # Compare with average launch metrics
            tvl_vs_avg_launch = ((current_tvl - avg_launch_tvl) / avg_launch_tvl * 100) if (current_tvl is not None and avg_launch_tvl and avg_launch_tvl > 0) else None
            stable_vs_avg_launch = ((current_total_stable - avg_launch_stable) / avg_launch_stable * 100) if (current_total_stable is not None and avg_launch_stable and avg_launch_stable > 0) else None
            
            result = {
                'Chain': chain_name,
                'Status': 'To-Be-Launched',
                'Current_TVL': current_tvl,
                'Current_USDC': current_usdc,
                'Current_Total_Stable': current_total_stable,
                'Avg_Launch_TVL': avg_launch_tvl,
                'TVL_vs_Avg_Launch_Percent': tvl_vs_avg_launch,
                'Avg_Launch_Total_Stable': avg_launch_stable,
                'Total_Stable_vs_Avg_Launch_Percent': stable_vs_avg_launch
            }
            
            results.append(result)
            
            print(f"  Current TVL: ${current_tvl:,.2f}" if current_tvl is not None else "  Current TVL: N/A")
            print(f"  Current USDC: ${current_usdc:,.2f}" if current_usdc is not None else "  Current USDC: N/A")
            print(f"  Current Total Stable: ${current_total_stable:,.2f}" if current_total_stable is not None else "  Current Total Stable: N/A")
            
            if tvl_vs_avg_launch is not None:
                print(f"  TVL vs Avg Launch: {tvl_vs_avg_launch:+.2f}%")
            else:
                print("  TVL vs Avg Launch: N/A (no data available)")
                
            if stable_vs_avg_launch is not None:
                print(f"  Total Stable vs Avg Launch: {stable_vs_avg_launch:+.2f}%")
            else:
                print("  Total Stable vs Avg Launch: N/A (no data available)")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        results_df.to_csv('launch_vs_current_comparison.csv', index=False)
        
        # Create summary
        print("\n" + "="*80)
        print("SUMMARY OF LAUNCH VS CURRENT ANALYSIS")
        print("="*80)
        
        print(f"\nLAUNCHED CHAINS DETAILED ANALYSIS ({len(launched_chains)}):")
        print("=" * 60)
        
        # Get current metrics for launched chains for comparison
        for chain_name, launch_date in launched_chains.items():
            metrics = launch_metrics[chain_name]
            current_tvl = self.fetch_historical_tvl(chain_name, today)
            current_total_stable = self.get_total_stablecoin_circulation(chain_name, today)
            
            print(f"\n{chain_name}")
            print("-" * 40)
            print(f"Launch Date: {launch_date.strftime('%Y-%m-%d')}")
            print(f"Launch TVL: ${metrics['launch_tvl']:,.2f}" if metrics['launch_tvl'] else "Launch TVL: N/A")
            print(f"Launch USDC: ${metrics['launch_usdc']:,.2f}" if metrics['launch_usdc'] else "Launch USDC: N/A")
            print(f"Launch Total Stable: ${metrics['launch_total_stable']:,.2f}" if metrics['launch_total_stable'] else "Launch Total Stable: N/A")
            
            print(f"Current TVL: ${current_tvl:,.2f}" if current_tvl is not None else "Current TVL: N/A")
            print(f"Current Total Stable: ${current_total_stable:,.2f}" if current_total_stable is not None else "Current Total Stable: N/A")
            
            # Calculate growth since launch
            if metrics['launch_tvl'] and current_tvl and metrics['launch_tvl'] > 0:
                tvl_growth = ((current_tvl - metrics['launch_tvl']) / metrics['launch_tvl']) * 100
                print(f"TVL Growth Since Launch: {tvl_growth:+.2f}%")
            else:
                print("TVL Growth Since Launch: N/A")
                
            if metrics['launch_total_stable'] and current_total_stable and metrics['launch_total_stable'] > 0:
                stable_growth = ((current_total_stable - metrics['launch_total_stable']) / metrics['launch_total_stable']) * 100
                print(f"Total Stable Growth Since Launch: {stable_growth:+.2f}%")
            else:
                print("Total Stable Growth Since Launch: N/A")
        
        print(f"\nAVERAGE LAUNCH METRICS:")
        print("-" * 30)
        print(f"Average Launch TVL: ${avg_launch_tvl:,.2f}")
        print(f"Average Launch Total Stable: ${avg_launch_stable:,.2f}")
        
        print(f"\nTO-BE-LAUNCHED CHAINS ANALYSIS ({len(to_be_launched_chains)}):")
        print("=" * 60)
        for _, row in results_df.iterrows():
            print(f"\n{row['Chain']}")
            print("-" * 30)
            print(f"Current TVL: ${row['Current_TVL']:,.2f}" if row['Current_TVL'] is not None else "Current TVL: N/A")
            print(f"Current Total Stable: ${row['Current_Total_Stable']:,.2f}" if row['Current_Total_Stable'] is not None else "Current Total Stable: N/A")
            
            if row['TVL_vs_Avg_Launch_Percent'] is not None:
                print(f"TVL vs Avg Launch: {row['TVL_vs_Avg_Launch_Percent']:+.2f}%")
            else:
                print("TVL vs Avg Launch: N/A (no data available)")
                
            if row['Total_Stable_vs_Avg_Launch_Percent'] is not None:
                print(f"Total Stable vs Avg Launch: {row['Total_Stable_vs_Avg_Launch_Percent']:+.2f}%")
            else:
                print("Total Stable vs Avg Launch: N/A (no data available)")
        
        print(f"\nResults saved to: launch_vs_current_comparison.csv")
        print(f"Database saved to: {self.db_path}")
        
        return results_df

    def run_both_analyses(self):
        """Run both the original comparison analysis and the launch vs current analysis"""
        print("Running both analyses sequentially...")
        print("=" * 80)
        
        # Run original analysis
        print("\n1. RUNNING ORIGINAL COMPARISON ANALYSIS")
        print("=" * 50)
        original_results = self.run_comparison_analysis()
        
        print("\n" + "="*80)
        print("2. RUNNING LAUNCH VS CURRENT ANALYSIS")
        print("=" * 50)
        launch_vs_current_results = self.run_launch_vs_current_analysis()
        
        print("\n" + "="*80)
        print("BOTH ANALYSES COMPLETE")
        print("=" * 80)
        print("Files generated:")
        print("- chain_comparison_results.csv")
        print("- launch_vs_current_comparison.csv")
        print(f"- {self.db_path}")
        
        return original_results, launch_vs_current_results

def main():
    """Main function to run the analysis"""
    print("Chain Comparison Analysis")
    print("=" * 50)
    
    # Initialize analysis
    analysis = ChainComparisonAnalysis()
    
    # Load existing data
    analysis.load_existing_data()
    
    # Ask user which analysis to run
    print("\nChoose analysis to run:")
    print("1. Original comparison analysis (launched chains: launch date vs today)")
    print("2. Launch vs Current analysis (launched chains launch metrics vs to-be-launched chains current metrics)")
    print("3. Run both analyses sequentially")
    
    while True:
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3")
    
    if choice == '1':
        print("\nRunning original comparison analysis...")
        results = analysis.run_comparison_analysis()
    elif choice == '2':
        print("\nRunning launch vs current analysis...")
        results = analysis.run_launch_vs_current_analysis()
    else:
        print("\nRunning both analyses sequentially...")
        results = analysis.run_both_analyses()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()