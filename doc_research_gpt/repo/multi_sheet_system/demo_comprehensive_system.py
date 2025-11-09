#!/usr/bin/env python3
"""
Comprehensive Drive Metadata Analysis Demo
Demonstration of the complete system with Google Drive API integration,
advanced duplicate detection, and auto-scaling Google Sheets
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from comprehensive_drive_manager import ComprehensiveDriveManager
    from drive_metadata_manager import DriveMetadataManager
    from auto_scaling_sheets import AutoScalingSheetManager
    from advanced_duplicate_detector import AdvancedDuplicateDetector
    import enhanced_config as config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required files are present and dependencies are installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOGGING_CONFIG['level']),
    format=config.LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print demo banner"""
    banner = """
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║    🚀 COMPREHENSIVE GOOGLE DRIVE METADATA ANALYSIS SYSTEM                      ║
║                                                                                ║
║    Features:                                                                   ║
║    📡 Complete Google Drive API metadata extraction                            ║
║    🔍 Advanced multi-algorithm duplicate detection                             ║
║    📊 Auto-scaling Google Sheets with cross-referencing                       ║
║    🔐 Security analysis and sharing pattern detection                          ║
║    📈 Comprehensive reporting and recommendations                              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_section(title: str, description: str = None):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"🔷 {title}")
    if description:
        print(f"   {description}")
    print('='*80)

def validate_prerequisites():
    """Validate that all prerequisites are met"""
    print_section("PREREQUISITE VALIDATION", "Checking system requirements and configuration")
    
    errors = []
    warnings = []
    
    # Check service account file
    if not os.path.exists(config.SERVICE_ACCOUNT_FILE):
        errors.append(f"Service account file not found: {config.SERVICE_ACCOUNT_FILE}")
    else:
        print(f"✅ Service account file found: {config.SERVICE_ACCOUNT_FILE}")
    
    # Check configuration
    config_errors = config.validate_config()
    if config_errors:
        errors.extend(config_errors)
    else:
        print("✅ Configuration validation passed")
    
    # Test Google API connectivity
    try:
        print("🔄 Testing Google API connectivity...")
        manager = DriveMetadataManager(config.SERVICE_ACCOUNT_FILE)
        print("✅ Google Drive API connection successful")
    except Exception as e:
        errors.append(f"Google API connection failed: {e}")
    
    # Check optional dependencies
    try:
        from fuzzywuzzy import fuzz
        print("✅ FuzzyWuzzy available for advanced matching")
    except ImportError:
        warnings.append("FuzzyWuzzy not available - some duplicate detection features disabled")
    
    try:
        from PIL import Image
        print("✅ PIL/Pillow available for image analysis")
    except ImportError:
        warnings.append("PIL/Pillow not available - image duplicate detection disabled")
    
    # Print results
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print("\n❌ Errors found:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease resolve these errors before continuing.")
        return False
    
    print("\n🎉 All prerequisites validated successfully!")
    return True

def demo_drive_metadata_extraction(max_files: int = 50):
    """Demonstrate Google Drive metadata extraction"""
    print_section("DRIVE METADATA EXTRACTION", 
                 f"Extracting comprehensive metadata from up to {max_files} files")
    
    try:
        # Initialize the drive manager
        drive_manager = DriveMetadataManager(config.SERVICE_ACCOUNT_FILE)
        
        # Extract metadata
        start_time = time.time()
        files = drive_manager.scan_all_drive_files(
            include_trashed=config.INCLUDE_TRASHED_FILES,
            max_files=max_files
        )
        extraction_time = time.time() - start_time
        
        # Display results
        print(f"📊 Extraction Results:")
        print(f"   Files found: {len(files):,}")
        print(f"   Extraction time: {extraction_time:.2f} seconds")
        print(f"   Average time per file: {extraction_time/len(files)*1000:.1f} ms")
        
        # Analyze file types
        file_types = {}
        total_size = 0
        for file_data in files:
            file_type = file_data.get('file_category', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_size += file_data.get('file_size_mb', 0)
        
        print(f"\n📁 File Type Distribution:")
        for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {file_type}: {count:,} files")
        
        print(f"\n💾 Storage Analysis:")
        print(f"   Total size: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
        print(f"   Average file size: {total_size/len(files):.2f} MB")
        
        # Show sample metadata
        if files:
            sample_file = files[0]
            print(f"\n📄 Sample File Metadata:")
            print(f"   Name: {sample_file.get('name', 'Unknown')}")
            print(f"   Type: {sample_file.get('mimeType', 'Unknown')}")
            print(f"   Size: {sample_file.get('file_size_mb', 0):.2f} MB")
            print(f"   Created: {sample_file.get('createdTime', 'Unknown')}")
            print(f"   Owner: {sample_file.get('owner_email', 'Unknown')}")
            print(f"   Sharing: {sample_file.get('sharing_status', 'Unknown')}")
        
        return files
        
    except Exception as e:
        logger.error(f"❌ Metadata extraction failed: {e}")
        raise

def demo_duplicate_detection(files: list):
    """Demonstrate advanced duplicate detection"""
    print_section("ADVANCED DUPLICATE DETECTION", 
                 f"Analyzing {len(files)} files for duplicates using multiple algorithms")
    
    try:
        # Initialize duplicate detector
        detector = AdvancedDuplicateDetector(config.DUPLICATE_DETECTION)
        
        # Run detection
        start_time = time.time()
        duplicate_results = detector.detect_all_duplicates(files)
        detection_time = time.time() - start_time
        
        # Extract results
        duplicates = duplicate_results['duplicates']
        statistics = duplicate_results['statistics']
        analysis_report = duplicate_results['analysis_report']
        
        # Display results
        print(f"🔍 Detection Results:")
        print(f"   Analysis time: {detection_time:.2f} seconds")
        print(f"   Files analyzed: {statistics['total_files_analyzed']:,}")
        print(f"   Duplicate groups found: {statistics['total_duplicate_groups']:,}")
        print(f"   Total duplicates: {statistics['total_duplicates_found']:,}")
        print(f"   Potential space savings: {statistics['potential_space_saved_mb']:.2f} MB")
        
        # Show detection methods used
        print(f"\n🛠️  Detection Methods Used:")
        for category, count in statistics['files_by_category'].items():
            if count > 0:
                print(f"   {category}: {count:,} files")
        
        # Show confidence breakdown
        confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
        for group_data in duplicates.values():
            confidence = group_data.get('confidence', 'low')
            confidence_counts[confidence] += 1
        
        print(f"\n📊 Confidence Level Breakdown:")
        for level, count in confidence_counts.items():
            if count > 0:
                print(f"   {level.title()} confidence: {count:,} groups")
        
        # Show top duplicate groups
        ranked_duplicates = duplicate_results.get('ranked_duplicates', [])
        if ranked_duplicates:
            print(f"\n🏆 Top Duplicate Groups:")
            for i, group in enumerate(ranked_duplicates[:5], 1):
                print(f"   {i}. {group['type']} ({group['confidence']} confidence)")
                print(f"      Files: {group['duplicate_count']}, Savings: {group['potential_savings_mb']:.2f} MB")
                if group['files']:
                    sample_names = [f.get('name', 'Unknown') for f in group['files'][:2]]
                    print(f"      Sample: {', '.join(sample_names)}...")
        
        # Show recommendations
        recommendations = analysis_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. [{rec['priority'].upper()}] {rec['action']}")
                if 'potential_savings_mb' in rec:
                    print(f"      Potential savings: {rec['potential_savings_mb']:.2f} MB")
        
        return duplicate_results
        
    except Exception as e:
        logger.error(f"❌ Duplicate detection failed: {e}")
        raise

def demo_auto_scaling_sheets(files: list, duplicates: dict):
    """Demonstrate auto-scaling Google Sheets management"""
    print_section("AUTO-SCALING GOOGLE SHEETS", 
                 f"Creating sheets and populating with {len(files)} files")
    
    try:
        # Initialize sheets manager
        sheets_manager = AutoScalingSheetManager(
            config.SERVICE_ACCOUNT_FILE,
            f"{config.BASE_SHEET_NAME}_Demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Add file data to sheets
        print("📝 Adding file metadata to sheets...")
        start_time = time.time()
        file_summary = sheets_manager.add_file_data(files, batch_size=config.BATCH_SIZE)
        file_time = time.time() - start_time
        
        print(f"   ✅ File data added: {file_summary['rows_added']:,} rows in {file_time:.2f}s")
        print(f"   Sheets used: {len(file_summary['sheets_used'])}")
        
        # Add duplicate analysis
        print("🔍 Adding duplicate analysis to sheets...")
        start_time = time.time()
        duplicate_summary = sheets_manager.add_duplicate_analysis(duplicates)
        duplicate_time = time.time() - start_time
        
        print(f"   ✅ Duplicate analysis added: {duplicate_summary['duplicate_groups_added']:,} groups in {duplicate_time:.2f}s")
        
        # Get sheet registry
        registry = sheets_manager.get_sheet_registry()
        
        # Display sheet information
        print(f"\n📊 Sheet Information:")
        print(f"   Total sheets created: {len(registry['sheets'])}")
        print(f"   Total rows used: {registry['total_rows_used']:,}")
        print(f"   Last updated: {registry['last_updated']}")
        
        # Show sheet details
        print(f"\n📋 Sheet Details:")
        for i, sheet in enumerate(registry['sheets'], 1):
            main_ws = sheet['worksheets']['main']
            print(f"   {i}. {sheet['name']}")
            print(f"      URL: {sheet['url']}")
            print(f"      Rows used: {main_ws['rows_used']:,}/{main_ws['max_rows']:,}")
            print(f"      Worksheets: {len(sheet['worksheets'])}")
        
        return registry
        
    except Exception as e:
        logger.error(f"❌ Sheets management failed: {e}")
        raise

def demo_comprehensive_analysis(max_files: int = 100):
    """Demonstrate the complete comprehensive analysis system"""
    print_section("COMPREHENSIVE ANALYSIS SYSTEM", 
                 f"Running end-to-end analysis on up to {max_files} files")
    
    try:
        # Initialize comprehensive manager
        manager = ComprehensiveDriveManager(
            config_file='enhanced_config.py',
            credentials_file=config.SERVICE_ACCOUNT_FILE
        )
        
        # Run comprehensive analysis
        print("🚀 Starting comprehensive analysis...")
        start_time = time.time()
        results = manager.run_comprehensive_analysis(max_files=max_files)
        total_time = time.time() - start_time
        
        # Display phase results
        print(f"\n⏱️  Phase Timing Summary:")
        for phase_name, phase_data in results['phases'].items():
            duration = phase_data.get('duration_seconds', 0)
            status = phase_data.get('status', 'unknown')
            print(f"   {phase_name}: {duration:.2f}s ({status})")
        
        print(f"   Total analysis time: {total_time:.2f}s")
        
        # Display comprehensive summary
        summary = results.get('summary', {})
        overview = summary.get('analysis_overview', {})
        
        print(f"\n📈 Analysis Overview:")
        print(f"   Files analyzed: {overview.get('total_files', 0):,}")
        print(f"   Total size: {overview.get('total_size_mb', 0):.2f} MB")
        print(f"   Analysis timestamp: {overview.get('analysis_timestamp', 'Unknown')}")
        
        # Show duplicate summary
        dup_summary = summary.get('duplicate_summary', {})
        print(f"\n🔍 Duplicate Summary:")
        print(f"   Duplicate groups: {dup_summary.get('total_groups', 0):,}")
        print(f"   Total duplicates: {dup_summary.get('total_duplicates', 0):,}")
        print(f"   High confidence groups: {dup_summary.get('high_confidence_groups', 0):,}")
        print(f"   Potential savings: {dup_summary.get('potential_savings_mb', 0):.2f} MB")
        
        # Show sheet summary
        sheets_summary = summary.get('sheets_summary', {})
        print(f"\n📊 Sheets Summary:")
        print(f"   Sheets created: {sheets_summary.get('total_sheets', 0):,}")
        print(f"   Total rows: {sheets_summary.get('total_rows_used', 0):,}")
        
        # Show recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Key Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"      {rec['description']}")
        
        # Export results
        print(f"\n💾 Exporting Results:")
        json_file = manager.export_results(results, 'json')
        summary_file = manager.export_results(results, 'summary')
        
        print(f"   📄 JSON export: {json_file}")
        print(f"   📝 Summary export: {summary_file}")
        
        # Show sheet URLs
        sheets_info = results.get('sheets_info', {})
        registry = sheets_info.get('registry', {})
        if registry.get('sheets'):
            print(f"\n🔗 Google Sheets URLs:")
            for sheet in registry['sheets']:
                print(f"   📊 {sheet['name']}")
                print(f"      {sheet['url']}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Comprehensive analysis failed: {e}")
        raise

def interactive_menu():
    """Show interactive menu for demo options"""
    while True:
        print(f"\n{'='*80}")
        print("🎛️  DEMO MENU - Choose a demonstration:")
        print("1. Quick Drive Metadata Extraction (50 files)")
        print("2. Advanced Duplicate Detection Demo")
        print("3. Auto-Scaling Google Sheets Demo")
        print("4. Complete Comprehensive Analysis (100 files)")
        print("5. Configuration Summary")
        print("6. Prerequisites Validation")
        print("0. Exit")
        print('='*80)
        
        try:
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                files = demo_drive_metadata_extraction(50)
                input("\nPress Enter to continue...")
            elif choice == '2':
                print("First extracting files for duplicate detection...")
                files = demo_drive_metadata_extraction(100)
                demo_duplicate_detection(files)
                input("\nPress Enter to continue...")
            elif choice == '3':
                print("First extracting files and detecting duplicates...")
                files = demo_drive_metadata_extraction(100)
                duplicates = demo_duplicate_detection(files)['duplicates']
                demo_auto_scaling_sheets(files, duplicates)
                input("\nPress Enter to continue...")
            elif choice == '4':
                demo_comprehensive_analysis(100)
                input("\nPress Enter to continue...")
            elif choice == '5':
                print_section("CONFIGURATION SUMMARY")
                summary = config.get_config_summary()
                for key, value in summary.items():
                    print(f"   {key}: {value}")
                input("\nPress Enter to continue...")
            elif choice == '6':
                validate_prerequisites()
                input("\nPress Enter to continue...")
            else:
                print("❌ Invalid choice. Please enter a number between 0 and 6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")

def main():
    """Main demo function"""
    print_banner()
    
    # Show configuration summary
    print_section("SYSTEM CONFIGURATION")
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Validate prerequisites
    if not validate_prerequisites():
        print("\n❌ Prerequisites validation failed. Please resolve issues and try again.")
        return
    
    # Ask user for demo preference
    print(f"\n🎯 Demo Options:")
    print("1. Interactive Menu (choose specific demos)")
    print("2. Quick Demo (metadata + duplicates, 50 files)")
    print("3. Full Demo (comprehensive analysis, 100 files)")
    
    try:
        choice = input("\nChoose demo type (1-3): ").strip()
        
        if choice == '1':
            interactive_menu()
        elif choice == '2':
            files = demo_drive_metadata_extraction(50)
            duplicates = demo_duplicate_detection(files)
            print("\n🎉 Quick demo completed successfully!")
        elif choice == '3':
            demo_comprehensive_analysis(100)
            print("\n🎉 Full demo completed successfully!")
        else:
            print("❌ Invalid choice. Running quick demo by default.")
            files = demo_drive_metadata_extraction(50)
            demo_duplicate_detection(files)
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user.")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()