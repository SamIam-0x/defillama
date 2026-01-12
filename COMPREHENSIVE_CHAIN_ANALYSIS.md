# Comprehensive Chain Analysis

This document explains how to use the new comprehensive chain analysis functionality that fetches detailed metrics for blockchain chains from DeFiLlama's API.

## Overview

The comprehensive chain analysis collects the following data for each blockchain:

1. **Chain Token Price** - Current price of the chain's native token
2. **Market Cap** - Market capitalization of the chain's token
3. **FDV (Fully Diluted Valuation)** - Calculated as price × total supply
4. **DeFi TVL** - Total Value Locked in DeFi protocols on the chain
5. **Stablecoin Market Cap** - Total stablecoin circulating supply on the chain
6. **Bridged TVL** - Total value of assets bridged to/from the chain
7. **Active Addresses** - Number of active addresses (if available via API)

## Usage

### Option 1: Run Standalone Script

Run the dedicated comprehensive chain analysis script:

```bash
python src/comprehensive_chain_analysis.py
```

This will:
- Fetch data for the top 100 chains by TVL
- Save results to `comprehensive_chain_metrics.csv` and `comprehensive_chain_metrics.json`
- Display summary statistics and top 10 chains

### Option 2: Run as Part of Main Import

The comprehensive chain analysis is now integrated into the main import script:

```bash
python src/defillama_import.py
```

Select option `1` (Fetch fresh data) and the comprehensive chain analysis will run automatically after the other data collection steps.

## Output Files

### comprehensive_chain_metrics.csv

A CSV file containing all metrics for each chain with the following columns:

- `chain` - Chain name
- `defi_tvl` - DeFi Total Value Locked
- `token_symbol` - Native token symbol
- `chain_id` - Chain ID
- `gecko_id` - CoinGecko ID
- `cmc_id` - CoinMarketCap ID
- `token_price` - Current token price in USD
- `market_cap` - Token market capitalization
- `fdv` - Fully Diluted Valuation
- `stablecoin_mcap` - Total stablecoin market cap on chain
- `bridged_tvl` - Total bridged TVL
- `active_addresses` - Number of active addresses
- `stablecoin_to_tvl_ratio` - Ratio of stablecoin mcap to DeFi TVL
- `market_cap_to_tvl_ratio` - Ratio of token market cap to DeFi TVL
- `data_timestamp` - Timestamp when data was collected

### comprehensive_chain_metrics.json

The same data in JSON format for easier programmatic access.

## API Endpoints Used

The script uses the following API endpoints:

1. **Chains List**: `https://api.llama.fi/v2/chains` (DeFiLlama)
   - Returns list of all chains with basic TVL data

2. **Token Prices**: `https://coins.llama.fi/prices/current/coingecko:{gecko_id}` (DeFiLlama)
   - Returns current token price

3. **Market Cap & FDV**: `https://api.coingecko.com/api/v3/coins/{gecko_id}` (CoinGecko Public API)
   - Returns market cap, fully diluted valuation, and supply data
   - Note: CoinGecko has rate limits (10-50 calls/minute for free tier)

4. **Bridge Data**: `https://bridges.llama.fi/bridgevolume/{chain_name}?id=0` (DeFiLlama)
   - Returns bridged TVL data

5. **Overview Data**: `https://api.llama.fi/overview/chains/{chain_name}` (DeFiLlama)
   - Returns active addresses and other chain metrics (may require Pro API)

6. **Stablecoin Data**: Uses locally cached data from `all_stablecoins_chain_distribution.csv`
   - If this file doesn't exist, stablecoin market cap will be 0
   - Run the main import script first to generate this data

## Requirements

- Python 3.x
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - requests
  - urllib3

## Notes

### Active Addresses

Active address data may not be available for all chains. This metric often requires a DeFiLlama Pro API subscription. If not available, the value will be 0.

### Stablecoin Data

For stablecoin market cap data to be accurate, you need to run the main import script first to generate the stablecoin distribution data:

```bash
python src/defillama_import.py
```

Select option `1` to fetch fresh stablecoin data.

### Rate Limiting

The script includes delays between API calls to respect rate limits:
- 0.25 seconds between DeFiLlama API calls
- 0.5 seconds between CoinGecko API calls

**Processing Time**: Due to CoinGecko rate limits and the additional API calls needed for market cap data, processing 100 chains now takes approximately **10-15 minutes** (previously 5-10 minutes).

**CoinGecko Rate Limits**: The free tier allows 10-50 calls per minute. If you hit the rate limit (HTTP 429), the script will automatically wait 60 seconds before continuing.

### SSL Verification

SSL verification is disabled in the script to avoid certificate issues. This is generally safe for read-only API calls but be aware of this if you're concerned about security.

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

[2/100] Processing: Tron
  ✓ Token: TRX
  ✓ Price: $0.1234
  ✓ Market Cap: $10,987,654,321
  ...
```

## Calculated Metrics

The script also calculates two useful ratios:

1. **Stablecoin to TVL Ratio**: `stablecoin_mcap / defi_tvl`
   - Shows what percentage of the chain's DeFi TVL is in stablecoins
   - Higher ratios indicate more stablecoin usage relative to other assets

2. **Market Cap to TVL Ratio**: `market_cap / defi_tvl`
   - Shows how the chain's token valuation compares to its DeFi ecosystem size
   - Can indicate if a chain is over/undervalued relative to its DeFi activity

## Troubleshooting

### Missing Stablecoin Data

If you see:
```
⚠ Stablecoin data file not found. Stablecoin market cap will be 0.
```

Run the main import script first:
```bash
python src/defillama_import.py
```

### API Errors

If you encounter API errors, the script will continue processing other chains and mark failed metrics as 0. Common issues:

- Rate limiting: The script includes delays, but you may need to increase them
- Chain name mismatches: Some chains may have different names in different API endpoints
- Missing data: Not all chains have all metrics available

### SSL Certificate Errors

The script disables SSL verification by default. If you prefer to keep it enabled, modify these lines in the script:

```python
session = requests.Session()
session.verify = False  # Change to True
```

## Integration with Google Sheets

The comprehensive chain metrics can be uploaded to Google Sheets by modifying the `google_sheets_upload.py` script to include the new CSV file.

## Future Enhancements

Potential improvements:

1. Add historical tracking of metrics over time
2. Calculate growth rates (7d, 30d, 90d) for each metric
3. Add more chain-specific metrics (fees, transactions, etc.)
4. Create visualizations of the data
5. Add alerts for significant changes in metrics
6. Compare chains side-by-side with ranking system

