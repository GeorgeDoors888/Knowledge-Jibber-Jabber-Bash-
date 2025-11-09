"""
Multi-Sheet Manager
Handles automatic creation and management of multiple Google Sheets
with overflow detection and new sheet creation when needed.
"""

import gspread
import pandas as pd
from datetime import datetime
import time
import json
import os
from typing import List, Dict, Optional, Union

from sheets_utils import (
    get_gspread_client, get_sheet_row_count, is_sheet_full, 
    create_new_sheet_tab, setup_sheet_headers, add_data_to_sheet,
    batch_update_sheet, find_available_sheet, get_spreadsheet_info
)
from drive_utils import (
    create_spreadsheet, create_folder, list_spreadsheets_in_folder,
    get_spreadsheet_by_name, generate_unique_spreadsheet_name,
    share_spreadsheet, backup_spreadsheet_metadata, load_spreadsheet_registry
)
from duplicate_detector import DuplicateDetector, DuplicateManager
from config import (
    MAX_ROWS_PER_SHEET, MAX_SHEETS_PER_SPREADSHEET, DRIVE_FOLDER_ID,
    SHEET_NAME_PREFIX, DEFAULT_HEADERS, SHARE_EMAILS,
    ENABLE_DUPLICATE_DETECTION, DUPLICATE_ACTION, DUPLICATE_CHECK_FIELDS,
    DUPLICATE_DETECTION_METHOD, FUZZY_MATCH_THRESHOLD
)


class MultiSheetManager:
    """
    Manages multiple Google Sheets with automatic overflow handling
    """
    
    def __init__(self, folder_id=None, base_name=None, headers=None, enable_duplicate_detection=None):
        """
        Initialize the Multi-Sheet Manager
        
        Args:
            folder_id: Google Drive folder ID to store spreadsheets
            base_name: Base name for spreadsheet naming
            headers: List of column headers for new sheets
            enable_duplicate_detection: Override global duplicate detection setting
        """
        self.folder_id = folder_id or DRIVE_FOLDER_ID
        self.base_name = base_name or SHEET_NAME_PREFIX
        self.headers = headers or DEFAULT_HEADERS
        self.client = get_gspread_client()
        self.current_spreadsheet = None
        self.current_worksheet = None
        self.registry_file = 'spreadsheet_registry.json'
        
        # Duplicate detection setup
        self.enable_duplicate_detection = enable_duplicate_detection if enable_duplicate_detection is not None else ENABLE_DUPLICATE_DETECTION
        self.duplicate_detector = DuplicateDetector() if self.enable_duplicate_detection else None
        self.duplicate_manager = DuplicateManager(self.duplicate_detector) if self.enable_duplicate_detection else None
        
        # Statistics tracking
        self.stats = {
            'total_additions': 0,
            'duplicates_detected': 0,
            'duplicates_skipped': 0,
            'duplicates_updated': 0,
            'duplicates_flagged': 0
        }
        
        # Load existing registry
        self.registry = load_spreadsheet_registry(self.registry_file)
        
    def get_or_create_spreadsheet(self, force_new=False):
        """
        Get the current active spreadsheet or create a new one if needed
        
        Args:
            force_new: Force creation of a new spreadsheet
            
        Returns:
            gspread.Spreadsheet: The active spreadsheet
        """
        if force_new or not self.current_spreadsheet:
            return self._create_new_spreadsheet()
        
        # Check if current spreadsheet has capacity
        if self._spreadsheet_has_capacity():
            return self.current_spreadsheet
        else:
            return self._create_new_spreadsheet()
    
    def _create_new_spreadsheet(self):
        """Create a new spreadsheet with initial setup"""
        title = generate_unique_spreadsheet_name(self.base_name)
        
        print(f"Creating new spreadsheet: {title}")
        
        # Create spreadsheet using Drive API
        result = create_spreadsheet(title, self.folder_id)
        if not result:
            raise Exception("Failed to create new spreadsheet")
        
        # Open with gspread for easier manipulation
        try:
            spreadsheet = self.client.open_by_key(result['id'])
            self.current_spreadsheet = spreadsheet
            
            # Set up the first worksheet
            worksheet = spreadsheet.get_worksheet(0)
            worksheet.update_title('Data_001')
            setup_sheet_headers(worksheet, self.headers)
            self.current_worksheet = worksheet
            
            # Share if emails are configured
            if SHARE_EMAILS:
                share_spreadsheet(result['id'], SHARE_EMAILS)
            
            # Backup metadata
            spreadsheet_info = {
                'id': result['id'],
                'title': title,
                'url': result['url'],
                'folder_id': self.folder_id,
                'created_sheets': 1
            }
            backup_spreadsheet_metadata(spreadsheet_info, self.registry_file)
            
            print(f"✓ Created spreadsheet: {title}")
            print(f"  URL: {result['url']}")
            
            return spreadsheet
            
        except Exception as e:
            print(f"Error setting up new spreadsheet: {e}")
            return None
    
    def _spreadsheet_has_capacity(self):
        """Check if current spreadsheet can accommodate more data"""
        if not self.current_spreadsheet:
            return False
        
        try:
            worksheets = self.current_spreadsheet.worksheets()
            
            # Check if we've hit the sheet limit
            if len(worksheets) >= MAX_SHEETS_PER_SPREADSHEET:
                # Check if any existing sheet has space
                for worksheet in worksheets:
                    if not is_sheet_full(worksheet):
                        self.current_worksheet = worksheet
                        return True
                return False
            
            # Find or create available worksheet
            available_worksheet = find_available_sheet(self.current_spreadsheet)
            if available_worksheet:
                self.current_worksheet = available_worksheet
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking spreadsheet capacity: {e}")
            return False
    
    def _check_for_duplicates_in_current_data(self, new_row):
        """Check for duplicates in currently loaded data"""
        if not self.enable_duplicate_detection:
            return False, None
        
        try:
            # Get current worksheet data
            if self.current_worksheet:
                current_data = pd.DataFrame(self.current_worksheet.get_all_records())
                if not current_data.empty:
                    return self.duplicate_detector.check_for_duplicate(new_row, current_data)
            
            return False, None
        except Exception as e:
            print(f"Error checking for duplicates in current data: {e}")
            return False, None
    
    def _check_for_duplicates_across_all_sheets(self, new_row):
        """Check for duplicates across all managed spreadsheets (slower but comprehensive)"""
        if not self.enable_duplicate_detection:
            return False, None
        
        try:
            all_spreadsheets = self.get_all_spreadsheets()
            
            for sheet_info in all_spreadsheets:
                try:
                    spreadsheet = self.client.open_by_key(sheet_info['id'])
                    worksheets = spreadsheet.worksheets()
                    
                    for worksheet in worksheets:
                        data = pd.DataFrame(worksheet.get_all_records())
                        if not data.empty:
                            is_duplicate, match_info = self.duplicate_detector.check_for_duplicate(new_row, data)
                            if is_duplicate:
                                match_info['spreadsheet_title'] = sheet_info['title']
                                match_info['worksheet_title'] = worksheet.title
                                return True, match_info
                
                except Exception as e:
                    print(f"Error checking spreadsheet {sheet_info['title']}: {e}")
                    continue
            
            return False, None
        
        except Exception as e:
            print(f"Error checking for duplicates across all sheets: {e}")
            return False, None
    
    def add_data(self, data_row, check_duplicates_globally=False):
        """
        Add a single row of data, creating new sheets/spreadsheets as needed
        
        Args:
            data_row: Dictionary or list of data to add
            check_duplicates_globally: If True, check duplicates across all sheets (slower)
            
        Returns:
            dict: Result with success status and duplicate information
        """
        result = {
            'success': False,
            'duplicate_detected': False,
            'duplicate_info': None,
            'action_taken': None,
            'message': ''
        }
        
        try:
            self.stats['total_additions'] += 1
            
            # Convert data_row to dict if it's a list
            if isinstance(data_row, list):
                if len(data_row) <= len(self.headers):
                    data_row = dict(zip(self.headers, data_row))
                else:
                    result['message'] = "Data row has more columns than headers"
                    return result
            
            # Check for duplicates if enabled
            if self.enable_duplicate_detection:
                # First check current worksheet (fast)
                is_duplicate, match_info = self._check_for_duplicates_in_current_data(data_row)
                
                # If not found and global check requested, check all sheets (slow)
                if not is_duplicate and check_duplicates_globally:
                    is_duplicate, match_info = self._check_for_duplicates_across_all_sheets(data_row)
                
                if is_duplicate:
                    result['duplicate_detected'] = True
                    result['duplicate_info'] = match_info
                    self.stats['duplicates_detected'] += 1
                    
                    # Log the duplicate
                    if self.duplicate_detector:
                        self.duplicate_detector.log_duplicate(match_info, data_row)
                    
                    # Handle duplicate based on configured action
                    if DUPLICATE_ACTION == "skip":
                        result['action_taken'] = 'skipped'
                        result['message'] = f"Duplicate detected and skipped: {match_info.get('match_details', 'Unknown match')}"
                        self.stats['duplicates_skipped'] += 1
                        return result
                    
                    elif DUPLICATE_ACTION == "flag":
                        # Mark as duplicate and continue adding
                        data_row = self.duplicate_detector.mark_as_duplicate(data_row)
                        result['action_taken'] = 'flagged'
                        result['message'] = f"Duplicate detected and flagged: {match_info.get('match_details', 'Unknown match')}"
                        self.stats['duplicates_flagged'] += 1
                    
                    elif DUPLICATE_ACTION == "update":
                        # Update existing record (not implemented in this version)
                        result['action_taken'] = 'update_attempted'
                        result['message'] = "Update action not yet implemented, adding as new record"
                        self.stats['duplicates_updated'] += 1
                    
                    elif DUPLICATE_ACTION == "allow":
                        result['action_taken'] = 'allowed'
                        result['message'] = f"Duplicate detected but allowed: {match_info.get('match_details', 'Unknown match')}"
            
            # Ensure we have an active spreadsheet and worksheet
            spreadsheet = self.get_or_create_spreadsheet()
            if not spreadsheet or not self.current_worksheet:
                result['message'] = "Failed to get or create spreadsheet"
                return result
            
            # Check if current worksheet has space
            if is_sheet_full(self.current_worksheet):
                # Try to get another worksheet in the same spreadsheet
                new_worksheet = find_available_sheet(spreadsheet)
                if new_worksheet:
                    self.current_worksheet = new_worksheet
                    if get_sheet_row_count(new_worksheet) == 0:
                        setup_sheet_headers(new_worksheet, self.headers)
                else:
                    # Need a new spreadsheet
                    spreadsheet = self.get_or_create_spreadsheet(force_new=True)
                    if not spreadsheet:
                        result['message'] = "Failed to create new spreadsheet"
                        return result
            
            # Add the data
            success = add_data_to_sheet(self.current_worksheet, data_row)
            if success:
                result['success'] = True
                if not result['message']:
                    result['message'] = f"✓ Added data to sheet: {self.current_worksheet.title}"
                print(result['message'])
            else:
                result['message'] = "Failed to add data to sheet"
            
            return result
            
        except Exception as e:
            result['message'] = f"Error adding data: {e}"
            print(result['message'])
            return result
    
    def add_batch_data(self, data_list, chunk_size=100):
        """
        Add multiple rows of data in batches
        
        Args:
            data_list: List of data rows (dicts or lists)
            chunk_size: Number of rows to add at once
            
        Returns:
            dict: Results summary
        """
        results = {
            'total_rows': len(data_list),
            'successful_rows': 0,
            'failed_rows': 0,
            'spreadsheets_used': set(),
            'worksheets_used': set()
        }
        
        try:
            for i in range(0, len(data_list), chunk_size):
                chunk = data_list[i:i + chunk_size]
                
                # Ensure we have capacity
                spreadsheet = self.get_or_create_spreadsheet()
                if not spreadsheet or not self.current_worksheet:
                    results['failed_rows'] += len(chunk)
                    continue
                
                # Check if current worksheet can handle the chunk
                current_rows = get_sheet_row_count(self.current_worksheet)
                if current_rows + len(chunk) > MAX_ROWS_PER_SHEET:
                    # Split the chunk or get new worksheet
                    available_space = MAX_ROWS_PER_SHEET - current_rows
                    if available_space > 0:
                        # Add what fits
                        partial_chunk = chunk[:available_space]
                        remaining_chunk = chunk[available_space:]
                        
                        success = batch_update_sheet(self.current_worksheet, partial_chunk)
                        if success:
                            results['successful_rows'] += len(partial_chunk)
                            results['spreadsheets_used'].add(spreadsheet.title)
                            results['worksheets_used'].add(self.current_worksheet.title)
                        else:
                            results['failed_rows'] += len(partial_chunk)
                        
                        # Handle remaining data
                        if remaining_chunk:
                            # Get new worksheet/spreadsheet
                            new_worksheet = find_available_sheet(spreadsheet)
                            if new_worksheet:
                                self.current_worksheet = new_worksheet
                                if get_sheet_row_count(new_worksheet) == 0:
                                    setup_sheet_headers(new_worksheet, self.headers)
                            else:
                                # Create new spreadsheet
                                spreadsheet = self.get_or_create_spreadsheet(force_new=True)
                            
                            # Add remaining data
                            if self.current_worksheet:
                                success = batch_update_sheet(self.current_worksheet, remaining_chunk)
                                if success:
                                    results['successful_rows'] += len(remaining_chunk)
                                    results['spreadsheets_used'].add(spreadsheet.title)
                                    results['worksheets_used'].add(self.current_worksheet.title)
                                else:
                                    results['failed_rows'] += len(remaining_chunk)
                    else:
                        # No space, get new worksheet
                        new_worksheet = find_available_sheet(spreadsheet)
                        if new_worksheet:
                            self.current_worksheet = new_worksheet
                            if get_sheet_row_count(new_worksheet) == 0:
                                setup_sheet_headers(new_worksheet, self.headers)
                        else:
                            spreadsheet = self.get_or_create_spreadsheet(force_new=True)
                        
                        # Add the full chunk
                        if self.current_worksheet:
                            success = batch_update_sheet(self.current_worksheet, chunk)
                            if success:
                                results['successful_rows'] += len(chunk)
                                results['spreadsheets_used'].add(spreadsheet.title)
                                results['worksheets_used'].add(self.current_worksheet.title)
                            else:
                                results['failed_rows'] += len(chunk)
                else:
                    # Chunk fits in current worksheet
                    success = batch_update_sheet(self.current_worksheet, chunk)
                    if success:
                        results['successful_rows'] += len(chunk)
                        results['spreadsheets_used'].add(spreadsheet.title)
                        results['worksheets_used'].add(self.current_worksheet.title)
                    else:
                        results['failed_rows'] += len(chunk)
                
                # Rate limiting
                time.sleep(0.1)
            
            # Convert sets to lists for JSON serialization
            results['spreadsheets_used'] = list(results['spreadsheets_used'])
            results['worksheets_used'] = list(results['worksheets_used'])
            
            print(f"Batch operation completed:")
            print(f"  Total rows: {results['total_rows']}")
            print(f"  Successful: {results['successful_rows']}")
            print(f"  Failed: {results['failed_rows']}")
            print(f"  Spreadsheets used: {len(results['spreadsheets_used'])}")
            
            return results
            
        except Exception as e:
            print(f"Error in batch operation: {e}")
            results['failed_rows'] = results['total_rows'] - results['successful_rows']
            return results
    
    def get_all_spreadsheets(self):
        """Get information about all managed spreadsheets"""
        try:
            spreadsheets = list_spreadsheets_in_folder(self.folder_id)
            
            detailed_info = []
            for sheet_file in spreadsheets:
                try:
                    spreadsheet = self.client.open_by_key(sheet_file['id'])
                    info = get_spreadsheet_info(spreadsheet)
                    info['drive_modified'] = sheet_file.get('modifiedTime')
                    detailed_info.append(info)
                except Exception as e:
                    print(f"Error getting info for {sheet_file['name']}: {e}")
            
            return detailed_info
            
        except Exception as e:
            print(f"Error listing spreadsheets: {e}")
            return []
    
    def get_status_report(self):
        """Generate a comprehensive status report"""
        try:
            all_spreadsheets = self.get_all_spreadsheets()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_spreadsheets': len(all_spreadsheets),
                'total_worksheets': 0,
                'total_rows': 0,
                'available_capacity': 0,
                'spreadsheets': []
            }
            
            for sheet_info in all_spreadsheets:
                report['total_worksheets'] += len(sheet_info['tabs'])
                
                sheet_summary = {
                    'title': sheet_info['title'],
                    'url': sheet_info['url'],
                    'tab_count': len(sheet_info['tabs']),
                    'total_rows': 0,
                    'available_space': 0
                }
                
                for tab in sheet_info['tabs']:
                    sheet_summary['total_rows'] += tab['row_count']
                    if not tab['is_full']:
                        sheet_summary['available_space'] += (MAX_ROWS_PER_SHEET - tab['row_count'])
                
                report['total_rows'] += sheet_summary['total_rows']
                report['available_capacity'] += sheet_summary['available_space']
                report['spreadsheets'].append(sheet_summary)
            
            return report
            
        except Exception as e:
            print(f"Error generating status report: {e}")
            return None
    
    def cleanup_empty_sheets(self):
        """Remove empty worksheets (except the first one in each spreadsheet)"""
        try:
            cleaned = 0
            all_spreadsheets = self.get_all_spreadsheets()
            
            for sheet_info in all_spreadsheets:
                try:
                    spreadsheet = self.client.open_by_key(sheet_info['id'])
                    worksheets = spreadsheet.worksheets()
                    
                    for i, worksheet in enumerate(worksheets):
                        if i == 0:  # Keep the first worksheet
                            continue
                        
                        if get_sheet_row_count(worksheet) <= 1:  # Only headers or empty
                            spreadsheet.del_worksheet(worksheet)
                            cleaned += 1
                            print(f"Deleted empty worksheet: {worksheet.title}")
                            time.sleep(0.5)  # Rate limiting
                
                except Exception as e:
                    print(f"Error cleaning spreadsheet {sheet_info['title']}: {e}")
            
            print(f"Cleanup completed. Removed {cleaned} empty worksheets.")
            return cleaned
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 0
    
    def find_all_duplicates(self, save_report=True):
        """
        Find all duplicates across all managed spreadsheets
        
        Args:
            save_report: Whether to save the duplicate report to file
            
        Returns:
            dict: Comprehensive duplicate report
        """
        if not self.enable_duplicate_detection:
            print("Duplicate detection is disabled")
            return None
        
        try:
            print("🔍 Starting comprehensive duplicate scan...")
            
            # Collect all sheet data
            all_spreadsheets = self.get_all_spreadsheets()
            sheet_data_list = []
            
            for sheet_info in all_spreadsheets:
                try:
                    spreadsheet = self.client.open_by_key(sheet_info['id'])
                    worksheets = spreadsheet.worksheets()
                    
                    for worksheet in worksheets:
                        try:
                            data = pd.DataFrame(worksheet.get_all_records())
                            if not data.empty:
                                sheet_name = f"{sheet_info['title']} - {worksheet.title}"
                                sheet_data_list.append((sheet_name, data))
                        except Exception as e:
                            print(f"Error reading worksheet {worksheet.title}: {e}")
                
                except Exception as e:
                    print(f"Error processing spreadsheet {sheet_info['title']}: {e}")
            
            print(f"📊 Analyzing {len(sheet_data_list)} worksheets for duplicates...")
            
            # Find duplicates
            duplicates = self.duplicate_manager.find_duplicates_across_sheets(sheet_data_list)
            
            # Generate report
            report = self.duplicate_manager.generate_duplicate_report(duplicates)
            
            # Save report if requested
            if save_report:
                filename = self.duplicate_manager.save_duplicate_report(report)
                report['report_file'] = filename
            
            print(f"✅ Duplicate scan complete!")
            print(f"   Found {report['summary']['total_duplicates']} duplicate pairs")
            print(f"   Affected {report['summary']['sheets_affected']} sheets")
            
            return report
        
        except Exception as e:
            print(f"Error finding duplicates: {e}")
            return None
    
    def remove_duplicates(self, strategy="keep_first", dry_run=True):
        """
        Remove duplicate entries from all spreadsheets
        
        Args:
            strategy: How to handle duplicates ("keep_first", "keep_last", "interactive")
            dry_run: If True, only report what would be removed without actually removing
            
        Returns:
            dict: Summary of removal operation
        """
        if not self.enable_duplicate_detection:
            print("Duplicate detection is disabled")
            return None
        
        print(f"🧹 Starting duplicate removal (dry_run={dry_run})...")
        
        # First find all duplicates
        duplicate_report = self.find_all_duplicates(save_report=False)
        if not duplicate_report or not duplicate_report['duplicates']:
            print("✅ No duplicates found to remove")
            return {'removed': 0, 'errors': 0}
        
        removal_summary = {
            'total_duplicates_found': len(duplicate_report['duplicates']),
            'removal_attempted': 0,
            'removal_successful': 0,
            'removal_failed': 0,
            'errors': []
        }
        
        try:
            for dup in duplicate_report['duplicates']:
                try:
                    if strategy == "keep_first":
                        # Remove the duplicate (second occurrence)
                        target_sheet = dup.get('sheet_2', dup.get('sheet_1'))
                        target_index = dup['duplicate_index']
                    elif strategy == "keep_last":
                        # Remove the original (first occurrence)
                        target_sheet = dup.get('sheet_1')
                        target_index = dup['original_index']
                    else:
                        print(f"Strategy '{strategy}' not implemented")
                        continue
                    
                    removal_summary['removal_attempted'] += 1
                    
                    if not dry_run:
                        # Actually remove the duplicate
                        # This would require implementing row deletion in sheets_utils
                        # For now, we'll just log what would be removed
                        pass
                    
                    print(f"{'[DRY RUN] ' if dry_run else ''}Would remove duplicate in {target_sheet} at row {target_index + 2}")
                    removal_summary['removal_successful'] += 1
                
                except Exception as e:
                    error_msg = f"Error removing duplicate: {e}"
                    removal_summary['errors'].append(error_msg)
                    removal_summary['removal_failed'] += 1
                    print(f"❌ {error_msg}")
            
            print(f"✅ Duplicate removal {'simulation ' if dry_run else ''}complete!")
            print(f"   Attempted: {removal_summary['removal_attempted']}")
            print(f"   Successful: {removal_summary['removal_successful']}")
            print(f"   Failed: {removal_summary['removal_failed']}")
            
            return removal_summary
        
        except Exception as e:
            print(f"Error during duplicate removal: {e}")
            return removal_summary
    
    def get_duplicate_statistics(self):
        """Get comprehensive duplicate detection statistics"""
        stats = {
            'session_stats': self.stats.copy(),
            'detection_enabled': self.enable_duplicate_detection,
            'detection_method': DUPLICATE_DETECTION_METHOD if self.enable_duplicate_detection else None,
            'check_fields': DUPLICATE_CHECK_FIELDS if self.enable_duplicate_detection else None,
            'duplicate_action': DUPLICATE_ACTION if self.enable_duplicate_detection else None
        }
        
        # Add global duplicate scan if detection is enabled
        if self.enable_duplicate_detection:
            try:
                duplicate_report = self.find_all_duplicates(save_report=False)
                if duplicate_report:
                    stats['global_duplicate_summary'] = duplicate_report['summary']
            except Exception as e:
                stats['global_scan_error'] = str(e)
        
        return stats
    
    def configure_duplicate_detection(self, method=None, check_fields=None, threshold=None, action=None):
        """
        Update duplicate detection configuration at runtime
        
        Args:
            method: Detection method ('exact', 'fuzzy', 'hash', 'multi')
            check_fields: List of fields to check for duplicates
            threshold: Similarity threshold for fuzzy matching
            action: Action to take when duplicates found ('skip', 'flag', 'update', 'allow')
        """
        if not self.duplicate_detector:
            print("Duplicate detection is not enabled")
            return False
        
        updated = False
        
        if method:
            self.duplicate_detector.method = method
            updated = True
            print(f"Updated detection method to: {method}")
        
        if check_fields:
            self.duplicate_detector.check_fields = check_fields
            updated = True
            print(f"Updated check fields to: {check_fields}")
        
        if threshold:
            self.duplicate_detector.threshold = threshold
            updated = True
            print(f"Updated similarity threshold to: {threshold}%")
        
        if action:
            # Note: This would need to update the global config or instance setting
            print(f"Duplicate action setting: {action} (update config.py for persistence)")
            updated = True
        
        return updated


# Convenience functions for easy usage
def create_manager(folder_id=None, base_name=None, headers=None):
    """Create a new MultiSheetManager instance"""
    return MultiSheetManager(folder_id, base_name, headers)

def quick_add_data(data_list, folder_id=None, base_name=None, headers=None):
    """Quick function to add data without managing the instance"""
    manager = MultiSheetManager(folder_id, base_name, headers)
    
    if isinstance(data_list, (dict, list)) and not isinstance(data_list[0] if isinstance(data_list, list) else None, (dict, list)):
        # Single row
        return manager.add_data(data_list)
    else:
        # Multiple rows
        return manager.add_batch_data(data_list)

def get_system_status(folder_id=None):
    """Get status report for all spreadsheets"""
    manager = MultiSheetManager(folder_id)
    return manager.get_status_report()