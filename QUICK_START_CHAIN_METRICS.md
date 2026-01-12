# Quick Start: Comprehensive Chain Metrics

## TL;DR - Get Started in 3 Steps

### Step 1: Fetch the Data
```bash
# Activate virtual environment
source venv/bin/activate

# Run the comprehensive chain analysis
python src/comprehensive_chain_analysis.py
```

This will take ~10-15 minutes and create:
- `comprehensive_chain_metrics.csv` - All chain metrics in CSV format
- `comprehensive_chain_metrics.json` - Same data in JSON format

**Note**: The script fetches market cap and FDV data from CoinGecko's API, which requires rate limiting (0.5s between calls). This ensures accurate market cap and FDV values.

### Step 2: Analyze the Data
```bash
# Run the analysis script
python src/analyze_chain_metrics.py
```

This will show you:
- Top chains by TVL, market cap, and stablecoin usage
- Stablecoin dominance rankings
- Market cap to TVL ratios
- Bridge activity
- Side-by-side chain comparisons

### Step 3: Use the Data

#### In Python:
```python
import pandas as pd

# Load the data
df = pd.read_csv('comprehensive_chain_metrics.csv')

# Get Ethereum's metrics
eth = df[df['chain'] == 'Ethereum'].iloc[0]
print(f"Ethereum TVL: ${eth['defi_tvl']:,.0f}")
print(f"Ethereum Token Price: ${eth['token_price']:,.4f}")

# Find chains with high stablecoin usage
high_stable = df[df['stablecoin_to_tvl_ratio'] > 0.5]
print(f"Chains with >50% stablecoin TVL: {len(high_stable)}")
```

#### In Excel/Google Sheets:
Simply open `comprehensive_chain_metrics.csv` in your spreadsheet application.

## What Data Do You Get?

For each chain (top 100 by TVL), you get:

| Metric | Description | Example |
|--------|-------------|---------|
| `chain` | Chain name | "Ethereum" |
| `token_symbol` | Native token | "ETH" |
| `token_price` | Current price | 3456.78 |
| `market_cap` | Token market cap | 415234567890 |
| `fdv` | Fully diluted valuation | 415234567890 |
| `defi_tvl` | DeFi Total Value Locked | 67890123456 |
| `stablecoin_mcap` | Stablecoin market cap on chain | 89456789012 |
| `bridged_tvl` | Bridged assets TVL | 12345678901 |
| `active_addresses` | Active addresses (if available) | 500000 |
| `stablecoin_to_tvl_ratio` | Stablecoin % of TVL | 0.132 (13.2%) |
| `market_cap_to_tvl_ratio` | Market cap vs TVL | 6.12x |

## Common Use Cases

### 1. Find Chains with High Stablecoin Usage
```python
df = pd.read_csv('comprehensive_chain_metrics.csv')
high_stable = df[df['stablecoin_to_tvl_ratio'] > 0.3].sort_values('stablecoin_mcap', ascending=False)
print(high_stable[['chain', 'stablecoin_mcap', 'stablecoin_to_tvl_ratio']])
```

### 2. Compare L2s
```python
l2s = ['Arbitrum', 'Optimism', 'Base', 'Polygon', 'ZKsync Era']
l2_data = df[df['chain'].isin(l2s)]
print(l2_data[['chain', 'defi_tvl', 'stablecoin_mcap', 'bridged_tvl']])
```

### 3. Find Undervalued Chains
```python
# Low market cap to TVL ratio might indicate undervaluation
undervalued = df[(df['market_cap_to_tvl_ratio'] > 0) & 
                  (df['market_cap_to_tvl_ratio'] < 2)].sort_values('defi_tvl', ascending=False)
print(undervalued[['chain', 'market_cap', 'defi_tvl', 'market_cap_to_tvl_ratio']])
```

### 4. Analyze Bridge Activity
```python
high_bridge = df[df['bridged_tvl'] > 0].sort_values('bridged_tvl', ascending=False)
high_bridge['bridge_pct'] = high_bridge['bridged_tvl'] / high_bridge['defi_tvl'] * 100
print(high_bridge[['chain', 'bridged_tvl', 'bridge_pct']])
```

## Running with Main Import Script

The comprehensive chain analysis is also integrated into the main import script:

```bash
python src/defillama_import.py
```

Choose option `1` (Fetch fresh data) and it will run automatically after fetching stablecoin and TVL data.

## Troubleshooting

### "Stablecoin data file not found"
The stablecoin market cap requires data from the main import. Run:
```bash
python src/defillama_import.py
```
Choose option `1` to fetch stablecoin data first.

### Script is slow
This is normal! The script fetches data for 100 chains with multiple API calls per chain. It takes 5-10 minutes.

### Some metrics are 0
Not all chains have all data available:
- **Active addresses**: Often requires Pro API (not always available)
- **Bridged TVL**: Only available for chains with bridge integrations
- **Token price/market cap**: Only available if chain has a native token with CoinGecko listing

### SSL Certificate Errors
The script disables SSL verification by default. If you see errors, check your internet connection.

## Next Steps

1. **Automate**: Set up a cron job to run the script daily
2. **Visualize**: Create charts with matplotlib or plotly
3. **Alert**: Set up alerts for significant metric changes
4. **Track**: Save historical data to track trends over time
5. **Share**: Upload to Google Sheets for team access

## Need Help?

- Check `COMPREHENSIVE_CHAIN_ANALYSIS.md` for detailed documentation
- Look at `src/analyze_chain_metrics.py` for example analysis code
- Review the API responses if data looks incorrect

## Example Output

```
[1/100] Processing: Ethereum
  ✓ Token: ETH
  ✓ Price: $3,456.7890
  ✓ Market Cap: $415,234,567,890
  ✓ FDV: $415,234,567,890
  ✓ Stablecoin Market Cap: $89,456,789,012
  ✓ Bridged TVL: $12,345,678,901
  ✗ Active addresses not available
  ✓ DeFi TVL: $67,890,123,456

...

Analysis Complete!
Total chains analyzed: 100
Data saved to: comprehensive_chain_metrics.csv
```

That's it! You now have comprehensive metrics for the top 100 chains. 🚀

