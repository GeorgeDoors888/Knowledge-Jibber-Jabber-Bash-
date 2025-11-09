#!/usr/bin/env python3
"""
Multi-Sheet Manager Demo Script
Demonstrates the usage of the multi-sheet management system
with Google Sheets API and Google Drive API integration.
"""

import os
import sys
import json
from datetime import datetime
import random
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_sheet_manager import MultiSheetManager, create_manager, quick_add_data, get_system_status
from config import DEFAULT_HEADERS, DRIVE_FOLDER_ID


def demo_basic_usage():
    """Demonstrate basic multi-sheet manager usage"""
    print("=" * 60)
    print("DEMO 1: Basic Usage")
    print("=" * 60)
    
    # Create a manager instance
    print("1. Creating MultiSheetManager instance...")
    manager = create_manager(
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_BasicUsage",
        headers=DEFAULT_HEADERS
    )
    
    # Add a single row
    print("\n2. Adding a single row of data...")
    sample_data = {
        "Document ID": "DOC001",
        "Document Title": "Sample Document",
        "Source URL": "https://example.com/doc1.pdf",
        "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Content Type": "PDF",
        "Summary": "This is a sample document summary",
        "Tags": "sample, demo, test",
        "Status": "Processed",
        "Notes": "Demo data entry"
    }
    
    success = manager.add_data(sample_data)
    print(f"   Result: {'✓ Success' if success else '✗ Failed'}")
    
    # Add multiple rows
    print("\n3. Adding multiple rows of data...")
    batch_data = []
    for i in range(5):
        row = {
            "Document ID": f"DOC00{i+2}",
            "Document Title": f"Document {i+2}",
            "Source URL": f"https://example.com/doc{i+2}.pdf",
            "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Content Type": "PDF",
            "Summary": f"Summary for document {i+2}",
            "Tags": f"tag{i+1}, batch, demo",
            "Status": "Processed",
            "Notes": f"Batch entry #{i+1}"
        }
        batch_data.append(row)
    
    results = manager.add_batch_data(batch_data)
    print(f"   Batch results: {results['successful_rows']}/{results['total_rows']} successful")
    
    return manager


def demo_large_dataset():
    """Demonstrate handling large datasets with automatic sheet creation"""
    print("\n" + "=" * 60)
    print("DEMO 2: Large Dataset with Auto Sheet Creation")
    print("=" * 60)
    
    print("1. Creating manager for large dataset demo...")
    manager = create_manager(
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_LargeDataset",
        headers=DEFAULT_HEADERS
    )
    
    # Generate a large dataset
    print("\n2. Generating large sample dataset...")
    large_dataset = []
    
    document_types = ["PDF", "Word", "Excel", "PowerPoint", "Text"]
    tags_options = [
        ["research", "analysis"],
        ["policy", "regulation"], 
        ["technical", "specification"],
        ["report", "summary"],
        ["manual", "guide"]
    ]
    
    # Generate 150 sample records (should create multiple sheets if MAX_ROWS_PER_SHEET is set low)
    for i in range(150):
        doc_type = random.choice(document_types)
        tags = random.choice(tags_options)
        
        row = {
            "Document ID": f"LARGE_{i+1:04d}",
            "Document Title": f"Large Dataset Document {i+1}",
            "Source URL": f"https://example.com/large/doc{i+1}.{doc_type.lower()}",
            "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Content Type": doc_type,
            "Summary": f"Auto-generated summary for document {i+1} of type {doc_type}",
            "Tags": ", ".join(tags + ["large_dataset"]),
            "Status": "Processed" if i % 10 != 0 else "Pending",
            "Notes": f"Large dataset entry #{i+1}"
        }
        large_dataset.append(row)
    
    print(f"   Generated {len(large_dataset)} sample records")
    
    # Add the large dataset
    print("\n3. Adding large dataset (this may create multiple sheets)...")
    start_time = time.time()
    
    results = manager.add_batch_data(large_dataset, chunk_size=50)
    
    end_time = time.time()
    
    print(f"   Processing completed in {end_time - start_time:.2f} seconds")
    print(f"   Results: {results['successful_rows']}/{results['total_rows']} rows added")
    print(f"   Spreadsheets used: {len(results['spreadsheets_used'])}")
    print(f"   Worksheets used: {len(results['worksheets_used'])}")
    
    return manager


def demo_status_and_monitoring():
    """Demonstrate status monitoring and reporting features"""
    print("\n" + "=" * 60)
    print("DEMO 3: Status Monitoring and Reporting")
    print("=" * 60)
    
    print("1. Getting system-wide status report...")
    
    # Get comprehensive status
    status_report = get_system_status(DRIVE_FOLDER_ID)
    
    if status_report:
        print(f"\n📊 System Status Report (as of {status_report['timestamp']}):")
        print(f"   📁 Total Spreadsheets: {status_report['total_spreadsheets']}")
        print(f"   📄 Total Worksheets: {status_report['total_worksheets']}")
        print(f"   📝 Total Rows: {status_report['total_rows']}")
        print(f"   💾 Available Capacity: {status_report['available_capacity']} rows")
        
        print(f"\n📋 Spreadsheet Details:")
        for i, sheet in enumerate(status_report['spreadsheets'], 1):
            print(f"   {i}. {sheet['title']}")
            print(f"      • Tabs: {sheet['tab_count']}")
            print(f"      • Rows: {sheet['total_rows']}")
            print(f"      • Available: {sheet['available_space']} rows")
            print(f"      • URL: {sheet['url']}")
            print()
    else:
        print("   ⚠️  Could not retrieve status report")


def demo_quick_functions():
    """Demonstrate quick utility functions"""
    print("\n" + "=" * 60)
    print("DEMO 4: Quick Utility Functions")
    print("=" * 60)
    
    print("1. Using quick_add_data function for simple operations...")
    
    # Single row using quick function
    quick_data = {
        "Document ID": "QUICK_001",
        "Document Title": "Quick Function Test",
        "Source URL": "https://example.com/quick.pdf",
        "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Content Type": "PDF",
        "Summary": "Testing quick add functionality",
        "Tags": "quick, test, utility",
        "Status": "Processed",
        "Notes": "Added via quick function"
    }
    
    success = quick_add_data(
        quick_data,
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_QuickFunction"
    )
    
    print(f"   Quick add result: {'✓ Success' if success else '✗ Failed'}")
    
    # Multiple rows using quick function
    print("\n2. Batch adding with quick function...")
    quick_batch = []
    for i in range(3):
        row = {
            "Document ID": f"QUICK_{i+2:03d}",
            "Document Title": f"Quick Batch Document {i+1}",
            "Source URL": f"https://example.com/quick_batch_{i+1}.pdf",
            "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Content Type": "PDF",
            "Summary": f"Quick batch summary {i+1}",
            "Tags": f"quick, batch, item{i+1}",
            "Status": "Processed",
            "Notes": f"Quick batch entry #{i+1}"
        }
        quick_batch.append(row)
    
    batch_results = quick_add_data(
        quick_batch,
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_QuickBatch"
    )
    
    if isinstance(batch_results, dict):
        print(f"   Quick batch results: {batch_results['successful_rows']}/{batch_results['total_rows']} successful")
    else:
        print(f"   Quick batch result: {'✓ Success' if batch_results else '✗ Failed'}")


def demo_maintenance_operations():
    """Demonstrate maintenance and cleanup operations"""
    print("\n" + "=" * 60)
    print("DEMO 5: Maintenance Operations")
    print("=" * 60)
    
    print("1. Creating manager for maintenance demo...")
    manager = create_manager(
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_Maintenance"
    )
    
    print("\n2. Getting detailed information about all spreadsheets...")
    all_spreadsheets = manager.get_all_spreadsheets()
    
    print(f"   Found {len(all_spreadsheets)} spreadsheets")
    for sheet in all_spreadsheets:
        print(f"   • {sheet['title']}: {len(sheet['tabs'])} tabs")
    
    print("\n3. Running cleanup operation (removes empty worksheets)...")
    cleaned_count = manager.cleanup_empty_sheets()
    print(f"   Cleaned up {cleaned_count} empty worksheets")
    
    print("\n4. Generating final status report...")
    final_status = manager.get_status_report()
    if final_status:
        print(f"   Final status: {final_status['total_spreadsheets']} spreadsheets, {final_status['total_rows']} total rows")


def demo_duplicate_detection():
    """Demonstrate duplicate detection and management features"""
    print("\n" + "=" * 60)
    print("DEMO 6: Duplicate Detection and Management")
    print("=" * 60)
    
    print("1. Creating manager with duplicate detection enabled...")
    manager = create_manager(
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_DuplicateDetection",
        headers=DEFAULT_HEADERS
    )
    
    # Add some initial data
    print("\n2. Adding initial sample data...")
    initial_data = [
        {
            "Document ID": "DUP_001",
            "Document Title": "Sample Research Document",
            "Source URL": "https://example.com/research1.pdf",
            "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Content Type": "PDF",
            "Summary": "This is a research document about renewable energy",
            "Tags": "research, energy, renewable",
            "Status": "Processed",
            "Notes": "Original document"
        },
        {
            "Document ID": "DUP_002", 
            "Document Title": "Policy Guidelines Document",
            "Source URL": "https://example.com/policy1.pdf",
            "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Content Type": "PDF",
            "Summary": "Policy guidelines for environmental regulations",
            "Tags": "policy, environment, regulations",
            "Status": "Processed",
            "Notes": "Policy document"
        }
    ]
    
    for data in initial_data:
        result = manager.add_data(data)
        print(f"   Added: {data['Document ID']} - Success: {result['success']}")
    
    # Try to add exact duplicates
    print("\n3. Attempting to add exact duplicates...")
    exact_duplicate = initial_data[0].copy()  # Exact copy
    result = manager.add_data(exact_duplicate)
    print(f"   Exact duplicate result: {result['action_taken']} - {result['message']}")
    
    # Try to add similar documents (fuzzy matches)
    print("\n4. Attempting to add similar documents...")
    similar_document = {
        "Document ID": "DUP_001",  # Same ID (exact match)
        "Document Title": "Sample Research Document on Energy",  # Similar title
        "Source URL": "https://example.com/research1_v2.pdf",  # Different URL
        "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Content Type": "PDF",
        "Summary": "This is a research document about renewable energy sources",
        "Tags": "research, energy, renewable, updated",
        "Status": "Updated",
        "Notes": "Updated version"
    }
    
    result = manager.add_data(similar_document)
    print(f"   Similar document result: {result['action_taken']} - {result['message']}")
    
    # Add document with similar title but different ID
    print("\n5. Adding document with similar title...")
    similar_title_doc = {
        "Document ID": "DUP_003",
        "Document Title": "Sample Research Document About Energy",  # Very similar title
        "Source URL": "https://example.com/research_alt.pdf",
        "Processing Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Content Type": "PDF",
        "Summary": "Alternative research on renewable energy",
        "Tags": "research, energy, alternative",
        "Status": "Processed",
        "Notes": "Similar content"
    }
    
    result = manager.add_data(similar_title_doc)
    print(f"   Similar title result: {result['action_taken']} - {result['message']}")
    
    # Show duplicate statistics
    print("\n6. Checking duplicate detection statistics...")
    stats = manager.get_duplicate_statistics()
    print(f"   Total additions attempted: {stats['session_stats']['total_additions']}")
    print(f"   Duplicates detected: {stats['session_stats']['duplicates_detected']}")
    print(f"   Duplicates skipped: {stats['session_stats']['duplicates_skipped']}")
    print(f"   Duplicates flagged: {stats['session_stats']['duplicates_flagged']}")
    
    return manager


def demo_duplicate_scanning():
    """Demonstrate comprehensive duplicate scanning"""
    print("\n" + "=" * 60)
    print("DEMO 7: Comprehensive Duplicate Scanning")
    print("=" * 60)
    
    print("1. Creating manager for duplicate scanning...")
    manager = create_manager(
        folder_id=DRIVE_FOLDER_ID,
        base_name="Demo_DuplicateScanning"
    )
    
    # Add data with intentional duplicates across different scenarios
    print("\n2. Adding test data with various duplicate patterns...")
    test_data = [
        # Exact duplicates
        {"Document ID": "SCAN_001", "Document Title": "Exact Match Test", "Source URL": "https://test.com/exact1.pdf", "Summary": "Test document 1", "Tags": "test, exact", "Status": "Active"},
        {"Document ID": "SCAN_001", "Document Title": "Exact Match Test", "Source URL": "https://test.com/exact1.pdf", "Summary": "Test document 1", "Tags": "test, exact", "Status": "Active"},
        
        # Fuzzy matches - similar titles
        {"Document ID": "SCAN_002", "Document Title": "Climate Change Report", "Source URL": "https://test.com/climate1.pdf", "Summary": "Climate analysis", "Tags": "climate, report", "Status": "Active"},
        {"Document ID": "SCAN_003", "Document Title": "Climate Change Analysis Report", "Source URL": "https://test.com/climate2.pdf", "Summary": "Climate analysis detailed", "Tags": "climate, analysis", "Status": "Active"},
        
        # Content hash matches - different IDs but same content
        {"Document ID": "SCAN_004", "Document Title": "Energy Policy Brief", "Source URL": "https://test.com/energy1.pdf", "Summary": "Energy policy overview", "Tags": "energy, policy", "Status": "Active"},
        {"Document ID": "SCAN_005", "Document Title": "Different Title", "Source URL": "https://test.com/different.pdf", "Summary": "Energy policy overview", "Tags": "energy, policy", "Status": "Active"},
    ]
    
    # Add data with duplicate detection temporarily disabled for demo
    original_setting = manager.enable_duplicate_detection
    manager.enable_duplicate_detection = False
    
    for data in test_data:
        result = manager.add_data(data)
        print(f"   Added: {data['Document ID']} - {data['Document Title'][:30]}...")
    
    # Re-enable duplicate detection
    manager.enable_duplicate_detection = original_setting
    
    # Now scan for duplicates
    print("\n3. Scanning for duplicates across all data...")
    duplicate_report = manager.find_all_duplicates(save_report=True)
    
    if duplicate_report:
        print(f"   📊 Scan Results:")
        print(f"      Total duplicates found: {duplicate_report['summary']['total_duplicates']}")
        print(f"      Match types: {duplicate_report['summary']['match_types']}")
        print(f"      Sheets affected: {duplicate_report['summary']['sheets_affected']}")
        
        # Show details of first few duplicates
        print(f"\n   📋 Sample duplicates found:")
        for i, dup in enumerate(duplicate_report['duplicates'][:3], 1):
            print(f"      {i}. Match Type: {dup['match_info']['match_type']}")
            print(f"         Score: {dup['match_info']['match_score']}%")
            print(f"         Original: {dup['original_row'].get('Document ID')} - {dup['original_row'].get('Document Title', '')[:40]}...")
            print(f"         Duplicate: {dup['duplicate_row'].get('Document ID')} - {dup['duplicate_row'].get('Document Title', '')[:40]}...")
            print()
    
    return manager


def demo_duplicate_configuration():
    """Demonstrate duplicate detection configuration options"""
    print("\n" + "=" * 60)
    print("DEMO 8: Duplicate Detection Configuration")
    print("=" * 60)
    
    print("1. Testing different detection methods...")
    
    # Test data for different scenarios
    base_doc = {
        "Document ID": "CONFIG_001",
        "Document Title": "Configuration Test Document",
        "Source URL": "https://test.com/config.pdf",
        "Summary": "Testing configuration options",
        "Tags": "test, config",
        "Status": "Active"
    }
    
    similar_doc = {
        "Document ID": "CONFIG_002", 
        "Document Title": "Configuration Testing Document",  # Similar title
        "Source URL": "https://test.com/config_alt.pdf",
        "Summary": "Testing configuration settings",  # Similar summary
        "Tags": "test, configuration",
        "Status": "Active"
    }
    
    # Test exact matching
    print("\n2. Testing EXACT matching...")
    manager = create_manager(base_name="Demo_ExactMatching")
    manager.configure_duplicate_detection(method="exact", threshold=100)
    
    manager.add_data(base_doc)
    result = manager.add_data(base_doc.copy())  # Exact duplicate
    print(f"   Exact duplicate: {result['action_taken']}")
    
    result = manager.add_data(similar_doc)  # Similar but not exact
    print(f"   Similar document: {result['action_taken']}")
    
    # Test fuzzy matching
    print("\n3. Testing FUZZY matching...")
    manager.configure_duplicate_detection(method="fuzzy", threshold=80)
    
    result = manager.add_data(similar_doc)  # Should be caught by fuzzy matching
    print(f"   Fuzzy match result: {result['action_taken']}")
    
    # Test multi-method approach
    print("\n4. Testing MULTI-METHOD detection...")
    manager.configure_duplicate_detection(method="multi")
    
    # Add various types of potential duplicates
    test_cases = [
        base_doc.copy(),  # Exact match
        similar_doc,      # Fuzzy match
        {**base_doc, "Document ID": "CONFIG_003", "Summary": "Testing configuration options"},  # Content hash match
    ]
    
    for i, test_doc in enumerate(test_cases, 1):
        result = manager.add_data(test_doc)
        print(f"   Test case {i}: {result['action_taken']} - {result.get('duplicate_info', {}).get('match_type', 'none')}")
    
    return manager


def main():
    """Run all demonstration functions"""
    print("🚀 Multi-Sheet Manager with Duplicate Detection Demonstration")
    print("This demo will create several test spreadsheets to show functionality")
    print("Make sure your service_account.json file is configured correctly!")
    
    # Check if service account file exists
    if not os.path.exists("service_account.json"):
        print("\n❌ ERROR: service_account.json file not found!")
        print("Please ensure your Google Service Account credentials are properly configured.")
        print("See README for setup instructions.")
        return
    
    try:
        # Run all demos
        manager1 = demo_basic_usage()
        manager2 = demo_large_dataset()
        demo_status_and_monitoring()
        demo_quick_functions() 
        demo_maintenance_operations()
        
        # New duplicate detection demos
        manager6 = demo_duplicate_detection()
        manager7 = demo_duplicate_scanning()
        manager8 = demo_duplicate_configuration()
        
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("Check your Google Drive folder for the created spreadsheets.")
        print("Each demo created different spreadsheets with various data patterns.")
        print("The duplicate detection demos show how to prevent and manage duplicates.")
        
        # Show final summary including duplicate stats
        final_status = get_system_status(DRIVE_FOLDER_ID)
        if final_status:
            print(f"\n📈 Final System Summary:")
            print(f"   Total Spreadsheets Created: {final_status['total_spreadsheets']}")
            print(f"   Total Data Rows: {final_status['total_rows']}")
            print(f"   Available Capacity: {final_status['available_capacity']} rows")
        
        # Show duplicate detection summary
        print(f"\n🔍 Duplicate Detection Summary:")
        all_managers = [manager1, manager2, manager6, manager7, manager8]
        total_duplicates = 0
        for manager in all_managers:
            if hasattr(manager, 'stats'):
                total_duplicates += manager.stats.get('duplicates_detected', 0)
        
        print(f"   Total Duplicates Detected: {total_duplicates}")
        print(f"   Use 'python duplicate_manager.py scan' for comprehensive duplicate analysis")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("Please check your Google API credentials and permissions.")


if __name__ == "__main__":
    main()