from defillama import DefiLlama
import pandas as pd
import json
# initialize api client
llama = DefiLlama()

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

# List to store all records
all_records = []

# Iterate over stablecoin IDs 1-15
for stablecoin_id in range(1, 16):
    print(f"Processing stablecoin ID: {stablecoin_id}")
    
    try:
        # Get historical mcap sum of all stablecoins in a chain
        response = llama.get_stablecoins_historical_mcap_n_chain_distribution(stablecoin_id=stablecoin_id)
        
        # Print response structure for debugging
        print(f"Response type for ID {stablecoin_id}:", type(response))
        print(f"Response keys for ID {stablecoin_id}:", response.keys() if isinstance(response, dict) else "Not a dict")
        
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
                    # print("Data point structure:", json.dumps(data_point, indent=2))
                    continue
                    
    except Exception as e:
        print(f"Error processing stablecoin ID {stablecoin_id}: {str(e)}")
        continue

# Create DataFrame from all records
df = pd.DataFrame(all_records)

# Sort by date, stablecoin, and chain
df = df.sort_values(['date', 'stablecoin_id', 'chain'])

# saving to csv
df.to_csv('all_stablecoins_chain_distribution.csv', index=False)

