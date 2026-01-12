from defillama import DefiLlama
import pandas as pd
import json
import requests
import time
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings()

def fetch_protocol_tvl_history():
    """Fetch daily TVL history for all filtered protocols over the past year"""
    
    print("=" * 80)
    print("DeFiLlama Protocol TVL History Fetcher")
    print("=" * 80)
    
    # Load filtered protocols
    print("\n📂 Loading filtered protocols...")
    try:
        with open('filtered_protocols_by_category.json', 'r') as f:
            filtered_protocols = json.load(f)
        print(f"✅ Loaded {len(filtered_protocols)} protocols")
        
        # Sort by TVL and take top 250 (handle None values)
        filtered_protocols = sorted(filtered_protocols, key=lambda x: x.get('tvl') or 0, reverse=True)
        filtered_protocols = filtered_protocols[:250]
        print(f"📊 Limiting to top 250 protocols by TVL")
        
    except FileNotFoundError:
        print("❌ Error: filtered_protocols_by_category.json not found!")
        print("Please run fetch_protocols_by_category.py first.")
        return
    
    # Create a requests session with SSL verification disabled
    session = requests.Session()
    session.verify = False
    
    # Calculate date range (past 1 year)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"\n📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 Fetching TVL history for {len(filtered_protocols)} protocols...")
    print("⏱️  This will take approximately {:.1f} minutes...".format(len(filtered_protocols) * 0.5 / 60))
    
    all_tvl_data = []
    successful_protocols = 0
    failed_protocols = 0
    
    for i, protocol in enumerate(filtered_protocols, 1):
        protocol_slug = protocol.get('slug', '')
        protocol_name = protocol.get('name', '')
        protocol_category = protocol.get('category', '')
        
        if not protocol_slug:
            print(f"[{i}/{len(filtered_protocols)}] ⚠️  Skipping {protocol_name} - no slug available")
            failed_protocols += 1
            continue
        
        print(f"\n[{i}/{len(filtered_protocols)}] Processing: {protocol_name} ({protocol_category})")
        
        try:
            # Fetch TVL history from DeFiLlama API
            url = f"https://api.llama.fi/protocol/{protocol_slug}"
            response = session.get(url)
            time.sleep(0.5)  # Rate limiting - increased to avoid rate limits
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract TVL history
                if 'tvl' in data and isinstance(data['tvl'], list):
                    tvl_history = data['tvl']
                    
                    # Filter for past year and convert to records
                    for entry in tvl_history:
                        entry_date = datetime.fromtimestamp(entry['date'])
                        
                        # Only include data from the past year
                        if entry_date >= start_date:
                            record = {
                                'date': entry_date.strftime('%Y-%m-%d'),
                                'timestamp': entry['date'],
                                'protocol_name': protocol_name,
                                'protocol_slug': protocol_slug,
                                'category': protocol_category,
                                'tvl': entry.get('totalLiquidityUSD', 0)
                            }
                            all_tvl_data.append(record)
                    
                    print(f"  ✅ Successfully fetched {len([e for e in tvl_history if datetime.fromtimestamp(e['date']) >= start_date])} daily records")
                    successful_protocols += 1
                else:
                    print(f"  ⚠️  No TVL history found in response")
                    failed_protocols += 1
            else:
                print(f"  ❌ API returned status {response.status_code}")
                failed_protocols += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            failed_protocols += 1
            continue
        
        # Progress update every 50 protocols
        if i % 50 == 0:
            print(f"\n{'=' * 80}")
            print(f"Progress: {i}/{len(filtered_protocols)} protocols processed")
            print(f"Success: {successful_protocols} | Failed: {failed_protocols}")
            print(f"Total records collected: {len(all_tvl_data):,}")
            print(f"{'=' * 80}\n")
    
    print("\n" + "=" * 80)
    print("Data Collection Complete!")
    print("=" * 80)
    print(f"✅ Successful: {successful_protocols} protocols")
    print(f"❌ Failed: {failed_protocols} protocols")
    print(f"📊 Total records: {len(all_tvl_data):,}")
    
    if len(all_tvl_data) == 0:
        print("\n❌ No data collected. Exiting.")
        return
    
    # Convert to DataFrame
    print("\n📊 Creating DataFrame...")
    df = pd.DataFrame(all_tvl_data)
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date and protocol
    df = df.sort_values(['date', 'category', 'protocol_name'])
    
    # Save raw data
    output_file = 'protocol_tvl_history_1year_top250.csv'
    df.to_csv(output_file, index=False)
    print(f"✅ Saved raw data to: {output_file}")
    
    # Create aggregated data by category and date
    print("\n📈 Creating category aggregations...")
    category_daily_tvl = df.groupby(['date', 'category'])['tvl'].sum().reset_index()
    category_daily_tvl = category_daily_tvl.sort_values(['date', 'category'])
    
    category_output_file = 'category_tvl_history_1year_top250.csv'
    category_daily_tvl.to_csv(category_output_file, index=False)
    print(f"✅ Saved category aggregation to: {category_output_file}")
    
    # Create summary statistics
    print("\n" + "=" * 80)
    print("Summary Statistics:")
    print("=" * 80)
    
    # Get latest date stats
    latest_date = df['date'].max()
    latest_data = df[df['date'] == latest_date]
    
    print(f"\nLatest date: {latest_date.strftime('%Y-%m-%d')}")
    print(f"Total protocols with data: {df['protocol_slug'].nunique()}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Total days of data: {df['date'].nunique()}")
    
    # Category summary
    print("\n" + "=" * 80)
    print("TVL by Category (Latest Date):")
    print("=" * 80)
    
    latest_category_tvl = latest_data.groupby('category')['tvl'].sum().sort_values(ascending=False)
    
    for category, tvl in latest_category_tvl.items():
        protocol_count = latest_data[latest_data['category'] == category]['protocol_slug'].nunique()
        print(f"{category:30s}: ${tvl:20,.2f} ({protocol_count:3d} protocols)")
    
    print(f"\n{'Total':30s}: ${latest_category_tvl.sum():20,.2f}")
    
    # Calculate growth rates for each category
    print("\n" + "=" * 80)
    print("Category Growth Rates:")
    print("=" * 80)
    
    # Get earliest date data (1 year ago)
    earliest_date = df['date'].min()
    earliest_data = df[df['date'] == earliest_date]
    earliest_category_tvl = earliest_data.groupby('category')['tvl'].sum()
    
    growth_data = []
    for category in latest_category_tvl.index:
        latest_tvl = latest_category_tvl.get(category, 0)
        earliest_tvl = earliest_category_tvl.get(category, 0)
        
        if earliest_tvl > 0:
            growth_pct = ((latest_tvl - earliest_tvl) / earliest_tvl) * 100
            growth_abs = latest_tvl - earliest_tvl
        else:
            growth_pct = float('inf') if latest_tvl > 0 else 0
            growth_abs = latest_tvl
        
        growth_data.append({
            'category': category,
            'tvl_start': earliest_tvl,
            'tvl_end': latest_tvl,
            'growth_absolute': growth_abs,
            'growth_percentage': growth_pct
        })
    
    growth_df = pd.DataFrame(growth_data)
    growth_df = growth_df.sort_values('growth_absolute', ascending=False)
    
    for _, row in growth_df.iterrows():
        if row['growth_percentage'] == float('inf'):
            growth_str = "NEW"
        else:
            growth_str = f"{row['growth_percentage']:+.1f}%"
        
        print(f"{row['category']:30s}: {growth_str:>10s} (${row['growth_absolute']:+,.0f})")
    
    # Save growth summary
    growth_output_file = 'category_growth_summary_top250.csv'
    growth_df.to_csv(growth_output_file, index=False)
    print(f"\n✅ Saved growth summary to: {growth_output_file}")
    
    # Create a pivot table for easy charting
    print("\n📊 Creating pivot table for charting...")
    pivot_table = category_daily_tvl.pivot(index='date', columns='category', values='tvl')
    pivot_table = pivot_table.fillna(0)
    
    pivot_output_file = 'category_tvl_pivot_1year_top250.csv'
    pivot_table.to_csv(pivot_output_file)
    print(f"✅ Saved pivot table to: {pivot_output_file}")
    
    print("\n" + "=" * 80)
    print("✅ All Processing Complete!")
    print("=" * 80)
    print("\nOutput files created:")
    print(f"  1. {output_file} - Raw daily TVL data per protocol")
    print(f"  2. {category_output_file} - Aggregated daily TVL per category")
    print(f"  3. {pivot_output_file} - Pivot table format (date x category)")
    print(f"  4. {growth_output_file} - Growth summary by category")
    
    print("\n💡 Next steps:")
    print("  • Use the pivot table for creating stacked area charts")
    print("  • Use the category aggregation for line charts")
    print("  • Use the raw data for detailed protocol-level analysis")
    
    return df, category_daily_tvl, pivot_table, growth_df

if __name__ == "__main__":
    df, category_daily_tvl, pivot_table, growth_df = fetch_protocol_tvl_history()

