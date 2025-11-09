# GitHub Repository Management Scripts

This directory contains secure scripts to manage the visibility of your GitHub repositories.

## 🔐 Security First!

**⚠️ CRITICAL SECURITY WARNING:**
- **NEVER commit your GitHub token to a repository**
- The token I saw in your message should be rotated immediately
- Use environment variables or secure token storage

## 🚀 Quick Start

### 1. Set Up Your Token Securely
```bash
# Run the setup script for guidance
./setup_github_token.sh
```

### 2. Simple: Make All Repos Private
```bash
# Set your token (replace with your actual token)
export GITHUB_TOKEN="your_new_token_here"

# Run the simple script
./make_repos_private.sh
```

### 3. Advanced: Full Management
```bash
# Run the comprehensive manager
./github_repo_manager.sh
```

## 📝 Scripts Overview

### `setup_github_token.sh`
- **Purpose**: Helps you securely configure your GitHub token
- **Features**: 
  - Security guidance
  - Token validation
  - Interactive setup
- **Usage**: `./setup_github_token.sh`

### `make_repos_private.sh`
- **Purpose**: Simple script to make all your repos private (like your original)
- **Features**:
  - Batch processing with error handling
  - Confirmation prompts
  - Progress tracking
  - Rate limiting
- **Usage**: `./make_repos_private.sh`

### `github_repo_manager.sh`
- **Purpose**: Comprehensive repository management
- **Features**:
  - Interactive menu system
  - View repository status
  - Make all repos private
  - Make specific repos public
  - API rate limit monitoring
  - Detailed reporting
- **Usage**: `./github_repo_manager.sh`

## 🔧 Token Setup Options

### Option 1: Temporary (Current Session)
```bash
export GITHUB_TOKEN="your_token_here"
./make_repos_private.sh
```

### Option 2: Persistent (Add to Shell Profile)
```bash
# Add to ~/.zshrc (for zsh) or ~/.bash_profile (for bash)
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### Option 3: Environment File
```bash
# Create .env file (add to .gitignore!)
echo 'GITHUB_TOKEN=your_token_here' > .env
source .env
```

## 🛡️ Security Best Practices

### 1. Token Permissions
Your GitHub token needs these scopes:
- `repo` - Full control of repositories
- `public_repo` - Access to public repositories

### 2. Token Security
- ✅ Store in environment variables
- ✅ Use minimal required permissions
- ✅ Rotate tokens regularly
- ✅ Add token files to .gitignore
- ❌ Never commit tokens to git
- ❌ Never share tokens in plain text

### 3. Create New Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`
4. Copy the generated token
5. Store securely using methods above

## 📊 Usage Examples

### Check Current Status
```bash
./github_repo_manager.sh
# Choose option 1: Show current repository status
```

### Make All Repos Private
```bash
export GITHUB_TOKEN="your_token"
./make_repos_private.sh
```

### Make Specific Repos Public
```bash
./github_repo_manager.sh
# Choose option 3: Make specific repositories public
```

### Monitor API Usage
```bash
./github_repo_manager.sh
# Choose option 5: Check API rate limit
```

## 🔧 Troubleshooting

### "jq: command not found"
```bash
# Install jq
brew install jq  # macOS
sudo apt-get install jq  # Ubuntu/Debian
```

### "API Error: Bad credentials"
- Check your token is correct
- Ensure token has required permissions
- Verify token hasn't expired

### "API Error: Not Found"
- Check the repository name exists
- Verify you have access to the repository
- Ensure token has appropriate permissions

### Rate Limiting Issues
- The scripts include automatic delays
- Check rate limits with option 5 in the manager
- Wait if you've hit rate limits

## 🎯 What Each Script Does

### For Existing Repositories:
1. **Fetches all your repositories** (with pagination)
2. **Checks current visibility** status
3. **Updates visibility** as requested
4. **Provides detailed feedback** and error handling

### For Future Repositories:
- **Manual**: Select "Private" when creating via GitHub web interface
- **CLI**: Use `gh repo create --private repo-name`
- **API**: Include `"private": true` in repository creation calls

## 📋 Output Examples

### Status Check Output:
```
Repository                                     Visibility  Created      Description
Knowledge-Jibber-Jabber-Bash-                 public      2024-10-14   Research project
my-private-project                             private     2024-10-10   Personal work
...

Summary: 15 total repositories (8 private, 7 public)
```

### Privacy Update Output:
```
🔒 Making all repositories private for user: GeorgeDoors888

Found 15 repositories
Processing: Knowledge-Jibber-Jabber-Bash-
   ✅ Successfully made private
Processing: my-project
   ✅ Successfully made private

📊 SUMMARY:
   Total repositories: 15
   Successfully made private: 15
   Errors: 0
```

## 🔒 Token Rotation

If you suspect your token is compromised:

1. **Immediately revoke the old token**:
   - Go to: https://github.com/settings/tokens
   - Find your token and click "Delete"

2. **Create a new token**:
   - Generate new token with same permissions
   - Update your environment variables
   - Test with the scripts

3. **Check for unauthorized access**:
   - Review your repository audit logs
   - Check for unexpected changes

## 📞 Support

If you encounter issues:
1. Check your token permissions
2. Verify API rate limits
3. Review error messages in script output
4. Check GitHub's API status page
5. Ensure repositories exist and you have access