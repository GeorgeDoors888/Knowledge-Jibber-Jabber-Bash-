# Document Processing System

Tools for PDF processing, content analysis, and AI-powered summarization.

## 🚀 Quick Start

### 1. Setup Dependencies
```bash
pip install openai PyPDF2 pandas
```

### 2. Configure API Keys
Set your OpenAI API key in `config.py`:
```python
OPENAI_API_KEY = "your_openai_api_key"
```

### 3. Run Processing
```bash
python main.py
```

## 🛠️ Components

### `main.py`
- Main processing pipeline
- Coordinates PDF parsing and summarization
- Handles workflow orchestration

### `pdf_parser.py`  
- PDF text extraction
- Document structure analysis
- Content preprocessing

### `summarizer.py`
- AI-powered content summarization
- Key information extraction
- Tag generation

## 🎯 Features

### PDF Processing:
- Text extraction from PDF files
- Metadata extraction
- Content structure analysis

### AI Summarization:
- OpenAI GPT-powered summaries
- Configurable summary length
- Key topic identification
- Automatic tag generation

### Integration:
- Works with multi-sheet system for output
- Batch processing capabilities
- Error handling and logging

## ⚙️ Configuration

Edit settings in the main `config.py`:
```python
OPENAI_API_KEY = "your_key_here"
SEARCH_KEYWORDS = ["capacity", "forecast", "balancing"]
```

## 🔧 Usage Examples

### Process Single Document:
```python
from pdf_parser import extract_text_from_pdf
from summarizer import summarize_text

# Extract text
text = extract_text_from_pdf("document.pdf")

# Generate summary  
summary = summarize_text(text)
print(summary)
```

### Batch Processing:
```python
import os
from main import process_document_batch

# Process all PDFs in directory
pdf_files = [f for f in os.listdir(".") if f.endswith('.pdf')]
results = process_document_batch(pdf_files)
```

## 🔗 Integration with Multi-Sheet System

The document processing system integrates seamlessly with the multi-sheet management system:

```python
from multi_sheet_manager import MultiSheetManager
from pdf_parser import extract_text_from_pdf
from summarizer import summarize_text

manager = MultiSheetManager(base_name="DocumentProcessing")

# Process and store results
for pdf_file in pdf_files:
    text = extract_text_from_pdf(pdf_file)
    summary = summarize_text(text)
    
    result_data = {
        "Document ID": generate_id(pdf_file),
        "Document Title": extract_title(pdf_file),
        "Source URL": pdf_file,
        "Summary": summary,
        "Status": "Processed"
    }
    
    manager.add_data(result_data)
```

This automatically handles:
- Duplicate detection for processed documents
- Automatic sheet creation when capacity is reached
- Comprehensive tracking and reporting