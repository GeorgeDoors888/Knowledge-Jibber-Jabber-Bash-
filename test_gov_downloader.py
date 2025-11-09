#!/usr/bin/env python3
"""
Simple test version of UK Government Document Downloader
Tests the basic functionality with a few documents
"""

import os
import requests
import tempfile
import pickle
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Google Drive imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def setup_drive_service():
    """Set up Google Drive API service"""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials_2.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def create_drive_folder(service, folder_name, parent_folder_id='root'):
    """Create a folder in Google Drive"""
    try:
        # Check if folder already exists
        query = f"name='{folder_name}' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        
        if results['files']:
            folder_id = results['files'][0]['id']
            print(f"📁 Using existing folder: {folder_name}")
            return folder_id
        
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'parents': [parent_folder_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(body=folder_metadata).execute()
        folder_id = folder.get('id')
        print(f"📁 Created folder: {folder_name}")
        return folder_id
        
    except Exception as e:
        print(f"❌ Error creating folder {folder_name}: {e}")
        return None

def test_gov_uk_page():
    """Test downloading a few documents from a gov.uk page"""
    print("🧪 Testing gov.uk document download...")
    
    # Set up session with proper headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    # Test with HMRC VAT notices page (should have PDF documents)
    test_url = "https://www.gov.uk/government/collections/vat-notices"
    
    try:
        print(f"📄 Accessing: {test_url}")
        response = session.get(test_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for PDF links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.pdf' in href.lower():
                full_url = urljoin(test_url, href)
                pdf_links.append((full_url, link.get_text(strip=True)))
        
        print(f"📋 Found {len(pdf_links)} PDF links")
        
        # Show first few links
        for i, (url, title) in enumerate(pdf_links[:5]):
            print(f"{i+1}. {title[:60]}...")
            print(f"   URL: {url}")
        
        return pdf_links[:3]  # Return first 3 for testing
        
    except Exception as e:
        print(f"❌ Error accessing {test_url}: {e}")
        return []

def main():
    print("🧪 UK Government Document Download Test")
    print("=" * 50)
    
    # Test basic web scraping
    pdf_links = test_gov_uk_page()
    
    if not pdf_links:
        print("❌ No documents found to test with")
        return
    
    # Set up Google Drive
    try:
        service = setup_drive_service()
        print("✅ Google Drive authentication successful")
    except Exception as e:
        print(f"❌ Google Drive setup failed: {e}")
        return
    
    # Create test folder
    folder_id = create_drive_folder(service, "GOV_UK_Test")
    if not folder_id:
        print("❌ Failed to create test folder")
        return
    
    # Test downloading and uploading one document
    test_url, title = pdf_links[0]
    
    print(f"\n📥 Testing download: {title}")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download file
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            
            response = session.get(test_url, timeout=30)
            response.raise_for_status()
            
            # Save to temp file
            filename = f"test_document_{int(time.time())}.pdf"
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded: {len(response.content)} bytes")
            
            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype='application/pdf')
            
            file = service.files().create(
                body=file_metadata,
                media_body=media
            ).execute()
            
            print(f"✅ Uploaded to Google Drive: {filename}")
            print(f"📁 File ID: {file.get('id')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return
    
    print("\n🎉 Test completed successfully!")
    print("The full downloader should work properly.")

if __name__ == "__main__":
    main()