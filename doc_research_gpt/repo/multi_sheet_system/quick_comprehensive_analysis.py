#!/usr/bin/env python3
"""
Quick Complete Drive Analysis - Create sheets for ALL files without duplicate detection
This version skips the time-intensive duplicate detection and creates the comprehensive sheets
"""

from oauth_setup import OAuthDriveManager
from datetime import datetime

def create_comprehensive_sheets():
    """Create comprehensive Google Sheets for all files"""
    print("🚀 Creating Comprehensive Google Drive Analysis Sheets")
    print("=" * 60)
    
    # Setup OAuth authentication
    print("\n1️⃣ Authenticating...")
    manager = OAuthDriveManager('oauth_credentials.json')
    if not manager.authenticate():
        return
    
    print("\n2️⃣ Scanning ALL your Google Drive files...")
    
    # Get ALL files from Drive using pagination
    all_files = []
    page_token = None
    page_count = 0
    
    while True:
        page_count += 1
        print(f"   📄 Scanning page {page_count}...", end=" ")
        
        results = manager.drive_service.files().list(
            pageSize=1000,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime, owners, parents, webViewLink)"
        ).execute()
        
        page_files = results.get('files', [])
        all_files.extend(page_files)
        print(f"Found {len(page_files)} files")
        
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    
    files = all_files
    print(f"\n📊 Total files found: {len(files):,}")
    
    # Quick analysis
    file_types = {}
    total_size = 0
    
    for file in files:
        mime_type = file.get('mimeType', 'unknown')
        file_types[mime_type] = file_types.get(mime_type, 0) + 1
        
        size = file.get('size')
        if size:
            total_size += int(size)
    
    print(f"📁 File types found: {len(file_types)}")
    print(f"💾 Total storage: {total_size / (1024*1024*1024):.2f} GB")
    
    print("\n3️⃣ Creating comprehensive Google Sheets...")
    
    # Calculate sheets needed (1000 files per sheet for performance)
    files_per_sheet = 1000
    num_data_sheets = (len(files) + files_per_sheet - 1) // files_per_sheet
    
    print(f"   📊 Will create {num_data_sheets + 1} sheets ({num_data_sheets} data + 1 summary)")
    
    # Create spreadsheet structure
    sheets_config = [{'properties': {'title': 'Summary_Analysis'}}]
    
    # Add data sheets
    for i in range(num_data_sheets):
        start_idx = i * files_per_sheet
        end_idx = min(start_idx + files_per_sheet, len(files))
        sheet_title = f'Files_{start_idx+1}_to_{end_idx}'
        sheets_config.append({'properties': {'title': sheet_title}})
    
    # Create the spreadsheet
    spreadsheet_body = {
        'properties': {
            'title': f'COMPLETE Drive Analysis - {len(files):,} files - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        },
        'sheets': sheets_config
    }
    
    spreadsheet = manager.sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
    sheet_id = spreadsheet['spreadsheetId']
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    
    print(f"✅ Created master spreadsheet: {spreadsheet['properties']['title']}")
    
    # Create summary sheet
    print("   📋 Creating summary analysis...")
    
    summary_data = [
        ['🚀 COMPLETE GOOGLE DRIVE ANALYSIS', ''],
        ['', ''],
        ['📊 OVERVIEW', ''],
        ['Total Files Analyzed', f"{len(files):,}"],
        ['Total Pages Scanned', page_count],
        ['Analysis Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ['Total Storage (GB)', f"{total_size / (1024*1024*1024):.2f}"],
        ['Average File Size (KB)', f"{total_size / len(files) / 1024:.2f}" if files else "0"],
        ['', ''],
        ['📁 FILE TYPE BREAKDOWN (Top 20)', 'Count'],
    ]
    
    # Add top file types
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    for mime_type, count in sorted_types[:20]:
        display_type = mime_type.split('/')[-1].replace('vnd.google-apps.', 'Google ')
        summary_data.append([display_type, f"{count:,}"])
    
    if len(sorted_types) > 20:
        remaining_count = sum(count for _, count in sorted_types[20:])
        summary_data.append([f"... {len(sorted_types)-20} other types", f"{remaining_count:,}"])
    
    # Add storage breakdown
    summary_data.extend([
        ['', ''],
        ['💾 STORAGE BREAKDOWN', ''],
        ['Largest Files (Top 10)', 'Size (MB)'],
    ])
    
    # Add top 10 largest files
    files_with_size = [f for f in files if f.get('size')]
    largest_files = sorted(files_with_size, key=lambda x: int(x.get('size', 0)), reverse=True)
    
    for file in largest_files[:10]:
        name = file.get('name', 'Unknown')[:40] + '...' if len(file.get('name', '')) > 40 else file.get('name', 'Unknown')
        size_mb = int(file.get('size', 0)) / (1024*1024)
        summary_data.append([name, f"{size_mb:.2f}"])
    
    # Navigation links
    summary_data.extend([
        ['', ''],
        ['🔗 NAVIGATION', ''],
        ['Sheet Name', 'Files Range'],
    ])
    
    for i in range(num_data_sheets):
        start_idx = i * files_per_sheet + 1
        end_idx = min(start_idx + files_per_sheet - 1, len(files))
        sheet_name = f'Files_{start_idx}_to_{end_idx}'
        summary_data.append([sheet_name, f"Files {start_idx:,} to {end_idx:,}"])
    
    # Write summary
    range_name = 'Summary_Analysis!A1:B' + str(len(summary_data))
    body = {'values': summary_data}
    
    manager.sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    # Create data sheets
    headers = ['#', 'Name', 'Type', 'Size (MB)', 'Created', 'Modified', 'File ID', 'Drive Link']
    
    for sheet_idx in range(num_data_sheets):
        start_idx = sheet_idx * files_per_sheet
        end_idx = min(start_idx + files_per_sheet, len(files))
        sheet_files = files[start_idx:end_idx]
        
        sheet_name = f'Files_{start_idx+1}_to_{end_idx}'
        print(f"   📝 Creating sheet {sheet_idx+1}/{num_data_sheets}: {sheet_name} ({len(sheet_files)} files)")
        
        # Prepare data
        data = [headers]
        for i, file in enumerate(sheet_files, start_idx + 1):
            name = file.get('name', 'Unknown')
            mime_type = file.get('mimeType', 'unknown').split('/')[-1].replace('vnd.google-apps.', 'G.')
            size_mb = int(file.get('size', 0)) / (1024*1024) if file.get('size') else 0
            created = file.get('createdTime', '')[:10] if file.get('createdTime') else ''
            modified = file.get('modifiedTime', '')[:10] if file.get('modifiedTime') else ''
            file_id = file.get('id', '')
            link = file.get('webViewLink', '')
            
            data.append([i, name, mime_type, f"{size_mb:.2f}", created, modified, file_id, link])
        
        # Write data
        range_name = f'{sheet_name}!A1:H{len(data)}'
        body = {'values': data}
        
        manager.sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
    
    print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"📊 Master Analysis Sheet:")
    print(f"   🔗 {sheet_url}")
    print(f"")
    print(f"📋 What's included:")
    print(f"   • Summary with {len(files):,} total files")
    print(f"   • {len(file_types)} different file types")
    print(f"   • {num_data_sheets} detailed data sheets")
    print(f"   • Direct links to all files")
    print(f"   • Complete metadata for every file")
    print(f"")
    print(f"💡 Next steps:")
    print(f"   1. Open the sheet: {sheet_url}")
    print(f"   2. Check the Summary_Analysis tab for overview")
    print(f"   3. Browse individual file sheets for details")
    
    return sheet_url

if __name__ == "__main__":
    create_comprehensive_sheets()