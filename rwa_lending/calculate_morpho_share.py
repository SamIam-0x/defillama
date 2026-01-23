import pandas as pd

print("\n" + "=" * 100)
print("MORPHO MARKET SHARE OF RWA ASSETS ON PLUME")
print("=" * 100)

# Load Morpho market data
df = pd.read_csv('morpho_plume_markets.csv')

# Total TVL for each asset (provided by user)
total_tvl = {
    'nALPHA': 15_000_000,   # $15M
    'nOpal': 2_300_000,     # $2.3M (Note: check if this is nOPAL in the data)
    'nBASIS': 7_200_000,    # $7.2M
    'nTBILL': 1_900_000,    # $1.9M
    'nWISDOM': 3_300_000,   # $3.3M
    'nCREDIT': 273_000,     # $273k
    'nINSTO': 5_100_000     # $5.1M
}

print("\n📊 Calculating Morpho market share for each RWA asset...\n")

# Get supply amounts for each collateral asset from Morpho
# We need to sum up supply_usd for markets where this asset is the collateral
morpho_supply = df.groupby('collateral_asset')['supply_usd'].sum().to_dict()

# Get count of markets for each collateral asset
morpho_market_count = df.groupby('collateral_asset')['market_id'].count().to_dict()

# Also check if any of these are loan assets
morpho_loan = df.groupby('loan_asset')['supply_usd'].sum().to_dict()

print(f"{'Asset':<15} {'Total TVL':>15} {'Supplied on Morpho':>20} {'# Markets':>12} {'% on Morpho':>15}")
print("-" * 110)

results = []

for asset, total in total_tvl.items():
    # Check different possible naming variations
    morpho_amount = 0
    market_count = 0
    
    # Check exact match
    if asset in morpho_supply:
        morpho_amount = morpho_supply[asset]
        market_count = morpho_market_count.get(asset, 0)
    
    # Check without 'n' prefix (e.g., ALPHA instead of nALPHA)
    asset_without_n = asset[1:] if asset.startswith('n') else asset
    if asset_without_n in morpho_supply:
        morpho_amount = morpho_supply[asset_without_n]
        market_count = morpho_market_count.get(asset_without_n, 0)
    
    # Check uppercase variations
    asset_upper = asset.upper()
    if asset_upper in morpho_supply:
        morpho_amount = morpho_supply[asset_upper]
        market_count = morpho_market_count.get(asset_upper, 0)
    
    # Calculate percentage
    percentage = (morpho_amount / total * 100) if total > 0 else 0
    
    results.append({
        'asset': asset,
        'total_tvl': total,
        'morpho_supply': morpho_amount,
        'market_count': market_count,
        'percentage': percentage
    })
    
    print(f"{asset:<15} ${total:>14,.0f} ${morpho_amount:>18,.2f} {market_count:>11} {percentage:>14,.2f}%")

# Summary statistics
total_tvl_sum = sum(r['total_tvl'] for r in results)
total_morpho_sum = sum(r['morpho_supply'] for r in results)
total_markets = sum(r['market_count'] for r in results)
overall_percentage = (total_morpho_sum / total_tvl_sum * 100) if total_tvl_sum > 0 else 0

print("-" * 110)
print(f"{'TOTAL':<15} ${total_tvl_sum:>14,.0f} ${total_morpho_sum:>18,.2f} {total_markets:>11} {overall_percentage:>14,.2f}%")

print("\n" + "=" * 100)
print("DETAILED BREAKDOWN BY ASSET")
print("=" * 100)

# Show detailed breakdown for each asset
for result in results:
    asset = result['asset']
    print(f"\n{asset}")
    print(f"{'─' * 60}")
    print(f"  Total TVL on Plume:           ${result['total_tvl']:,.0f}")
    print(f"  Supplied on Morpho:           ${result['morpho_supply']:,.2f}")
    print(f"  Number of Morpho Markets:     {result['market_count']}")
    print(f"  Not on Morpho:                ${result['total_tvl'] - result['morpho_supply']:,.2f}")
    print(f"  Morpho Market Share:          {result['percentage']:.2f}%")
    print(f"  Other Protocols Share:        {100 - result['percentage']:.2f}%")

print("\n" + "=" * 100)
print("ASSETS FOUND IN MORPHO DATA")
print("=" * 100)

# Show all collateral assets found in Morpho data for reference
print("\nCollateral Assets in Morpho Markets:")
print("-" * 80)
print(f"  {'Asset':<20} {'Total Supply':>15} {'# Markets':>12}")
print("-" * 80)
for asset, amount in sorted(morpho_supply.items(), key=lambda x: x[1], reverse=True):
    if asset and amount > 0:  # Skip empty strings and zero amounts
        count = morpho_market_count.get(asset, 0)
        print(f"  {asset:<20} ${amount:>14,.2f} {count:>11}")

print("\n" + "=" * 100)
print("✅ ANALYSIS COMPLETE")
print("=" * 100)
print(f"\n💡 Key Insights:")
print(f"   • Overall Morpho penetration: {overall_percentage:.2f}% of tracked RWA TVL")
print(f"   • Total RWA TVL tracked: ${total_tvl_sum:,.0f}")
print(f"   • Total on Morpho: ${total_morpho_sum:,.2f}")

# Identify high and low penetration assets
high_penetration = [r for r in results if r['percentage'] > 30]
low_penetration = [r for r in results if r['percentage'] < 10 and r['percentage'] > 0]

if high_penetration:
    print(f"\n   📈 High Morpho adoption (>30%):")
    for r in sorted(high_penetration, key=lambda x: x['percentage'], reverse=True):
        print(f"      • {r['asset']}: {r['percentage']:.2f}%")

if low_penetration:
    print(f"\n   📉 Low Morpho adoption (<10%):")
    for r in sorted(low_penetration, key=lambda x: x['percentage']):
        print(f"      • {r['asset']}: {r['percentage']:.2f}%")

zero_penetration = [r for r in results if r['percentage'] == 0]
if zero_penetration:
    print(f"\n   ⚠️  Not found on Morpho:")
    for r in zero_penetration:
        print(f"      • {r['asset']}")

print()
