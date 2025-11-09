import datetime

# --- Google Drive Search ---
def search_google_drive(query, file_types=None, date_range=None, metadata_only=False, 
                      include_trashed=False, mime_type_filter=None, workspace_filter=None):
    # Enhanced implementation using Google Drive API with OAuth user credentials
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.errors import HttpError
    import pickle
    import os
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    # Use your credentials file
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_2.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    
    # Build enhanced search query
    q = f"fullText contains '{query}'"  # Search in file content too
    
    if not include_trashed:
        q += " and trashed=false"
    
    # Enhanced file type filtering
    if file_types or mime_type_filter:
        mime_types = []
        # Standard file types
        type_mapping = {
            "doc": ["application/vnd.google-apps.document", "application/msword", 
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            "sheet": ["application/vnd.google-apps.spreadsheet", "application/vnd.ms-excel",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
            "pdf": ["application/pdf"],
            "slide": ["application/vnd.google-apps.presentation", "application/vnd.ms-powerpoint",
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation"],
            "drawing": ["application/vnd.google-apps.drawing"],
            "form": ["application/vnd.google-apps.form"],
            "image": ["image/jpeg", "image/png", "image/gif", "image/svg+xml"],
            "video": ["video/mp4", "video/quicktime", "video/x-msvideo"],
            "audio": ["audio/mpeg", "audio/wav", "audio/x-m4a"]
        }
        
        if file_types:
            for ft in file_types:
                if ft in type_mapping:
                    mime_types.extend(type_mapping[ft])
                    
        if mime_type_filter:
            mime_types.append(mime_type_filter)
            
        if mime_types:
            mime_query = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
            q += f" and ({mime_query})"
            
    # Workspace filtering
    if workspace_filter:
        q += f" and '{workspace_filter}' in parents"
    # Date filter (createdTime)
    if date_range:
        start, end = date_range
        q += f" and createdTime >= '{start.isoformat()}' and createdTime <= '{end.isoformat()}'"
    
    results = service.files().list(q=q, fields="files(id, name, mimeType, createdTime, description)").execute()
    files = results.get('files', [])
    output = []
    
    def extract_content(file_id, mime_type):
        try:
            if 'google-apps.document' in mime_type:
                # For Google Docs
                doc = service.files().export(fileId=file_id, mimeType='text/plain').execute()
                return doc.decode('utf-8')
            elif 'google-apps.spreadsheet' in mime_type:
                # For Google Sheets
                sheet = service.files().export(fileId=file_id, mimeType='text/csv').execute()
                return sheet.decode('utf-8')
            elif 'pdf' in mime_type:
                # For PDFs
                content = service.files().get_media(fileId=file_id).execute()
                return content.decode('utf-8', errors='ignore')
            return None
        except Exception as e:
            print(f"Warning: Could not extract content: {str(e)}")
            return None

    for f in files:
        output.append({
            "name": f["name"],
            "type": f["mimeType"],
            "date": f["createdTime"],
            "link": f"https://drive.google.com/file/d/{f['id']}/view",
            "summary": "(Add summarization here)"
        })
    return output

# --- Main Search Dispatcher ---
def summarize_for_gpt(content, max_length=1000):
    """Prepare content for GPT processing"""
    if not content:
        return ""
    # Basic text cleanup
    content = content.replace('\r', ' ').replace('\n', ' ').strip()
    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "..."
    return content

def smart_search(query, source=None, file_types=None, date_range=None, include_content=True, 
                sort_by='relevance', max_results=50, owner=None, shared=False, 
                copilot_mode='interactive'):
    """
    Enhanced search function optimized for GitHub Copilot Pro integration.
    
    Parameters:
    - query: Search term or natural language query
    - source: Source to search (e.g., "google_drive")
    - file_types: List of file types to include
    - date_range: (start_date, end_date) tuple
    - include_content: Whether to extract and include file content
    - sort_by: How to sort results ('relevance', 'modified', 'created', 'name')
    - max_results: Maximum number of results to return
    - owner: Filter by file owner email
    - shared: Include only shared files if True
    - copilot_mode: Display mode ('interactive', 'analysis', 'code')
    
    Returns:
    List of dictionaries containing file info and content suitable for Copilot analysis
    """
    results = []
    if source in [None, "google_drive"]:
        results += search_google_drive(query, file_types, date_range)
    
    # Enhance results with content summaries
    if include_content:
        for r in results:
            if 'content' not in r and r.get('id'):
                content = extract_content(r['id'], r.get('type', ''))
                r['content_summary'] = summarize_for_gpt(content)
    
    # Sort results if specified
    if sort_by == 'relevance':
        results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    elif sort_by == 'modified':
        results.sort(key=lambda x: x.get('modified', ''), reverse=True)
    elif sort_by == 'created':
        results.sort(key=lambda x: x.get('date', ''), reverse=True)
    elif sort_by == 'name':
        results.sort(key=lambda x: x.get('name', '').lower())
    
    return results

# --- Example Usage ---
def create_gpt_prompt(results, query, analysis_mode='auto', use_github_copilot=True):
    """
    Create an advanced prompt optimized for GitHub Copilot Pro and ChatGPT web interface
    
    Parameters:
    - results: Search results from Google Drive
    - query: Original search query
    - analysis_mode: Type of analysis to perform ('auto', 'summarize', 'compare', 'extract', 'timeline')
    - use_github_copilot: Optimizes output for GitHub Copilot Pro integration
    """
    # Initialize prompt with context
    prompt = f"As an AI assistant analyzing Google Drive documents, I've searched for '{query}' and found these relevant items:\n\n"
    
    # Group documents by type for better organization
    docs_by_type = {}
    for r in results:
        file_type = r.get('type', 'other')
        if file_type not in docs_by_type:
            docs_by_type[file_type] = []
        docs_by_type[file_type].append(r)

    # Process each type of document
    for file_type, docs in docs_by_type.items():
        prompt += f"\n{file_type.upper()} FILES:\n"
        for i, r in enumerate(docs, 1):
            # Enhanced file info with emoji indicators
            type_emoji = {
                'document': '📄',
                'spreadsheet': '📊',
                'presentation': '📽️',
                'pdf': '📑',
                'image': '🖼️',
                'folder': '📁'
            }.get(r.get('type', ''), '📎')
            
            prompt += f"{type_emoji} {i}. {r['name']}\n"
            
            # Rich metadata section
            metadata = []
            if r.get('date'):
                metadata.append(f"📅 Created: {r['date']}")
            if r.get('modified'):
                metadata.append(f"🔄 Modified: {r['modified']}")
            if r.get('owner'):
                metadata.append(f"👤 Owner: {r['owner']}")
            if r.get('size'):
                metadata.append(f"📊 Size: {r['size']}")
            if r.get('shared') == True:
                metadata.append("🔗 Shared: Yes")
            if r.get('version_count'):
                metadata.append(f"📚 Versions: {r['version_count']}")
            if r.get('last_editor'):
                metadata.append(f"✏️ Last edited by: {r['last_editor']}")
            
        prompt += "Metadata: " + ", ".join(metadata) + "\n"
        
        # Content preview
        if r.get('content_summary'):
            preview = r['content_summary']
            if len(preview) > 300:
                preview = preview[:297] + "..."
            prompt += f"Preview: {preview}\n"
            
        # Link
        if r.get('link'):
            prompt += f"Link: {r['link']}\n"
            
        prompt += "---\n"
    
    # Add smart analysis based on document types and content
    def suggest_analysis(docs_by_type):
        suggestions = []
        
        if 'spreadsheet' in docs_by_type:
            suggestions.extend([
                "📊 Analyze numerical trends and patterns in spreadsheets",
                "📈 Create summary statistics from tabular data",
                "🔄 Compare data across different time periods"
            ])
            
        if 'document' in docs_by_type:
            suggestions.extend([
                "📝 Extract key points and main ideas",
                "📚 Generate executive summaries",
                "🔍 Find common themes across documents"
            ])
            
        if 'presentation' in docs_by_type:
            suggestions.extend([
                "🎯 Identify key takeaways from slides",
                "📊 Summarize presentation structures",
                "💡 Extract action items and next steps"
            ])
            
        if len(docs_by_type) > 1:
            suggestions.extend([
                "🔄 Compare information across different document types",
                "📅 Create a timeline of document updates",
                "👥 Analyze collaboration patterns"
            ])
            
        return suggestions

    # Add temporal analysis if dates are present
    has_dates = any(r.get('date') or r.get('modified') for r in results)
    if has_dates:
        prompt += "\n📅 TEMPORAL ANALYSIS:\n"
        prompt += "The documents span multiple dates. I can help you:\n"
        prompt += "• Track document evolution over time\n"
        prompt += "• Identify recent updates and changes\n"
        prompt += "• Create a chronological summary\n"

    # Add collaboration analysis if multiple owners/editors
    owners = set(r.get('owner') for r in results if r.get('owner'))
    if len(owners) > 1:
        prompt += "\n👥 COLLABORATION INSIGHTS:\n"
        prompt += "These documents involve multiple contributors. I can:\n"
        prompt += "• Analyze collaboration patterns\n"
        prompt += "• Track document ownership and sharing\n"
        prompt += "• Identify key stakeholders\n"

    # Add smart suggestions based on content
    suggestions = suggest_analysis(docs_by_type)
    if suggestions:
        prompt += "\n💡 SUGGESTED ANALYSES:\n"
        for suggestion in suggestions:
            prompt += f"• {suggestion}\n"

    prompt += "\n🤔 What specific aspects would you like me to analyze? You can ask about:"
    prompt += "\n1. Content summaries and key points"
    prompt += "\n2. Cross-document patterns and relationships"
    prompt += "\n3. Temporal trends and document evolution"
    prompt += "\n4. Collaboration insights and sharing patterns"
    prompt += "\n5. Specific information extraction"
    prompt += "\n\nI can also combine multiple analyses or focus on specific documents."
    
    return prompt

if __name__ == "__main__":
    import sys
    from copilot_handler import CopilotResultHandler
    
    if len(sys.argv) < 2:
        print("GitHub Copilot Drive Search")
        print("Usage: python search_framework.py <query> [mode]")
        print("\nModes:")
        print("  interactive    - Interactive exploration (default)")
        print("  analysis      - Detailed content analysis")
        print("  code          - Code-focused results")
        sys.exit(1)
    
    query = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'interactive'
    
    # Initialize handler with the specified mode
    handler = CopilotResultHandler(mode)
    
    # Perform search
    print(f"🔍 Searching Drive for: '{query}' (Mode: {mode})")
    results = smart_search(
        query=query,
        source="google_drive",
        include_content=True,
        copilot_mode=mode
    )
    
    if not results:
        print("No results found")
        sys.exit(0)
        
    # Format and display results
    formatted_output = handler.format_results(results, query)
    print("\n" + formatted_output)
