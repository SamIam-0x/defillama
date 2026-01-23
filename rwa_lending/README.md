# RWA Lending Analysis

This folder contains scripts and data for analyzing Real-World Asset (RWA) lending markets on blockchain networks, specifically focusing on Morpho protocol markets on Plume blockchain.

## 📁 Files

### Scripts

- **`fetch_morpho_plume_markets.py`** - Main script that fetches all Morpho markets on Plume blockchain
  - Queries Morpho's official GraphQL API (https://api.morpho.org/graphql)
  - Retrieves market pairs, deposits, borrows, APYs, and utilization rates
  - Outputs detailed CSV and JSON files

- **`morpho_plume_summary.py`** - Summary script that generates clean reports
  - Reads the CSV data and produces formatted summaries
  - Shows top markets, asset breakdowns, and key insights
  - Great for quick analysis and reporting

### Data Files

- **`morpho_plume_markets.csv`** - Complete market data in CSV format
  - All 45 Morpho markets on Plume blockchain
  - Includes: market IDs, pairs, collateral/loan assets, deposits, borrows, APYs, utilization rates
  - Updated: January 19, 2026

- **`morpho_plume_raw_response.json`** - Raw API response from Morpho
  - Full JSON response from the GraphQL API
  - Useful for debugging and exploring additional data fields

## 🚀 Usage

### Fetch Latest Data

```bash
python rwa_lending/fetch_morpho_plume_markets.py
```

This will:
1. Query Morpho's API for all markets on Plume (Chain ID: 98866)
2. Generate `morpho_plume_markets.csv` with detailed market data
3. Save raw API response to `morpho_plume_raw_response.json`

### View Summary Report

```bash
python rwa_lending/morpho_plume_summary.py
```

This displays:
- Overall statistics (total deposits, borrows, utilization)
- List of all active markets
- Top 10 markets by deposits
- Breakdown by loan asset (pUSD, WETH, USDC.e)
- Breakdown by collateral asset

## 📊 Key Findings (as of Jan 19, 2026)

### Overall Statistics
- **Total Markets**: 45 (29 active)
- **Total Deposits**: $13,025,890.37
- **Total Borrowed**: $5,628,362.70
- **Overall Utilization**: 43.21%

### Top Markets
1. **nALPHA/pUSD**: $3.4M deposits, 73% utilization
2. **nBASIS/pUSD**: $3.0M deposits, 84% utilization
3. **nTBILL/pUSD**: $468K deposits, 89% utilization

### Popular Assets
- **Most Popular Loan Asset**: pUSD (24 markets, $12.9M deposited)
- **Top Collateral Assets**: nALPHA, nBASIS, nTBILL

## 🔧 Technical Details

### API Endpoint
- **Morpho GraphQL API**: `https://api.morpho.org/graphql`
- **Plume Chain ID**: 98866
- **Documentation**: https://docs.morpho.org/tools/offchain/api/getting-started/

### Data Fields
Each market includes:
- Market ID (unique key)
- Collateral asset (symbol, address)
- Loan asset (symbol, address)
- Supply/borrow amounts (in tokens and USD)
- Collateral amount (in tokens and USD)
- APYs (supply and borrow)
- Utilization rate
- Oracle and IRM addresses
- LLTV (Loan-to-Value ratio)

### Rate Limits
- Morpho API: 5,000 requests per 5 minutes
- Max query complexity: 1,000,000

## 🌐 About Plume

Plume is a blockchain focused on Real-World Asset Finance (RWAfi). Key facts:
- **Chain ID**: 98866
- **Focus**: Tokenized real-world assets
- **Launch**: June 2025
- **DeFi Integrations**: 50+ protocols including Morpho

## 📚 Resources

- [Morpho Protocol](https://morpho.org)
- [Morpho API Documentation](https://docs.morpho.org/tools/offchain/api/getting-started/)
- [Plume Blockchain](https://plume.org)
- [Plume Genesis Launch Announcement](https://plume.org/blog/genesis)

## 🔄 Updating Data

To refresh the data, simply run the fetch script again:

```bash
cd /Users/sam.tolomei/Documents/GitHub/defillama
python rwa_lending/fetch_morpho_plume_markets.py
```

The script will overwrite the existing CSV and JSON files with fresh data.

## 📝 Notes

- All USD values are calculated by Morpho's oracles
- Markets with zero TVL are included but marked as inactive in summaries
- Some markets may have "Unknown" collateral if the asset information is not available in the API response
- APYs are net values (after fees) when available
