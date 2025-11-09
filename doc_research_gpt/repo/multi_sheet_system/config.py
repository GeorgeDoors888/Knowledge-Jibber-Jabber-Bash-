OPENAI_API_KEY = "sk-..."  # Replace with your real key
SERVICE_ACCOUNT_FILE = "service_account.json"  # Path to your service account file
SEARCH_KEYWORDS = ["capacity", "forecast", "balancing"]

# Multi-Sheet Manager Configuration
MAX_ROWS_PER_SHEET = 5000  # Maximum rows per worksheet before creating new tab
MAX_SHEETS_PER_SPREADSHEET = 10  # Maximum tabs per spreadsheet before creating new file
DRIVE_FOLDER_ID = None  # Google Drive folder ID to store spreadsheets (None = root folder)
SHEET_NAME_PREFIX = "DocumentResearch"  # Base name for new spreadsheets

# Default column headers for new sheets
DEFAULT_HEADERS = [
    "Document ID", 
    "Document Title", 
    "Source URL", 
    "Processing Date", 
    "Content Type",
    "Summary", 
    "Tags", 
    "Status",
    "Notes"
]

# Email addresses to share spreadsheets with (optional)
SHARE_EMAILS = [
    # "user1@example.com",
    # "user2@example.com"
]

# Rate limiting settings
API_DELAY = 0.1  # Delay between API calls (seconds)
BATCH_SIZE = 100  # Default batch size for bulk operations

# Backup settings
ENABLE_METADATA_BACKUP = True
BACKUP_FILE = "spreadsheet_registry.json"

# Duplicate Detection Configuration
ENABLE_DUPLICATE_DETECTION = True
DUPLICATE_CHECK_FIELDS = ["Document ID", "Source URL"]  # Primary fields to check for duplicates
DUPLICATE_DETECTION_METHOD = "exact"  # Options: "exact", "fuzzy", "hash", "multi"
FUZZY_MATCH_THRESHOLD = 85  # Percentage similarity for fuzzy matching (0-100)
DUPLICATE_ACTION = "skip"  # Options: "skip", "update", "flag", "allow"

# Advanced duplicate detection settings
ENABLE_FUZZY_TITLE_MATCHING = True  # Also check document titles for similarity
TITLE_SIMILARITY_THRESHOLD = 80  # Threshold for title similarity matching
ENABLE_CONTENT_HASH = True  # Generate content hash for duplicate detection
CONTENT_FIELDS_FOR_HASH = ["Summary", "Tags"]  # Fields to include in content hash

# Duplicate handling options
CREATE_DUPLICATE_LOG = True
DUPLICATE_LOG_FILE = "duplicate_log.json"
ADD_DUPLICATE_MARKER = True  # Add "DUPLICATE_" prefix to duplicate entries
DUPLICATE_MARKER_PREFIX = "DUPLICATE_"
