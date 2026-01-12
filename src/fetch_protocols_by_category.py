from defillama import DefiLlama
import pandas as pd
import json
import requests
import time
import urllib3

urllib3.disable_warnings()

# Target categories to filter
TARGET_CATEGORIES = [
    "Lending",
    "Liquid Staking",
    "Bridge",
    "Restaking",
    "Canonical Bridge",
    "RWA",
    "Basis Trading",
    "Liquid Restaking",
    "Yield",
    "Onchain Capital Allocator",
    "CDP",
    "Risk Curators",
    "Yield Aggregator",
    "Farm",
    "Restaked BTC",
    "Staking Pool",
    "Anchor BTC",
    "RWA Lending"
]

def fetch_protocols_by_categories():
    """Fetch all protocols from DeFiLlama API filtered by specified categories"""
    
    print("=" * 80)
    print("DeFiLlama Protocol Fetcher by Category")
    print("=" * 80)
    print(f"\nTarget Categories ({len(TARGET_CATEGORIES)}):")
    for i, category in enumerate(TARGET_CATEGORIES, 1):
        print(f"  {i:2d}. {category}")
    print("=" * 80)
    
    # Initialize API client
    llama = DefiLlama()
    llama.session.verify = False
    
    # Create a requests session with SSL verification disabled
    session = requests.Session()
    session.verify = False
    
    print("\n🔄 Fetching all protocols from DeFiLlama API...")
    
    try:
        # Fetch all protocols
        all_protocols = llama.get_all_protocols()
        time.sleep(0.25)
        
        print(f"✅ Successfully fetched {len(all_protocols)} protocols")
        
        # Save all protocols to JSON for reference
        with open('all_protocols.json', 'w') as f:
            json.dump(all_protocols, f, indent=2)
        print(f"📁 Saved all protocols to: all_protocols.json")
        
        # Filter protocols by target categories
        filtered_protocols = []
        category_counts = {}
        
        for protocol in all_protocols:
            # Check if protocol has a category field
            protocol_category = protocol.get('category', '')
            
            if protocol_category in TARGET_CATEGORIES:
                filtered_protocols.append(protocol)
                
                # Count protocols per category
                if protocol_category not in category_counts:
                    category_counts[protocol_category] = 0
                category_counts[protocol_category] += 1
        
        print(f"\n✅ Filtered to {len(filtered_protocols)} protocols matching target categories")
        
        # Display count by category
        print("\n" + "=" * 80)
        print("Protocol Count by Category:")
        print("=" * 80)
        for category in sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True):
            count = category_counts[category]
            print(f"  {category:30s}: {count:4d} protocols")
        
        # Check which target categories had no protocols
        missing_categories = set(TARGET_CATEGORIES) - set(category_counts.keys())
        if missing_categories:
            print("\n⚠️  Categories with no protocols found:")
            for category in sorted(missing_categories):
                print(f"  - {category}")
        
        # Save filtered protocols to JSON
        with open('filtered_protocols_by_category.json', 'w') as f:
            json.dump(filtered_protocols, f, indent=2)
        print(f"\n📁 Saved filtered protocols to: filtered_protocols_by_category.json")
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(filtered_protocols)
        
        # Save to CSV
        df.to_csv('filtered_protocols_by_category.csv', index=False)
        print(f"📁 Saved filtered protocols to: filtered_protocols_by_category.csv")
        
        # Display summary statistics
        print("\n" + "=" * 80)
        print("Summary Statistics:")
        print("=" * 80)
        
        # Sort by TVL
        df_sorted = df.sort_values('tvl', ascending=False)
        
        print(f"\nTotal protocols: {len(df)}")
        print(f"Total TVL: ${df['tvl'].sum():,.2f}")
        print(f"Average TVL: ${df['tvl'].mean():,.2f}")
        print(f"Median TVL: ${df['tvl'].median():,.2f}")
        
        # Top 10 protocols by TVL
        print("\n" + "=" * 80)
        print("Top 10 Protocols by TVL:")
        print("=" * 80)
        
        for i, row in df_sorted.head(10).iterrows():
            print(f"{row.name + 1:2d}. {row['name']:30s} | Category: {row['category']:25s} | TVL: ${row['tvl']:,.2f}")
        
        # Create a summary by category
        category_summary = df.groupby('category').agg({
            'tvl': ['sum', 'mean', 'count']
        }).round(2)
        
        category_summary.columns = ['Total_TVL', 'Avg_TVL', 'Protocol_Count']
        category_summary = category_summary.sort_values('Total_TVL', ascending=False)
        
        # Save category summary
        category_summary.to_csv('category_summary.csv')
        print(f"\n📁 Saved category summary to: category_summary.csv")
        
        print("\n" + "=" * 80)
        print("Category Summary (by Total TVL):")
        print("=" * 80)
        print(category_summary.to_string())
        
        # Check all unique categories in the dataset
        print("\n" + "=" * 80)
        print("All Available Categories in DeFiLlama:")
        print("=" * 80)
        all_categories = set()
        for protocol in all_protocols:
            if 'category' in protocol and protocol['category']:
                all_categories.add(protocol['category'])
        
        for category in sorted(all_categories):
            matched = "✓" if category in TARGET_CATEGORIES else " "
            print(f"  [{matched}] {category}")
        
        print(f"\n📊 Total unique categories: {len(all_categories)}")
        print(f"📊 Matched categories: {len(category_counts)}/{len(TARGET_CATEGORIES)}")
        
        print("\n" + "=" * 80)
        print("✅ Processing Complete!")
        print("=" * 80)
        print("\nOutput files created:")
        print("  1. all_protocols.json - All protocols from DeFiLlama")
        print("  2. filtered_protocols_by_category.json - Filtered protocols")
        print("  3. filtered_protocols_by_category.csv - Filtered protocols (CSV)")
        print("  4. category_summary.csv - Summary statistics by category")
        
        return filtered_protocols, df, category_summary
        
    except Exception as e:
        print(f"❌ Error fetching protocols: {str(e)}")
        raise

if __name__ == "__main__":
    filtered_protocols, df, category_summary = fetch_protocols_by_categories()

