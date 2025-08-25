from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pandas as pd
import numpy as np

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of the spreadsheet.
SPREADSHEET_ID = '1BkCCQKhBUrazaa-x260kb1cUswAAlt_d0xPS4O22-bc'

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json file not found. Please set up Google Sheets API credentials:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create a new project or select existing one\n"
                    "3. Enable Google Sheets API\n"
                    "4. Create credentials (OAuth 2.0 Client ID)\n"
                    "5. Download the credentials and save as 'credentials.json' in the project root"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_or_create_sheet(service, sheet_name):
    # Get all sheets in the spreadsheet
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    
    # Check if sheet exists
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    
    # If sheet doesn't exist, create it
    request = {
        'addSheet': {
            'properties': {
                'title': sheet_name
            }
        }
    }
    
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [request]}
    ).execute()
    
    # Get the new sheet ID
    new_sheet = response['replies'][0]['addSheet']
    return new_sheet['properties']['sheetId']

def clean_dataframe(df):
    # Create a copy to avoid modifying the original DataFrame
    df_clean = df.copy()
    
    # For each column, handle NaN values appropriately while preserving data types
    for col in df_clean.columns:
        if df_clean[col].dtype in ['float64', 'int64']:
            # For numeric columns, convert NaN to None (which becomes null in JSON)
            # This allows Google Sheets to treat them as empty cells while preserving numeric type
            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
        else:
            # For non-numeric columns, convert NaN to empty strings
            df_clean[col] = df_clean[col].fillna('')
    
    return df_clean

def update_sheet(service, sheet_name, data):
    # Clean the data
    data = clean_dataframe(data)
    
    # Convert DataFrame to list of lists
    values = [data.columns.tolist()] + data.values.tolist()
    
    # Get or create the sheet
    sheet_id = get_or_create_sheet(service, sheet_name)
    
    # Clear the entire sheet first
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:Z"  # or a larger range
    ).execute()
    
    # Update with new data
    body = {
        'values': values
    }
    
    # Use the sheet name directly in the range
    range_name = f"{sheet_name}!A1"
    
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

def main(files_to_upload=None):
    try:
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # Default list of CSV files and their corresponding sheet names if none provided
        if files_to_upload is None:
            files_to_upload = [
                # Core metadata and launch analysis
                ('stablecoin_metadata.csv', 'Stablecoin Metadata'),
                ('meta_stablecoins_chain_distribution.csv', 'Meta Distribution'),
                
                # Launch dates and performance
                ('usdt_launch_dates.csv', 'USDT Launches'),
                ('usdc_launch_dates.csv', 'USDC Launches'),
                ('usdt0_performance.csv', 'USDT0 Launches'),
                
                # Growth analysis
                ('usdc_growth_analysis.csv', 'USDC Growth Analysis'),
                ('usdc_rolling_7d_analysis.csv', 'USDC Rolling 7D Analysis'),
                ('usdt_growth_analysis.csv', 'USDT Growth Analysis'),
                
                # Chain analysis
                ('chain_stablecoin_growth.csv', 'Chains Total Stables Growth'),
                ('chain_launch_analysis.csv', 'Chain launch date of 1st stables'),
                
                # Comprehensive launch and growth analysis
                ('stablecoin_launch_analysis.csv', 'Stablecoin Launch by chain Dates'),
                ('stablecoin_aggregate_growth.csv', 'Stablecoin Launches Overall'),
                
                # TVL and DeFi analysis
                ('chain_tvl_stable_analysis.csv', 'Defi TVL by Chain'),
                
                # Market share analysis (from defillama_import.py)
                ('usdc_market_share_90days.csv', 'USDC Market Share 90 Days'),
                ('usdc_market_share_summary.csv', 'USDC Market Share Summary'),
                
                # Raw data files (optional)
                # ('all_stablecoins_chain_distribution.csv', 'Chain Distribution'),
                # ('stablecoins_list.csv', 'Stablecoins List'),
                # ('top_100_stablecoins.csv', 'Top 100 Stablecoins'),
            ]
        
        for csv_file, sheet_name in files_to_upload:
            if os.path.exists(csv_file):
                data = pd.read_csv(csv_file)
                update_sheet(service, sheet_name, data)
                print(f"Updated {sheet_name} sheet")
            else:
                print(f"Warning: {csv_file} not found")
                
    except FileNotFoundError as e:
        print(f"Error uploading to Google Sheets: {e}")
        print("Skipping Google Sheets upload. Data files have been saved locally.")
    except Exception as e:
        print(f"Error uploading to Google Sheets: {e}")
        print("Skipping Google Sheets upload. Data files have been saved locally.")

if __name__ == '__main__':
    main() 