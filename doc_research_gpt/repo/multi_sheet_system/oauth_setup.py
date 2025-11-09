"""
OAuth-based Google Drive Manager
Adapts the system to work with OAuth credentials instead of service account
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
from typing import Optional

class OAuthDriveManager:
    """Google Drive manager using OAuth authentication"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, credentials_file: str = 'oauth_credentials.json'):
        """Initialize OAuth Drive Manager"""
        self.credentials_file = credentials_file
        self.token_file = 'token.pickle'
        self.creds = None
        self.drive_service = None
        self.sheets_service = None
        
    def authenticate(self):
        """Authenticate using OAuth flow"""
        # Check if we have saved credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials are not valid, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                self.creds.refresh(Request())
            else:
                print("🔐 Starting OAuth authentication flow...")
                print("📖 This will open your browser for Google authentication")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
                
        print("✅ Authentication successful!")
        
        # Build services
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        
        return True
    
    def test_connection(self):
        """Test the connection by getting user info"""
        try:
            # Test Drive API
            about = self.drive_service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            # Test by listing a few files
            results = self.drive_service.files().list(
                pageSize=5,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            
            print(f"📧 Authenticated as: {user_email}")
            print(f"📁 Can access {len(files)} sample files from your Drive")
            
            if files:
                print("📄 Sample files:")
                for file in files[:3]:
                    print(f"   - {file['name']} ({file['mimeType']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

def quick_oauth_setup():
    """Quick setup function for OAuth authentication"""
    print("🚀 Setting up OAuth authentication for Google Drive...")
    
    # Check if credentials file exists
    if not os.path.exists('oauth_credentials.json'):
        print("❌ oauth_credentials.json not found")
        print("Please ensure your OAuth credentials file is in this directory")
        return False
    
    # Initialize manager
    manager = OAuthDriveManager('oauth_credentials.json')
    
    # Authenticate
    try:
        if manager.authenticate():
            # Test connection
            if manager.test_connection():
                print("\n🎉 OAuth setup successful!")
                print("✅ You can now use the Google Drive analysis system")
                return True
            else:
                print("\n❌ Authentication succeeded but connection test failed")
                return False
        else:
            print("\n❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"\n❌ OAuth setup failed: {e}")
        return False

if __name__ == "__main__":
    quick_oauth_setup()