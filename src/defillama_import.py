from defillama import DefiLlama
import pandas as pd
import json
import urllib3
urllib3.disable_warnings()

# initialize api client with verify=False
llama = DefiLlama()
llama.session.verify = False

# get list of stablecoins
response = llama.get_stablecoins(include_prices=True)

# saving response to json
with open('stablecoins_list.json', 'w') as f:
    json.dump(response, f)

# Print the response structure
print("Response type:", type(response))
print("Response keys:", response.keys() if isinstance(response, dict) else "Not a dict")
print("Response length:", len(response) if hasattr(response, '__len__') else "No length")

# Create DataFrame from peggedAssets
df = pd.DataFrame(response['peggedAssets'])

# saving to csv
df.to_csv('stablecoins_list.csv', index=False)

# Function to extract peggedUSD value from circulating field
def extract_circulating(value):
    try:
        # Convert string representation of dict to actual dict
        if isinstance(value, str):
            value = eval(value)  # Using eval since the string is a valid Python dict
        return value.get('peggedUSD', 0)
    except:
        return 0

# Extract circulating supply values from existing df
df['circulating_supply'] = df['circulating'].apply(extract_circulating)

# Sort by circulating supply in descending order and get top 100
top_100_stablecoins = df.sort_values('circulating_supply', ascending=False).head(100)

# Save top 100 to a new CSV
top_100_stablecoins.to_csv('top_100_stablecoins.csv', index=False)

print("\nTop 100 stablecoins by circulating supply:")
print(top_100_stablecoins[['name', 'symbol', 'circulating_supply']].to_string())

# List to store all records
all_records = []

# Iterate over top 40 stablecoins
for _, stablecoin in top_100_stablecoins.iterrows():
    stablecoin_id = stablecoin['id']
    print(f"Processing stablecoin: {stablecoin['name']} (ID: {stablecoin_id})")
    
    try:
        # Get historical mcap sum of all stablecoins in a chain
        response = llama.get_stablecoins_historical_mcap_n_chain_distribution(stablecoin_id=stablecoin_id)
        
        # Print response structure for debugging
        print(f"Response type for {stablecoin['name']}:", type(response))
        print(f"Response keys for {stablecoin['name']}:", response.keys() if isinstance(response, dict) else "Not a dict")
        
        # Transform the data into records
        for chain, daily_data in response['chainBalances'].items():
            for data_point in daily_data['tokens']:
                try:
                    # Extract circulating amount, defaulting to 0 if not present
                    circulating = data_point.get('circulating', {}).get('peggedUSD', 0)
                    
                    record = {
                        'stablecoin_id': stablecoin_id,
                        'stablecoin_name': response.get('name', 'Unknown'),
                        'stablecoin_symbol': response.get('symbol', 'Unknown'),
                        'date': pd.to_datetime(data_point['date'], unit='s'),
                        'chain': chain,
                        'circulating': circulating
                    }
                    all_records.append(record)
                except Exception as e:
                    print(f"Error processing data point for chain {chain}: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"Error processing stablecoin {stablecoin['name']}: {str(e)}")
        continue

# Create DataFrame from all records
df = pd.DataFrame(all_records)

# Add native_bridged_standard column with blank values
df['native_bridged_standard'] = ''

# Set USDT0 for specific chains
usdt0_chains = ['Corn', 'Unichain', 'Sei', 'Berachain', 'Ink', 'Optimism', 'Arbitrum', 'Flare']
df.loc[(df['stablecoin_symbol'] == 'USDT') & (df['chain'].isin(usdt0_chains)), 'native_bridged_standard'] = 'USDT0'

# Set USDC as native for specific chains
usdc_native_chains = [
    'Ethereum', 'Solana', 'Base', 'Arbitrum', 'Avalanche', 'Polygon', 'Sui',
    'Noble', 'Stellar', 'Aptos', 'Optimism', 'Algorand', 'Near', 'Hedera',
    'zkSync', 'Polkadot', 'Tron', 'Celo', 'Linea', 'Unichain'
]
df.loc[(df['stablecoin_symbol'] == 'USDC') & (df['chain'].isin(usdc_native_chains)), 'native_bridged_standard'] = 'native'

# Set USDT as native for specific chains
usdt_native_chains = [
    'Bitcoin',  # Omni Protocol Token via Bitcoin Blockchain
    'Ethereum', 'Avalanche', 'Cosmos', 'Celo',  # ERC20 Token via various blockchains
    'Tron',  # TRC20 Token via Tron Blockchain
    'EOS',  # EOSIO.TOKEN via EOS Blockchain
    'Liquid',  # Liquid Asset via Liquid Blockchain
    'Algorand',  # Algorand Asset via Algorand Blockchain
    'Bitcoin Cash',  # SLP Token via Bitcoin Cash Blockchain
    'Solana',  # Solana Token via Solana Blockchain
    'Polkadot',  # Statemint Asset via Polkadot Network
    'Kusama',  # Statemine Asset via Kusama Network
    'Tezos',  # Tezos Token via Tezos Blockchain
    'Ton',  # Ton Jetton via Ton Blockchain
    'Aptos'  # Fungible Asset via Aptos Blockchain
]
df.loc[(df['stablecoin_symbol'] == 'USDT') & (df['chain'].isin(usdt_native_chains)), 'native_bridged_standard'] = 'native'

# Sort by date, stablecoin, and chain
df = df.sort_values(['date', 'stablecoin_id', 'chain'])

# saving to csv
df.to_csv('all_stablecoins_chain_distribution.csv', index=False)

# creating a dataframe of just meta stablecoin in df; dropping date and circulating and grouping by chain and stablecoin symbol
meta_df = df.drop(columns=['date', 'circulating']).groupby(['chain', 'stablecoin_symbol', 'native_bridged_standard', 'stablecoin_id', 'stablecoin_name']).sum().reset_index()

# saving meta df to csv
meta_df.to_csv('meta_stablecoins_chain_distribution.csv', index=False)


