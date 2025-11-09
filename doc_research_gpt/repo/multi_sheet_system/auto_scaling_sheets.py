#!/usr/bin/env python3
"""
Auto-Scaling Google Sheets Manager
Comprehensive system for managing multiple Google Sheets with automatic overflow and cross-referencing
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging
import math
import time

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoScalingSheetManager:
    """
    Manages multiple Google Sheets with automatic creation when size limits are reached
    Includes comprehensive cross-referencing and metadata tracking
    """
    
    # Google Sheets limits
    MAX_CELLS_PER_SHEET = 2000000  # 2M cells limit
    MAX_ROWS_PER_SHEET = 1000000   # 1M rows limit
    MAX_COLUMNS_PER_SHEET = 18278  # Column limit (A to ZZZ)
    SAFE_CELL_LIMIT = 1800000      # Safe limit (90% of max)
    SAFE_ROW_LIMIT = 900000        # Safe row limit (90% of max)
    
    def __init__(self, credentials_file: str = 'service_account.json', 
                 base_sheet_name: str = "Drive_Metadata_Tracking"):
        """
        Initialize the auto-scaling sheet manager
        
        Args:
            credentials_file: Path to service account JSON file
            base_sheet_name: Base name for the sheet series
        """
        self.credentials_file = credentials_file
        self.base_sheet_name = base_sheet_name
        self.gc = None
        self.sheets_service = None
        self._setup_services()
        
        # Track active sheets
        self.sheet_registry = {
            'sheets': [],
            'current_sheet_index': 0,
            'total_rows_used': 0,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        # Define standard column schema for metadata tracking
        self.metadata_columns = [
            'file_id', 'name', 'mimeType', 'size', 'file_size_mb', 
            'createdTime', 'modifiedTime', 'file_age_days', 'last_modified_days',
            'owner_email', 'owner_name', 'sharing_status', 'is_public',
            'parent_folders', 'parent_folder_ids', 'permission_count',
            'file_category', 'fileExtension', 'content_hash',
            'md5Checksum', 'sha1Checksum', 'sha256Checksum',
            'webViewLink', 'webContentLink', 'thumbnailLink',
            'trashed', 'version', 'scan_timestamp', 'sheet_id', 'row_number'
        ]
        
        # Cross-reference columns for duplicate tracking
        self.duplicate_columns = [
            'duplicate_group_id', 'duplicate_type', 'confidence_level',
            'original_file_id', 'duplicate_file_ids', 'duplicate_count',
            'total_size_mb', 'potential_savings_mb', 'recommendation',
            'last_verified', 'notes'
        ]
        
    def _setup_services(self):
        """Setup Google Sheets API services"""
        try:
            # Setup gspread
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
            self.gc = gspread.authorize(creds)
            
            # Setup Sheets API v4
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 
                       'https://www.googleapis.com/auth/drive']
            )
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            
            logger.info("✅ Google Sheets services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Sheets services: {e}")
            raise
    
    def create_new_sheet(self, suffix: str = None) -> Dict[str, Any]:
        """
        Create a new Google Sheet with proper structure and formatting
        
        Args:
            suffix: Optional suffix for sheet name
            
        Returns:
            Dictionary with sheet information
        """
        if suffix is None:
            suffix = f"_{len(self.sheet_registry['sheets']) + 1:03d}"
        
        sheet_name = f"{self.base_sheet_name}{suffix}"
        
        logger.info(f"📊 Creating new sheet: {sheet_name}")
        
        try:
            # Create the spreadsheet
            spreadsheet = self.gc.create(sheet_name)
            
            # Get the first worksheet and rename it
            main_worksheet = spreadsheet.get_worksheet(0)
            main_worksheet.update_title("File_Metadata")
            
            # Create additional worksheets
            duplicates_worksheet = spreadsheet.add_worksheet("Duplicate_Analysis", 1000, len(self.duplicate_columns))
            summary_worksheet = spreadsheet.add_worksheet("Summary_Stats", 100, 10)
            cross_ref_worksheet = spreadsheet.add_worksheet("Cross_References", 10000, 5)
            
            # Setup headers for main worksheet
            main_worksheet.update('1:1', [self.metadata_columns])
            
            # Setup headers for duplicates worksheet
            duplicates_worksheet.update('1:1', [self.duplicate_columns])
            
            # Setup cross-reference headers
            cross_ref_worksheet.update('1:1', [
                ['sheet_name', 'sheet_id', 'row_range', 'file_count', 'last_updated']
            ])
            
            # Format headers
            self._format_sheet_headers(spreadsheet.id, main_worksheet.id)
            self._format_sheet_headers(spreadsheet.id, duplicates_worksheet.id)
            self._format_sheet_headers(spreadsheet.id, summary_worksheet.id)
            self._format_sheet_headers(spreadsheet.id, cross_ref_worksheet.id)
            
            # Create sheet info
            sheet_info = {
                'name': sheet_name,
                'id': spreadsheet.id,
                'url': spreadsheet.url,
                'worksheets': {
                    'main': {
                        'id': main_worksheet.id,
                        'name': 'File_Metadata',
                        'rows_used': 1,  # Header row
                        'max_rows': self.SAFE_ROW_LIMIT
                    },
                    'duplicates': {
                        'id': duplicates_worksheet.id,
                        'name': 'Duplicate_Analysis',
                        'rows_used': 1
                    },
                    'summary': {
                        'id': summary_worksheet.id,
                        'name': 'Summary_Stats',
                        'rows_used': 0
                    },
                    'cross_ref': {
                        'id': cross_ref_worksheet.id,
                        'name': 'Cross_References',
                        'rows_used': 1
                    }
                },
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'active'
            }
            
            # Add to registry
            self.sheet_registry['sheets'].append(sheet_info)
            
            # Update cross-references in all sheets
            self._update_cross_references()
            
            logger.info(f"✅ Sheet created successfully: {sheet_name}")
            return sheet_info
            
        except Exception as e:
            logger.error(f"❌ Failed to create sheet {sheet_name}: {e}")
            raise
    
    def _format_sheet_headers(self, spreadsheet_id: str, worksheet_id: int):
        """Apply formatting to sheet headers"""
        try:
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": worksheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                                "textFormat": {
                                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                                    "bold": True
                                },
                                "horizontalAlignment": "CENTER"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": worksheet_id,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to format headers: {e}")
    
    def get_current_sheet(self) -> Dict[str, Any]:
        """Get the current active sheet for data entry"""
        if not self.sheet_registry['sheets']:
            return self.create_new_sheet()
        
        current_sheet = self.sheet_registry['sheets'][self.sheet_registry['current_sheet_index']]
        
        # Check if current sheet is near capacity
        main_worksheet = current_sheet['worksheets']['main']
        if main_worksheet['rows_used'] >= main_worksheet['max_rows']:
            logger.info("📈 Current sheet near capacity, creating new sheet...")
            new_sheet = self.create_new_sheet()
            self.sheet_registry['current_sheet_index'] = len(self.sheet_registry['sheets']) - 1
            return new_sheet
        
        return current_sheet
    
    def add_file_data(self, file_data: List[Dict[str, Any]], 
                     batch_size: int = 1000) -> Dict[str, Any]:
        """
        Add file metadata to sheets with automatic overflow management
        
        Args:
            file_data: List of file metadata dictionaries
            batch_size: Number of rows to process per batch
            
        Returns:
            Summary of data insertion
        """
        logger.info(f"📝 Adding {len(file_data)} files to sheets...")
        
        total_added = 0
        sheets_used = []
        
        # Process in batches
        for i in range(0, len(file_data), batch_size):
            batch = file_data[i:i + batch_size]
            
            # Get current sheet (may create new one if needed)
            current_sheet = self.get_current_sheet()
            sheets_used.append(current_sheet['name'])
            
            # Prepare data for insertion
            rows_to_add = []
            for file_info in batch:
                # Add sheet tracking info
                file_info['sheet_id'] = current_sheet['id']
                file_info['row_number'] = current_sheet['worksheets']['main']['rows_used'] + len(rows_to_add) + 1
                
                # Create row data in column order
                row_data = []
                for col in self.metadata_columns:
                    value = file_info.get(col, '')
                    # Convert datetime objects to strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_data.append(str(value))
                
                rows_to_add.append(row_data)
            
            # Insert batch into sheet
            try:
                spreadsheet = self.gc.open_by_key(current_sheet['id'])
                main_worksheet = spreadsheet.worksheet('File_Metadata')
                
                # Calculate insert range
                start_row = current_sheet['worksheets']['main']['rows_used'] + 1
                end_row = start_row + len(rows_to_add) - 1
                range_name = f'A{start_row}:Z{end_row}'
                
                # Insert data
                main_worksheet.update(range_name, rows_to_add)
                
                # Update sheet info
                current_sheet['worksheets']['main']['rows_used'] += len(rows_to_add)
                total_added += len(rows_to_add)
                
                logger.info(f"   ✅ Batch {i//batch_size + 1}: {len(rows_to_add)} rows added to {current_sheet['name']}")
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Failed to add batch to sheet: {e}")
                continue
        
        # Update registry
        self.sheet_registry['total_rows_used'] += total_added
        self.sheet_registry['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Update summary statistics
        self._update_summary_stats()
        
        summary = {
            'files_processed': len(file_data),
            'rows_added': total_added,
            'sheets_used': list(set(sheets_used)),
            'total_sheets': len(self.sheet_registry['sheets']),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ Data insertion complete: {total_added} rows added across {len(set(sheets_used))} sheets")
        return summary
    
    def add_duplicate_analysis(self, duplicates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add duplicate analysis results to dedicated worksheet
        
        Args:
            duplicates: Dictionary of duplicate groups from duplicate detection
            
        Returns:
            Summary of duplicate insertion
        """
        logger.info(f"🔍 Adding {len(duplicates)} duplicate groups to analysis sheets...")
        
        total_added = 0
        
        for group_id, group_data in duplicates.items():
            # Get current sheet
            current_sheet = self.get_current_sheet()
            
            try:
                spreadsheet = self.gc.open_by_key(current_sheet['id'])
                duplicates_worksheet = spreadsheet.worksheet('Duplicate_Analysis')
                
                # Prepare duplicate row data
                files = group_data['files']
                original_file = files[0]  # First file as "original"
                duplicate_file_ids = [f['id'] for f in files[1:]]
                
                total_size = sum(float(f.get('size', 0)) for f in files)
                potential_savings = total_size * (len(files) - 1) / len(files)  # Estimate savings
                
                row_data = [
                    group_id,
                    group_data['type'],
                    group_data['confidence'],
                    original_file['id'],
                    ','.join(duplicate_file_ids),
                    len(files),
                    total_size / (1024 * 1024),  # Convert to MB
                    potential_savings / (1024 * 1024),  # Convert to MB
                    self._get_duplicate_recommendation(group_data),
                    datetime.now(timezone.utc).isoformat(),
                    f"Found {len(files)} duplicates of '{original_file.get('name', 'Unknown')}'"
                ]
                
                # Find next empty row
                next_row = len(duplicates_worksheet.get_all_values()) + 1
                range_name = f'A{next_row}:K{next_row}'
                
                duplicates_worksheet.update(range_name, [row_data])
                total_added += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to add duplicate group {group_id}: {e}")
                continue
        
        summary = {
            'duplicate_groups_added': total_added,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ Duplicate analysis complete: {total_added} groups added")
        return summary
    
    def _get_duplicate_recommendation(self, group_data: Dict[str, Any]) -> str:
        """Generate recommendation for handling duplicates"""
        confidence = group_data['confidence']
        duplicate_type = group_data['type']
        
        if confidence == 'high' and duplicate_type == 'content_hash':
            return "SAFE_TO_DELETE - Identical content confirmed"
        elif confidence == 'medium' and duplicate_type == 'same_name':
            return "REVIEW_REQUIRED - Same name, verify content"
        elif confidence == 'low':
            return "MANUAL_REVIEW - Low confidence, needs inspection"
        else:
            return "INVESTIGATE - Unknown duplicate pattern"
    
    def _update_summary_stats(self):
        """Update summary statistics in all sheets"""
        logger.info("📊 Updating summary statistics...")
        
        try:
            # Calculate overall statistics
            total_files = sum(sheet['worksheets']['main']['rows_used'] - 1 
                            for sheet in self.sheet_registry['sheets'])
            
            stats_data = [
                ['Metric', 'Value', 'Last Updated'],
                ['Total Files Tracked', total_files, datetime.now(timezone.utc).isoformat()],
                ['Total Sheets', len(self.sheet_registry['sheets']), ''],
                ['Active Sheet', self.sheet_registry['sheets'][self.sheet_registry['current_sheet_index']]['name'] if self.sheet_registry['sheets'] else 'None', ''],
                ['System Status', 'Active', ''],
                ['Last Scan', self.sheet_registry['last_updated'], '']
            ]
            
            # Update summary in all sheets
            for sheet_info in self.sheet_registry['sheets']:
                try:
                    spreadsheet = self.gc.open_by_key(sheet_info['id'])
                    summary_worksheet = spreadsheet.worksheet('Summary_Stats')
                    summary_worksheet.update('A1:C6', stats_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update summary in {sheet_info['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to update summary statistics: {e}")
    
    def _update_cross_references(self):
        """Update cross-reference information across all sheets"""
        logger.info("🔗 Updating cross-references...")
        
        try:
            cross_ref_data = [['sheet_name', 'sheet_id', 'row_range', 'file_count', 'last_updated']]
            
            for sheet_info in self.sheet_registry['sheets']:
                main_ws = sheet_info['worksheets']['main']
                file_count = max(0, main_ws['rows_used'] - 1)  # Exclude header
                
                cross_ref_data.append([
                    sheet_info['name'],
                    sheet_info['id'],
                    f"A2:Z{main_ws['rows_used']}" if main_ws['rows_used'] > 1 else "No data",
                    file_count,
                    sheet_info.get('created_at', '')
                ])
            
            # Update cross-references in all sheets
            for sheet_info in self.sheet_registry['sheets']:
                try:
                    spreadsheet = self.gc.open_by_key(sheet_info['id'])
                    cross_ref_worksheet = spreadsheet.worksheet('Cross_References')
                    cross_ref_worksheet.clear()
                    cross_ref_worksheet.update('A1', cross_ref_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update cross-ref in {sheet_info['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to update cross-references: {e}")
    
    def get_sheet_registry(self) -> Dict[str, Any]:
        """Get current sheet registry information"""
        return self.sheet_registry.copy()
    
    def find_file_location(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Find which sheet and row contains a specific file
        
        Args:
            file_id: Google Drive file ID to find
            
        Returns:
            Location information or None if not found
        """
        for sheet_info in self.sheet_registry['sheets']:
            try:
                spreadsheet = self.gc.open_by_key(sheet_info['id'])
                main_worksheet = spreadsheet.worksheet('File_Metadata')
                
                # Find file_id column
                headers = main_worksheet.row_values(1)
                if 'file_id' in headers:
                    file_id_col = headers.index('file_id') + 1
                    
                    # Search for file ID
                    file_ids = main_worksheet.col_values(file_id_col)
                    if file_id in file_ids:
                        row_num = file_ids.index(file_id) + 1
                        return {
                            'sheet_name': sheet_info['name'],
                            'sheet_id': sheet_info['id'],
                            'row_number': row_num,
                            'sheet_url': f"https://docs.google.com/spreadsheets/d/{sheet_info['id']}/edit#gid={sheet_info['worksheets']['main']['id']}&range=A{row_num}"
                        }
                        
            except Exception as e:
                logger.warning(f"⚠️ Error searching in sheet {sheet_info['name']}: {e}")
                continue
        
        return None
    
    def export_registry(self, filename: str = None) -> str:
        """
        Export sheet registry to JSON file
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sheet_registry_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.sheet_registry, f, indent=2, default=str)
        
        logger.info(f"✅ Sheet registry exported to {filename}")
        return filename

if __name__ == "__main__":
    # Demo usage
    try:
        manager = AutoScalingSheetManager()
        
        # Create initial sheet
        logger.info("🚀 Creating initial sheet...")
        sheet_info = manager.create_new_sheet("_Demo")
        
        print(f"✅ Demo sheet created: {sheet_info['name']}")
        print(f"   URL: {sheet_info['url']}")
        print(f"   Worksheets: {list(sheet_info['worksheets'].keys())}")
        
        # Export registry
        registry_file = manager.export_registry()
        print(f"📄 Registry exported to: {registry_file}")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")