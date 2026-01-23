# LST/LRT TVL by Chain Analysis

This analysis tracks total TVL for specific Liquid Staking Tokens (LSTs) and Liquid Restaking Tokens (LRTs) across all chains.

## 📊 What Does This Analysis Show?

This analysis provides a comprehensive view of LST/LRT distribution across chains, answering questions like:
- **Where is WEETH (Ether.fi) being used?**
- **Which chains have the most WSTETH (Lido) TVL?**
- **How is LST/LRT TVL distributed across the ecosystem?**

## 🎯 Tracked Tokens (18 LSTs/LRTs)

### Top LSTs by Protocol:
- **WEETH** - Ether.fi
- **WSTETH** - Lido  
- **RSETH** - KelpDAO
- **EZETH** - Renzo
- **WRSETH** - KelpDAO
- **CBETH** - Coinbase
- **RETH** - Rocket Pool
- **METH** - Mantle
- **TETH** - Tangible
- **STEAKETH** - Steakhouse

### Additional Tokens:
- WSUPEROETHB (Superform)
- GTMSETHC (Gravita)
- DETH (DineroDAO)
- FLRETH (Flare)
- YOETH (Yearn)
- CSETH (Coinshift)
- BSDETH (Based)
- NWETH (Nimbora)

## 🚀 How to Run

### Run standalone:
```bash
venv/bin/python src/lst_lrt_tvl_by_chain.py
```

### Run as part of full data collection:
```bash
venv/bin/python src/defillama_import.py
```
(The LST/LRT analysis is automatically included in the full data collection)

## 📁 Output Files

### 1. `lst_lrt_tvl_by_chain_detailed.csv`
**Most comprehensive file** - Complete breakdown by token and chain

**Columns:**
- `symbol`: Token symbol (e.g., WEETH, WSTETH)
- `protocol`: Protocol name (e.g., Ether.fi, Lido)
- `chain`: Chain name (e.g., Ethereum, Arbitrum, Base)
- `total_tvl_usd`: Total USD value of this token on this chain
- `num_pools`: Number of pools/vaults using this token
- `num_projects`: Number of unique projects
- `projects`: Comma-separated list of projects

**Example use cases:**
- Find where WEETH is being used across chains
- See which protocols integrate WSTETH on Arbitrum
- Compare LST adoption across different chains

### 2. `lst_lrt_tvl_by_token_summary.csv`
Summary by token, aggregated across all chains

**Columns:**
- `symbol`: Token symbol
- `protocol`: Protocol name
- `total_tvl`: Total TVL across all chains
- `num_chains`: Number of chains where this token exists
- `total_pools`: Total number of pools
- `total_projects`: Total number of projects using it

### 3. `lst_lrt_tvl_by_chain_summary.csv`
Summary by chain, aggregated across all tokens

**Columns:**
- `chain`: Chain name
- `total_tvl`: Total LST/LRT TVL on this chain
- `num_tokens`: Number of different LST/LRT tokens
- `total_pools`: Total number of pools

### 4. `lst_lrt_token_chain_matrix.csv`
Pivot table showing token distribution across chains (useful for Excel/analysis)

## 📈 Key Metrics (Latest Run)

### Overall:
- **Total LST/LRT TVL**: $37.38B
- **Chains with LST/LRT activity**: 24
- **Total pools tracked**: 358

### Top 5 LST/LRT Tokens:
1. **WEETH (Ether.fi)**: $18.40B (49.2%)
2. **WSTETH (Lido)**: $8.81B (23.6%)
3. **RETH (Rocket Pool)**: $4.27B (11.4%)
4. **RSETH (KelpDAO)**: $2.88B (7.7%)
5. **EZETH (Renzo)**: $1.05B (2.8%)

### Top 5 Chains by LST/LRT TVL:
1. **Ethereum**: $35.43B (94.8%)
2. **Arbitrum**: $756M (2.0%)
3. **Base**: $533M (1.4%)
4. **Plasma**: $255M (0.7%)
5. **Katana**: $104M (0.3%)

## 💡 Example Queries

### Where is WEETH being used?
```python
import pandas as pd

df = pd.read_csv('lst_lrt_tvl_by_chain_detailed.csv')
weeth = df[df['symbol'] == 'WEETH'].sort_values('total_tvl_usd', ascending=False)
print(weeth[['chain', 'total_tvl_usd', 'num_projects', 'projects']])
```

**Result**: WEETH has $18.4B TVL across 11 chains:
- Ethereum: $17.5B (95.4%)
- Plasma: $255M
- Base: $238M
- Arbitrum: $226M

### Which LSTs are on Base?
```python
import pandas as pd

df = pd.read_csv('lst_lrt_tvl_by_chain_detailed.csv')
base_lsts = df[df['chain'] == 'Base'].sort_values('total_tvl_usd', ascending=False)
print(base_lsts[['symbol', 'protocol', 'total_tvl_usd', 'num_projects']])
```

**Result**: Base has 13 different LSTs with $533M total TVL

### Compare Lido (WSTETH) vs Ether.fi (WEETH) across chains
```python
import pandas as pd

df = pd.read_csv('lst_lrt_tvl_by_chain_detailed.csv')
comparison = df[df['symbol'].isin(['WEETH', 'WSTETH'])].pivot_table(
    index='chain',
    columns='symbol',
    values='total_tvl_usd',
    aggfunc='sum',
    fill_value=0
).sort_values('WEETH', ascending=False)
print(comparison.head(10))
```

### Which protocols use the most LST/LRTs?
```python
import pandas as pd

df = pd.read_csv('lst_lrt_tvl_by_chain_detailed.csv')

# Split projects and count occurrences
all_projects = []
for _, row in df.iterrows():
    for project in row['projects'].split(', '):
        all_projects.append({
            'project': project,
            'tvl': row['total_tvl_usd']
        })

project_df = pd.DataFrame(all_projects)
project_totals = project_df.groupby('project')['tvl'].sum().sort_values(ascending=False)
print(project_totals.head(20))
```

## 🔍 Key Insights

### 1. **Ethereum Dominance**
Ethereum accounts for **94.8%** of all LST/LRT TVL ($35.4B), which makes sense as:
- Most LSTs are native to Ethereum
- Largest DeFi ecosystem
- Most liquid markets for these assets

### 2. **WEETH (Ether.fi) Leadership**
WEETH is the largest LST/LRT with **$18.4B TVL** (49% of total):
- Available on 11 chains
- 69 different pools
- Integrated by 24+ protocols

### 3. **Cross-Chain Expansion**
While Ethereum dominates, significant TVL exists on L2s:
- **Arbitrum**: $756M across 6 LSTs
- **Base**: $533M across 13 LSTs (most diverse)
- Growing presence on newer chains (Plasma, Katana)

### 4. **KelpDAO's Dual Strategy**
KelpDAO has two major tokens:
- **RSETH**: $2.88B (focused on Ethereum + Arbitrum)
- **WRSETH**: $147M (focused on Base + Avalanche)

### 5. **Protocol Integration**
Top protocols integrating LSTs/LRTs:
- **Aave V3**: Present across most chains
- **Compound V3**: Major integrator on Ethereum, Arbitrum, Base
- **Morpho**: Growing presence, especially for newer LSTs

## 📊 Chain-Specific Analysis

### Ethereum ($35.4B)
- **12 different LST/LRTs**
- Dominated by WEETH ($17.5B) and WSTETH ($8.3B)
- Home to all major LST protocols
- 131 different pools

### Arbitrum ($756M)
- **6 different LST/LRTs**
- WEETH: $226M, WSTETH: $203M, RSETH: $198M
- Strong Aave and Compound presence
- Growing as main L2 for LST activity

### Base ($533M)
- **13 different LST/LRTs** (most diverse L2)
- WEETH: $238M, WSTETH: $130M
- Emerging as key L2 for LST expansion
- High integration with Coinbase assets (CBETH)

### Plasma ($255M)
- Only WEETH available
- Specialized chain with focused use case
- Single Aave V3 integration

## 🔄 Data Freshness

Data is fetched directly from DeFiLlama's yield pools API in real-time. This captures:
- Lending protocols
- Liquidity pools
- Yield vaults
- Restaking protocols

**Note**: This may not capture all TVL if tokens are held in:
- Simple wallets (not in protocols)
- DEX liquidity (non-yield generating)
- Protocols not tracked by DeFiLlama

## 📝 Notes

### What's Included:
✅ Lending protocols (Aave, Compound, etc.)
✅ Yield vaults (Morpho, Euler, etc.)
✅ Liquidity mining pools
✅ Restaking protocols
✅ Cross-chain bridges with yield

### What's NOT Included:
❌ Simple token holdings (wallets)
❌ Non-yield DEX liquidity
❌ Tokens in transit/bridges
❌ Protocols not tracked by DeFiLlama

## 🆘 Troubleshooting

### Token not found
If a token you're looking for isn't in the results:
- Check if it's spelled correctly (case-sensitive in the script)
- Token might not be in any yield-generating pools
- Token might be too new or too small

### TVL seems lower than expected
Remember this only tracks tokens in **yield-generating protocols**. Total circulating supply will be higher.

### Chain missing
The analysis uses DeFiLlama's chain naming. Some chains might use different names than expected.

## 🔗 Related Files

- `src/lending_assets_by_chain.py` - Lending protocol asset breakdown (all assets)
- `src/lst_lrt_tvl_by_chain.py` - This analysis (LST/LRT specific)
- `src/defillama_import.py` - Main data collection script

## 🎯 Use Cases

1. **Protocol Integration Planning**: See which LSTs have the most TVL and where
2. **Chain Analysis**: Understand LST/LRT adoption on different chains
3. **Competitive Analysis**: Compare different LST protocols' market penetration
4. **Risk Assessment**: Identify concentration risks (e.g., Ethereum dominance)
5. **Market Research**: Track LST/LRT trends and growth patterns
