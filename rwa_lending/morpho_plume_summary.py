import pandas as pd

print("\n" + "=" * 100)
print("MORPHO MARKETS ON PLUME BLOCKCHAIN - SUMMARY")
print("=" * 100)

# Load the data
df = pd.read_csv('morpho_plume_markets.csv')

# Filter out markets with no activity (nan values or zero supply)
active_markets = df[
    (df['supply_usd'].notna()) & 
    (df['supply_usd'] > 0)
].copy()

print(f"\nTotal Markets Found: {len(df)}")
print(f"Active Markets (with TVL): {len(active_markets)}")

# Calculate totals
total_supply = active_markets['supply_usd'].sum()
total_borrowed = active_markets['borrow_usd'].sum()
total_available = total_supply - total_borrowed

print(f"\n{'='*100}")
print("OVERALL STATISTICS")
print(f"{'='*100}")
print(f"Total Deposits (Supply): ${total_supply:,.2f}")
print(f"Total Borrowed:          ${total_borrowed:,.2f}")
print(f"Available to Borrow:     ${total_available:,.2f}")
print(f"Overall Utilization:     {(total_borrowed/total_supply*100) if total_supply > 0 else 0:.2f}%")

# Display all active markets
print(f"\n{'='*100}")
print("ALL MORPHO MARKETS ON PLUME")
print(f"{'='*100}")
print(f"\n{'#':<4} {'Market Pair':<30} {'Deposits (USD)':>20} {'Borrowed (USD)':>20} {'Utilization':>15}")
print("-" * 100)

for idx, (i, row) in enumerate(active_markets.iterrows(), 1):
    utilization = row['utilization'] * 100 if row['utilization'] else 0
    print(f"{idx:<4} {row['pair']:<30} ${row['supply_usd']:>18,.2f} ${row['borrow_usd']:>18,.2f} {utilization:>13,.2f}%")

# Top 10 markets by deposits
print(f"\n{'='*100}")
print("TOP 10 MARKETS BY DEPOSITS")
print(f"{'='*100}")

top_10 = active_markets.nlargest(10, 'supply_usd')

for idx, (i, row) in enumerate(top_10.iterrows(), 1):
    utilization = row['utilization'] * 100 if row['utilization'] else 0
    print(f"\n{idx}. {row['pair']}")
    print(f"   {'─' * 60}")
    print(f"   Collateral: {row['collateral_asset'] if row['collateral_asset'] else 'N/A'}")
    print(f"   Loan Asset: {row['loan_asset']}")
    print(f"   Deposits:   ${row['supply_usd']:,.2f}")
    print(f"   Borrowed:   ${row['borrow_usd']:,.2f}")
    print(f"   Available:  ${row['liquidity_usd']:,.2f}")
    print(f"   Utilization: {utilization:.2f}%")
    if row['supply_apy'] or row['borrow_apy']:
        print(f"   Supply APY: {row['supply_apy']*100:.2f}%")
        print(f"   Borrow APY: {row['borrow_apy']*100:.2f}%")

# Asset breakdown
print(f"\n{'='*100}")
print("BREAKDOWN BY LOAN ASSET")
print(f"{'='*100}")

asset_summary = active_markets.groupby('loan_asset').agg({
    'supply_usd': 'sum',
    'borrow_usd': 'sum',
    'market_id': 'count'
}).reset_index()
asset_summary.columns = ['Loan Asset', 'Total Deposits', 'Total Borrowed', 'Number of Markets']
asset_summary = asset_summary.sort_values('Total Deposits', ascending=False)

print(f"\n{'Loan Asset':<15} {'# Markets':>12} {'Total Deposits':>20} {'Total Borrowed':>20} {'Utilization':>15}")
print("-" * 100)
for idx, row in asset_summary.iterrows():
    utilization = (row['Total Borrowed'] / row['Total Deposits'] * 100) if row['Total Deposits'] > 0 else 0
    print(f"{row['Loan Asset']:<15} {row['Number of Markets']:>12.0f} ${row['Total Deposits']:>18,.2f} ${row['Total Borrowed']:>18,.2f} {utilization:>13,.2f}%")

# Collateral breakdown
print(f"\n{'='*100}")
print("BREAKDOWN BY COLLATERAL ASSET")
print(f"{'='*100}")

collateral_summary = active_markets[active_markets['collateral_asset'] != ''].groupby('collateral_asset').agg({
    'supply_usd': 'sum',
    'borrow_usd': 'sum',
    'market_id': 'count'
}).reset_index()
collateral_summary.columns = ['Collateral Asset', 'Total Deposits', 'Total Borrowed', 'Number of Markets']
collateral_summary = collateral_summary.sort_values('Total Deposits', ascending=False)

print(f"\n{'Collateral Asset':<20} {'# Markets':>12} {'Total Deposits':>20} {'Total Borrowed':>20}")
print("-" * 100)
for idx, row in collateral_summary.iterrows():
    print(f"{row['Collateral Asset']:<20} {row['Number of Markets']:>12.0f} ${row['Total Deposits']:>18,.2f} ${row['Total Borrowed']:>18,.2f}")

print(f"\n{'='*100}")
print("✅ SUMMARY COMPLETE")
print(f"{'='*100}")
print("\n💡 Key Insights:")
print(f"   • Plume has {len(active_markets)} active Morpho lending markets")
print(f"   • Total value deposited: ${total_supply:,.2f}")
print(f"   • Most popular loan asset: {asset_summary.iloc[0]['Loan Asset']} (${asset_summary.iloc[0]['Total Deposits']:,.2f})")
if len(collateral_summary) > 0:
    print(f"   • Most popular collateral: {collateral_summary.iloc[0]['Collateral Asset']} (used in {collateral_summary.iloc[0]['Number of Markets']:.0f} markets)")
print(f"   • Average market utilization: {active_markets['utilization'].mean()*100:.2f}%")

print(f"\n📊 Data Source: Morpho GraphQL API (https://api.morpho.org/graphql)")
print(f"📁 Full data available in: morpho_plume_markets.csv")
print()
