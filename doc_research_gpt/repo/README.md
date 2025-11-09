# Knowledge Jibber Jabber Bash Repository

This repository contains a comprehensive collection of tools for document research, Google Sheets management, and GitHub repository management.

## 📂 Directory Structure

```
repo/
├── multi_sheet_system/     # Google Sheets management with duplicate detection
├── github_management/      # GitHub repository visibility management
├── document_processing/    # PDF processing and summarization tools
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Multi-Sheet Google Sheets System
Advanced Google Sheets management with automatic overflow and duplicate detection.

```bash
cd multi_sheet_system/
# Follow README_MultiSheets.md for setup
```

**Key Features:**
- Automatic sheet creation when capacity is reached
- Comprehensive duplicate detection (exact, fuzzy, hash-based)
- Batch processing for large datasets
- Real-time monitoring and reporting
- Smart data distribution across multiple sheets

### 2. GitHub Repository Management
Secure tools to manage GitHub repository visibility.

```bash
cd github_management/
# Follow README_GitHub_Scripts.md for setup
./setup_github_token.sh    # Set up token securely
./github_repo_manager.sh   # Interactive management
./make_repos_private.sh    # Batch make repos private
```

**Key Features:**
- Make all repositories private with one command
- Interactive repository management
- Security-first approach with token protection
- API rate limiting and error handling
- Selective repository visibility control

### 3. Document Processing
Tools for PDF processing and content summarization.

```bash
cd document_processing/
python main.py             # Main processing script
```

**Key Features:**
- PDF text extraction
- AI-powered summarization
- Content analysis and tagging
- Integration with Google Sheets for results

## 🛠️ Setup Requirements

### Common Dependencies
```bash
pip install -r multi_sheet_system/requirements.txt
```

### Google Sheets Setup
1. Create a Google Service Account
2. Download credentials as `service_account.json`
3. Enable Google Sheets API and Google Drive API
4. Place credentials in the multi_sheet_system directory

### GitHub Management Setup
1. Create a GitHub Personal Access Token
2. Grant `repo` permissions
3. Set token as environment variable: `export GITHUB_TOKEN="your_token"`

## 📋 Key Components

### Multi-Sheet System Components:
- **`multi_sheet_manager.py`** - Main orchestration class
- **`duplicate_detector.py`** - Advanced duplicate detection algorithms
- **`sheets_utils.py`** - Google Sheets API utilities
- **`drive_utils.py`** - Google Drive API utilities
- **`config.py`** - Configuration settings
- **`demo_multi_sheets.py`** - Comprehensive demonstration
- **`duplicate_manager.py`** - CLI duplicate management tool

### GitHub Management Components:
- **`github_repo_manager.sh`** - Interactive repository manager
- **`make_repos_private.sh`** - Simple batch privacy tool
- **`setup_github_token.sh`** - Secure token setup utility

### Document Processing Components:
- **`main.py`** - Main processing pipeline
- **`pdf_parser.py`** - PDF text extraction
- **`summarizer.py`** - AI summarization

## 🔧 Configuration

### Multi-Sheet System Config (`config.py`):
```python
# Sheet capacity limits
MAX_ROWS_PER_SHEET = 5000
MAX_SHEETS_PER_SPREADSHEET = 10

# Duplicate detection
ENABLE_DUPLICATE_DETECTION = True
DUPLICATE_DETECTION_METHOD = "multi"
DUPLICATE_ACTION = "skip"

# Google Drive folder
DRIVE_FOLDER_ID = None  # None for root folder
```

### GitHub Management:
```bash
# Required environment variable
export GITHUB_TOKEN="your_github_token"
```

## 🎯 Use Cases

### 1. Large-Scale Document Processing
Process thousands of documents with automatic Google Sheets organization:
```python
from multi_sheet_manager import MultiSheetManager

manager = MultiSheetManager(enable_duplicate_detection=True)
for doc in documents:
    result = manager.add_data(process_document(doc))
```

### 2. Repository Privacy Management
Make all GitHub repositories private:
```bash
export GITHUB_TOKEN="your_token"
./make_repos_private.sh
```

### 3. Duplicate-Free Data Collection
Collect data with automatic duplicate prevention:
```python
manager = MultiSheetManager()
manager.configure_duplicate_detection(method="fuzzy", threshold=85)
results = manager.add_batch_data(large_dataset)
```

## 🛡️ Security Features

### GitHub Management:
- Environment variable token storage
- Token format validation
- API rate limiting
- Comprehensive error handling
- Secure token setup guidance

### Multi-Sheet System:
- Service account authentication
- Configurable access controls
- Audit logging for duplicates
- Data integrity checks

## 📊 Monitoring and Reporting

### Multi-Sheet System:
- Real-time capacity monitoring
- Duplicate detection statistics
- Comprehensive status reports
- Performance metrics

### GitHub Management:
- Repository status overview
- Batch operation results
- API usage tracking
- Error reporting

## 🔍 Advanced Features

### Duplicate Detection Strategies:
- **Exact Match**: Perfect field matching
- **Fuzzy Match**: Similarity-based detection (configurable threshold)
- **Content Hash**: Content fingerprinting
- **Title Similarity**: Document title matching
- **Multi-Method**: Combined approach

### GitHub Repository Management:
- Pagination for large repository counts
- Interactive repository selection
- Bulk operations with confirmations
- Rate limit monitoring

## 📚 Documentation

Each component has detailed documentation:
- **Multi-Sheet System**: `multi_sheet_system/README_MultiSheets.md`
- **GitHub Management**: `github_management/README_GitHub_Scripts.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## 📞 Support

For issues:
1. Check component-specific README files
2. Review configuration settings
3. Check API credentials and permissions
4. Verify dependencies are installed
5. Review error logs and messages

## 🔒 Security Notes

- Never commit API tokens or credentials to version control
- Use environment variables for sensitive data
- Regularly rotate access tokens
- Follow principle of least privilege for API permissions
- Review and audit access logs regularly

---

**Last Updated**: October 14, 2025  
**Version**: 1.0.0  
**Author**: GeorgeDoors888