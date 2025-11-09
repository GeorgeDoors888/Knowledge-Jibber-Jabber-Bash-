#!/usr/bin/env python3
"""
Google Drive Metadata Manager
Enhanced system for comprehensive file metadata extraction and tracking
"""

import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriveMetadataManager:
    """Comprehensive Google Drive API manager for metadata extraction and file tracking"""
    
    def __init__(self, credentials_file: str = 'service_account.json'):
        """Initialize the Drive API client with enhanced capabilities"""
        self.credentials_file = credentials_file
        self.drive_service = None
        self.sheets_service = None
        self._setup_services()
        
        # Comprehensive field list for metadata extraction
        self.metadata_fields = (
            'id,name,mimeType,size,createdTime,modifiedTime,lastModifyingUser,'
            'owners,parents,shared,webViewLink,webContentLink,thumbnailLink,'
            'iconLink,hasThumbnail,trashed,explicitlyTrashed,spaces,version,'
            'originalFilename,fileExtension,md5Checksum,sha1Checksum,sha256Checksum,'
            'copyRequiresWriterPermission,writersCanShare,viewedByMe,viewedByMeTime,'
            'permissions,capabilities,properties,appProperties,folderColorRgb,'
            'isAppAuthorized,teamDriveId,driveId,hasAugmentedPermissions'
        )
        
    def _setup_services(self):
        """Setup Google Drive and Sheets API services"""
        try:
            # Setup Drive API
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=[
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/drive.metadata.readonly',
                    'https://www.googleapis.com/auth/spreadsheets'
                ]
            )
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            
            logger.info("✅ Google Drive and Sheets API services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google API services: {e}")
            raise
    
    def scan_all_drive_files(self, include_trashed: bool = False, 
                           max_files: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Comprehensive scan of all files in Google Drive with full metadata
        
        Args:
            include_trashed: Include files in trash
            max_files: Maximum number of files to scan (None for all)
            
        Returns:
            List of file metadata dictionaries
        """
        logger.info("🔍 Starting comprehensive Google Drive scan...")
        
        all_files = []
        page_token = None
        files_processed = 0
        
        try:
            while True:
                # Build query
                query_parts = []
                if not include_trashed:
                    query_parts.append("trashed=false")
                
                query = " and ".join(query_parts) if query_parts else ""
                
                # Execute API call
                results = self.drive_service.files().list(
                    q=query,
                    pageSize=1000,  # Maximum allowed
                    fields=f'nextPageToken, files({self.metadata_fields})',
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                files = results.get('files', [])
                
                for file_data in files:
                    # Process and enhance metadata
                    enhanced_metadata = self._enhance_file_metadata(file_data)
                    all_files.append(enhanced_metadata)
                    
                    files_processed += 1
                    
                    if files_processed % 100 == 0:
                        logger.info(f"   Processed {files_processed} files...")
                    
                    # Check max files limit
                    if max_files and files_processed >= max_files:
                        logger.info(f"   Reached maximum file limit: {max_files}")
                        return all_files
                
                # Check for next page
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as e:
            logger.error(f"❌ Drive API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during drive scan: {e}")
            raise
        
        logger.info(f"✅ Drive scan complete. Found {len(all_files)} files")
        return all_files
    
    def _enhance_file_metadata(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance file metadata with additional computed fields and standardization
        
        Args:
            file_data: Raw file data from Drive API
            
        Returns:
            Enhanced metadata dictionary
        """
        enhanced = file_data.copy()
        
        # Add computed fields
        enhanced['scan_timestamp'] = datetime.now(timezone.utc).isoformat()
        enhanced['file_size_mb'] = self._bytes_to_mb(enhanced.get('size', '0'))
        enhanced['file_age_days'] = self._calculate_file_age(enhanced.get('createdTime'))
        enhanced['last_modified_days'] = self._calculate_file_age(enhanced.get('modifiedTime'))
        
        # Extract file extension if not present
        if 'fileExtension' not in enhanced and 'name' in enhanced:
            name = enhanced['name']
            if '.' in name:
                enhanced['fileExtension'] = name.split('.')[-1].lower()
            else:
                enhanced['fileExtension'] = ''
        
        # Standardize MIME type categories
        enhanced['file_category'] = self._categorize_file_type(enhanced.get('mimeType', ''))
        
        # Extract owner information
        owners = enhanced.get('owners', [])
        if owners:
            owner = owners[0]  # Primary owner
            enhanced['owner_email'] = owner.get('emailAddress', '')
            enhanced['owner_name'] = owner.get('displayName', '')
        else:
            enhanced['owner_email'] = ''
            enhanced['owner_name'] = ''
        
        # Calculate sharing status
        enhanced['sharing_status'] = self._determine_sharing_status(enhanced)
        
        # Extract parent folder information
        parents = enhanced.get('parents', [])
        enhanced['parent_folders'] = len(parents)
        enhanced['parent_folder_ids'] = ','.join(parents) if parents else ''
        
        # Security and permission analysis
        enhanced['permission_count'] = len(enhanced.get('permissions', []))
        enhanced['is_public'] = self._is_file_public(enhanced)
        
        # Content hashes for duplicate detection
        enhanced['content_hash'] = self._get_best_hash(enhanced)
        
        return enhanced
    
    def _bytes_to_mb(self, size_str: str) -> float:
        """Convert bytes string to MB"""
        try:
            return int(size_str) / (1024 * 1024)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_file_age(self, timestamp_str: Optional[str]) -> int:
        """Calculate file age in days from timestamp string"""
        if not timestamp_str:
            return 0
        
        try:
            file_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - file_time).days
        except Exception:
            return 0
    
    def _categorize_file_type(self, mime_type: str) -> str:
        """Categorize file by MIME type"""
        if not mime_type:
            return 'unknown'
        
        categories = {
            'image': ['image/'],
            'video': ['video/'],
            'audio': ['audio/'],
            'document': [
                'application/vnd.google-apps.document',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml',
                'text/'
            ],
            'spreadsheet': [
                'application/vnd.google-apps.spreadsheet',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml'
            ],
            'presentation': [
                'application/vnd.google-apps.presentation',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml'
            ],
            'folder': ['application/vnd.google-apps.folder'],
            'archive': ['application/zip', 'application/x-rar', 'application/x-7z'],
            'code': ['text/x-python', 'text/javascript', 'text/html', 'text/css']
        }
        
        mime_lower = mime_type.lower()
        for category, patterns in categories.items():
            if any(pattern in mime_lower for pattern in patterns):
                return category
        
        return 'other'
    
    def _determine_sharing_status(self, file_data: Dict[str, Any]) -> str:
        """Determine file sharing status"""
        if file_data.get('shared', False):
            permissions = file_data.get('permissions', [])
            if len(permissions) > 1:  # More than just owner
                return 'shared'
        
        return 'private'
    
    def _is_file_public(self, file_data: Dict[str, Any]) -> bool:
        """Check if file is publicly accessible"""
        permissions = file_data.get('permissions', [])
        for perm in permissions:
            if perm.get('type') == 'anyone':
                return True
        return False
    
    def _get_best_hash(self, file_data: Dict[str, Any]) -> str:
        """Get the best available hash for duplicate detection"""
        # Prefer in order: SHA256, SHA1, MD5
        for hash_field in ['sha256Checksum', 'sha1Checksum', 'md5Checksum']:
            if hash_field in file_data and file_data[hash_field]:
                return file_data[hash_field]
        
        # If no hash available, create one from metadata
        metadata_str = f"{file_data.get('name', '')}-{file_data.get('size', '')}-{file_data.get('mimeType', '')}"
        return hashlib.md5(metadata_str.encode()).hexdigest()
    
    def get_file_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        """Get detailed permissions for a specific file"""
        try:
            permissions = self.drive_service.permissions().list(
                fileId=file_id,
                fields='permissions(id,type,emailAddress,role,displayName,allowFileDiscovery)'
            ).execute()
            
            return permissions.get('permissions', [])
            
        except HttpError as e:
            logger.error(f"❌ Failed to get permissions for file {file_id}: {e}")
            return []
    
    def get_folder_structure(self, folder_id: str = None, max_depth: int = 5) -> Dict[str, Any]:
        """
        Build comprehensive folder structure with metadata
        
        Args:
            folder_id: Starting folder ID (None for root)
            max_depth: Maximum depth to traverse
            
        Returns:
            Nested dictionary representing folder structure
        """
        logger.info("📁 Building folder structure...")
        
        def _traverse_folder(folder_id: str, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {}
            
            try:
                # Get folder contents
                query = f"'{folder_id}' in parents and trashed=false"
                results = self.drive_service.files().list(
                    q=query,
                    fields=f'files({self.metadata_fields})',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                files = results.get('files', [])
                folder_structure = {
                    'folders': {},
                    'files': [],
                    'metadata': {
                        'total_files': 0,
                        'total_folders': 0,
                        'total_size': 0
                    }
                }
                
                for file_data in files:
                    enhanced_metadata = self._enhance_file_metadata(file_data)
                    
                    if file_data.get('mimeType') == 'application/vnd.google-apps.folder':
                        # It's a folder - recurse
                        folder_name = file_data.get('name', 'Untitled Folder')
                        folder_structure['folders'][folder_name] = _traverse_folder(
                            file_data['id'], 
                            current_depth + 1
                        )
                        folder_structure['metadata']['total_folders'] += 1
                    else:
                        # It's a file
                        folder_structure['files'].append(enhanced_metadata)
                        folder_structure['metadata']['total_files'] += 1
                        folder_structure['metadata']['total_size'] += int(file_data.get('size', 0))
                
                return folder_structure
                
            except HttpError as e:
                logger.error(f"❌ Failed to traverse folder {folder_id}: {e}")
                return {}
        
        # Start from root if no folder specified
        if folder_id is None:
            folder_id = 'root'
        
        return _traverse_folder(folder_id)
    
    def find_duplicate_candidates(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find potential duplicate files using multiple strategies
        
        Args:
            files: List of file metadata dictionaries
            
        Returns:
            Dictionary mapping duplicate group IDs to lists of duplicate files
        """
        logger.info("🔍 Analyzing files for duplicates...")
        
        duplicates = {}
        
        # Group by content hash (most reliable)
        hash_groups = {}
        name_groups = {}
        size_groups = {}
        
        for file_data in files:
            content_hash = file_data.get('content_hash')
            file_name = file_data.get('name', '').lower()
            file_size = file_data.get('size', '0')
            
            # Group by hash
            if content_hash:
                if content_hash not in hash_groups:
                    hash_groups[content_hash] = []
                hash_groups[content_hash].append(file_data)
            
            # Group by name (case-insensitive)
            if file_name:
                if file_name not in name_groups:
                    name_groups[file_name] = []
                name_groups[file_name].append(file_data)
            
            # Group by size
            if file_size and file_size != '0':
                if file_size not in size_groups:
                    size_groups[file_size] = []
                size_groups[file_size].append(file_data)
        
        # Find duplicates by hash (highest confidence)
        for content_hash, group in hash_groups.items():
            if len(group) > 1:
                duplicates[f"hash_{content_hash}"] = {
                    'type': 'content_hash',
                    'confidence': 'high',
                    'files': group,
                    'count': len(group)
                }
        
        # Find duplicates by name (medium confidence)
        for file_name, group in name_groups.items():
            if len(group) > 1:
                # Skip if already found by hash
                hash_key = f"hash_{group[0].get('content_hash')}"
                if hash_key not in duplicates:
                    duplicates[f"name_{hashlib.md5(file_name.encode()).hexdigest()[:8]}"] = {
                        'type': 'same_name',
                        'confidence': 'medium',
                        'files': group,
                        'count': len(group)
                    }
        
        # Find duplicates by size (lower confidence, only for larger files)
        for file_size, group in size_groups.items():
            if len(group) > 1 and int(file_size) > 1024 * 1024:  # > 1MB
                # Skip if already found by hash or name
                existing_keys = [k for k in duplicates.keys() if any(
                    f['id'] == group[0]['id'] for f in duplicates[k]['files']
                )]
                if not existing_keys:
                    duplicates[f"size_{file_size}"] = {
                        'type': 'same_size',
                        'confidence': 'low',
                        'files': group,
                        'count': len(group)
                    }
        
        logger.info(f"✅ Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def export_metadata_summary(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive metadata summary"""
        
        summary = {
            'scan_info': {
                'total_files': len(files),
                'scan_timestamp': datetime.now(timezone.utc).isoformat(),
                'fields_collected': len(self.metadata_fields.split(','))
            },
            'file_types': {},
            'size_distribution': {
                'under_1mb': 0,
                'under_10mb': 0,
                'under_100mb': 0,
                'under_1gb': 0,
                'over_1gb': 0
            },
            'age_distribution': {
                'under_week': 0,
                'under_month': 0,
                'under_year': 0,
                'over_year': 0
            },
            'sharing_analysis': {
                'private': 0,
                'shared': 0,
                'public': 0
            },
            'top_owners': {},
            'largest_files': [],
            'oldest_files': [],
            'most_shared_files': []
        }
        
        for file_data in files:
            # File type analysis
            category = file_data.get('file_category', 'unknown')
            summary['file_types'][category] = summary['file_types'].get(category, 0) + 1
            
            # Size distribution
            size_mb = file_data.get('file_size_mb', 0)
            if size_mb < 1:
                summary['size_distribution']['under_1mb'] += 1
            elif size_mb < 10:
                summary['size_distribution']['under_10mb'] += 1
            elif size_mb < 100:
                summary['size_distribution']['under_100mb'] += 1
            elif size_mb < 1000:
                summary['size_distribution']['under_1gb'] += 1
            else:
                summary['size_distribution']['over_1gb'] += 1
            
            # Age distribution
            age_days = file_data.get('file_age_days', 0)
            if age_days < 7:
                summary['age_distribution']['under_week'] += 1
            elif age_days < 30:
                summary['age_distribution']['under_month'] += 1
            elif age_days < 365:
                summary['age_distribution']['under_year'] += 1
            else:
                summary['age_distribution']['over_year'] += 1
            
            # Sharing analysis
            if file_data.get('is_public', False):
                summary['sharing_analysis']['public'] += 1
            elif file_data.get('sharing_status') == 'shared':
                summary['sharing_analysis']['shared'] += 1
            else:
                summary['sharing_analysis']['private'] += 1
            
            # Owner analysis
            owner_email = file_data.get('owner_email', 'Unknown')
            summary['top_owners'][owner_email] = summary['top_owners'].get(owner_email, 0) + 1
        
        # Sort and limit top lists
        summary['top_owners'] = dict(sorted(
            summary['top_owners'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        # Get top files by various metrics
        files_sorted = sorted(files, key=lambda x: x.get('file_size_mb', 0), reverse=True)
        summary['largest_files'] = files_sorted[:10]
        
        files_sorted = sorted(files, key=lambda x: x.get('file_age_days', 0), reverse=True)
        summary['oldest_files'] = files_sorted[:10]
        
        files_sorted = sorted(files, key=lambda x: x.get('permission_count', 0), reverse=True)
        summary['most_shared_files'] = files_sorted[:10]
        
        return summary

if __name__ == "__main__":
    # Demo usage
    try:
        manager = DriveMetadataManager()
        
        # Scan first 50 files for demo
        logger.info("🚀 Starting Drive metadata extraction demo...")
        files = manager.scan_all_drive_files(max_files=50)
        
        # Find duplicates
        duplicates = manager.find_duplicate_candidates(files)
        
        # Generate summary
        summary = manager.export_metadata_summary(files)
        
        # Print results
        print(f"\n📊 Scan Results:")
        print(f"   Files scanned: {len(files)}")
        print(f"   Duplicate groups found: {len(duplicates)}")
        print(f"   File types: {summary['file_types']}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'drive_metadata_{timestamp}.json', 'w') as f:
            json.dump({
                'files': files,
                'duplicates': duplicates,
                'summary': summary
            }, f, indent=2, default=str)
        
        print(f"✅ Results saved to drive_metadata_{timestamp}.json")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")