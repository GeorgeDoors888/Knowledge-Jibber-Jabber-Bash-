#!/usr/bin/env python3
"""
Quick script to find and list all created spreadsheets
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from multi_sheet_manager import get_system_status
    from config import DRIVE_FOLDER_ID, SHEET_NAME_PREFIX
    
    print("🔍 Searching for created spreadsheets...")
    print(f"📁 Target folder: {'Root Drive folder (My Drive)' if DRIVE_FOLDER_ID is None else DRIVE_FOLDER_ID}")
    print(f"🏷️  Looking for sheets with prefix: {SHEET_NAME_PREFIX}")
    print("\n" + "="*60)
    
    # Get status report
    status = get_system_status(DRIVE_FOLDER_ID)
    
    if status and status['total_spreadsheets'] > 0:
        print(f"📊 Found {status['total_spreadsheets']} spreadsheet(s):")
        print(f"📝 Total data rows: {status['total_rows']}")
        print(f"💾 Available capacity: {status['available_capacity']} rows")
        
        print(f"\n📋 Spreadsheet Details:")
        for i, sheet in enumerate(status['spreadsheets'], 1):
            print(f"\n{i}. 📄 {sheet['title']}")
            print(f"   🔗 URL: {sheet['url']}")
            print(f"   📊 Tabs: {sheet['tab_count']}")
            print(f"   📝 Rows: {sheet['total_rows']}")
            print(f"   💾 Available: {sheet['available_space']} rows")
            
    else:
        print("❌ No spreadsheets found!")
        print("\n💡 Possible reasons:")
        print("   1. No spreadsheets have been created yet")
        print("   2. Service account doesn't have access to the folder")
        print("   3. Spreadsheets are in a different folder")
        
        print(f"\n🚀 To create test spreadsheets, run:")
        print(f"   python demo_multi_sheets.py")

except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("🔧 Install requirements: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Ensure service_account.json is configured")
    print("   2. Check Google API credentials and permissions")
    print("   3. Verify Google Sheets and Drive APIs are enabled")
    
print("\n" + "="*60)
print("✅ Search complete!")