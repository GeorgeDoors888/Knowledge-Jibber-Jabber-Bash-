#!/bin/bash

# Knowledge Jibber Jabber Bash - Complete Setup Script
# This script helps set up all components of the repository

echo "🚀 Knowledge Jibber Jabber Bash - Setup"
echo "======================================="
echo ""

# Check current directory
if [ ! -d "multi_sheet_system" ] || [ ! -d "github_management" ] || [ ! -d "document_processing" ]; then
    echo "❌ Error: Run this script from the repo directory"
    echo "Expected directory structure:"
    echo "  repo/"
    echo "  ├── multi_sheet_system/"
    echo "  ├── github_management/"
    echo "  └── document_processing/"
    exit 1
fi

echo "✅ Repository structure verified"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.6+"
    exit 1
fi

echo "✅ Python found: $($PYTHON_CMD --version)"

# Check pip
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo "❌ pip not found. Please install pip"
    exit 1
fi

echo "✅ pip found"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd multi_sheet_system
$PIP_CMD install -r requirements.txt
cd ..

echo "✅ Python dependencies installed"

# Check for jq (needed for GitHub management)
if command_exists jq; then
    echo "✅ jq found"
else
    echo "⚠️  jq not found - needed for GitHub management"
    if command_exists brew; then
        echo "   Installing jq via Homebrew..."
        brew install jq
        echo "✅ jq installed"
    else
        echo "   Please install jq manually:"
        echo "   - macOS: brew install jq"
        echo "   - Ubuntu: sudo apt-get install jq"
        echo "   - Others: https://stedolan.github.io/jq/download/"
    fi
fi

# Make GitHub scripts executable
echo ""
echo "🔧 Setting up GitHub management scripts..."
cd github_management
chmod +x *.sh
cd ..
echo "✅ GitHub scripts made executable"

# Setup instructions
echo ""
echo "🎯 SETUP COMPLETE!"
echo "=================="
echo ""
echo "Next steps:"
echo ""

echo "1️⃣  MULTI-SHEET SYSTEM SETUP:"
echo "   cd multi_sheet_system/"
echo "   # Place your service_account.json file here"
echo "   # Edit config.py with your settings"
echo "   python demo_multi_sheets.py  # Run demo"
echo ""

echo "2️⃣  GITHUB MANAGEMENT SETUP:"
echo "   cd github_management/"
echo "   ./setup_github_token.sh     # Setup token securely"
echo "   ./github_repo_manager.sh    # Interactive management"
echo ""

echo "3️⃣  DOCUMENT PROCESSING SETUP:"
echo "   cd document_processing/"
echo "   # Edit config.py with OpenAI API key"
echo "   python main.py               # Run processing"
echo ""

echo "📚 Documentation:"
echo "   • Main README: README.md"
echo "   • Multi-Sheet: multi_sheet_system/README_MultiSheets.md"
echo "   • GitHub: github_management/README_GitHub_Scripts.md"
echo ""

echo "🔐 Security reminders:"
echo "   • Never commit API keys or tokens"
echo "   • Use environment variables for secrets"
echo "   • Review all configuration files"
echo ""

echo "✨ You're ready to go! Choose a component to start with."