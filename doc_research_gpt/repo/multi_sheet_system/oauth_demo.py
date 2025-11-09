#!/usr/bin/env python3
"""
OAuth-Compatible Demo for Comprehensive Drive Analysis
Uses OAuth authentication instead of service account
"""

import os
import sys
from oauth_setup import OAuthDriveManager

def run_oauth_demo():
    """Run demo using OAuth authentication"""
    print("🚀 Google Drive Analysis - OAuth Demo")
    print("=" * 50)
    
    # Setup OAuth authentication
    print("\n1️⃣ Setting up OAuth authentication...")
    manager = OAuthDriveManager('/Users/georgemajor/Knowledge Jibber Jabber Bash/doc_research_gpt/repo/multi_sheet_system/oauth_credentials.json')
    
    if not manager.authenticate():
        print("❌ Authentication failed")
        return
    
    if not manager.test_connection():
        print("❌ Connection test failed") 
        return
        
    print("\n2️⃣ Scanning ALL your Google Drive files...")
    
    try:
        # Get ALL files from Drive using pagination
        all_files = []
        page_token = None
        page_count = 0
        
        # Update the folder ID to the one shared earlier
        folder_id = '1bjWA-yeViuMIucgXIN9KJOzabOP2vUPl'

        while True:
            page_count += 1
            print(f"   📄 Scanning page {page_count}...", end=" ")
            
            # Request files with pagination
            results = manager.drive_service.files().list(
                q=f"'{folder_id}' in parents",
                pageSize=1000,  # Maximum allowed by API
                pageToken=page_token,
                fields="nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime, owners, parents, webViewLink)"
            ).execute()
            
            page_files = results.get('files', [])
            all_files.extend(page_files)
            print(f"Found {len(page_files)} files")
            
            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        files = all_files
        
        print(f"📊 Found {len(files)} files in your Google Drive")
        
        # Analyze file types
        file_types = {}
        total_size = 0
        
        for file in files:
            mime_type = file.get('mimeType', 'unknown')
            file_types[mime_type] = file_types.get(mime_type, 0) + 1
            
            # Get size if available
            size = file.get('size')
            if size:
                total_size += int(size)
        
        print(f"\n📁 File Type Analysis:")
        for mime_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            # Simplify mime type display
            display_type = mime_type.split('/')[-1].replace('vnd.google-apps.', 'Google ')
            print(f"   {display_type}: {count} files")
        
        print(f"\n💾 Storage Info:")
        print(f"   Total size: {total_size / (1024*1024):.2f} MB")
        print(f"   Average per file: {total_size / len(files) / 1024:.2f} KB")
        
        print(f"\n📄 Sample Files:")
        for i, file in enumerate(files[:5], 1):
            name = file.get('name', 'Unknown')
            size_mb = int(file.get('size', 0)) / (1024*1024) if file.get('size') else 0
            mime_type = file.get('mimeType', 'unknown').split('/')[-1]
            print(f"   {i}. {name} ({size_mb:.2f} MB, {mime_type})")
        
        # Simple duplicate detection by name
        print(f"\n🔍 Quick Duplicate Check (by filename similarity)...")
        names = [f.get('name', '').lower() for f in files]
        potential_duplicates = []
        
        for i, name in enumerate(names):
            for j, other_name in enumerate(names[i+1:], i+1):
                if name and other_name and name in other_name or other_name in name:
                    if abs(len(name) - len(other_name)) < 5:  # Similar length
                        potential_duplicates.append((files[i]['name'], files[j]['name']))
        
        if potential_duplicates:
            print(f"   Found {len(potential_duplicates)} potential duplicate pairs:")
            for orig, dup in potential_duplicates[:3]:
                print(f"   - '{orig}' ≈ '{dup}'")
            if len(potential_duplicates) > 3:
                print(f"   ... and {len(potential_duplicates) - 3} more")
        else:
            print("   No obvious filename duplicates found")
        
        # Create Google Sheets with ALL files (auto-scaling)
        print(f"\n3️⃣ Creating Google Sheets with ALL {len(files)} files...")
        
        # Calculate how many sheets we need (Google Sheets limit: ~5M cells, use 1000 files per sheet to be safe)
        files_per_sheet = 1000
        num_sheets_needed = (len(files) + files_per_sheet - 1) // files_per_sheet
        
        print(f"   📊 Will create {num_sheets_needed} sheet(s) to hold all {len(files)} files")
        
        # Create new spreadsheet with multiple sheets if needed
        sheets_config = []
        for i in range(num_sheets_needed):
            start_idx = i * files_per_sheet
            end_idx = min(start_idx + files_per_sheet, len(files))
            sheet_title = f'Files_{start_idx+1}_to_{end_idx}' if num_sheets_needed > 1 else 'All_Files'
            sheets_config.append({
                'properties': {
                    'title': sheet_title
                }
            })
        
        # Add summary sheet
        sheets_config.insert(0, {
            'properties': {
                'title': 'Summary_Analysis'
            }
        })
        
        spreadsheet = {
            'properties': {
                'title': f'Complete Drive Analysis - {len(files)} files - {page_count} pages'
            },
            'sheets': sheets_config
        }
        
        sheet = manager.sheets_service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = sheet['spreadsheetId']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        
        # Create summary data first
        summary_data = [
            ['Google Drive Complete Analysis Summary'],
            [''],
            ['Total Files Found', len(files)],
            ['Total Pages Scanned', page_count],
            ['Analysis Date', f"{files[0].get('createdTime', 'Unknown')[:10] if files else 'Unknown'}"],
            [''],
            ['File Type Breakdown', 'Count'],
        ]
        
        # Add file type counts to summary
        for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            display_type = file_type.split('/')[-1].replace('vnd.google-apps.', 'Google ')
            summary_data.append([display_type, count])
        
        if len(file_types) > 10:
            summary_data.append([f'... and {len(file_types)-10} more types', ''])
        
        # Add storage summary
        summary_data.extend([
            [''],
            ['Storage Analysis', ''],
            ['Total Size (MB)', f"{total_size / (1024*1024):.2f}"],
            ['Average File Size (KB)', f"{total_size / len(files) / 1024:.2f}" if files else "0"],
            ['Largest Files', 'Size (MB)'],
        ])
        
        # Add top 5 largest files
        sorted_files = sorted([f for f in files if f.get('size')], 
                            key=lambda x: int(x.get('size', 0)), reverse=True)
        for file in sorted_files[:5]:
            name = file.get('name', 'Unknown')[:30] + '...' if len(file.get('name', '')) > 30 else file.get('name', 'Unknown')
            size_mb = int(file.get('size', 0)) / (1024*1024)
            summary_data.append([name, f"{size_mb:.2f}"])
        
        # Write summary to first sheet
        range_name = 'Summary_Analysis!A1:B' + str(len(summary_data))
        body = {'values': summary_data}
        
        manager.sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        # Now create detailed file sheets
        headers = ['Name', 'Type', 'Size (MB)', 'Created', 'Modified', 'File ID', 'Link']
        sheets_created = 0
        
        for sheet_idx in range(num_sheets_needed):
            start_idx = sheet_idx * files_per_sheet
            end_idx = min(start_idx + files_per_sheet, len(files))
            sheet_files = files[start_idx:end_idx]
            
            sheet_title = f'Files_{start_idx+1}_to_{end_idx}' if num_sheets_needed > 1 else 'All_Files'
            
            print(f"   📝 Writing {len(sheet_files)} files to sheet: {sheet_title}")
            
            # Prepare data for this sheet
            data = [headers]
            for file in sheet_files:
                name = file.get('name', 'Unknown')
                mime_type = file.get('mimeType', 'unknown').split('/')[-1].replace('vnd.google-apps.', 'G.')
                size_mb = int(file.get('size', 0)) / (1024*1024) if file.get('size') else 0
                created = file.get('createdTime', 'Unknown')[:10] if file.get('createdTime') else 'Unknown'
                modified = file.get('modifiedTime', 'Unknown')[:10] if file.get('modifiedTime') else 'Unknown'
                file_id = file.get('id', '')
                link = file.get('webViewLink', '')
                
                data.append([name, mime_type, f"{size_mb:.2f}", created, modified, file_id, link])
            
            # Write data to sheet
            range_name = f'{sheet_title}!A1:G' + str(len(data))
            body = {'values': data}
            
            manager.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            sheets_created += 1
        
        print(f"✅ Google Sheets created successfully!")
        print(f"🔗 Master Sheet URL: {sheet_url}")
        print(f"📊 Created {sheets_created + 1} sheets with ALL {len(files)} files")
        
        print(f"\n🎉 COMPLETE GOOGLE DRIVE ANALYSIS FINISHED!")
        print(f"="*60)
        print(f"📊 COMPREHENSIVE SUMMARY:")
        print(f"   • Total Files Scanned: {len(files):,}")
        print(f"   • API Pages Processed: {page_count}")
        print(f"   • File Types Found: {len(file_types)}")
        print(f"   • Total Storage: {total_size / (1024*1024):.2f} MB")
        print(f"   • Potential Duplicates: {len(potential_duplicates)}")
        print(f"   • Sheets Created: {sheets_created + 1}")
        print(f"")
        print(f"🔗 Access Your Complete Analysis:")
        print(f"   Master Sheet: {sheet_url}")
        print(f"")
        print(f"📋 What's Included:")
        print(f"   • Summary analysis with file type breakdown")
        print(f"   • Complete file listing with metadata")
        print(f"   • Direct links to all files")
        print(f"   • Storage analysis and largest files")
        print(f"   • Duplicate detection results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_oauth_demo()