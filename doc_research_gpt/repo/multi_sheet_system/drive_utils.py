from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import os
import json
from datetime import datetime
from google.oauth2 import service_account
from config import SERVICE_ACCOUNT_FILE, DRIVE_FOLDER_ID, SHEET_NAME_PREFIX

def get_drive_service():
    """Get Google Drive API service"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
    )
    return build('drive', 'v3', credentials=creds)

def get_sheets_service():
    """Get Google Sheets API service"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
    )
    return build('sheets', 'v4', credentials=creds)

def create_folder(folder_name, parent_folder_id=None):
    """Create a new folder in Google Drive"""
    service = get_drive_service()
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    try:
        folder = service.files().create(body=file_metadata, fields='id,name,webViewLink').execute()
        return folder
    except HttpError as error:
        print(f'An error occurred creating folder: {error}')
        return None

def create_spreadsheet(title, folder_id=None):
    """Create a new Google Spreadsheet"""
    sheets_service = get_sheets_service()
    drive_service = get_drive_service()
    
    # Create the spreadsheet
    spreadsheet_body = {
        'properties': {
            'title': title
        },
        'sheets': [{
            'properties': {
                'title': 'Data_001',
                'gridProperties': {
                    'rowCount': 1000,
                    'columnCount': 26
                }
            }
        }]
    }
    
    try:
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Move to folder if specified
        if folder_id:
            drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents='root',
                fields='id, parents'
            ).execute()
        
        # Get the web URL
        file_info = drive_service.files().get(fileId=spreadsheet_id, fields='webViewLink').execute()
        
        return {
            'id': spreadsheet_id,
            'title': title,
            'url': file_info.get('webViewLink'),
            'spreadsheet': spreadsheet
        }
        
    except HttpError as error:
        print(f'An error occurred creating spreadsheet: {error}')
        return None

def list_spreadsheets_in_folder(folder_id=None):
    """List all spreadsheets in a specific folder"""
    service = get_drive_service()
    
    query = "mimeType='application/vnd.google-apps.spreadsheet'"
    if folder_id:
        query += f" and '{folder_id}' in parents"
    
    try:
        results = service.files().list(
            q=query,
            fields='files(id, name, webViewLink, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()
        
        return results.get('files', [])
    except HttpError as error:
        print(f'An error occurred listing spreadsheets: {error}')
        return []

def get_spreadsheet_by_name(name, folder_id=None):
    """Find a spreadsheet by name in a specific folder"""
    service = get_drive_service()
    
    query = f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet'"
    if folder_id:
        query += f" and '{folder_id}' in parents"
    
    try:
        results = service.files().list(q=query, fields='files(id, name, webViewLink)').execute()
        files = results.get('files', [])
        
        if files:
            return files[0]  # Return the first match
        return None
    except HttpError as error:
        print(f'An error occurred searching for spreadsheet: {error}')
        return None

def generate_unique_spreadsheet_name(base_name=None):
    """Generate a unique spreadsheet name with timestamp"""
    if base_name is None:
        base_name = SHEET_NAME_PREFIX
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}"

def share_spreadsheet(spreadsheet_id, email_addresses=None, role='writer'):
    """Share a spreadsheet with specified users"""
    service = get_drive_service()
    
    if not email_addresses:
        return True  # Nothing to share
    
    if isinstance(email_addresses, str):
        email_addresses = [email_addresses]
    
    try:
        for email in email_addresses:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
        return True
    except HttpError as error:
        print(f'An error occurred sharing spreadsheet: {error}')
        return False

def get_folder_info(folder_id):
    """Get information about a folder"""
    service = get_drive_service()
    
    try:
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, webViewLink, parents'
        ).execute()
        return folder
    except HttpError as error:
        print(f'An error occurred getting folder info: {error}')
        return None

def download_file(file_id, mime_type='application/pdf', save_as=None):
    """Download a file from Google Drive"""
    service = get_drive_service()
    
    try:
        request = service.files().export_media(fileId=file_id, mimeType=mime_type) if mime_type != 'application/octet-stream' else service.files().get_media(fileId=file_id)
        if not save_as:
            save_as = f"{file_id}.pdf"
        fh = io.FileIO(save_as, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return save_as
    except HttpError as error:
        print(f'An error occurred downloading file: {error}')
        return None

def backup_spreadsheet_metadata(spreadsheet_info, backup_file='spreadsheet_registry.json'):
    """Backup spreadsheet metadata to a JSON file"""
    try:
        # Load existing data
        if os.path.exists(backup_file):
            with open(backup_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'spreadsheets': []}
        
        # Add timestamp
        spreadsheet_info['created_at'] = datetime.now().isoformat()
        
        # Add to registry
        data['spreadsheets'].append(spreadsheet_info)
        
        # Save updated data
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error backing up metadata: {e}")
        return False

def load_spreadsheet_registry(backup_file='spreadsheet_registry.json'):
    """Load spreadsheet registry from backup file"""
    try:
        if os.path.exists(backup_file):
            with open(backup_file, 'r') as f:
                return json.load(f)
        return {'spreadsheets': []}
    except Exception as e:
        print(f"Error loading registry: {e}")
        return {'spreadsheets': []}
