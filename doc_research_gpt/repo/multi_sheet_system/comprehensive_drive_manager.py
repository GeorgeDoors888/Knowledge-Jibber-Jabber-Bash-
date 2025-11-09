#!/usr/bin/env python3
"""
Comprehensive Drive Metadata & Duplicate Management System
Main orchestration system integrating all components
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Import our custom modules
from drive_metadata_manager import DriveMetadataManager
from auto_scaling_sheets import AutoScalingSheetManager
from advanced_duplicate_detector import AdvancedDuplicateDetector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDriveManager:
    """
    Main orchestration system that combines Drive metadata extraction,
    duplicate detection, and auto-scaling Google Sheets management
    """
    
    def __init__(self, config_file: str = 'config.py', credentials_file: str = 'service_account.json'):
        """
        Initialize the comprehensive drive manager
        
        Args:
            config_file: Configuration file path
            credentials_file: Service account credentials file
        """
        self.config = self._load_config(config_file)
        self.credentials_file = credentials_file
        
        # Initialize components
        logger.info("🚀 Initializing Comprehensive Drive Manager...")
        
        try:
            self.drive_manager = DriveMetadataManager(credentials_file)
            self.sheets_manager = AutoScalingSheetManager(
                credentials_file, 
                self.config.get('base_sheet_name', 'Drive_Metadata_Tracking')
            )
            self.duplicate_detector = AdvancedDuplicateDetector(
                self.config.get('duplicate_detection', {})
            )
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
        
        # Tracking and statistics
        self.session_stats = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'files_processed': 0,
            'sheets_created': 0,
            'duplicates_found': 0,
            'total_space_analyzed_mb': 0,
            'potential_savings_mb': 0,
            'operations_completed': []
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from Python file"""
        try:
            if os.path.exists(config_file):
                # Import config as module
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_file)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                # Extract configuration
                config = {}
                for attr in dir(config_module):
                    if not attr.startswith('_'):
                        config[attr] = getattr(config_module, attr)
                
                return config
            else:
                logger.warning(f"Config file {config_file} not found, using defaults")
                return self._get_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'base_sheet_name': 'Drive_Metadata_Tracking',
            'max_files_per_scan': None,
            'include_trashed_files': False,
            'batch_size': 1000,
            'duplicate_detection': {
                'name_similarity_threshold': 85,
                'fuzzy_match_threshold': 90,
                'size_variance_threshold': 0.05,
                'min_file_size_mb': 0.1,
                'enable_fuzzy_matching': True,
                'enable_image_analysis': True,
                'enable_content_analysis': True
            },
            'export_settings': {
                'create_summary_report': True,
                'export_duplicate_details': True,
                'export_file_metadata': True,
                'export_format': 'json'
            }
        }
    
    def run_comprehensive_analysis(self, max_files: Optional[int] = None) -> Dict[str, Any]:
        """
        Run complete analysis: scan Drive, detect duplicates, populate sheets
        
        Args:
            max_files: Maximum number of files to analyze (None for all)
            
        Returns:
            Comprehensive analysis results
        """
        logger.info("🔄 Starting comprehensive Drive analysis...")
        
        analysis_start_time = time.time()
        results = {
            'analysis_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'phases': {},
            'summary': {},
            'files': [],
            'duplicates': {},
            'sheets_info': {}
        }
        
        try:
            # Phase 1: Drive Metadata Extraction
            logger.info("📡 Phase 1: Extracting Drive metadata...")
            phase1_start = time.time()
            
            files = self.drive_manager.scan_all_drive_files(
                include_trashed=self.config.get('include_trashed_files', False),
                max_files=max_files or self.config.get('max_files_per_scan')
            )
            
            results['files'] = files
            results['phases']['metadata_extraction'] = {
                'duration_seconds': time.time() - phase1_start,
                'files_found': len(files),
                'total_size_mb': sum(f.get('file_size_mb', 0) for f in files),
                'status': 'completed'
            }
            
            self.session_stats['files_processed'] = len(files)
            self.session_stats['total_space_analyzed_mb'] = sum(f.get('file_size_mb', 0) for f in files)
            
            logger.info(f"   ✅ Phase 1 complete: {len(files)} files extracted")
            
            # Phase 2: Duplicate Detection
            logger.info("🔍 Phase 2: Advanced duplicate detection...")
            phase2_start = time.time()
            
            duplicate_analysis = self.duplicate_detector.detect_all_duplicates(files)
            
            results['duplicates'] = duplicate_analysis
            results['phases']['duplicate_detection'] = {
                'duration_seconds': time.time() - phase2_start,
                'duplicate_groups': len(duplicate_analysis['duplicates']),
                'total_duplicates': duplicate_analysis['statistics']['total_duplicates_found'],
                'potential_savings_mb': duplicate_analysis['statistics']['potential_space_saved_mb'],
                'status': 'completed'
            }
            
            self.session_stats['duplicates_found'] = duplicate_analysis['statistics']['total_duplicates_found']
            self.session_stats['potential_savings_mb'] = duplicate_analysis['statistics']['potential_space_saved_mb']
            
            logger.info(f"   ✅ Phase 2 complete: {len(duplicate_analysis['duplicates'])} duplicate groups found")
            
            # Phase 3: Google Sheets Population
            logger.info("📊 Phase 3: Populating Google Sheets...")
            phase3_start = time.time()
            
            # Add file metadata to sheets
            file_insertion_summary = self.sheets_manager.add_file_data(
                files, 
                batch_size=self.config.get('batch_size', 1000)
            )
            
            # Add duplicate analysis to sheets
            duplicate_insertion_summary = self.sheets_manager.add_duplicate_analysis(
                duplicate_analysis['duplicates']
            )
            
            # Get sheet registry for results
            sheet_registry = self.sheets_manager.get_sheet_registry()
            
            results['sheets_info'] = {
                'file_insertion': file_insertion_summary,
                'duplicate_insertion': duplicate_insertion_summary,
                'registry': sheet_registry
            }
            
            results['phases']['sheets_population'] = {
                'duration_seconds': time.time() - phase3_start,
                'sheets_used': len(sheet_registry['sheets']),
                'rows_inserted': file_insertion_summary['rows_added'],
                'duplicate_groups_inserted': duplicate_insertion_summary['duplicate_groups_added'],
                'status': 'completed'
            }
            
            self.session_stats['sheets_created'] = len(sheet_registry['sheets'])
            
            logger.info(f"   ✅ Phase 3 complete: {file_insertion_summary['rows_added']} rows added to {len(sheet_registry['sheets'])} sheets")
            
            # Phase 4: Generate Summary and Reports
            logger.info("📋 Phase 4: Generating reports and summaries...")
            phase4_start = time.time()
            
            summary_report = self._generate_comprehensive_summary(
                files, duplicate_analysis, sheet_registry
            )
            
            results['summary'] = summary_report
            results['phases']['report_generation'] = {
                'duration_seconds': time.time() - phase4_start,
                'status': 'completed'
            }
            
            # Calculate total analysis time
            total_duration = time.time() - analysis_start_time
            results['total_duration_seconds'] = total_duration
            results['completion_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Update session stats
            self.session_stats['operations_completed'].append({
                'operation': 'comprehensive_analysis',
                'timestamp': results['completion_timestamp'],
                'duration_seconds': total_duration,
                'files_processed': len(files),
                'duplicates_found': duplicate_analysis['statistics']['total_duplicates_found']
            })
            
            logger.info("🎉 Comprehensive analysis completed successfully!")
            logger.info(f"   Total time: {total_duration:.2f} seconds")
            logger.info(f"   Files analyzed: {len(files)}")
            logger.info(f"   Duplicates found: {duplicate_analysis['statistics']['total_duplicates_found']}")
            logger.info(f"   Potential savings: {duplicate_analysis['statistics']['potential_space_saved_mb']:.2f} MB")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed: {e}")
            results['error'] = str(e)
            results['status'] = 'failed'
            raise
    
    def _generate_comprehensive_summary(self, files: List[Dict[str, Any]], 
                                      duplicate_analysis: Dict[str, Any],
                                      sheet_registry: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        
        # File statistics
        total_files = len(files)
        total_size_mb = sum(f.get('file_size_mb', 0) for f in files)
        
        # File type breakdown
        file_types = {}
        for file_data in files:
            file_type = file_data.get('file_category', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Owner analysis
        owners = {}
        for file_data in files:
            owner = file_data.get('owner_email', 'Unknown')
            owners[owner] = owners.get(owner, 0) + 1
        
        # Duplicate statistics
        duplicate_stats = duplicate_analysis['statistics']
        
        # Sheet information
        sheets_summary = {
            'total_sheets': len(sheet_registry['sheets']),
            'total_rows_used': sheet_registry.get('total_rows_used', 0),
            'sheet_details': [
                {
                    'name': sheet['name'],
                    'id': sheet['id'],
                    'url': sheet['url'],
                    'rows_used': sheet['worksheets']['main']['rows_used']
                }
                for sheet in sheet_registry['sheets']
            ]
        }
        
        # Top recommendations
        recommendations = []
        
        if duplicate_stats['total_duplicates_found'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'duplicates',
                'title': f"Review {duplicate_stats['total_duplicate_groups']} duplicate groups",
                'description': f"Found {duplicate_stats['total_duplicates_found']} duplicate files with potential savings of {duplicate_stats['potential_space_saved_mb']:.2f} MB",
                'action': 'Review duplicate analysis worksheet and delete confirmed duplicates'
            })
        
        if total_size_mb > 1000:  # > 1GB
            recommendations.append({
                'priority': 'medium',
                'category': 'storage',
                'title': 'Large file analysis',
                'description': f"Drive contains {total_size_mb:.2f} MB of files",
                'action': 'Review largest files for archival or deletion opportunities'
            })
        
        # Security recommendations
        public_files = [f for f in files if f.get('is_public', False)]
        if public_files:
            recommendations.append({
                'priority': 'high',
                'category': 'security',
                'title': f"Review {len(public_files)} publicly shared files",
                'description': 'Files with public access may pose security risks',
                'action': 'Review public file sharing settings'
            })
        
        return {
            'analysis_overview': {
                'total_files': total_files,
                'total_size_mb': total_size_mb,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_time_seconds': sum(
                    phase.get('duration_seconds', 0) 
                    for phase in self.session_stats.get('operations_completed', [{}])[-1:] 
                    if isinstance(phase, dict)
                )
            },
            'file_breakdown': {
                'by_type': file_types,
                'by_owner': dict(sorted(owners.items(), key=lambda x: x[1], reverse=True)[:10]),
                'size_distribution': self._calculate_size_distribution(files)
            },
            'duplicate_summary': {
                'total_groups': duplicate_stats['total_duplicate_groups'],
                'total_duplicates': duplicate_stats['total_duplicates_found'],
                'potential_savings_mb': duplicate_stats['potential_space_saved_mb'],
                'high_confidence_groups': len([
                    g for g in duplicate_analysis['duplicates'].values() 
                    if g.get('confidence') == 'high'
                ]),
                'detection_methods': duplicate_stats.get('detection_methods', [])
            },
            'sheets_summary': sheets_summary,
            'recommendations': recommendations,
            'next_steps': [
                'Review duplicate analysis in Google Sheets',
                'Verify high-confidence duplicates before deletion',
                'Set up regular monitoring for new duplicates',
                'Review public file sharing settings',
                'Archive old or large unused files'
            ]
        }
    
    def _calculate_size_distribution(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate file size distribution"""
        distribution = {
            'under_1mb': 0,
            'under_10mb': 0,
            'under_100mb': 0,
            'under_1gb': 0,
            'over_1gb': 0
        }
        
        for file_data in files:
            size_mb = file_data.get('file_size_mb', 0)
            
            if size_mb < 1:
                distribution['under_1mb'] += 1
            elif size_mb < 10:
                distribution['under_10mb'] += 1
            elif size_mb < 100:
                distribution['under_100mb'] += 1
            elif size_mb < 1000:
                distribution['under_1gb'] += 1
            else:
                distribution['over_1gb'] += 1
        
        return distribution
    
    def export_results(self, results: Dict[str, Any], format: str = 'json') -> str:
        """
        Export analysis results to file
        
        Args:
            results: Analysis results dictionary
            format: Export format ('json', 'summary')
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filename = f"drive_analysis_complete_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
                
        elif format == 'summary':
            filename = f"drive_analysis_summary_{timestamp}.txt"
            with open(filename, 'w') as f:
                summary = results.get('summary', {})
                
                f.write("COMPREHENSIVE DRIVE ANALYSIS SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                # Overview
                overview = summary.get('analysis_overview', {})
                f.write(f"Analysis Date: {overview.get('analysis_timestamp', 'Unknown')}\n")
                f.write(f"Total Files: {overview.get('total_files', 0):,}\n")
                f.write(f"Total Size: {overview.get('total_size_mb', 0):.2f} MB\n\n")
                
                # Duplicates
                dup_summary = summary.get('duplicate_summary', {})
                f.write("DUPLICATE ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Duplicate Groups: {dup_summary.get('total_groups', 0)}\n")
                f.write(f"Total Duplicates: {dup_summary.get('total_duplicates', 0)}\n")
                f.write(f"Potential Savings: {dup_summary.get('potential_savings_mb', 0):.2f} MB\n\n")
                
                # Recommendations
                recommendations = summary.get('recommendations', [])
                if recommendations:
                    f.write("RECOMMENDATIONS\n")
                    f.write("-" * 15 + "\n")
                    for i, rec in enumerate(recommendations, 1):
                        f.write(f"{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('title', 'No title')}\n")
                        f.write(f"   {rec.get('description', 'No description')}\n")
                        f.write(f"   Action: {rec.get('action', 'No action specified')}\n\n")
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"✅ Results exported to {filename}")
        return filename
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        self.session_stats['session_duration_seconds'] = (
            datetime.now(timezone.utc) - 
            datetime.fromisoformat(self.session_stats['start_time'].replace('Z', '+00:00'))
        ).total_seconds()
        
        return self.session_stats.copy()

if __name__ == "__main__":
    try:
        # Initialize comprehensive manager
        manager = ComprehensiveDriveManager()
        
        # Run analysis on first 100 files for demo
        logger.info("🚀 Running comprehensive Drive analysis demo...")
        results = manager.run_comprehensive_analysis(max_files=100)
        
        # Export results
        json_file = manager.export_results(results, 'json')
        summary_file = manager.export_results(results, 'summary')
        
        # Print session statistics
        stats = manager.get_session_statistics()
        
        print("\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print("=" * 50)
        print(f"Files Processed: {stats['files_processed']:,}")
        print(f"Sheets Created: {stats['sheets_created']}")
        print(f"Duplicates Found: {stats['duplicates_found']:,}")
        print(f"Space Analyzed: {stats['total_space_analyzed_mb']:.2f} MB")
        print(f"Potential Savings: {stats['potential_savings_mb']:.2f} MB")
        print(f"Session Duration: {stats.get('session_duration_seconds', 0):.1f} seconds")
        print(f"\nResults exported to:")
        print(f"  📄 {json_file}")
        print(f"  📝 {summary_file}")
        
        # Show Google Sheets URLs
        sheets_info = results.get('sheets_info', {})
        registry = sheets_info.get('registry', {})
        if registry.get('sheets'):
            print(f"\n📊 Google Sheets created:")
            for sheet in registry['sheets']:
                print(f"  🔗 {sheet['name']}: {sheet['url']}")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()