#!/bin/bash

# GitHub Token Setup Script
# This script helps you securely set up your GitHub token

echo "🔐 GitHub Token Setup"
echo "===================="
echo ""

# Check if token is already set
if [ ! -z "$GITHUB_TOKEN" ]; then
    echo "✅ GitHub token is already set in environment"
    echo "Token starts with: ${GITHUB_TOKEN:0:8}..."
    echo ""
else
    echo "⚠️  GitHub token not found in environment"
    echo ""
fi

echo "SECURITY RECOMMENDATIONS:"
echo "========================"
echo ""
echo "1. 🚫 NEVER commit tokens to git repositories"
echo "2. 🔒 Store tokens in environment variables or secure vaults"
echo "3. 🔄 Rotate tokens regularly"
echo "4. 📝 Use minimal required permissions (repo scope)"
echo ""

echo "SAFE WAYS TO SET YOUR TOKEN:"
echo "============================"
echo ""

echo "Option 1: Temporary (current session only)"
echo "export GITHUB_TOKEN='your_token_here'"
echo ""

echo "Option 2: Persistent (add to ~/.zshrc or ~/.bash_profile)"
echo "echo 'export GITHUB_TOKEN=\"your_token_here\"' >> ~/.zshrc"
echo "source ~/.zshrc"
echo ""

echo "Option 3: Use a .env file (then load it)"
echo "echo 'GITHUB_TOKEN=your_token_here' > .env"
echo "source .env"
echo ""

echo "TOKEN PERMISSIONS NEEDED:"
echo "========================"
echo "Your GitHub token needs these scopes:"
echo "• repo (Full control of private repositories)"
echo "• public_repo (Access to public repositories)"
echo ""

echo "TO CREATE A NEW TOKEN:"
echo "====================="
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select required scopes: 'repo'"
echo "4. Copy the generated token"
echo "5. Set it using one of the methods above"
echo ""

# Offer to set token interactively
echo "Would you like to set the token now? (It will only be set for this session)"
read -p "Set token interactively? (y/N): " set_token

if [[ $set_token =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔒 Enter your GitHub token (input will be hidden):"
    read -s github_token
    
    if [ ! -z "$github_token" ]; then
        export GITHUB_TOKEN="$github_token"
        echo ""
        echo "✅ Token set for current session!"
        echo "Token starts with: ${GITHUB_TOKEN:0:8}..."
        
        # Validate token format
        if [[ "$GITHUB_TOKEN" =~ ^ghp_[A-Za-z0-9]{36}$ ]]; then
            echo "✅ Token format looks correct"
        else
            echo "⚠️  Warning: Token format doesn't match expected GitHub format"
        fi
        
        echo ""
        echo "You can now run: ./github_repo_manager.sh"
    else
        echo ""
        echo "❌ No token entered"
    fi
fi

echo ""
echo "📚 Next steps:"
echo "1. Set your GitHub token using one of the methods above"
echo "2. Run: ./github_repo_manager.sh"
echo "3. Choose option 1 to see current repository status"
echo "4. Choose option 2 to make all repos private"