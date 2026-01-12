from google.oauth2 import service_account
from googleapiclient.discovery import build
import os.path
import pandas as pd
import numpy as np

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of the spreadsheet.
SPREADSHEET_ID = '1BkCCQKhBUrazaa-x260kb1cUswAAlt_d0xPS4O22-bc'

def get_credentials():
    """Get credentials using service account (doesn't expire)"""
    # Try service account first (key.json)
    if os.path.exists('key.json'):
        creds = service_account.Credentials.from_service_account_file(
            'key.json', scopes=SCOPES)
        return creds
    
    # Fallback to OAuth flow if service account not available
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                print("Deleting expired token and re-authenticating...")
                if os.path.exists('token.json'):
                    os.remove('token.json')
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "Neither key.json (service account) nor credentials.json (OAuth) found.\n"
                    "Please set up Google Sheets API credentials:\n"
                    "Option 1 (Recommended): Service Account\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create a service account\n"
                    "3. Download the key and save as 'key.json'\n"
                    "4. Share the spreadsheet with the service account email\n\n"
                    "Option 2: OAuth 2.0\n"
                    "1. Create OAuth 2.0 Client ID credentials\n"
                    "2. Download and save as 'credentials.json'"
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
    
    # Replace all NaN values with None first (which will serialize as null in JSON)
    df_clean = df_clean.where(pd.notna(df_clean), None)
    
    return df_clean

def update_sheet(service, sheet_name, data):
    # Clean the data
    data = clean_dataframe(data)
    
    # Convert DataFrame to list of lists, ensuring JSON serializable values
    def make_json_serializable(val):
        if pd.isna(val) or val is np.nan:
            return ""  # Empty string for Google Sheets
        elif isinstance(val, (np.integer, np.floating)):
            # Handle special float values that aren't JSON serializable
            if np.isinf(val) or np.isneginf(val):
                return ""  # Empty string for infinite values
            return val.item()  # Convert numpy types to Python native types
        elif isinstance(val, (int, float)):
            # Handle Python native numeric types
            if val == float('inf') or val == float('-inf'):
                return ""  # Empty string for infinite values
            return val
        else:
            return val
    
    # Convert DataFrame to list of lists with proper type handling
    values = [data.columns.tolist()]
    for _, row in data.iterrows():
        row_values = [make_json_serializable(val) for val in row]
        values.append(row_values)
    
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
        valueInputOption='USER_ENTERED',
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