# Google Drive Comprehensive Analysis System

## 🚀 Overview

A powerful system for comprehensive Google Drive metadata extraction, advanced duplicate detection, and auto-scaling Google Sheets management. This system provides complete visibility into your Google Drive usage with sophisticated duplicate detection and automated reporting.

### ✨ Key Features

- **📡 Complete Google Drive API Integration**: Extract comprehensive metadata from all files
- **🔍 Advanced Multi-Algorithm Duplicate Detection**: Uses hashes, fuzzy matching, perceptual image analysis
- **📊 Auto-Scaling Google Sheets**: Automatically create new sheets when size limits are reached
- **🔐 Security Analysis**: Detect sharing patterns and permission issues
- **📈 Comprehensive Reporting**: Detailed analysis with actionable recommendations
- **⚡ Performance Optimized**: Parallel processing, caching, and intelligent batching

## 🛠️ Quick Setup

### 1. Prerequisites
- Python 3.8+
- Google Cloud Project with Drive and Sheets APIs enabled
- Service Account with JSON credentials

### 2. Installation
```bash
# Install all required dependencies
pip install -r requirements.txt
```

### 3. Configuration
Place your service account JSON file in the project directory and update `enhanced_config.py`:
```python
SERVICE_ACCOUNT_FILE = 'path/to/your/service-account.json'
```

### 4. Quick Start Demo
```bash
# Run interactive demo
python demo_comprehensive_system.py
```

## 📊 System Components

### Core Modules

1. **`drive_metadata_manager.py`**: Complete Google Drive API integration
2. **`advanced_duplicate_detector.py`**: Multi-strategy duplicate detection  
3. **`auto_scaling_sheets.py`**: Auto-scaling Google Sheets management
4. **`comprehensive_drive_manager.py`**: Main orchestration system
5. **`enhanced_config.py`**: Comprehensive configuration management

### Usage Examples
duplicate_report = manager.find_all_duplicates()
```

## 🔍 Duplicate Detection Features

- **Multiple Detection Methods**: exact, fuzzy, hash, multi-method
- **Configurable Actions**: skip, flag, update, allow duplicates
- **Smart Field Selection**: choose which fields to check
- **Real-time Prevention**: detect before adding data
- **Comprehensive Reporting**: detailed duplicate analysis

## 🛠️ Tools Included

- **`multi_sheet_manager.py`** - Main management class
- **`duplicate_detector.py`** - Advanced duplicate detection
- **`duplicate_manager.py`** - CLI duplicate management tool  
- **`demo_multi_sheets.py`** - Comprehensive examples
- **`find_spreadsheets.py`** - Locate existing spreadsheets

## 📊 Demo

Run the comprehensive demonstration:
```bash
python demo_multi_sheets.py
```

This creates test spreadsheets showing:
- Basic operations
- Large dataset handling
- Duplicate detection scenarios
- Status monitoring
- Cleanup operations

## ⚙️ Configuration Options

```python
# Sheet capacity
MAX_ROWS_PER_SHEET = 5000
MAX_SHEETS_PER_SPREADSHEET = 10

# Duplicate detection
DUPLICATE_CHECK_FIELDS = ["Document ID", "Source URL"]
DUPLICATE_DETECTION_METHOD = "multi"  # exact, fuzzy, hash, multi
FUZZY_MATCH_THRESHOLD = 85

# Actions for duplicates
DUPLICATE_ACTION = "skip"  # skip, flag, update, allow
```

For complete documentation, see `README_MultiSheets.md`.