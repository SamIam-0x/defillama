import pandas as pd
import numpy as np
import requests
import json
import sqlite3
from datetime import datetime, timedelta
import time
import os
from pathlib import Path

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

def main():
    """Main function to run the analysis"""
    print("Chain Comparison Analysis")
    print("=" * 50)
    
    # Initialize analysis
    analysis = ChainComparisonAnalysis()
    
    # Load existing data
    analysis.load_existing_data()
    
    # Run comparison
    results = analysis.run_comparison_analysis()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()