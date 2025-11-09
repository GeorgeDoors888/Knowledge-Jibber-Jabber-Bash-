#!/usr/bin/env python3
"""
Advanced Duplicate Detection System
Multi-layered approach for comprehensive duplicate file identification
"""

import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
from pathlib import Path
import re
from collections import defaultdict
import difflib

try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available - some fuzzy matching features disabled")

import Levenshtein
from imagehash import phash, average_hash, dhash, whash
from PIL import Image
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedDuplicateDetector:
    """
    Comprehensive duplicate detection system using multiple algorithms and strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the duplicate detector with configurable parameters
        
        Args:
            config: Configuration dictionary for detection thresholds
        """
        self.config = config or self._get_default_config()
        
        # Detection strategies and their weights
        self.detection_strategies = {
            'exact_hash': {'weight': 1.0, 'confidence': 'high'},
            'content_similarity': {'weight': 0.9, 'confidence': 'high'},
            'name_similarity': {'weight': 0.6, 'confidence': 'medium'},
            'size_similarity': {'weight': 0.3, 'confidence': 'low'},
            'metadata_similarity': {'weight': 0.7, 'confidence': 'medium'},
            'image_similarity': {'weight': 0.8, 'confidence': 'high'},
            'semantic_similarity': {'weight': 0.5, 'confidence': 'medium'}
        }
        
        # File type handlers
        self.file_type_handlers = {
            'image': self._detect_image_duplicates,
            'document': self._detect_document_duplicates,
            'video': self._detect_video_duplicates,
            'audio': self._detect_audio_duplicates,
            'code': self._detect_code_duplicates,
            'other': self._detect_generic_duplicates
        }
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for duplicate detection"""
        return {
            'name_similarity_threshold': 80,
            'fuzzy_match_threshold': 85,
            'size_variance_threshold': 0.1,  # 10% variance allowed
            'image_hash_threshold': 5,
            'content_similarity_threshold': 90,
            'metadata_weight_threshold': 0.7,
            'min_file_size_mb': 0.1,  # Ignore very small files
            'enable_fuzzy_matching': FUZZY_AVAILABLE,
            'enable_image_analysis': True,
            'enable_content_analysis': True,
            'max_comparison_group_size': 1000
        }
    
    def detect_all_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive duplicate detection using all available strategies
        
        Args:
            files: List of file metadata dictionaries
            
        Returns:
            Comprehensive duplicate analysis results
        """
        logger.info(f"🔍 Starting comprehensive duplicate detection on {len(files)} files...")
        
        # Filter files by minimum size if configured
        min_size = self.config['min_file_size_mb'] * 1024 * 1024
        filtered_files = [f for f in files if float(f.get('size', 0)) >= min_size]
        
        logger.info(f"   Analyzing {len(filtered_files)} files (filtered by min size)")
        
        # Group files by category for optimized detection
        file_groups = self._group_files_by_category(filtered_files)
        
        all_duplicates = {}
        detection_stats = {
            'total_files_analyzed': len(filtered_files),
            'files_by_category': {cat: len(files) for cat, files in file_groups.items()},
            'strategies_used': [],
            'total_duplicate_groups': 0,
            'total_duplicates_found': 0,
            'potential_space_saved_mb': 0
        }
        
        # Apply detection strategies by file category
        for category, category_files in file_groups.items():
            if not category_files:
                continue
                
            logger.info(f"   🔍 Analyzing {category} files: {len(category_files)} items")
            
            # Get appropriate handler for this file category
            handler = self.file_type_handlers.get(category, self._detect_generic_duplicates)
            
            try:
                category_duplicates = handler(category_files)
                
                # Merge results with unique keys
                for group_id, group_data in category_duplicates.items():
                    unique_key = f"{category}_{group_id}"
                    all_duplicates[unique_key] = group_data
                    all_duplicates[unique_key]['category'] = category
                    
                logger.info(f"      ✅ Found {len(category_duplicates)} duplicate groups in {category}")
                
            except Exception as e:
                logger.error(f"❌ Error detecting duplicates in {category}: {e}")
                continue
        
        # Apply cross-category detection for potential matches
        cross_category_duplicates = self._detect_cross_category_duplicates(file_groups)
        for group_id, group_data in cross_category_duplicates.items():
            all_duplicates[f"cross_{group_id}"] = group_data
        
        # Calculate statistics
        detection_stats['total_duplicate_groups'] = len(all_duplicates)
        detection_stats['total_duplicates_found'] = sum(
            group['duplicate_count'] for group in all_duplicates.values()
        )
        detection_stats['potential_space_saved_mb'] = sum(
            group.get('potential_savings_mb', 0) for group in all_duplicates.values()
        )
        
        # Rank duplicates by confidence and potential savings
        ranked_duplicates = self._rank_duplicate_groups(all_duplicates)
        
        # Generate detailed analysis report
        analysis_report = self._generate_analysis_report(all_duplicates, detection_stats)
        
        logger.info(f"✅ Duplicate detection complete:")
        logger.info(f"   Groups found: {detection_stats['total_duplicate_groups']}")
        logger.info(f"   Total duplicates: {detection_stats['total_duplicates_found']}")
        logger.info(f"   Potential savings: {detection_stats['potential_space_saved_mb']:.2f} MB")
        
        return {
            'duplicates': all_duplicates,
            'ranked_duplicates': ranked_duplicates,
            'statistics': detection_stats,
            'analysis_report': analysis_report,
            'detection_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _group_files_by_category(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group files by category for optimized detection"""
        groups = defaultdict(list)
        
        for file_data in files:
            category = file_data.get('file_category', 'other')
            groups[category].append(file_data)
        
        return dict(groups)
    
    def _detect_image_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicates among image files using perceptual hashing"""
        duplicates = {}
        
        if not self.config['enable_image_analysis']:
            logger.info("   Image analysis disabled, using generic detection")
            return self._detect_generic_duplicates(files)
        
        logger.info(f"   🖼️  Analyzing {len(files)} image files...")
        
        # First, try exact hash matching
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Then, try perceptual hash matching for remaining files
        try:
            perceptual_duplicates = self._find_perceptual_image_duplicates(files)
            duplicates.update(perceptual_duplicates)
        except Exception as e:
            logger.warning(f"⚠️ Perceptual image analysis failed: {e}")
        
        return duplicates
    
    def _find_perceptual_image_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find image duplicates using perceptual hashing"""
        duplicates = {}
        
        # Calculate perceptual hashes for images with thumbnails
        image_hashes = {}
        
        for file_data in files:
            thumbnail_link = file_data.get('thumbnailLink')
            if not thumbnail_link:
                continue
                
            try:
                # Download and process thumbnail
                response = requests.get(thumbnail_link, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    
                    # Calculate multiple hash types
                    hashes = {
                        'phash': str(phash(image)),
                        'ahash': str(average_hash(image)),
                        'dhash': str(dhash(image)),
                        'whash': str(whash(image))
                    }
                    
                    image_hashes[file_data['id']] = {
                        'file_data': file_data,
                        'hashes': hashes
                    }
                    
            except Exception as e:
                logger.debug(f"Failed to process image {file_data.get('name', 'Unknown')}: {e}")
                continue
        
        # Compare perceptual hashes
        threshold = self.config['image_hash_threshold']
        processed_ids = set()
        
        for file_id1, data1 in image_hashes.items():
            if file_id1 in processed_ids:
                continue
                
            similar_files = [data1['file_data']]
            
            for file_id2, data2 in image_hashes.items():
                if file_id2 == file_id1 or file_id2 in processed_ids:
                    continue
                
                # Compare all hash types
                hash_distances = []
                for hash_type in ['phash', 'ahash', 'dhash', 'whash']:
                    if hash_type in data1['hashes'] and hash_type in data2['hashes']:
                        distance = Levenshtein.hamming(data1['hashes'][hash_type], data2['hashes'][hash_type])
                        hash_distances.append(distance)
                
                if hash_distances:
                    avg_distance = sum(hash_distances) / len(hash_distances)
                    if avg_distance <= threshold:
                        similar_files.append(data2['file_data'])
                        processed_ids.add(file_id2)
            
            if len(similar_files) > 1:
                group_id = f"perceptual_{hashlib.md5(file_id1.encode()).hexdigest()[:8]}"
                duplicates[group_id] = {
                    'type': 'perceptual_image',
                    'confidence': 'high',
                    'files': similar_files,
                    'duplicate_count': len(similar_files),
                    'detection_method': 'perceptual_hashing',
                    'avg_hash_distance': sum(hash_distances) / len(hash_distances) if hash_distances else 0
                }
                
            processed_ids.add(file_id1)
        
        return duplicates
    
    def _detect_document_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicates among document files"""
        logger.info(f"   📄 Analyzing {len(files)} document files...")
        
        duplicates = {}
        
        # Exact hash matching first
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Name and size similarity
        similarity_duplicates = self._find_name_size_similarity_matches(files)
        duplicates.update(similarity_duplicates)
        
        # Content analysis for Google Docs (if API access available)
        if self.config['enable_content_analysis']:
            content_duplicates = self._find_content_similarity_matches(files)
            duplicates.update(content_duplicates)
        
        return duplicates
    
    def _detect_video_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicates among video files"""
        logger.info(f"   🎥 Analyzing {len(files)} video files...")
        
        # For videos, rely heavily on size and hash matching
        duplicates = {}
        
        # Exact matches
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Size-based matching (more reliable for videos)
        size_duplicates = self._find_size_based_matches(files, strict=True)
        duplicates.update(size_duplicates)
        
        return duplicates
    
    def _detect_audio_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicates among audio files"""
        logger.info(f"   🎵 Analyzing {len(files)} audio files...")
        
        duplicates = {}
        
        # Exact hash matching
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Name similarity (common for music files)
        name_duplicates = self._find_fuzzy_name_matches(files)
        duplicates.update(name_duplicates)
        
        return duplicates
    
    def _detect_code_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicates among code files"""
        logger.info(f"   💻 Analyzing {len(files)} code files...")
        
        duplicates = {}
        
        # Exact hash matching
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Name-based matching (common for similar code files)
        name_duplicates = self._find_fuzzy_name_matches(files, threshold=95)
        duplicates.update(name_duplicates)
        
        return duplicates
    
    def _detect_generic_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generic duplicate detection for other file types"""
        logger.info(f"   📋 Analyzing {len(files)} files with generic detection...")
        
        duplicates = {}
        
        # Exact hash matching
        hash_duplicates = self._find_exact_hash_matches(files)
        duplicates.update(hash_duplicates)
        
        # Name similarity
        name_duplicates = self._find_fuzzy_name_matches(files)
        duplicates.update(name_duplicates)
        
        # Size similarity
        size_duplicates = self._find_size_based_matches(files)
        duplicates.update(size_duplicates)
        
        return duplicates
    
    def _find_exact_hash_matches(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find files with identical content hashes"""
        duplicates = {}
        hash_groups = defaultdict(list)
        
        for file_data in files:
            # Check multiple hash types
            content_hash = None
            for hash_field in ['sha256Checksum', 'sha1Checksum', 'md5Checksum', 'content_hash']:
                if file_data.get(hash_field):
                    content_hash = file_data[hash_field]
                    break
            
            if content_hash:
                hash_groups[content_hash].append(file_data)
        
        for content_hash, group in hash_groups.items():
            if len(group) > 1:
                total_size = sum(float(f.get('size', 0)) for f in group)
                potential_savings = total_size * (len(group) - 1) / (1024 * 1024)
                
                duplicates[f"hash_{content_hash[:8]}"] = {
                    'type': 'exact_content',
                    'confidence': 'high',
                    'files': group,
                    'duplicate_count': len(group),
                    'detection_method': 'content_hash',
                    'content_hash': content_hash,
                    'potential_savings_mb': potential_savings
                }
        
        return duplicates
    
    def _find_fuzzy_name_matches(self, files: List[Dict[str, Any]], 
                                threshold: int = None) -> Dict[str, Any]:
        """Find files with similar names using fuzzy matching"""
        if not FUZZY_AVAILABLE:
            return {}
        
        threshold = threshold or self.config['fuzzy_match_threshold']
        duplicates = {}
        processed_files = set()
        
        for i, file1 in enumerate(files):
            if file1['id'] in processed_files:
                continue
            
            name1 = file1.get('name', '').lower()
            if not name1:
                continue
            
            similar_files = [file1]
            
            for j, file2 in enumerate(files[i+1:], i+1):
                if file2['id'] in processed_files:
                    continue
                
                name2 = file2.get('name', '').lower()
                if not name2:
                    continue
                
                # Calculate similarity score
                similarity = fuzz.ratio(name1, name2)
                
                if similarity >= threshold:
                    similar_files.append(file2)
                    processed_files.add(file2['id'])
            
            if len(similar_files) > 1:
                total_size = sum(float(f.get('size', 0)) for f in similar_files)
                potential_savings = total_size * (len(similar_files) - 1) / (1024 * 1024)
                
                group_id = f"fuzzy_{hashlib.md5(name1.encode()).hexdigest()[:8]}"
                duplicates[group_id] = {
                    'type': 'fuzzy_name',
                    'confidence': 'medium',
                    'files': similar_files,
                    'duplicate_count': len(similar_files),
                    'detection_method': 'fuzzy_name_matching',
                    'similarity_threshold': threshold,
                    'potential_savings_mb': potential_savings
                }
            
            processed_files.add(file1['id'])
        
        return duplicates
    
    def _find_size_based_matches(self, files: List[Dict[str, Any]], 
                               strict: bool = False) -> Dict[str, Any]:
        """Find files with identical or very similar sizes"""
        duplicates = {}
        size_groups = defaultdict(list)
        
        # Group by exact size first
        for file_data in files:
            size = file_data.get('size', '0')
            if size and size != '0':
                size_groups[size].append(file_data)
        
        # Find exact size matches
        for size, group in size_groups.items():
            if len(group) > 1:
                # Only consider larger files for size-based matching
                size_mb = int(size) / (1024 * 1024)
                if size_mb > 1.0:  # > 1MB
                    total_size = int(size) * len(group)
                    potential_savings = total_size * (len(group) - 1) / (1024 * 1024)
                    
                    duplicates[f"size_{size}"] = {
                        'type': 'exact_size',
                        'confidence': 'low' if not strict else 'medium',
                        'files': group,
                        'duplicate_count': len(group),
                        'detection_method': 'size_matching',
                        'file_size_mb': size_mb,
                        'potential_savings_mb': potential_savings
                    }
        
        return duplicates
    
    def _find_name_size_similarity_matches(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find files with similar names AND sizes"""
        if not FUZZY_AVAILABLE:
            return self._find_size_based_matches(files)
        
        duplicates = {}
        processed_files = set()
        
        for i, file1 in enumerate(files):
            if file1['id'] in processed_files:
                continue
            
            name1 = file1.get('name', '').lower()
            size1 = float(file1.get('size', 0))
            
            if not name1 or size1 == 0:
                continue
            
            similar_files = [file1]
            
            for j, file2 in enumerate(files[i+1:], i+1):
                if file2['id'] in processed_files:
                    continue
                
                name2 = file2.get('name', '').lower()
                size2 = float(file2.get('size', 0))
                
                if not name2 or size2 == 0:
                    continue
                
                # Check name similarity
                name_similarity = fuzz.ratio(name1, name2)
                
                # Check size similarity
                size_diff = abs(size1 - size2) / max(size1, size2) if max(size1, size2) > 0 else 1
                
                if (name_similarity >= self.config['name_similarity_threshold'] and 
                    size_diff <= self.config['size_variance_threshold']):
                    similar_files.append(file2)
                    processed_files.add(file2['id'])
            
            if len(similar_files) > 1:
                total_size = sum(float(f.get('size', 0)) for f in similar_files)
                potential_savings = total_size * (len(similar_files) - 1) / (1024 * 1024)
                
                group_id = f"namesize_{hashlib.md5((name1 + str(int(size1))).encode()).hexdigest()[:8]}"
                duplicates[group_id] = {
                    'type': 'name_size_similarity',
                    'confidence': 'medium',
                    'files': similar_files,
                    'duplicate_count': len(similar_files),
                    'detection_method': 'name_size_similarity',
                    'potential_savings_mb': potential_savings
                }
            
            processed_files.add(file1['id'])
        
        return duplicates
    
    def _find_content_similarity_matches(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find files with similar content (for documents)"""
        # This would require content extraction from documents
        # For now, return empty - could be enhanced with Google Docs API
        logger.debug("Content similarity matching not implemented yet")
        return {}
    
    def _detect_cross_category_duplicates(self, file_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Detect duplicates across different file categories"""
        logger.info("   🔄 Checking for cross-category duplicates...")
        
        duplicates = {}
        
        # Collect all files for cross-category analysis
        all_files = []
        for files in file_groups.values():
            all_files.extend(files)
        
        # Only check exact hash matches across categories
        hash_duplicates = self._find_exact_hash_matches(all_files)
        
        # Filter to only include cross-category matches
        for group_id, group_data in hash_duplicates.items():
            categories = set(f.get('file_category', 'unknown') for f in group_data['files'])
            if len(categories) > 1:
                duplicates[f"cross_{group_id}"] = group_data
                duplicates[f"cross_{group_id}"]['type'] = 'cross_category'
                duplicates[f"cross_{group_id}"]['categories'] = list(categories)
        
        return duplicates
    
    def _rank_duplicate_groups(self, duplicates: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank duplicate groups by confidence and potential savings"""
        
        confidence_scores = {'high': 3, 'medium': 2, 'low': 1}
        
        ranked_groups = []
        for group_id, group_data in duplicates.items():
            confidence = group_data.get('confidence', 'low')
            potential_savings = group_data.get('potential_savings_mb', 0)
            duplicate_count = group_data.get('duplicate_count', 0)
            
            # Calculate composite score
            score = (
                confidence_scores.get(confidence, 1) * 100 +
                min(potential_savings, 1000) +  # Cap at 1000MB for scoring
                duplicate_count * 10
            )
            
            ranked_groups.append({
                'group_id': group_id,
                'score': score,
                'confidence': confidence,
                'duplicate_count': duplicate_count,
                'potential_savings_mb': potential_savings,
                'type': group_data.get('type', 'unknown'),
                'files': group_data.get('files', [])
            })
        
        # Sort by score (descending)
        ranked_groups.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_groups
    
    def _generate_analysis_report(self, duplicates: Dict[str, Any], 
                                stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        report = {
            'summary': {
                'total_duplicate_groups': len(duplicates),
                'high_confidence_groups': len([g for g in duplicates.values() if g.get('confidence') == 'high']),
                'medium_confidence_groups': len([g for g in duplicates.values() if g.get('confidence') == 'medium']),
                'low_confidence_groups': len([g for g in duplicates.values() if g.get('confidence') == 'low']),
                'total_potential_savings_mb': sum(g.get('potential_savings_mb', 0) for g in duplicates.values()),
                'detection_methods_used': list(set(g.get('detection_method', 'unknown') for g in duplicates.values()))
            },
            'recommendations': [],
            'top_priority_groups': [],
            'statistics': stats
        }
        
        # Generate recommendations
        high_confidence_groups = [g for g in duplicates.values() if g.get('confidence') == 'high']
        if high_confidence_groups:
            total_savings = sum(g.get('potential_savings_mb', 0) for g in high_confidence_groups)
            report['recommendations'].append({
                'priority': 'high',
                'action': 'Review and delete high-confidence duplicates',
                'potential_savings_mb': total_savings,
                'groups_count': len(high_confidence_groups)
            })
        
        # Identify top priority groups (high confidence + large savings)
        sorted_groups = sorted(
            duplicates.items(),
            key=lambda x: (
                1 if x[1].get('confidence') == 'high' else 0,
                x[1].get('potential_savings_mb', 0)
            ),
            reverse=True
        )
        
        report['top_priority_groups'] = [
            {
                'group_id': group_id,
                'type': group_data.get('type'),
                'confidence': group_data.get('confidence'),
                'duplicate_count': group_data.get('duplicate_count'),
                'potential_savings_mb': group_data.get('potential_savings_mb'),
                'sample_files': [f.get('name', 'Unknown') for f in group_data.get('files', [])[:3]]
            }
            for group_id, group_data in sorted_groups[:10]
        ]
        
        return report

if __name__ == "__main__":
    # Demo usage
    try:
        detector = AdvancedDuplicateDetector()
        
        # Sample file data for testing
        sample_files = [
            {
                'id': 'file1',
                'name': 'document.pdf',
                'size': '1048576',
                'file_category': 'document',
                'md5Checksum': 'abc123'
            },
            {
                'id': 'file2', 
                'name': 'document_copy.pdf',
                'size': '1048576',
                'file_category': 'document',
                'md5Checksum': 'abc123'
            }
        ]
        
        results = detector.detect_all_duplicates(sample_files)
        
        print(f"✅ Demo complete:")
        print(f"   Duplicate groups: {results['statistics']['total_duplicate_groups']}")
        print(f"   Total duplicates: {results['statistics']['total_duplicates_found']}")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")