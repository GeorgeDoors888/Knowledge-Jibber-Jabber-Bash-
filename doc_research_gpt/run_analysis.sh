#!/bin/bash

# Google Drive Analysis Runner Script
# Run this from anywhere to start the analysis

echo "🚀 Starting Google Drive Analysis System..."

# Navigate to project directory
cd "/Users/georgemajor/Knowledge Jibber Jabber Bash/doc_research_gpt"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Navigate to system directory
cd repo/multi_sheet_system

# Check if OAuth credentials exist
if [ ! -f "oauth_credentials.json" ]; then
    echo "❌ oauth_credentials.json not found!"
    echo "Please ensure your OAuth credentials are in: $(pwd)"
    exit 1
fi

# Run the analysis
echo "📊 Running comprehensive Google Drive analysis..."
python oauth_demo.py

echo "✅ Analysis complete!"