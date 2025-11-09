# Enhanced Configuration for Comprehensive Drive Management System
# This file contains all configuration options for the multi-sheet system with Google Drive integration

import os
from datetime import datetime

# =============================================================================
# GOOGLE API CONFIGURATION
# =============================================================================

# Service Account Configuration
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# =============================================================================
# GOOGLE SHEETS CONFIGURATION
# =============================================================================

# Base name for the sheet series
BASE_SHEET_NAME = "Drive_Metadata_Analysis"

# Sheet size limits and safety margins
MAX_CELLS_PER_SHEET = 2000000      # Google Sheets limit: 2M cells
MAX_ROWS_PER_SHEET = 1000000       # Google Sheets limit: 1M rows
SAFE_CELL_LIMIT = 1800000          # 90% of max (safety margin)
SAFE_ROW_LIMIT = 900000            # 90% of max (safety margin)

# Batch processing settings
BATCH_SIZE = 1000                  # Files to process per batch
API_DELAY_SECONDS = 0.1            # Delay between API calls to avoid rate limits

# =============================================================================
# GOOGLE DRIVE SCANNING CONFIGURATION
# =============================================================================

# File scanning limits
MAX_FILES_PER_SCAN = None          # None for unlimited, or set a number
INCLUDE_TRASHED_FILES = False      # Whether to include files in trash
ENABLE_FOLDER_STRUCTURE_SCAN = True  # Build complete folder hierarchy

# Metadata fields to extract (comprehensive list)
DRIVE_METADATA_FIELDS = (
    'id,name,mimeType,size,createdTime,modifiedTime,lastModifyingUser,'
    'owners,parents,shared,webViewLink,webContentLink,thumbnailLink,'
    'iconLink,hasThumbnail,trashed,explicitlyTrashed,spaces,version,'
    'originalFilename,fileExtension,md5Checksum,sha1Checksum,sha256Checksum,'
    'copyRequiresWriterPermission,writersCanShare,viewedByMe,viewedByMeTime,'
    'permissions,capabilities,properties,appProperties,folderColorRgb,'
    'isAppAuthorized,teamDriveId,driveId,hasAugmentedPermissions'
)

# File filtering options
MIN_FILE_SIZE_BYTES = 0            # Minimum file size to include (0 for all)
MAX_FILE_SIZE_BYTES = None         # Maximum file size (None for unlimited)
EXCLUDE_FILE_TYPES = [             # MIME types to exclude
    'application/vnd.google-apps.shortcut'
]

# =============================================================================
# DUPLICATE DETECTION CONFIGURATION
# =============================================================================

# Main duplicate detection settings
DUPLICATE_DETECTION = {
    # Similarity thresholds (0-100)
    'name_similarity_threshold': 85,      # For fuzzy name matching
    'fuzzy_match_threshold': 90,          # For advanced fuzzy matching
    'content_similarity_threshold': 95,    # For content comparison
    
    # Size comparison settings
    'size_variance_threshold': 0.05,      # 5% size variance allowed
    'min_file_size_mb': 0.1,             # Ignore files smaller than 100KB
    
    # Image analysis settings
    'image_hash_threshold': 5,            # Perceptual hash difference threshold
    'enable_image_analysis': True,        # Enable image duplicate detection
    
    # Advanced features
    'enable_fuzzy_matching': True,        # Enable fuzzy string matching
    'enable_content_analysis': True,      # Enable content-based detection
    'enable_cross_category_detection': True,  # Check across file types
    
    # Performance settings
    'max_comparison_group_size': 1000,    # Max files to compare in one group
    'parallel_processing': False,         # Enable parallel processing (experimental)
    'cache_results': True                 # Cache intermediate results
}

# Detection strategy weights (0.0 to 1.0)
DETECTION_STRATEGIES = {
    'exact_hash': {'weight': 1.0, 'confidence': 'high'},
    'content_similarity': {'weight': 0.9, 'confidence': 'high'},
    'perceptual_image': {'weight': 0.8, 'confidence': 'high'},
    'metadata_similarity': {'weight': 0.7, 'confidence': 'medium'},
    'name_similarity': {'weight': 0.6, 'confidence': 'medium'},
    'semantic_similarity': {'weight': 0.5, 'confidence': 'medium'},
    'size_similarity': {'weight': 0.3, 'confidence': 'low'}
}

# =============================================================================
# EXPORT AND REPORTING CONFIGURATION
# =============================================================================

# Export settings
EXPORT_SETTINGS = {
    'create_summary_report': True,        # Generate text summary
    'export_duplicate_details': True,     # Export detailed duplicate info
    'export_file_metadata': True,         # Export complete metadata
    'export_format': 'json',             # Default format: 'json' or 'csv'
    'include_thumbnails': False,          # Download and include thumbnails
    'compress_exports': True              # Compress large export files
}

# Report generation settings
REPORT_SETTINGS = {
    'include_recommendations': True,      # Generate actionable recommendations
    'security_analysis': True,           # Analyze sharing and permissions
    'storage_optimization': True,        # Analyze storage usage patterns
    'trend_analysis': False,             # Historical trend analysis (requires multiple scans)
    'detailed_statistics': True         # Include detailed statistical breakdowns
}

# =============================================================================
# SECURITY AND PRIVACY CONFIGURATION
# =============================================================================

# Security settings
SECURITY_SETTINGS = {
    'analyze_public_files': True,        # Flag publicly accessible files
    'analyze_sharing_patterns': True,    # Analyze unusual sharing
    'check_external_sharing': True,      # Flag files shared outside domain
    'privacy_scan': True,               # Scan for potentially sensitive files
    'permission_audit': True            # Audit file permissions
}

# Privacy-sensitive file patterns
PRIVACY_PATTERNS = [
    r'.*password.*',
    r'.*secret.*',
    r'.*key.*',
    r'.*credential.*',
    r'.*token.*',
    r'.*ssn.*',
    r'.*social.*security.*'
]

# =============================================================================
# PERFORMANCE AND OPTIMIZATION SETTINGS
# =============================================================================

# Performance tuning
PERFORMANCE_SETTINGS = {
    'concurrent_requests': 10,           # Max concurrent API requests
    'request_timeout': 30,               # Request timeout in seconds
    'retry_attempts': 3,                 # Number of retry attempts
    'backoff_multiplier': 2,            # Exponential backoff multiplier
    'enable_caching': True,             # Enable response caching
    'cache_duration_hours': 24          # Cache validity duration
}

# Memory management
MEMORY_SETTINGS = {
    'max_files_in_memory': 50000,       # Max files to keep in memory
    'enable_streaming': True,            # Stream large datasets
    'temp_file_cleanup': True,          # Clean up temporary files
    'memory_limit_gb': 4                # Memory usage limit
}

# =============================================================================
# LOGGING AND MONITORING CONFIGURATION
# =============================================================================

# Logging settings
LOGGING_CONFIG = {
    'level': 'INFO',                    # Log level: DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_logging': True,               # Enable file logging
    'log_file': f'drive_analysis_{datetime.now().strftime("%Y%m%d")}.log',
    'max_log_size_mb': 100,            # Max log file size
    'backup_count': 5                   # Number of backup log files
}

# Progress monitoring
MONITORING_SETTINGS = {
    'enable_progress_bar': True,        # Show progress bars
    'progress_update_interval': 100,    # Update every N files
    'estimate_completion_time': True,   # Estimate time remaining
    'detailed_timing': True            # Track detailed timing information
}

# =============================================================================
# NOTIFICATION CONFIGURATION
# =============================================================================

# Notification settings (optional)
NOTIFICATIONS = {
    'enable_notifications': False,      # Enable email/webhook notifications
    'email_on_completion': False,       # Email when analysis completes
    'webhook_url': None,               # Webhook URL for notifications
    'notification_threshold_files': 10000,  # Notify for large analyses
    'error_notifications': True        # Notify on errors
}

# =============================================================================
# CUSTOM ANALYSIS RULES
# =============================================================================

# Custom rules for specific use cases
CUSTOM_RULES = {
    'large_file_threshold_mb': 100,     # Flag files larger than this
    'old_file_threshold_days': 365,     # Flag files older than this
    'inactive_file_threshold_days': 90,  # Flag files not accessed recently
    'duplicate_priority_types': [       # Prioritize these file types for duplicate checking
        'image/', 'video/', 'audio/', 'application/pdf'
    ],
    'exclude_system_files': True,       # Exclude system/hidden files
    'focus_user_files': True          # Focus on user-created content
}

# File categorization rules
CATEGORIZATION_RULES = {
    'image_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
    'video_extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
    'audio_extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
    'document_extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'spreadsheet_extensions': ['.xls', '.xlsx', '.csv', '.ods'],
    'presentation_extensions': ['.ppt', '.pptx', '.odp'],
    'archive_extensions': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'code_extensions': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.php']
}

# =============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =============================================================================

# Override settings based on environment variables
def apply_env_overrides():
    """Apply configuration overrides from environment variables"""
    global MAX_FILES_PER_SCAN, BATCH_SIZE, MIN_FILE_SIZE_BYTES
    
    # Override from environment variables if present
    if os.getenv('MAX_FILES_PER_SCAN'):
        MAX_FILES_PER_SCAN = int(os.getenv('MAX_FILES_PER_SCAN'))
    
    if os.getenv('BATCH_SIZE'):
        BATCH_SIZE = int(os.getenv('BATCH_SIZE'))
    
    if os.getenv('MIN_FILE_SIZE_BYTES'):
        MIN_FILE_SIZE_BYTES = int(os.getenv('MIN_FILE_SIZE_BYTES'))
    
    if os.getenv('SERVICE_ACCOUNT_FILE'):
        SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

# Apply environment overrides
apply_env_overrides()

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required files
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        errors.append(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    
    # Check numeric ranges
    if not 0 <= DUPLICATE_DETECTION['name_similarity_threshold'] <= 100:
        errors.append("name_similarity_threshold must be between 0 and 100")
    
    if not 0 <= DUPLICATE_DETECTION['size_variance_threshold'] <= 1:
        errors.append("size_variance_threshold must be between 0 and 1")
    
    # Check batch size
    if BATCH_SIZE <= 0:
        errors.append("BATCH_SIZE must be positive")
    
    return errors

# =============================================================================
# CONFIGURATION SUMMARY
# =============================================================================

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        'service_account_file': SERVICE_ACCOUNT_FILE,
        'base_sheet_name': BASE_SHEET_NAME,
        'max_files_per_scan': MAX_FILES_PER_SCAN,
        'batch_size': BATCH_SIZE,
        'duplicate_detection_enabled': True,
        'image_analysis_enabled': DUPLICATE_DETECTION['enable_image_analysis'],
        'fuzzy_matching_enabled': DUPLICATE_DETECTION['enable_fuzzy_matching'],
        'security_analysis_enabled': SECURITY_SETTINGS['analyze_public_files'],
        'export_format': EXPORT_SETTINGS['export_format'],
        'logging_level': LOGGING_CONFIG['level']
    }

# Validate configuration on import
config_errors = validate_config()
if config_errors:
    print("⚠️ Configuration errors found:")
    for error in config_errors:
        print(f"  - {error}")