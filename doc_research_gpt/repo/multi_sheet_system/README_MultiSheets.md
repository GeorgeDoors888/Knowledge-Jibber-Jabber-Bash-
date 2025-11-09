# Multi-Sheet Manager for Google Sheets

A powerful Python system for automatically managing multiple Google Sheets with overflow detection and automatic creation of new sheets and spreadsheets when capacity limits are reached.

## Features

🚀 **Automatic Sheet Management**
- Automatically creates new worksheet tabs when current sheet reaches row limit
- Automatically creates new spreadsheet files when tab limit is reached
- Configurable limits for rows per sheet and sheets per spreadsheet

📊 **Batch Processing**
- Add single rows or process large datasets in batches
- Intelligent data distribution across multiple sheets
- Rate limiting to respect Google API quotas

🔄 **Smart Overflow Handling**
- Monitors sheet capacity in real-time
- Seamlessly transitions between sheets and spreadsheets
- Maintains data integrity during overflow operations

📈 **Monitoring & Reporting**
- Comprehensive status reports across all spreadsheets
- Track usage, capacity, and performance metrics
- Built-in cleanup tools for maintenance

🔒 **Google API Integration**
- Full Google Sheets API v4 support
- Google Drive API for file management
- Service account authentication for secure access

## Quick Start

### 1. Setup Google Service Account

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account and download the JSON credentials
5. Save the credentials as `service_account.json` in your project directory

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Settings

Edit `config.py` to customize your settings:

```python
# Sheet capacity limits
MAX_ROWS_PER_SHEET = 5000  # Rows before creating new tab
MAX_SHEETS_PER_SPREADSHEET = 10  # Tabs before creating new file

# Google Drive folder (optional)
DRIVE_FOLDER_ID = "your_folder_id"  # None for root folder

# Customize naming and headers
SHEET_NAME_PREFIX = "YourProject"
DEFAULT_HEADERS = ["Column1", "Column2", "Column3"]  # Customize as needed

# Email sharing (optional)
SHARE_EMAILS = ["user@example.com"]
```

### 4. Basic Usage

```python
from multi_sheet_manager import MultiSheetManager

# Create manager instance
manager = MultiSheetManager(
    folder_id="your_drive_folder_id",  # Optional
    base_name="MyProject",
    headers=["ID", "Title", "Data", "Status"]
)

# Add single row
data_row = {
    "ID": "001", 
    "Title": "Sample Document",
    "Data": "Some content",
    "Status": "Processed"
}
manager.add_data(data_row)

# Add multiple rows
batch_data = [
    {"ID": "002", "Title": "Doc 2", "Data": "Content 2", "Status": "Pending"},
    {"ID": "003", "Title": "Doc 3", "Data": "Content 3", "Status": "Complete"}
]
results = manager.add_batch_data(batch_data)
```

## API Reference

### MultiSheetManager Class

#### Initialization
```python
MultiSheetManager(folder_id=None, base_name=None, headers=None)
```
- `folder_id`: Google Drive folder ID (optional)
- `base_name`: Prefix for spreadsheet names
- `headers`: List of column headers

#### Methods

##### `add_data(data_row)`
Add a single row of data.
- **Parameters**: `data_row` (dict or list) - The data to add
- **Returns**: `bool` - Success status

##### `add_batch_data(data_list, chunk_size=100)`
Add multiple rows in batches.
- **Parameters**: 
  - `data_list` (list) - List of data rows
  - `chunk_size` (int) - Batch size for processing
- **Returns**: `dict` - Results summary with counts and status

##### `get_status_report()`
Generate comprehensive system status.
- **Returns**: `dict` - Detailed report of all spreadsheets and usage

##### `cleanup_empty_sheets()`
Remove empty worksheets.
- **Returns**: `int` - Number of sheets cleaned up

### Convenience Functions

##### `quick_add_data(data_list, folder_id=None, base_name=None, headers=None)`
Quick function for simple data addition without managing instances.

##### `get_system_status(folder_id=None)`
Get status report without creating manager instance.

## Configuration Options

### Capacity Limits
```python
MAX_ROWS_PER_SHEET = 5000  # Rows per worksheet
MAX_SHEETS_PER_SPREADSHEET = 10  # Worksheets per spreadsheet
```

### Naming Convention
```python
SHEET_NAME_PREFIX = "DocumentResearch"  # Base name for files
```

### Default Headers
```python
DEFAULT_HEADERS = [
    "Document ID", "Document Title", "Source URL", 
    "Processing Date", "Content Type", "Summary", 
    "Tags", "Status", "Notes"
]
```

### Sharing Settings
```python
SHARE_EMAILS = [
    "user1@example.com",
    "user2@example.com" 
]
```

## Examples

### Example 1: Document Processing Pipeline
```python
from multi_sheet_manager import create_manager
from datetime import datetime

# Create specialized manager for document processing
manager = create_manager(
    folder_id="1234567890abcdef",
    base_name="DocumentProcessing",
    headers=["Doc_ID", "Title", "URL", "Summary", "Status"]
)

# Process documents
for doc in documents:
    doc_data = {
        "Doc_ID": doc.id,
        "Title": doc.title,
        "URL": doc.source_url,
        "Summary": process_document(doc),
        "Status": "Completed"
    }
    manager.add_data(doc_data)

# Get processing report
report = manager.get_status_report()
print(f"Processed {report['total_rows']} documents")
```

### Example 2: Large Dataset Import
```python
from multi_sheet_manager import quick_add_data

# Import large CSV dataset
import pandas as pd

df = pd.read_csv('large_dataset.csv')
data_list = df.to_dict('records')

# Automatically handle overflow across multiple sheets
results = quick_add_data(
    data_list, 
    folder_id="your_folder_id",
    base_name="ImportedData"
)

print(f"Imported {results['successful_rows']} rows across {len(results['spreadsheets_used'])} spreadsheets")
```

### Example 3: Real-time Data Streaming
```python
import time
from multi_sheet_manager import MultiSheetManager

manager = MultiSheetManager(base_name="RealtimeData")

# Simulate real-time data processing
for i in range(10000):  # Will automatically create new sheets as needed
    data = {
        "Timestamp": datetime.now().isoformat(),
        "Value": random.randint(1, 100),
        "Status": "Active"
    }
    manager.add_data(data)
    time.sleep(0.1)  # Rate limiting
```

## Monitoring and Maintenance

### Status Monitoring
```python
from multi_sheet_manager import get_system_status

# Get comprehensive status
status = get_system_status()

print(f"Total Spreadsheets: {status['total_spreadsheets']}")
print(f"Total Rows: {status['total_rows']}")
print(f"Available Capacity: {status['available_capacity']}")

# Per-spreadsheet details
for sheet in status['spreadsheets']:
    print(f"📊 {sheet['title']}: {sheet['total_rows']} rows")
```

### Cleanup Operations
```python
manager = MultiSheetManager()

# Remove empty worksheets
cleaned = manager.cleanup_empty_sheets()
print(f"Cleaned up {cleaned} empty sheets")

# Get updated status
status = manager.get_status_report()
```

## Error Handling

The system includes comprehensive error handling:

```python
try:
    manager = MultiSheetManager(folder_id="invalid_id")
    result = manager.add_data(data)
    if not result:
        print("Failed to add data - check logs for details")
except Exception as e:
    print(f"Error: {e}")
```

## Rate Limiting

The system respects Google API rate limits:
- Automatic delays between API calls
- Batch processing to minimize API usage
- Configurable rate limiting settings

## Performance Tips

1. **Use Batch Processing**: For large datasets, use `add_batch_data()` instead of multiple `add_data()` calls
2. **Optimize Chunk Size**: Adjust `chunk_size` parameter based on your data size and API limits
3. **Monitor Capacity**: Regular status checks help optimize performance
4. **Cleanup Regularly**: Use `cleanup_empty_sheets()` to maintain optimal performance

## Troubleshooting

### Common Issues

**Authentication Errors**
- Ensure `service_account.json` is in the correct location
- Verify Google APIs are enabled in your project
- Check service account permissions

**Permission Denied**
- Service account needs access to the target Drive folder
- Ensure APIs are enabled and quotas are not exceeded

**Rate Limiting**
- Increase delays in configuration
- Reduce batch sizes
- Monitor API usage in Google Cloud Console

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Demo Script

Run the comprehensive demo to test all features:
```bash
python demo_multi_sheets.py
```

This will create test spreadsheets and demonstrate:
- Basic single and batch operations
- Large dataset handling with auto-overflow
- Status monitoring and reporting
- Cleanup operations

## Duplicate Detection and Management

### 🔍 **Advanced Duplicate Detection**

The system includes comprehensive duplicate detection using multiple strategies:

#### **Detection Methods:**
- **Exact Match**: Identifies identical entries in key fields
- **Fuzzy Match**: Finds similar entries using similarity scoring (85% threshold default)
- **Content Hash**: Detects duplicates based on content fingerprinting
- **Title Similarity**: Catches similar document titles
- **Multi-Method**: Combines all strategies for comprehensive detection

#### **Configuration Options:**
```python
# In config.py
ENABLE_DUPLICATE_DETECTION = True
DUPLICATE_CHECK_FIELDS = ["Document ID", "Source URL"]  # Primary fields to check
DUPLICATE_DETECTION_METHOD = "multi"  # "exact", "fuzzy", "hash", "multi"
FUZZY_MATCH_THRESHOLD = 85  # Similarity percentage (0-100)
DUPLICATE_ACTION = "skip"  # "skip", "update", "flag", "allow"
```

#### **Duplicate Handling Actions:**
- **Skip**: Don't add duplicates (default)
- **Flag**: Add duplicates with "DUPLICATE_" prefix
- **Update**: Replace existing entry (future feature)
- **Allow**: Add duplicates without restriction

### 🛠 **Using Duplicate Detection**

#### **Basic Usage with Duplicate Checking:**
```python
from multi_sheet_manager import MultiSheetManager

# Enable duplicate detection
manager = MultiSheetManager(enable_duplicate_detection=True)

# Add data with duplicate checking
result = manager.add_data({
    "Document ID": "DOC001",
    "Title": "Sample Document",
    "URL": "https://example.com/doc.pdf"
})

# Check result
if result['duplicate_detected']:
    print(f"Duplicate found: {result['duplicate_info']['match_type']}")
    print(f"Action taken: {result['action_taken']}")
```

#### **Comprehensive Duplicate Scanning:**
```python
# Scan all existing data for duplicates
duplicate_report = manager.find_all_duplicates(save_report=True)

print(f"Found {duplicate_report['summary']['total_duplicates']} duplicates")
print(f"Match types: {duplicate_report['summary']['match_types']}")
```

#### **Configure Detection at Runtime:**
```python
# Change detection method
manager.configure_duplicate_detection(
    method="fuzzy",
    threshold=90,
    check_fields=["Document ID", "Title", "URL"]
)
```

### 📊 **Duplicate Management Tools**

#### **Command-Line Duplicate Manager:**
```bash
# Scan for duplicates
python duplicate_manager.py scan --folder-id "your_folder_id"

# Clean up duplicates (dry run)
python duplicate_manager.py clean --strategy keep_first --dry-run

# Interactive duplicate review
python duplicate_manager.py review

# Analyze duplicate patterns
python duplicate_manager.py analyze

# Generate prevention recommendations
python duplicate_manager.py prevent
```

#### **Duplicate Statistics:**
```python
# Get comprehensive statistics
stats = manager.get_duplicate_statistics()

print(f"Session duplicates detected: {stats['session_stats']['duplicates_detected']}")
print(f"Detection method: {stats['detection_method']}")
print(f"Check fields: {stats['check_fields']}")
```

### 🔧 **Advanced Duplicate Features**

#### **Content Hash Matching:**
Detects duplicates based on content similarity even when IDs differ:
```python
# Enable content hash detection
ENABLE_CONTENT_HASH = True
CONTENT_FIELDS_FOR_HASH = ["Summary", "Tags"]  # Fields to hash
```

#### **Fuzzy Title Matching:**
Catches similar document titles with slight variations:
```python
ENABLE_FUZZY_TITLE_MATCHING = True
TITLE_SIMILARITY_THRESHOLD = 80  # Minimum similarity percentage
```

#### **Duplicate Logging:**
Maintains detailed logs of all duplicate detections:
```python
CREATE_DUPLICATE_LOG = True
DUPLICATE_LOG_FILE = "duplicate_log.json"
```

### 📈 **Duplicate Prevention Best Practices**

1. **Configure Appropriate Thresholds**: 
   - Use 95%+ for strict matching
   - Use 80-90% for flexible matching
   - Use 70-80% for very loose matching

2. **Choose Right Detection Method**:
   - `exact`: Fast, catches identical entries
   - `fuzzy`: Catches similar entries with variations  
   - `hash`: Catches content duplicates regardless of metadata
   - `multi`: Comprehensive but slower

3. **Select Key Fields Carefully**:
   ```python
   # Good for documents
   DUPLICATE_CHECK_FIELDS = ["Document ID", "Source URL", "Title"]
   
   # Good for data records
   DUPLICATE_CHECK_FIELDS = ["Record ID", "Email", "Phone"]
   ```

4. **Regular Maintenance**:
   ```python
   # Schedule regular duplicate scans
   duplicate_report = manager.find_all_duplicates()
   
   # Clean up duplicates periodically
   manager.remove_duplicates(strategy="keep_first", dry_run=False)
   ```

### 🎯 **Duplicate Detection Examples**

#### **Example 1: Document Processing with Duplicate Prevention**
```python
from multi_sheet_manager import MultiSheetManager

# Setup with strict duplicate detection
manager = MultiSheetManager(
    base_name="DocumentProcessing",
    enable_duplicate_detection=True
)
manager.configure_duplicate_detection(method="multi", threshold=90)

# Process documents with automatic duplicate prevention
for doc in document_list:
    result = manager.add_data({
        "Document ID": doc.id,
        "Title": doc.title,
        "URL": doc.url,
        "Summary": extract_summary(doc),
        "Status": "Processed"
    })
    
    if result['duplicate_detected']:
        print(f"⚠️ Duplicate detected: {doc.title}")
        print(f"   Match type: {result['duplicate_info']['match_type']}")
        print(f"   Action: {result['action_taken']}")
```

#### **Example 2: Batch Import with Duplicate Handling**
```python
# Import large dataset with duplicate management
import pandas as pd

df = pd.read_csv('large_dataset.csv')
data_list = df.to_dict('records')

# Configure to flag duplicates instead of skipping
manager.configure_duplicate_detection(method="fuzzy", action="flag")

# Batch import with duplicate tracking
results = manager.add_batch_data(data_list)
stats = manager.get_duplicate_statistics()

print(f"Imported: {results['successful_rows']} rows")
print(f"Duplicates flagged: {stats['session_stats']['duplicates_flagged']}")
```

#### **Example 3: Duplicate Cleanup Operation**
```python
# Find and clean up all duplicates
print("Scanning for duplicates...")
report = manager.find_all_duplicates(save_report=True)

if report['summary']['total_duplicates'] > 0:
    print(f"Found {report['summary']['total_duplicates']} duplicates")
    
    # Interactive cleanup
    for dup in report['duplicates'][:5]:  # Review first 5
        print(f"\nDuplicate pair:")
        print(f"  Original: {dup['original_row']['Document ID']}")
        print(f"  Duplicate: {dup['duplicate_row']['Document ID']}")
        print(f"  Match: {dup['match_info']['match_type']} ({dup['match_info']['match_score']}%)")
        
        action = input("Keep (o)riginal, (d)elete duplicate, or (s)kip? ")
        if action == 'd':
            # Mark for deletion (implementation depends on your needs)
            print("Marked for deletion")
```

## License

MIT License - feel free to use and modify for your projects.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Google Sheets API documentation
3. Check duplicate detection logs in `duplicate_log.json`
4. Use the duplicate manager CLI for diagnostics
5. Open an issue with detailed error information