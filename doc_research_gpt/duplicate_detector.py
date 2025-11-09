"""
Duplicate Detection Utilities
Provides various methods for detecting and handling duplicate entries
across Google Sheets with fuzzy matching, hash-based detection, and exact matching.
"""

import hashlib
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Union
import difflib
from fuzzywuzzy import fuzz, process
import re

from config import (
    DUPLICATE_CHECK_FIELDS, DUPLICATE_DETECTION_METHOD, FUZZY_MATCH_THRESHOLD,
    ENABLE_FUZZY_TITLE_MATCHING, TITLE_SIMILARITY_THRESHOLD, 
    ENABLE_CONTENT_HASH, CONTENT_FIELDS_FOR_HASH,
    CREATE_DUPLICATE_LOG, DUPLICATE_LOG_FILE,
    ADD_DUPLICATE_MARKER, DUPLICATE_MARKER_PREFIX
)


class DuplicateDetector:
    """
    Handles duplicate detection using various strategies
    """
    
    def __init__(self, check_fields=None, method=None, threshold=None):
        """
        Initialize duplicate detector
        
        Args:
            check_fields: List of fields to check for duplicates
            method: Detection method ('exact', 'fuzzy', 'hash', 'multi')
            threshold: Similarity threshold for fuzzy matching (0-100)
        """
        self.check_fields = check_fields or DUPLICATE_CHECK_FIELDS
        self.method = method or DUPLICATE_DETECTION_METHOD
        self.threshold = threshold or FUZZY_MATCH_THRESHOLD
        self.duplicate_log = []
        
    def normalize_text(self, text):
        """Normalize text for comparison"""
        if not text or pd.isna(text):
            return ""
        
        # Convert to string and strip whitespace
        text = str(text).strip().lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common punctuation for better matching
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def generate_content_hash(self, row_data, fields=None):
        """Generate a hash from specified content fields"""
        if fields is None:
            fields = CONTENT_FIELDS_FOR_HASH
        
        # Collect content from specified fields
        content_parts = []
        for field in fields:
            if field in row_data and row_data[field]:
                normalized = self.normalize_text(row_data[field])
                if normalized:
                    content_parts.append(normalized)
        
        # Create hash from combined content
        if content_parts:
            combined_content = "|".join(sorted(content_parts))
            return hashlib.md5(combined_content.encode('utf-8')).hexdigest()
        
        return None
    
    def generate_record_key(self, row_data):
        """Generate a unique key for duplicate detection"""
        key_parts = []
        
        for field in self.check_fields:
            if field in row_data and row_data[field]:
                normalized = self.normalize_text(row_data[field])
                if normalized:
                    key_parts.append(f"{field}:{normalized}")
        
        return "|".join(key_parts) if key_parts else None
    
    def exact_match(self, new_row, existing_data):
        """Check for exact matches in key fields"""
        new_key = self.generate_record_key(new_row)
        if not new_key:
            return False, None
        
        for idx, existing_row in existing_data.iterrows():
            existing_key = self.generate_record_key(existing_row.to_dict())
            if existing_key == new_key:
                return True, {
                    'match_type': 'exact',
                    'match_score': 100,
                    'matched_row_index': idx,
                    'matched_fields': self.check_fields,
                    'match_details': f"Exact match on key: {new_key}"
                }
        
        return False, None
    
    def fuzzy_match(self, new_row, existing_data):
        """Check for fuzzy matches using similarity scoring"""
        new_key = self.generate_record_key(new_row)
        if not new_key:
            return False, None
        
        best_match = None
        best_score = 0
        best_index = None
        
        for idx, existing_row in existing_data.iterrows():
            existing_key = self.generate_record_key(existing_row.to_dict())
            if not existing_key:
                continue
            
            # Calculate similarity score
            score = fuzz.ratio(new_key, existing_key)
            
            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = existing_row.to_dict()
                best_index = idx
        
        if best_match:
            return True, {
                'match_type': 'fuzzy',
                'match_score': best_score,
                'matched_row_index': best_index,
                'matched_fields': self.check_fields,
                'match_details': f"Fuzzy match (score: {best_score}%) on key fields"
            }
        
        return False, None
    
    def title_similarity_match(self, new_row, existing_data):
        """Check for similar titles using fuzzy matching"""
        if not ENABLE_FUZZY_TITLE_MATCHING:
            return False, None
        
        title_field = "Document Title"
        if title_field not in new_row or not new_row[title_field]:
            return False, None
        
        new_title = self.normalize_text(new_row[title_field])
        if not new_title:
            return False, None
        
        best_match = None
        best_score = 0
        best_index = None
        
        for idx, existing_row in existing_data.iterrows():
            if title_field not in existing_row or not existing_row[title_field]:
                continue
            
            existing_title = self.normalize_text(existing_row[title_field])
            if not existing_title:
                continue
            
            # Calculate title similarity
            score = fuzz.ratio(new_title, existing_title)
            
            if score > best_score and score >= TITLE_SIMILARITY_THRESHOLD:
                best_score = score
                best_match = existing_row.to_dict()
                best_index = idx
        
        if best_match:
            return True, {
                'match_type': 'title_similarity',
                'match_score': best_score,
                'matched_row_index': best_index,
                'matched_fields': [title_field],
                'match_details': f"Similar title (score: {best_score}%): '{new_title}' vs '{self.normalize_text(best_match[title_field])}'"
            }
        
        return False, None
    
    def content_hash_match(self, new_row, existing_data):
        """Check for content hash matches"""
        if not ENABLE_CONTENT_HASH:
            return False, None
        
        new_hash = self.generate_content_hash(new_row)
        if not new_hash:
            return False, None
        
        for idx, existing_row in existing_data.iterrows():
            existing_hash = self.generate_content_hash(existing_row.to_dict())
            if existing_hash == new_hash:
                return True, {
                    'match_type': 'content_hash',
                    'match_score': 100,
                    'matched_row_index': idx,
                    'matched_fields': CONTENT_FIELDS_FOR_HASH,
                    'match_details': f"Content hash match: {new_hash}"
                }
        
        return False, None
    
    def check_for_duplicate(self, new_row, existing_data):
        """
        Check if a new row is a duplicate of existing data
        
        Args:
            new_row: Dictionary of new row data
            existing_data: DataFrame of existing data
            
        Returns:
            tuple: (is_duplicate, match_info)
        """
        if existing_data is None or existing_data.empty:
            return False, None
        
        # Convert new_row to ensure consistent format
        if isinstance(new_row, list):
            # Assume it matches the column order
            if not existing_data.empty:
                new_row = dict(zip(existing_data.columns, new_row))
            else:
                return False, None
        
        # Try different matching strategies based on method
        if self.method == "exact":
            return self.exact_match(new_row, existing_data)
        
        elif self.method == "fuzzy":
            is_dup, match_info = self.fuzzy_match(new_row, existing_data)
            if is_dup:
                return is_dup, match_info
            
            # Also check title similarity if enabled
            return self.title_similarity_match(new_row, existing_data)
        
        elif self.method == "hash":
            return self.content_hash_match(new_row, existing_data)
        
        elif self.method == "multi":
            # Try multiple strategies, return first match found
            strategies = [
                self.exact_match,
                self.fuzzy_match,
                self.title_similarity_match,
                self.content_hash_match
            ]
            
            for strategy in strategies:
                try:
                    is_dup, match_info = strategy(new_row, existing_data)
                    if is_dup:
                        return is_dup, match_info
                except Exception as e:
                    continue  # Skip failed strategies
            
            return False, None
        
        else:
            # Default to exact match
            return self.exact_match(new_row, existing_data)
    
    def log_duplicate(self, duplicate_info, new_row, existing_row=None):
        """Log duplicate detection information"""
        if not CREATE_DUPLICATE_LOG:
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'match_type': duplicate_info.get('match_type'),
            'match_score': duplicate_info.get('match_score'),
            'matched_fields': duplicate_info.get('matched_fields'),
            'match_details': duplicate_info.get('match_details'),
            'new_row_data': new_row,
            'existing_row_data': existing_row.to_dict() if existing_row is not None else None
        }
        
        self.duplicate_log.append(log_entry)
        
        # Save to file
        try:
            # Load existing log
            existing_log = []
            try:
                with open(DUPLICATE_LOG_FILE, 'r') as f:
                    existing_log = json.load(f)
            except FileNotFoundError:
                pass
            
            # Append new entry
            existing_log.append(log_entry)
            
            # Save updated log
            with open(DUPLICATE_LOG_FILE, 'w') as f:
                json.dump(existing_log, f, indent=2)
        
        except Exception as e:
            print(f"Error saving duplicate log: {e}")
    
    def mark_as_duplicate(self, row_data):
        """Mark row data as duplicate by adding prefix"""
        if not ADD_DUPLICATE_MARKER:
            return row_data
        
        marked_data = row_data.copy()
        
        # Add duplicate marker to primary identifier fields
        for field in self.check_fields:
            if field in marked_data and marked_data[field]:
                if not str(marked_data[field]).startswith(DUPLICATE_MARKER_PREFIX):
                    marked_data[field] = f"{DUPLICATE_MARKER_PREFIX}{marked_data[field]}"
        
        # Add duplicate flag if not already present
        if "Duplicate_Flag" not in marked_data:
            marked_data["Duplicate_Flag"] = "TRUE"
        
        if "Duplicate_Detected_Date" not in marked_data:
            marked_data["Duplicate_Detected_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return marked_data


class DuplicateManager:
    """
    Manages duplicate detection and cleanup across multiple sheets
    """
    
    def __init__(self, detector=None):
        """Initialize duplicate manager"""
        self.detector = detector or DuplicateDetector()
    
    def find_duplicates_in_dataframe(self, df):
        """Find all duplicate rows within a single DataFrame"""
        if df.empty:
            return []
        
        duplicates = []
        processed_indices = set()
        
        for i, row in df.iterrows():
            if i in processed_indices:
                continue
            
            row_dict = row.to_dict()
            
            # Check against remaining rows
            for j, other_row in df.iloc[i+1:].iterrows():
                if j in processed_indices:
                    continue
                
                is_dup, match_info = self.detector.check_for_duplicate(
                    row_dict, 
                    pd.DataFrame([other_row])
                )
                
                if is_dup:
                    duplicates.append({
                        'original_index': i,
                        'duplicate_index': j,
                        'match_info': match_info,
                        'original_row': row_dict,
                        'duplicate_row': other_row.to_dict()
                    })
                    processed_indices.add(j)
        
        return duplicates
    
    def find_duplicates_across_sheets(self, sheet_data_list):
        """Find duplicates across multiple sheets"""
        all_duplicates = []
        
        # First find duplicates within each sheet
        for sheet_idx, (sheet_name, df) in enumerate(sheet_data_list):
            internal_duplicates = self.find_duplicates_in_dataframe(df)
            for dup in internal_duplicates:
                dup['sheet_1'] = sheet_name
                dup['sheet_2'] = sheet_name
                all_duplicates.append(dup)
        
        # Then find duplicates across different sheets
        for i in range(len(sheet_data_list)):
            for j in range(i + 1, len(sheet_data_list)):
                sheet1_name, df1 = sheet_data_list[i]
                sheet2_name, df2 = sheet_data_list[j]
                
                cross_sheet_duplicates = self.find_cross_sheet_duplicates(
                    df1, df2, sheet1_name, sheet2_name
                )
                all_duplicates.extend(cross_sheet_duplicates)
        
        return all_duplicates
    
    def find_cross_sheet_duplicates(self, df1, df2, sheet1_name, sheet2_name):
        """Find duplicates between two different sheets"""
        duplicates = []
        
        for i, row1 in df1.iterrows():
            row1_dict = row1.to_dict()
            
            is_dup, match_info = self.detector.check_for_duplicate(row1_dict, df2)
            
            if is_dup:
                matched_row = df2.iloc[match_info['matched_row_index']]
                duplicates.append({
                    'original_index': i,
                    'duplicate_index': match_info['matched_row_index'],
                    'match_info': match_info,
                    'original_row': row1_dict,
                    'duplicate_row': matched_row.to_dict(),
                    'sheet_1': sheet1_name,
                    'sheet_2': sheet2_name
                })
        
        return duplicates
    
    def generate_duplicate_report(self, duplicates):
        """Generate a comprehensive duplicate report"""
        if not duplicates:
            return {
                'summary': {
                    'total_duplicates': 0,
                    'duplicate_pairs': 0,
                    'sheets_affected': 0,
                    'match_types': {}
                },
                'duplicates': []
            }
        
        # Analyze duplicates
        match_types = {}
        sheets_affected = set()
        
        for dup in duplicates:
            match_type = dup['match_info']['match_type']
            match_types[match_type] = match_types.get(match_type, 0) + 1
            
            sheets_affected.add(dup.get('sheet_1', 'Unknown'))
            sheets_affected.add(dup.get('sheet_2', 'Unknown'))
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_duplicates': len(duplicates),
                'duplicate_pairs': len(duplicates),  # Each entry represents a pair
                'sheets_affected': len(sheets_affected),
                'match_types': match_types,
                'affected_sheets': list(sheets_affected)
            },
            'duplicates': duplicates
        }
        
        return report
    
    def save_duplicate_report(self, report, filename=None):
        """Save duplicate report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"Duplicate report saved to: {filename}")
            return filename
        
        except Exception as e:
            print(f"Error saving duplicate report: {e}")
            return None


# Convenience functions
def detect_duplicate(new_row, existing_data, method=None, threshold=None):
    """Quick function to detect if a row is duplicate"""
    detector = DuplicateDetector(method=method, threshold=threshold)
    return detector.check_for_duplicate(new_row, existing_data)

def find_all_duplicates(sheet_data_list):
    """Quick function to find all duplicates across multiple sheets"""
    manager = DuplicateManager()
    return manager.find_duplicates_across_sheets(sheet_data_list)

def generate_duplicate_report(duplicates, save_to_file=True):
    """Quick function to generate and optionally save duplicate report"""
    manager = DuplicateManager()
    report = manager.generate_duplicate_report(duplicates)
    
    if save_to_file:
        manager.save_duplicate_report(report)
    
    return report