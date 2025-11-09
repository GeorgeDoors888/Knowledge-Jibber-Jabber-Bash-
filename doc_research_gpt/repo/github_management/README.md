# GitHub Repository Management

Secure tools for managing GitHub repository visibility with comprehensive error handling and safety features.

## 🔐 Security First!

**⚠️ NEVER commit GitHub tokens to repositories!**

## 🚀 Quick Start

### 1. Setup Token Securely
```bash
./setup_github_token.sh
```

### 2. Set Environment Variable
```bash
export GITHUB_TOKEN="your_new_token_here"
```

### 3. Choose Your Tool

#### Simple: Make All Repos Private
```bash
./make_repos_private.sh
```

#### Advanced: Interactive Management
```bash
./github_repo_manager.sh
```

## 🛠️ Tools Included

### `setup_github_token.sh`
- Security guidance and best practices
- Interactive token setup
- Token validation and format checking

### `make_repos_private.sh`
- Simple batch operation to make all repos private
- Improved version of basic GitHub API script
- Confirmation prompts and error handling

### `github_repo_manager.sh`
- Full interactive management system
- View repository status
- Selective repository updates
- API rate limit monitoring

## 🔧 Token Requirements

Your GitHub token needs:
- **Scope**: `repo` (Full control of repositories)
- **Permissions**: Read/write access to repository settings

### Create Token:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select `repo` scope
4. Copy token and store securely

## 📋 Features

### Security Features:
- Environment variable token storage
- Token format validation
- Never hardcode credentials
- Secure setup guidance

### Management Features:
- Batch operations with progress tracking
- Individual repository selection
- Comprehensive status reporting
- API rate limiting and error handling

### Safety Features:
- Confirmation prompts for destructive actions
- Dry-run capabilities
- Detailed error reporting
- Rate limit monitoring

## 🎯 Use Cases

### Make All Repositories Private:
```bash
export GITHUB_TOKEN="your_token"
./make_repos_private.sh
```

### Interactive Repository Management:
```bash
./github_repo_manager.sh
# Choose from menu:
# 1) Show current repository status
# 2) Make all existing repositories private  
# 3) Make specific repositories public
# 4) Check API rate limit
```

### Check Repository Status:
```bash
./github_repo_manager.sh
# Option 1 shows detailed status of all repos
```

## 🛡️ Security Best Practices

1. **Token Storage**: Use environment variables only
2. **Token Permissions**: Minimal required scopes
3. **Token Rotation**: Regular token updates
4. **Access Control**: Never share tokens
5. **Monitoring**: Review repository access logs

## 🔧 Troubleshooting

### Common Issues:
- **"Bad credentials"**: Check token is correct and has permissions
- **"jq not found"**: Install with `brew install jq`
- **Rate limiting**: Wait and retry, or use built-in delays

For complete documentation, see `README_GitHub_Scripts.md`.