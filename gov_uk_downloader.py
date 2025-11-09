#!/usr/bin/env python3
"""
UK Government Document Downloader
Downloads documents from HMRC, Department for Transport, and Department for Communities
and uploads them to organized folders in Google Drive
"""

import os
import sys
import requests
import time
import tempfile
import pickle
from urllib.parse import urljoin, urlparse, quote
from pathlib import Path
import json
import re
from datetime import datetime

# Google Drive imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Web scraping imports
from bs4 import BeautifulSoup
import urllib.robotparser

class GovUKDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Google Drive setup
        self.drive_service = None
        self.setup_drive_service()
        
        # Department configurations
        self.departments = {
            'HMRC': {
                'name': 'HM Revenue and Customs',
                'base_urls': [
                    'https://www.gov.uk/government/organisations/hm-revenue-customs/publications',
                    'https://www.gov.uk/government/collections/tax-bulletins',
                    'https://www.gov.uk/government/collections/vat-notices',
                    'https://www.gov.uk/government/collections/excise-notices'
                ],
                'folder_id': None
            },
            'DfT': {
                'name': 'Department for Transport', 
                'base_urls': [
                    'https://www.gov.uk/government/organisations/department-for-transport/publications',
                    'https://www.gov.uk/government/collections/transport-statistics-great-britain',
                    'https://www.gov.uk/government/collections/renewable-transport-fuel-statistics'
                ],
                'folder_id': None
            },
            'DLUHC': {
                'name': 'Department for Levelling Up, Housing and Communities',
                'base_urls': [
                    'https://www.gov.uk/government/organisations/department-for-levelling-up-housing-and-communities/publications',
                    'https://www.gov.uk/government/collections/local-government-finance-statistics',
                    'https://www.gov.uk/government/collections/planning-applications-statistics'
                ],
                'folder_id': None
            }
        }
        
        self.downloaded_count = 0
        self.max_downloads_per_dept = 50  # Limit to avoid overwhelming
        
    def setup_drive_service(self):
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
        
        self.drive_service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive authentication successful")
    
    def create_drive_folder(self, folder_name, parent_folder_id='root'):
        """Create a folder in Google Drive"""
        try:
            # Check if folder already exists
            query = f"name='{folder_name}' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder'"
            results = self.drive_service.files().list(q=query).execute()
            
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
            
            folder = self.drive_service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            print(f"📁 Created folder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            print(f"❌ Error creating folder {folder_name}: {e}")
            return None
    
    def upload_to_drive(self, file_path, filename, folder_id):
        """Upload a file to Google Drive"""
        try:
            # Check if file already exists
            query = f"name='{filename}' and parents in '{folder_id}'"
            results = self.drive_service.files().list(q=query).execute()
            
            if results['files']:
                print(f"⚠️  File already exists: {filename}")
                return results['files'][0]['id']
            
            # Upload file
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            # Determine mime type based on file extension
            mime_type = 'application/octet-stream'
            if filename.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            elif filename.lower().endswith(('.doc', '.docx')):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif filename.lower().endswith(('.xls', '.xlsx')):
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif filename.lower().endswith('.csv'):
                mime_type = 'text/csv'
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media
            ).execute()
            
            print(f"✅ Uploaded: {filename}")
            return file.get('id')
            
        except Exception as e:
            print(f"❌ Error uploading {filename}: {e}")
            return None
    
    def check_robots_txt(self, base_url):
        """Check robots.txt for crawling permissions"""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = '*'
            return rp.can_fetch(user_agent, base_url)
        except:
            return True  # Assume allowed if can't check
    
    def download_file(self, url, temp_dir):
        """Download a file from URL"""
        try:
            print(f"📥 Downloading: {url}")
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get filename from URL or Content-Disposition header
            filename = None
            if 'Content-Disposition' in response.headers:
                content_disp = response.headers['Content-Disposition']
                filename_match = re.search(r'filename[*]?=([^;]+)', content_disp)
                if filename_match:
                    filename = filename_match.group(1).strip('"\'')
            
            if not filename:
                filename = os.path.basename(urlparse(url).path)
                if not filename or '.' not in filename:
                    # Generate filename based on content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'pdf' in content_type:
                        filename = f"document_{int(time.time())}.pdf"
                    elif 'excel' in content_type or 'spreadsheet' in content_type:
                        filename = f"document_{int(time.time())}.xlsx"
                    elif 'word' in content_type:
                        filename = f"document_{int(time.time())}.docx"
                    else:
                        filename = f"document_{int(time.time())}.html"
            
            # Clean filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            file_path = os.path.join(temp_dir, filename)
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return file_path, filename
            
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            return None, None
    
    def extract_document_links(self, page_url, max_links=20):
        """Extract document download links from a page"""
        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for document links
            document_links = []
            
            # Common selectors for gov.uk document links
            selectors = [
                'a[href*=".pdf"]',
                'a[href*=".doc"]', 
                'a[href*=".xls"]',
                'a[href*=".csv"]',
                '.attachment-details a',
                '.publication-documents a',
                '.document-list a',
                'a[class*="download"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        full_url = urljoin(page_url, href)
                        
                        # Filter for document types
                        if any(ext in href.lower() for ext in ['.pdf', '.doc', '.xls', '.csv']):
                            if full_url not in document_links:
                                document_links.append(full_url)
                                
                                if len(document_links) >= max_links:
                                    break
                
                if len(document_links) >= max_links:
                    break
            
            return document_links
            
        except Exception as e:
            print(f"❌ Error extracting links from {page_url}: {e}")
            return []
    
    def get_publication_pages(self, base_url, max_pages=5):
        """Get pagination links from publications page"""
        try:
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for publication links
            publication_links = [base_url]  # Include the base page
            
            # Look for individual publication pages
            pub_selectors = [
                '.document-row a',
                '.publication-item a', 
                '.document-list-item a',
                'h3 a',
                '.gem-c-document-list__item a'
            ]
            
            for selector in pub_selectors:
                links = soup.select(selector)
                for link in links[:max_pages]:
                    href = link.get('href')
                    if href and '/publications/' in href:
                        full_url = urljoin(base_url, href)
                        if full_url not in publication_links:
                            publication_links.append(full_url)
            
            return publication_links[:max_pages]
            
        except Exception as e:
            print(f"❌ Error getting publication pages from {base_url}: {e}")
            return [base_url]
    
    def process_department(self, dept_code):
        """Process all documents for a department"""
        dept_info = self.departments[dept_code]
        print(f"\n🏛️  Processing {dept_info['name']}")
        
        # Create department folder
        folder_id = self.create_drive_folder(f"GOV_UK_{dept_code}_{dept_info['name']}")
        if not folder_id:
            print(f"❌ Failed to create folder for {dept_code}")
            return
        
        dept_info['folder_id'] = folder_id
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            dept_download_count = 0
            
            for base_url in dept_info['base_urls']:
                if dept_download_count >= self.max_downloads_per_dept:
                    break
                    
                print(f"\n📄 Processing: {base_url}")
                
                # Check robots.txt
                if not self.check_robots_txt(base_url):
                    print(f"⚠️  Robots.txt disallows crawling {base_url}")
                    continue
                
                # Get publication pages
                pub_pages = self.get_publication_pages(base_url, max_pages=3)
                
                for pub_page in pub_pages:
                    if dept_download_count >= self.max_downloads_per_dept:
                        break
                        
                    print(f"🔍 Extracting documents from: {pub_page}")
                    
                    # Extract document links
                    doc_links = self.extract_document_links(pub_page, max_links=5)
                    
                    for doc_url in doc_links:
                        if dept_download_count >= self.max_downloads_per_dept:
                            break
                            
                        # Download document
                        file_path, filename = self.download_file(doc_url, temp_dir)
                        
                        if file_path and filename:
                            # Upload to Google Drive
                            file_id = self.upload_to_drive(file_path, filename, folder_id)
                            
                            if file_id:
                                dept_download_count += 1
                                self.downloaded_count += 1
                                print(f"📊 Department: {dept_download_count}/{self.max_downloads_per_dept}, Total: {self.downloaded_count}")
                            
                            # Clean up local file
                            try:
                                os.remove(file_path)
                            except:
                                pass
                    
                    # Add delay between pages
                    time.sleep(3)
        
        print(f"✅ Completed {dept_info['name']}: {dept_download_count} documents")
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting UK Government Document Downloader")
        print("=" * 60)
        
        # Create main folder for all gov.uk documents
        main_folder_id = self.create_drive_folder("UK_Government_Documents")
        
        if not main_folder_id:
            print("❌ Failed to create main folder")
            return
        
        # Update all departments to use main folder as parent
        for dept_code in self.departments:
            self.departments[dept_code]['parent_folder'] = main_folder_id
        
        # Process each department
        for dept_code in self.departments.keys():
            try:
                self.process_department(dept_code)
            except KeyboardInterrupt:
                print("\n⚠️  Process interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error processing {dept_code}: {e}")
                continue
        
        print(f"\n🎉 Download complete! Total documents: {self.downloaded_count}")
        print("📁 Check your Google Drive for the organized folders")

def main():
    """Main function"""
    print("UK Government Document Downloader")
    print("This will download documents from HMRC, DfT, and DLUHC")
    print("and organize them in Google Drive folders")
    
    # Warning about rate limits
    print("\n⚠️  IMPORTANT NOTES:")
    print("- This script respects robots.txt and adds delays between requests")
    print("- Limited to 50 documents per department to avoid overwhelming servers")
    print("- Process may take 30-60 minutes to complete")
    print("- Ensure you have sufficient Google Drive storage space")
    
    proceed = input("\nProceed with download? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Download cancelled")
        return
    
    try:
        downloader = GovUKDownloader()
        downloader.run()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()