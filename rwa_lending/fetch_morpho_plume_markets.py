import requests
import pandas as pd
import json
import urllib3
from datetime import datetime

urllib3.disable_warnings()

print("\n" + "=" * 80)
print("Fetching Morpho Markets on Plume Blockchain")
print("=" * 80)

# Morpho GraphQL API endpoint
MORPHO_API_URL = "https://api.morpho.org/graphql"

# Create a session with SSL verification disabled
session = requests.Session()
session.verify = False

# Plume chain ID
PLUME_CHAIN_ID = 98866

# GraphQL query to fetch all markets on Plume
query = """
query GetPlumeMarkets($chainId: Int!) {
  markets(
    where: { chainId_in: [$chainId] }
    first: 1000
  ) {
    items {
      uniqueKey
      lltv
      oracleAddress
      irmAddress
      loanAsset {
        address
        symbol
        name
        decimals
      }
      collateralAsset {
        address
        symbol
        name
        decimals
      }
      state {
        supplyAssets
        supplyAssetsUsd
        borrowAssets
        borrowAssetsUsd
        collateralAssets
        collateralAssetsUsd
        liquidityAssets
        liquidityAssetsUsd
        supplyApy
        borrowApy
        utilization
        fee
        timestamp
      }
      dailyApys {
        netSupplyApy
        netBorrowApy
      }
    }
  }
}
"""

# Prepare the request
headers = {
    "Content-Type": "application/json",
}

payload = {
    "query": query,
    "variables": {
        "chainId": PLUME_CHAIN_ID
    }
}

print(f"\n🔍 Querying Morpho API for Plume markets (Chain ID: {PLUME_CHAIN_ID})...")

try:
    response = session.post(MORPHO_API_URL, json=payload, headers=headers)
    
    # Try to parse response even if status code isn't 200
    try:
        data = response.json()
    except:
        print(f"\n❌ Failed to parse JSON response. Status: {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        exit(1)
    
    # Check HTTP status code
    if response.status_code != 200:
        print(f"\n❌ HTTP Error {response.status_code}: {response.reason}")
        print(f"\nResponse data:")
        print(json.dumps(data, indent=2))
        exit(1)
    
    # Check for errors in the response
    if "errors" in data:
        print("\n❌ GraphQL API returned errors:")
        for error in data["errors"]:
            print(f"  - {error.get('message', 'Unknown error')}")
        
        # Save error response for debugging
        with open('morpho_plume_error.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\n📝 Error details saved to morpho_plume_error.json")
        exit(1)
    
    # Extract markets data
    markets = data.get("data", {}).get("markets", {}).get("items", [])
    
    if not markets:
        print("\n⚠️  No markets found on Plume blockchain.")
        print("    This could mean:")
        print("    1. Morpho markets haven't been deployed on Plume yet")
        print("    2. Plume chain ID is not yet supported in Morpho's API")
        print("    3. Markets exist but have no activity yet")
        
        # Save the full response for inspection
        with open('morpho_plume_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\n📝 Full API response saved to morpho_plume_response.json")
        exit(0)
    
    print(f"\n✅ Found {len(markets)} Morpho markets on Plume!")
    
    # Save raw response
    with open('morpho_plume_raw_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Raw data saved to morpho_plume_raw_response.json")
    
    # Process markets into a DataFrame
    market_data = []
    
    for market in markets:
        loan_asset = market.get("loanAsset") or {}
        collateral_asset = market.get("collateralAsset") or {}
        state = market.get("state") or {}
        daily_apys = market.get("dailyApys") or {}
        
        # Create market pair name
        pair = f"{collateral_asset.get('symbol', 'Unknown')}/{loan_asset.get('symbol', 'Unknown')}"
        
        market_info = {
            'market_id': market.get('uniqueKey', ''),
            'pair': pair,
            'collateral_asset': collateral_asset.get('symbol', ''),
            'collateral_address': collateral_asset.get('address', ''),
            'loan_asset': loan_asset.get('symbol', ''),
            'loan_address': loan_asset.get('address', ''),
            'lltv': market.get('lltv', 0),  # Loan-to-Value ratio
            
            # Supply (Deposits) data
            'supply_assets': state.get('supplyAssets', 0),
            'supply_usd': state.get('supplyAssetsUsd', 0),
            
            # Borrow data
            'borrow_assets': state.get('borrowAssets', 0),
            'borrow_usd': state.get('borrowAssetsUsd', 0),
            
            # Collateral data
            'collateral_assets': state.get('collateralAssets', 0),
            'collateral_usd': state.get('collateralAssetsUsd', 0),
            
            # Liquidity (available to borrow)
            'liquidity_assets': state.get('liquidityAssets', 0),
            'liquidity_usd': state.get('liquidityAssetsUsd', 0),
            
            # APYs
            'supply_apy': state.get('supplyApy', 0),
            'borrow_apy': state.get('borrowApy', 0),
            'net_supply_apy': daily_apys.get('netSupplyApy', 0),
            'net_borrow_apy': daily_apys.get('netBorrowApy', 0),
            
            # Utilization
            'utilization': state.get('utilization', 0),
            'fee': state.get('fee', 0),
            
            # Oracle and IRM addresses
            'oracle_address': market.get('oracleAddress', ''),
            'irm_address': market.get('irmAddress', ''),
            
            # Timestamp
            'last_updated': datetime.fromtimestamp(state.get('timestamp', 0)) if state.get('timestamp') else None
        }
        
        market_data.append(market_info)
    
    # Create DataFrame
    df = pd.DataFrame(market_data)
    
    # Sort by supply USD (largest deposits first)
    df = df.sort_values('supply_usd', ascending=False)
    
    # Save to CSV
    output_file = 'morpho_plume_markets.csv'
    df.to_csv(output_file, index=False)
    print(f"✓ Market data saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Morpho Markets on Plume - Summary")
    print("=" * 80)
    
    total_supply = df['supply_usd'].sum()
    total_borrow = df['borrow_usd'].sum()
    total_collateral = df['collateral_usd'].sum()
    
    print(f"\n📊 Total Market Statistics:")
    print(f"  • Number of Markets: {len(df)}")
    print(f"  • Total Supply (Deposits): ${total_supply:,.2f}")
    print(f"  • Total Borrowed: ${total_borrow:,.2f}")
    print(f"  • Total Collateral: ${total_collateral:,.2f}")
    print(f"  • Overall Utilization: {(total_borrow / total_supply * 100) if total_supply > 0 else 0:.2f}%")
    
    # Print individual markets
    print("\n" + "=" * 80)
    print("Individual Market Details")
    print("=" * 80)
    print(f"\n{'Pair':<25} {'Supply (USD)':>20} {'Borrowed (USD)':>20} {'Utilization':>15}")
    print("-" * 80)
    
    for idx, row in df.iterrows():
        print(f"{row['pair']:<25} ${row['supply_usd']:>18,.2f} ${row['borrow_usd']:>18,.2f} {row['utilization']*100:>13,.2f}%")
    
    # Detailed market information
    print("\n" + "=" * 80)
    print("Detailed Market Information")
    print("=" * 80)
    
    for idx, row in df.iterrows():
        print(f"\n{'='*80}")
        print(f"Market: {row['pair']}")
        print(f"{'='*80}")
        print(f"  Market ID: {row['market_id']}")
        print(f"  ")
        print(f"  Collateral Asset: {row['collateral_asset']} ({row['collateral_address']})")
        print(f"  Loan Asset: {row['loan_asset']} ({row['loan_address']})")
        print(f"  ")
        print(f"  📥 Deposits (Supply):")
        print(f"    • Amount: {row['supply_assets']:,.6f} {row['loan_asset']}")
        print(f"    • USD Value: ${row['supply_usd']:,.2f}")
        print(f"    • Supply APY: {row['supply_apy']*100:.2f}%")
        print(f"    • Net Supply APY: {row['net_supply_apy']*100:.2f}%")
        print(f"  ")
        print(f"  💸 Borrowed:")
        print(f"    • Amount: {row['borrow_assets']:,.6f} {row['loan_asset']}")
        print(f"    • USD Value: ${row['borrow_usd']:,.2f}")
        print(f"    • Borrow APY: {row['borrow_apy']*100:.2f}%")
        print(f"    • Net Borrow APY: {row['net_borrow_apy']*100:.2f}%")
        print(f"  ")
        print(f"  🔒 Collateral:")
        print(f"    • Amount: {row['collateral_assets']:,.6f} {row['collateral_asset']}")
        print(f"    • USD Value: ${row['collateral_usd']:,.2f}")
        print(f"  ")
        print(f"  📊 Market Metrics:")
        print(f"    • Utilization: {row['utilization']*100:.2f}%")
        print(f"    • Available Liquidity: ${row['liquidity_usd']:,.2f}")
        print(f"    • LLTV (Loan-to-Value): {row['lltv']/1e18*100:.2f}%")
        print(f"    • Fee: {row['fee']*100:.4f}%")
        print(f"  ")
        print(f"  🔗 Contract Addresses:")
        print(f"    • Oracle: {row['oracle_address']}")
        print(f"    • IRM (Interest Rate Model): {row['irm_address']}")
        print(f"  ")
        if row['last_updated']:
            print(f"  ⏰ Last Updated: {row['last_updated']}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis Complete!")
    print("=" * 80)
    print(f"\n📁 Output files:")
    print(f"  • {output_file} - Market data in CSV format")
    print(f"  • morpho_plume_raw_response.json - Raw API response")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Error making request to Morpho API: {e}")
    exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
