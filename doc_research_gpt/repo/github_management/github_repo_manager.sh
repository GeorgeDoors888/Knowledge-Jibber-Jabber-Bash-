#!/bin/bash

# GitHub Repository Visibility Management Script
# This script helps manage the visibility of your GitHub repositories
# 
# SECURITY WARNING: Never commit GitHub tokens to repositories!
# Use environment variables or secure token storage instead.

set -e  # Exit on any error

# Configuration
GITHUB_USER="GeorgeDoors888"

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GITHUB_TOKEN environment variable not set"
    echo "Please set your GitHub token:"
    echo "export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

# Validate GitHub token format
if [[ ! "$GITHUB_TOKEN" =~ ^ghp_[A-Za-z0-9]{36}$ ]]; then
    echo "⚠️  WARNING: Token format doesn't match expected GitHub personal access token format"
    echo "Expected format: ghp_[36 characters]"
    echo "Proceeding anyway..."
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ ERROR: jq is required but not installed"
    echo "Install with: brew install jq (on macOS) or apt-get install jq (on Ubuntu)"
    exit 1
fi

# Function to check API rate limit
check_rate_limit() {
    local response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
        "https://api.github.com/rate_limit")
    
    local remaining=$(echo "$response" | jq -r '.rate.remaining // 0')
    local limit=$(echo "$response" | jq -r '.rate.limit // 0')
    
    echo "📊 API Rate Limit: $remaining/$limit requests remaining"
    
    if [ "$remaining" -lt 10 ]; then
        echo "⚠️  WARNING: Low API rate limit remaining. Consider waiting before proceeding."
    fi
}

# Function to get all repositories
get_all_repos() {
    echo "📡 Fetching all repositories for user: $GITHUB_USER"
    
    local all_repos=""
    local page=1
    local per_page=100
    
    while true; do
        echo "   Fetching page $page..."
        
        local response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/user/repos?per_page=$per_page&page=$page&sort=created&direction=desc")
        
        # Check for API errors
        local error=$(echo "$response" | jq -r '.message // empty')
        if [ ! -z "$error" ]; then
            echo "❌ API Error: $error"
            exit 1
        fi
        
        local repos=$(echo "$response" | jq -r '.[].full_name // empty')
        
        if [ -z "$repos" ]; then
            break
        fi
        
        all_repos="$all_repos$repos\n"
        page=$((page + 1))
        
        # Rate limiting - small delay between requests
        sleep 0.5
    done
    
    echo -e "$all_repos" | grep -v '^$'
}

# Function to get repository info
get_repo_info() {
    local repo_name=$1
    
    local response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$repo_name")
    
    local private=$(echo "$response" | jq -r '.private // false')
    local created_at=$(echo "$response" | jq -r '.created_at // ""')
    local updated_at=$(echo "$response" | jq -r '.updated_at // ""')
    local description=$(echo "$response" | jq -r '.description // "No description"')
    
    echo "$private|$created_at|$updated_at|$description"
}

# Function to update repository visibility
update_repo_visibility() {
    local repo_name=$1
    local make_private=$2
    local current_private=$3
    
    # Skip if already in desired state
    if [ "$make_private" = true ] && [ "$current_private" = "true" ]; then
        echo "   ✓ Already private, skipping"
        return 0
    elif [ "$make_private" = false ] && [ "$current_private" = "false" ]; then
        echo "   ✓ Already public, skipping"
        return 0
    fi
    
    # Determine action
    local visibility_text="public"
    if [ "$make_private" = true ]; then
        visibility_text="private"
    fi
    
    echo "   🔄 Making $visibility_text..."
    
    local response=$(curl -s -X PATCH \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$repo_name" \
        -d "{\"private\": $make_private}")
    
    # Check for errors
    local error=$(echo "$response" | jq -r '.message // empty')
    if [ ! -z "$error" ]; then
        echo "   ❌ Error: $error"
        return 1
    fi
    
    local new_private=$(echo "$response" | jq -r '.private // false')
    if [ "$new_private" = "$make_private" ]; then
        echo "   ✅ Successfully updated to $visibility_text"
        return 0
    else
        echo "   ❌ Update failed - visibility not changed"
        return 1
    fi
}

# Function to make existing repos private
make_existing_repos_private() {
    echo ""
    echo "🔒 Making all existing repositories private..."
    echo ""
    
    local repos=$(get_all_repos)
    local total_count=$(echo "$repos" | wc -l | tr -d ' ')
    local current=0
    local success_count=0
    local skip_count=0
    local error_count=0
    
    echo "Found $total_count repositories to process"
    echo ""
    
    while IFS= read -r repo; do
        if [ -z "$repo" ]; then
            continue
        fi
        
        current=$((current + 1))
        echo "[$current/$total_count] Processing: $repo"
        
        # Get current repo info
        local info=$(get_repo_info "$repo")
        local current_private=$(echo "$info" | cut -d'|' -f1)
        local created_at=$(echo "$info" | cut -d'|' -f2)
        
        echo "   Current status: $([ "$current_private" = "true" ] && echo "private" || echo "public")"
        echo "   Created: $(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$created_at" "+%Y-%m-%d" 2>/dev/null || echo "$created_at")"
        
        if update_repo_visibility "$repo" true "$current_private"; then
            if [ "$current_private" = "true" ]; then
                skip_count=$((skip_count + 1))
            else
                success_count=$((success_count + 1))
            fi
        else
            error_count=$((error_count + 1))
        fi
        
        echo ""
        sleep 1  # Rate limiting
    done <<< "$repos"
    
    echo "📊 Summary:"
    echo "   Total repositories: $total_count"
    echo "   Successfully updated: $success_count"
    echo "   Already private (skipped): $skip_count"
    echo "   Errors: $error_count"
}

# Function to set default visibility for future repos (via organization settings)
configure_future_repos() {
    echo ""
    echo "⚙️  Configuring default visibility for future repositories..."
    echo ""
    
    echo "ℹ️  Note: GitHub personal accounts don't have organization-level settings."
    echo "   Future repository visibility must be set when creating each repo."
    echo "   Consider using the GitHub CLI or API with default templates."
    echo ""
    echo "   For new repos created via web interface:"
    echo "   1. Go to https://github.com/new"
    echo "   2. Select 'Private' by default"
    echo ""
    echo "   For new repos via CLI:"
    echo "   gh repo create --private your-repo-name"
}

# Function to show current repository status
show_repo_status() {
    echo ""
    echo "📋 Current Repository Status:"
    echo ""
    
    local repos=$(get_all_repos)
    local total=0
    local private_count=0
    local public_count=0
    
    printf "%-50s %-10s %-12s %s\n" "Repository" "Visibility" "Created" "Description"
    printf "%-50s %-10s %-12s %s\n" "$(printf '%.0s-' {1..50})" "$(printf '%.0s-' {1..10})" "$(printf '%.0s-' {1..12})" "$(printf '%.0s-' {1..20})"
    
    while IFS= read -r repo; do
        if [ -z "$repo" ]; then
            continue
        fi
        
        local info=$(get_repo_info "$repo")
        local private=$(echo "$info" | cut -d'|' -f1)
        local created_at=$(echo "$info" | cut -d'|' -f2)
        local description=$(echo "$info" | cut -d'|' -f4)
        
        local visibility="public"
        if [ "$private" = "true" ]; then
            visibility="private"
            private_count=$((private_count + 1))
        else
            public_count=$((public_count + 1))
        fi
        
        local created_date=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$created_at" "+%Y-%m-%d" 2>/dev/null || echo "unknown")
        local short_desc="${description:0:30}"
        
        printf "%-50s %-10s %-12s %s\n" "${repo:0:49}" "$visibility" "$created_date" "$short_desc"
        total=$((total + 1))
        
        sleep 0.2  # Small delay to avoid rate limiting
    done <<< "$repos"
    
    echo ""
    echo "📊 Summary: $total total repositories ($private_count private, $public_count public)"
}

# Main menu
show_menu() {
    echo ""
    echo "🚀 GitHub Repository Visibility Manager"
    echo "======================================"
    echo ""
    echo "User: $GITHUB_USER"
    echo ""
    echo "Options:"
    echo "1) Show current repository status"
    echo "2) Make all existing repositories private"
    echo "3) Make specific repositories public"
    echo "4) Configure future repository settings"
    echo "5) Check API rate limit"
    echo "6) Exit"
    echo ""
}

# Function to make specific repos public
make_specific_repos_public() {
    echo ""
    echo "🌍 Make specific repositories public"
    echo ""
    
    local repos=$(get_all_repos)
    echo "Available repositories:"
    echo ""
    
    local i=1
    local repo_array=()
    
    while IFS= read -r repo; do
        if [ -z "$repo" ]; then
            continue
        fi
        
        local info=$(get_repo_info "$repo")
        local private=$(echo "$info" | cut -d'|' -f1)
        local visibility="public"
        
        if [ "$private" = "true" ]; then
            visibility="private"
        fi
        
        echo "$i) $repo ($visibility)"
        repo_array+=("$repo")
        i=$((i + 1))
        sleep 0.1
    done <<< "$repos"
    
    echo ""
    echo "Enter repository numbers to make public (comma-separated, e.g., 1,3,5):"
    echo "Or 'all' to make all repositories public:"
    read -r selection
    
    if [ "$selection" = "all" ]; then
        echo "Making all repositories public..."
        while IFS= read -r repo; do
            if [ -z "$repo" ]; then
                continue
            fi
            
            local info=$(get_repo_info "$repo")
            local current_private=$(echo "$info" | cut -d'|' -f1)
            
            echo "Processing: $repo"
            update_repo_visibility "$repo" false "$current_private"
            sleep 1
        done <<< "$repos"
    else
        # Parse comma-separated selection
        IFS=',' read -ra SELECTED <<< "$selection"
        
        for num in "${SELECTED[@]}"; do
            num=$(echo "$num" | tr -d ' ')  # Remove whitespace
            
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#repo_array[@]}" ]; then
                local repo="${repo_array[$((num-1))]}"
                local info=$(get_repo_info "$repo")
                local current_private=$(echo "$info" | cut -d'|' -f1)
                
                echo "Processing: $repo"
                update_repo_visibility "$repo" false "$current_private"
                sleep 1
            else
                echo "⚠️  Invalid selection: $num"
            fi
        done
    fi
}

# Main execution
main() {
    echo "🔐 GitHub Repository Visibility Manager"
    echo "====================================="
    
    # Initial checks
    check_rate_limit
    
    while true; do
        show_menu
        read -p "Choose an option (1-6): " choice
        
        case $choice in
            1)
                show_repo_status
                ;;
            2)
                echo ""
                read -p "⚠️  This will make ALL your repositories private. Continue? (y/N): " confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    make_existing_repos_private
                else
                    echo "Operation cancelled."
                fi
                ;;
            3)
                make_specific_repos_public
                ;;
            4)
                configure_future_repos
                ;;
            5)
                check_rate_limit
                ;;
            6)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please choose 1-6."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main