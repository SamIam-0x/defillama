# Comprehensive Chain Metrics - Workflow Guide

## Visual Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     COMPREHENSIVE CHAIN METRICS                  │
│                         Workflow Overview                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Data Collection                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Option A: Standalone Script (Quick)                             │
│  ┌────────────────────────────────────────────────────┐         │
│  │ $ python src/comprehensive_chain_analysis.py       │         │
│  │                                                     │         │
│  │ • Fetches top 100 chains                           │         │
│  │ • Gets token prices, market caps, FDV              │         │
│  │ • Gets DeFi TVL                                    │         │
│  │ • Gets stablecoin market cap (if available)        │         │
│  │ • Gets bridged TVL                                 │         │
│  │ • Gets active addresses (if available)             │         │
│  │                                                     │         │
│  │ ⏱️  Takes ~5-10 minutes                            │         │
│  └────────────────────────────────────────────────────┘         │
│                           │                                       │
│                           ▼                                       │
│  Option B: Integrated with Main Import (Complete)                │
│  ┌────────────────────────────────────────────────────┐         │
│  │ $ python src/defillama_import.py                   │         │
│  │ Select: 1 (Fetch fresh data)                       │         │
│  │                                                     │         │
│  │ • Fetches stablecoin data (200 stablecoins)        │         │
│  │ • Fetches TVL data (500 chains)                    │         │
│  │ • Runs comprehensive chain analysis                │         │
│  │ • Runs stablecoin analysis                         │         │
│  │ • Uploads to Google Sheets                         │         │
│  │                                                     │         │
│  │ ⏱️  Takes ~15-20 minutes                           │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Output Files Generated                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📄 comprehensive_chain_metrics.csv                              │
│     • All chain metrics in CSV format                            │
│     • 15 columns × 100 rows                                      │
│     • Ready for Excel/Google Sheets                              │
│                                                                   │
│  📄 comprehensive_chain_metrics.json                             │
│     • Same data in JSON format                                   │
│     • Easy for programmatic access                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Analysis & Insights                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Option A: Run Pre-built Analysis                                │
│  ┌────────────────────────────────────────────────────┐         │
│  │ $ python src/analyze_chain_metrics.py              │         │
│  │                                                     │         │
│  │ Shows:                                              │         │
│  │ • Top chains by TVL                                │         │
│  │ • Top chains by stablecoin market cap              │         │
│  │ • Top chains by market cap                         │         │
│  │ • Stablecoin dominance rankings                    │         │
│  │ • Market cap to TVL ratio analysis                 │         │
│  │ • Bridge activity analysis                         │         │
│  │ • Chain-by-chain comparisons                       │         │
│  │                                                     │         │
│  │ ⏱️  Takes <1 second                                │         │
│  └────────────────────────────────────────────────────┘         │
│                           │                                       │
│                           ▼                                       │
│  Option B: Custom Analysis with Python                           │
│  ┌────────────────────────────────────────────────────┐         │
│  │ import pandas as pd                                │         │
│  │ df = pd.read_csv('comprehensive_chain_metrics.csv')│         │
│  │                                                     │         │
│  │ # Your custom analysis here                        │         │
│  │ high_stable = df[df['stablecoin_to_tvl_ratio']>0.3]│         │
│  └────────────────────────────────────────────────────┘         │
│                           │                                       │
│                           ▼                                       │
│  Option C: Open in Excel/Google Sheets                           │
│  ┌────────────────────────────────────────────────────┐         │
│  │ Open: comprehensive_chain_metrics.csv              │         │
│  │                                                     │         │
│  │ • Create pivot tables                              │         │
│  │ • Create charts                                    │         │
│  │ • Filter and sort                                  │         │
│  │ • Share with team                                  │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Export to Different Formats (Optional)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  $ python src/export_chain_metrics.py                            │
│                                                                   │
│  Generates:                                                       │
│  📄 comprehensive_chain_metrics_formatted.json (nested)          │
│  📄 chain_metrics_summary.json (summary stats)                   │
│  📄 chain_rankings.csv (rankings by metric)                      │
│  📄 comprehensive_chain_metrics_excel.csv (formatted)            │
│  📄 top_20_chains.csv (top 20 only)                              │
│  📄 l2_comparison.csv (L2 chains comparison)                     │
│  📄 major_chains_comparison.csv (major chains)                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────┐
│  DeFiLlama APIs  │
└────────┬─────────┘
         │
         │ Fetch data for each chain:
         │
         ├─► Token Price & Market Cap
         │   (coins.llama.fi)
         │
         ├─► DeFi TVL
         │   (api.llama.fi/v2/chains)
         │
         ├─► Stablecoin Market Cap
         │   (local CSV data)
         │
         ├─► Bridged TVL
         │   (bridges.llama.fi)
         │
         └─► Active Addresses
             (api.llama.fi/overview)
                    │
                    ▼
         ┌──────────────────────┐
         │  Process & Calculate │
         │  • Ratios            │
         │  • Rankings          │
         │  • Aggregations      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Output Files       │
         │  • CSV               │
         │  • JSON              │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Analysis Tools     │
         │  • Python scripts    │
         │  • Excel/Sheets      │
         │  • Custom code       │
         └──────────────────────┘
```

## Quick Command Reference

### First Time Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### Fetch Fresh Data
```bash
# Option 1: Quick - Just chain metrics
python src/comprehensive_chain_analysis.py

# Option 2: Complete - All data including stablecoins
python src/defillama_import.py  # Select option 1
```

### Analyze Data
```bash
# Run pre-built analysis
python src/analyze_chain_metrics.py

# Export to multiple formats
python src/export_chain_metrics.py
```

### Custom Analysis (Python)
```python
import pandas as pd

# Load data
df = pd.read_csv('comprehensive_chain_metrics.csv')

# Example: Find L2s with high TVL
l2s = ['Arbitrum', 'Optimism', 'Base', 'Polygon']
l2_data = df[df['chain'].isin(l2s)]
print(l2_data[['chain', 'defi_tvl', 'stablecoin_mcap']])

# Example: Find undervalued chains
undervalued = df[df['market_cap_to_tvl_ratio'] < 2]
print(undervalued.sort_values('defi_tvl', ascending=False))
```

## File Organization

```
defillama/
│
├── src/
│   ├── comprehensive_chain_analysis.py    ← Main data collection
│   ├── analyze_chain_metrics.py           ← Pre-built analysis
│   ├── export_chain_metrics.py            ← Export utilities
│   ├── defillama_import.py                ← Integrated workflow
│   └── ...
│
├── comprehensive_chain_metrics.csv         ← Output: Main data file
├── comprehensive_chain_metrics.json        ← Output: JSON format
│
├── COMPREHENSIVE_CHAIN_ANALYSIS.md         ← Detailed docs
├── QUICK_START_CHAIN_METRICS.md            ← Quick start guide
├── NEW_FEATURE_SUMMARY.md                  ← Feature summary
└── WORKFLOW_GUIDE.md                       ← This file
```

## Data Schema

### Main Metrics Table

| Column | Type | Example | Source |
|--------|------|---------|--------|
| chain | string | "Ethereum" | API |
| token_symbol | string | "ETH" | API |
| token_price | float | 3456.78 | coins.llama.fi |
| market_cap | float | 415234567890 | coins.llama.fi |
| fdv | float | 415234567890 | Calculated |
| defi_tvl | float | 67890123456 | api.llama.fi |
| stablecoin_mcap | float | 89456789012 | Local CSV |
| bridged_tvl | float | 12345678901 | bridges.llama.fi |
| active_addresses | int | 500000 | api.llama.fi |
| stablecoin_to_tvl_ratio | float | 0.132 | Calculated |
| market_cap_to_tvl_ratio | float | 6.12 | Calculated |

## Common Use Cases

### 1. Daily Monitoring
```bash
# Set up cron job to run daily
0 9 * * * cd /path/to/defillama && source venv/bin/activate && python src/comprehensive_chain_analysis.py
```

### 2. Weekly Reports
```bash
# Generate weekly report
python src/comprehensive_chain_analysis.py
python src/analyze_chain_metrics.py > weekly_report.txt
```

### 3. Chain Research
```python
# Deep dive on specific chain
df = pd.read_csv('comprehensive_chain_metrics.csv')
chain = df[df['chain'] == 'Arbitrum'].iloc[0]

print(f"Arbitrum Analysis:")
print(f"TVL: ${chain['defi_tvl']:,.0f}")
print(f"Stablecoin %: {chain['stablecoin_to_tvl_ratio']:.1%}")
print(f"Bridge TVL: ${chain['bridged_tvl']:,.0f}")
```

### 4. Comparative Analysis
```python
# Compare L1s vs L2s
l1s = ['Ethereum', 'Solana', 'Avalanche']
l2s = ['Arbitrum', 'Optimism', 'Base']

l1_data = df[df['chain'].isin(l1s)]
l2_data = df[df['chain'].isin(l2s)]

print(f"L1 Avg TVL: ${l1_data['defi_tvl'].mean():,.0f}")
print(f"L2 Avg TVL: ${l2_data['defi_tvl'].mean():,.0f}")
```

## Troubleshooting Flowchart

```
┌─────────────────────┐
│  Problem?           │
└──────┬──────────────┘
       │
       ├─► "File not found" error
       │   └─► Run: python src/comprehensive_chain_analysis.py
       │
       ├─► "Stablecoin data not found" warning
       │   └─► Run: python src/defillama_import.py (option 1)
       │
       ├─► API errors for some chains
       │   └─► Normal! Script continues, marks as 0
       │
       ├─► Script is slow
       │   └─► Normal! Takes 5-10 minutes for 100 chains
       │
       ├─► Active addresses all 0
       │   └─► Normal! Requires Pro API (not always available)
       │
       └─► SSL certificate errors
           └─► Script disables SSL by default (safe for read-only)
```

## Integration Points

### With Existing Scripts
- ✅ Uses stablecoin data from `defillama_import.py`
- ✅ Can be added to `google_sheets_upload.py`
- ✅ Can be stored in `chain_data.db`
- ✅ Runs automatically with main import

### With External Tools
- ✅ Excel/Google Sheets (CSV format)
- ✅ Tableau/PowerBI (CSV format)
- ✅ Python/Pandas (CSV or JSON)
- ✅ JavaScript/Node.js (JSON format)
- ✅ R/RStudio (CSV format)

## Best Practices

### 1. Data Freshness
- Run daily for up-to-date metrics
- Store historical data for trend analysis
- Compare changes over time

### 2. Data Quality
- Check for 0 values (missing data)
- Validate against DeFiLlama website
- Note API limitations (active addresses)

### 3. Performance
- Don't reduce API delays (rate limits)
- Run during off-peak hours if automated
- Consider caching for frequent access

### 4. Analysis
- Always filter out 0 values for ratios
- Use multiple metrics for decisions
- Cross-reference with other data sources

## Next Steps

1. **Run the script**: `python src/comprehensive_chain_analysis.py`
2. **Explore the data**: Open CSV in Excel or run analysis script
3. **Customize**: Modify scripts for your specific needs
4. **Automate**: Set up daily runs via cron
5. **Integrate**: Add to your existing workflows
6. **Share**: Upload to Google Sheets or share CSV files

---

**Need Help?**
- 📖 Read: `COMPREHENSIVE_CHAIN_ANALYSIS.md` for details
- 🚀 Quick Start: `QUICK_START_CHAIN_METRICS.md`
- 📝 Summary: `NEW_FEATURE_SUMMARY.md`
- 🔄 This Guide: `WORKFLOW_GUIDE.md`

**Ready to start?** Run: `python src/comprehensive_chain_analysis.py` 🚀

