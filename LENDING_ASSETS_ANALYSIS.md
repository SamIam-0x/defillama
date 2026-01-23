# Lending Assets by Chain Analysis

This analysis breaks down supplied assets for lending protocols by chain using DeFiLlama's yield pools data.

## 📊 What Does This Analysis Show?

This analysis answers questions like:
- **How much ETH has been lent out on Ethereum?**
- **How much BTC/wBTC/cbBTC has been lent across all chains?**
- **Which protocols are providing lending for specific assets?**

## 🚀 How to Run

### Run standalone:
```bash
venv/bin/python src/lending_assets_by_chain.py
```

### Run as part of full data collection:
```bash
venv/bin/python src/defillama_import.py
```
(The lending assets analysis is automatically included in the full data collection)

## 📁 Output Files

### 1. `lending_assets_by_chain_detailed.csv`
**Most useful file** - Complete breakdown by chain and asset

**Columns:**
- `chain`: Name of the EVM chain
- `symbol`: Asset symbol (e.g., WETH, WBTC, USDC)
- `total_tvl_usd`: Total USD value of this asset lent on this chain
- `num_protocols`: Number of lending protocols offering this asset
- `protocols`: Comma-separated list of protocol names
- `underlyingTokens`: Token contract addresses

**Example use cases:**
- Find how much WETH is lent on Arbitrum
- See which protocols offer USDC lending on Base
- Compare asset availability across chains

### 2. `lending_assets_by_chain_summary.csv`
Summary statistics by chain

**Columns:**
- `chain`: Chain name
- `total_tvl`: Total lending TVL on this chain
- `num_unique_assets`: Number of different assets available
- `total_protocol_count`: Total protocol-asset combinations

### 3. `lending_assets_total_across_chains.csv`
Assets aggregated across all EVM chains

**Columns:**
- `symbol`: Asset symbol
- `total_tvl`: Total USD value across all chains
- `num_chains`: Number of chains where this asset is available
- `total_protocols`: Total number of protocol offerings

**Example use cases:**
- Find the total amount of WETH lent across all EVM chains
- Compare popularity of different stablecoins (USDC vs USDT vs DAI)
- Identify which assets have the widest distribution

### 4. `lending_eth_btc_variants_by_chain.csv`
**Focused view** on ETH and BTC variants

**Assets tracked:**
- **ETH variants**: ETH, WETH, stETH, wstETH, rETH, cbETH, sfrxETH, frxETH, eETH, weETH
- **BTC variants**: BTC, WBTC, tBTC, renBTC, sBTC, cbBTC, BTCB

**Additional column:**
- `asset_type`: Either "ETH" or "BTC" for easy filtering

### 5. `yield_pools_raw.json`
Raw API response from DeFiLlama for debugging

## 📈 Key Metrics (as of latest run)

- **Total EVM chains analyzed**: 29
- **Total unique assets**: 569
- **Total lending TVL on EVM chains**: $59.76B
- **Total lending pools analyzed**: 2,343

### Top Chains by Lending TVL:
1. Ethereum: $45.0B
2. Base: $4.7B
3. Plasma: $2.9B
4. BSC: $2.7B
5. Arbitrum: $2.2B

### Top Supplied Assets (Aggregated):
1. WEETH: $9.0B (10 chains)
2. WSTETH: $8.2B (12 chains)
3. WBTC: $5.6B (14 chains)
4. CBBTC: $5.4B (2 chains)
5. USDC: $4.2B (20 chains)

## 💡 Example Queries

### How much BTC has been lent on Ethereum?
```python
import pandas as pd

df = pd.read_csv('lending_assets_by_chain_detailed.csv')
eth_btc = df[(df['chain'] == 'Ethereum') & (df['symbol'] == 'WBTC')]
print(f"WBTC on Ethereum: ${eth_btc['total_tvl_usd'].sum():,.2f}")
```

### Which chains have the most ETH lending?
```python
import pandas as pd

df = pd.read_csv('lending_eth_btc_variants_by_chain.csv')
eth_variants = df[df['asset_type'] == 'ETH']
by_chain = eth_variants.groupby('chain')['total_tvl_usd'].sum().sort_values(ascending=False)
print(by_chain.head(10))
```

### What are all the BTC variants on Ethereum?
```python
import pandas as pd

df = pd.read_csv('lending_assets_by_chain_detailed.csv')
btc_variants = ['WBTC', 'CBBTC', 'TBTC', 'LBTC', 'SOLVBTC', 'FBTC', 'EBTC']
eth_btc = df[(df['chain'] == 'Ethereum') & (df['symbol'].isin(btc_variants))]
print(eth_btc[['symbol', 'total_tvl_usd', 'num_protocols', 'protocols']])
```

### Which stablecoin is most lent across all chains?
```python
import pandas as pd

df = pd.read_csv('lending_assets_total_across_chains.csv')
stablecoins = ['USDC', 'USDT', 'DAI', 'USDS', 'FRAXUSD', 'CRVUSD']
stable_data = df[df['symbol'].isin(stablecoins)].sort_values('total_tvl', ascending=False)
print(stable_data[['symbol', 'total_tvl', 'num_chains', 'total_protocols']])
```

### What protocols offer WETH lending on Base?
```python
import pandas as pd

df = pd.read_csv('lending_assets_by_chain_detailed.csv')
base_weth = df[(df['chain'] == 'Base') & (df['symbol'] == 'WETH')]
print(base_weth['protocols'].values[0])
```

## 🔍 EVM Chains Included

The analysis includes all major EVM-compatible chains:
- Ethereum, Arbitrum, Optimism, Base, Polygon
- BSC, Avalanche, Fantom, Gnosis, Celo
- Linea, Scroll, zkSync Era, Polygon zkEVM
- Mantle, Blast, Mode, Sonic
- And many more...

## ⚡ Performance

- Fetches ~20,000 yield pools from DeFiLlama
- Filters for ~2,300 lending protocol pools
- Processes data for 29 EVM chains
- Runtime: ~10-15 seconds

## 🔄 Data Freshness

Data is fetched directly from DeFiLlama's API in real-time. Run the script whenever you need the latest data.

## 📝 Notes

- **TVL values** are in USD
- **EVM chains only** - Solana, Sui, Aptos, etc. are excluded
- **Lending protocols only** - DEX, staking, etc. are filtered out
- **Supplied assets** - This shows what has been supplied to lending protocols (not borrowed amounts)
- Some protocols may have the same asset listed multiple times (different pools/markets)

## 🆘 Troubleshooting

### "KeyError: 'category'" error
Make sure you have run `defillama_import.py` first to generate `tvl_data.csv`, which is used to identify lending protocols.

### No data for a specific chain
The chain might not have any lending protocols with yield pools, or it might not be classified as an EVM chain in the script.

### Network errors
The script requires internet access to fetch data from DeFiLlama's API. Check your connection and try again.

## 🔗 Related Files

- `src/lending_tvl_by_chain.py` - Original lending analysis (by protocol, not by asset)
- `src/defillama_import.py` - Main data collection script
- `tvl_data.csv` - All protocols data (used to identify lending protocols)
