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
    # Replace NaN values with empty strings
    df = df.replace({np.nan: ''})
    # Convert all values to strings to ensure proper JSON serialization
    df = df.astype(str)
    return df

def update_sheet(service, sheet_name, data):
    # Clean the data
    data = clean_dataframe(data)
    
    # Convert DataFrame to list of lists
    values = [data.columns.tolist()] + data.values.tolist()
    
    # Get or create the sheet
    sheet_id = get_or_create_sheet(service, sheet_name)
    
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
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    # Default list of CSV files and their corresponding sheet names if none provided
    if files_to_upload is None:
        files_to_upload = [
            ('usdt_launch_dates.csv', 'USDT Launch Dates'),
            ('usdc_growth_analysis.csv', 'USDC Growth Analysis'),
            ('usdt0_performance.csv', 'USDT0 Performance'),
            ('usdc_launch_dates.csv', 'USDC Launch Dates'),
            ('stablecoin_launch_analysis.csv', 'Stablecoin Launch Analysis'),
            ('chain_stablecoin_growth.csv', '30-Day Growth Analysis'),
            ('usdt_growth_analysis.csv', 'USDT Growth Analysis'),
            ('stablecoin_aggregate_growth.csv', 'Stablecoin_growth'),
            ('chain_launch_analysis.csv', 'Chain Launch Analysis'),
            ('chain_tvl_stable_analysis.csv', 'Defi Chain Launch')
        ]
    
    for csv_file, sheet_name in files_to_upload:
        if os.path.exists(csv_file):
            data = pd.read_csv(csv_file)
            update_sheet(service, sheet_name, data)
            print(f"Updated {sheet_name} sheet")
        else:
            print(f"Warning: {csv_file} not found")

if __name__ == '__main__':
    main() 