import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
from datetime import datetime
from config import SERVICE_ACCOUNT_FILE, MAX_ROWS_PER_SHEET, SHEET_NAME_PREFIX

def get_credentials():
    """Get Google API credentials"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    return ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)

def get_gspread_client():
    """Get gspread client"""
    creds = get_credentials()
    return gspread.authorize(creds)

def get_sheets_service():
    """Get Google Sheets API service"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return build('sheets', 'v4', credentials=creds)

def load_sheet(sheet_url, tab_index=0):
    """Load data from a specific sheet tab"""
    client = get_gspread_client()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(tab_index)
    data = worksheet.get_all_records()
    return pd.DataFrame(data), worksheet

def get_sheet_row_count(worksheet):
    """Get the number of rows with data in a worksheet"""
    try:
        all_values = worksheet.get_all_values()
        # Count non-empty rows
        row_count = 0
        for row in all_values:
            if any(cell.strip() for cell in row):
                row_count += 1
        return row_count
    except Exception as e:
        print(f"Error getting row count: {e}")
        return 0

def is_sheet_full(worksheet, max_rows=None):
    """Check if a sheet has reached its capacity limit"""
    if max_rows is None:
        max_rows = MAX_ROWS_PER_SHEET
    
    current_rows = get_sheet_row_count(worksheet)
    return current_rows >= max_rows

def create_new_sheet_tab(spreadsheet, tab_name=None):
    """Create a new tab in an existing spreadsheet"""
    if tab_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tab_name = f"Data_{timestamp}"
    
    try:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=20)
        return worksheet
    except Exception as e:
        print(f"Error creating new tab: {e}")
        return None

def setup_sheet_headers(worksheet, headers):
    """Set up headers for a new worksheet"""
    try:
        # Convert headers to list if it's not already
        if isinstance(headers, dict):
            headers = list(headers.keys())
        
        # Update the first row with headers
        worksheet.update('A1', [headers])
        return True
    except Exception as e:
        print(f"Error setting up headers: {e}")
        return False

def add_data_to_sheet(worksheet, data_row):
    """Add a single row of data to a worksheet"""
    try:
        # Find the next empty row
        current_rows = get_sheet_row_count(worksheet)
        next_row = current_rows + 1
        
        # Convert data_row to list if it's a dict
        if isinstance(data_row, dict):
            data_row = list(data_row.values())
        
        # Update the next available row
        worksheet.update(f'A{next_row}', [data_row])
        return True
    except Exception as e:
        print(f"Error adding data to sheet: {e}")
        return False

def batch_update_sheet(worksheet, data_list, start_row=None):
    """Add multiple rows of data to a worksheet in batch"""
    try:
        if start_row is None:
            start_row = get_sheet_row_count(worksheet) + 1
        
        # Convert data to proper format
        formatted_data = []
        for row in data_list:
            if isinstance(row, dict):
                formatted_data.append(list(row.values()))
            else:
                formatted_data.append(row)
        
        # Calculate the range
        end_row = start_row + len(formatted_data) - 1
        range_name = f'A{start_row}:Z{end_row}'  # Assumes max 26 columns
        
        # Update in batch
        worksheet.update(range_name, formatted_data)
        return True
    except Exception as e:
        print(f"Error batch updating sheet: {e}")
        return False

def find_available_sheet(spreadsheet, max_rows=None):
    """Find the first available sheet tab that's not full"""
    if max_rows is None:
        max_rows = MAX_ROWS_PER_SHEET
    
    worksheets = spreadsheet.worksheets()
    
    for worksheet in worksheets:
        if not is_sheet_full(worksheet, max_rows):
            return worksheet
    
    # If no available sheet found, create a new one
    return create_new_sheet_tab(spreadsheet)

def update_summary(worksheet, row, summary, tags):
    """Update summary and tags for a specific row (legacy function)"""
    try:
        worksheet.update_cell(row, 6, summary)  # Column F
        worksheet.update_cell(row, 7, tags)     # Column G
        return True
    except Exception as e:
        print(f"Error updating summary: {e}")
        return False

def get_spreadsheet_info(spreadsheet):
    """Get information about a spreadsheet including all tabs and their row counts"""
    info = {
        'title': spreadsheet.title,
        'id': spreadsheet.id,
        'url': spreadsheet.url,
        'tabs': []
    }
    
    try:
        worksheets = spreadsheet.worksheets()
        for worksheet in worksheets:
            tab_info = {
                'name': worksheet.title,
                'id': worksheet.id,
                'row_count': get_sheet_row_count(worksheet),
                'is_full': is_sheet_full(worksheet)
            }
            info['tabs'].append(tab_info)
    except Exception as e:
        print(f"Error getting spreadsheet info: {e}")
    
    return info
