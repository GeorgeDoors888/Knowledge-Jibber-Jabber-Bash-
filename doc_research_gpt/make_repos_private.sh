#!/bin/bash

# Simple GitHub Repository Privacy Script
# Based on your original script but with security and error handling improvements

set -e  # Exit on error

# Configuration
GITHUB_USER="GeorgeDoors888"

# Security check
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GITHUB_TOKEN not set"
    echo "Run: ./setup_github_token.sh first"
    exit 1
fi

echo "🔒 Making all repositories private for user: $GITHUB_USER"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install jq
    else
        echo "Please install jq: brew install jq"
        exit 1
    fi
fi

# Fetch all repos with pagination
echo "📡 Fetching repositories..."
all_repos=""
page=1

while true; do
    response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/user/repos?per_page=100&page=$page")
    
    # Check for API errors
    error=$(echo "$response" | jq -r '.message // empty')
    if [ ! -z "$error" ]; then
        echo "❌ API Error: $error"
        echo "Check your token permissions and rate limits"
        exit 1
    fi
    
    repos=$(echo "$response" | jq -r '.[].name // empty')
    
    if [ -z "$repos" ]; then
        break
    fi
    
    all_repos="$all_repos $repos"
    page=$((page + 1))
    echo "   Fetched page $page..."
done

# Convert to array and count
repo_array=($all_repos)
total_repos=${#repo_array[@]}

echo "Found $total_repos repositories"
echo ""

# Confirmation
echo "⚠️  This will make ALL $total_repos repositories PRIVATE"
echo "Current repositories:"
for repo in "${repo_array[@]:0:10}"; do
    echo "   • $repo"
done

if [ $total_repos -gt 10 ]; then
    echo "   ... and $((total_repos - 10)) more"
fi

echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled"
    exit 0
fi

# Process each repository
echo ""
echo "🔄 Processing repositories..."
success_count=0
error_count=0

for repo in "${repo_array[@]}"; do
    echo "Processing: $repo"
    
    response=$(curl -s -X PATCH \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$GITHUB_USER/$repo" \
        -d '{"private": true}')
    
    # Check result
    error=$(echo "$response" | jq -r '.message // empty')
    private=$(echo "$response" | jq -r '.private // false')
    
    if [ ! -z "$error" ]; then
        echo "   ❌ Error: $error"
        error_count=$((error_count + 1))
    elif [ "$private" = "true" ]; then
        echo "   ✅ Successfully made private"
        success_count=$((success_count + 1))
    else
        echo "   ⚠️  Unexpected response"
        error_count=$((error_count + 1))
    fi
    
    # Rate limiting
    sleep 1
done

# Summary
echo ""
echo "📊 SUMMARY:"
echo "   Total repositories: $total_repos"
echo "   Successfully made private: $success_count"
echo "   Errors: $error_count"
echo ""

if [ $error_count -gt 0 ]; then
    echo "⚠️  Some repositories had errors. Check your token permissions."
    echo "Required scopes: 'repo' (full repository access)"
else
    echo "🎉 All repositories successfully made private!"
fi

echo ""
echo "ℹ️  For future repositories:"
echo "   - Use GitHub CLI: gh repo create --private your-repo-name"
echo "   - Or select 'Private' when creating via web interface"