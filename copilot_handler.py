from datetime import datetime
from typing import List, Dict, Any

class CopilotResultHandler:
    """
    Handles formatting and display of search results optimized for GitHub Copilot Pro.
    Supports multiple display modes for different use cases.
    """
    
    def __init__(self, mode: str = 'interactive'):
        """
        Initialize the handler with a specific display mode.
        
        Args:
            mode (str): Display mode - 'interactive', 'analysis', or 'code'
        """
        self.mode = mode
        self.context_history = []
        self._type_emojis = {
            'document': '📄',
            'spreadsheet': '📊',
            'presentation': '📽️',
            'pdf': '📑',
            'image': '🖼️',
            'folder': '📁',
            'application/vnd.google-apps.document': '📄',
            'application/vnd.google-apps.spreadsheet': '📊',
            'application/vnd.google-apps.presentation': '📽️',
            'application/pdf': '📑'
        }
    
    def format_results(self, results: List[Dict[Any, Any]], query: str) -> str:
        """
        Format search results according to the specified mode.
        
        Args:
            results: List of search result dictionaries
            query: Original search query
            
        Returns:
            Formatted string output
        """
        if not results:
            return "No results found."
            
        if self.mode == 'interactive':
            return self._format_interactive(results, query)
        elif self.mode == 'analysis':
            return self._format_analysis(results, query)
        elif self.mode == 'code':
            return self._format_code_generation(results, query)
        else:
            return self._format_interactive(results, query)  # Default to interactive
        
    def _format_interactive(self, results: List[Dict[Any, Any]], query: str) -> str:
        """Format results for interactive exploration"""
        output = [f"📊 Found {len(results)} results for '{query}'\n"]
        
        for i, result in enumerate(results, 1):
            emoji = self._get_emoji(result.get('type', ''))
            name = result.get('name', 'Untitled')
            date = self._format_date(result.get('date', 'No date'))
            link = result.get('link', '#')
            
            # Format each result as a clickable item
            output.append(f"{i}. {emoji} {name}")
            output.append(f"   📅 {date}")
            
            # Add preview if available
            if 'content_summary' in result:
                preview = result['content_summary'][:200]
                if len(preview) == 200:
                    preview += "..."
                output.append(f"   💡 {preview}")
            
            output.append(f"   🔗 {link}\n")
        
        return "\n".join(output)

    def _get_emoji(self, file_type: str) -> str:
        """Get emoji for file type"""
        return self._type_emojis.get(file_type, '📎')
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if date_str == 'No date':
            return date_str
        try:
            # Try to parse and format the date
            from datetime import datetime
            if isinstance(date_str, str):
                # Handle various date formats
                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        dt = datetime.strptime(date_str.replace('Z', ''), fmt.replace('Z', ''))
                        return dt.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        continue
            return str(date_str)
        except:
            return str(date_str)
    
    def _format_analysis(self, results: List[Dict[Any, Any]], query: str) -> str:
        """Format results for detailed content analysis"""
        output = [
            f"🔍 Content Analysis for '{query}'",
            f"📊 Total Results: {len(results)}\n"
        ]
        
        # Group by type
        by_type = {}
        for r in results:
            file_type = r.get('type', 'unknown')
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(r)
        
        # Summary by type
        output.append("Document Types:")
        for file_type, items in by_type.items():
            emoji = self._get_emoji(file_type)
            output.append(f"{emoji} {file_type}: {len(items)} files")
        
        # Detailed analysis
        output.append("\n📑 Detailed Analysis:")
        for r in results:
            name = r.get('name', 'Untitled')
            date = self._format_date(r.get('date', 'No date'))
            
            output.append(f"\n{self._get_emoji(r.get('type', ''))} {name}")
            output.append(f"Created: {date}")
            
            if 'content_summary' in r:
                summary = r['content_summary']
                output.append("Content Preview:")
                output.append(f"{summary[:500]}...")
            
            output.append(f"Link: {r.get('link', '#')}")
            output.append("-" * 40)
        
        return "\n".join(output)
    
    def _format_code(self, results: List[Dict[Any, Any]], query: str) -> str:
        """Format results focusing on code and technical content"""
        output = [
            f"💻 Code-Related Results for '{query}'",
            f"Found {len(results)} potentially relevant files\n"
        ]
        
        for r in results:
            name = r.get('name', 'Untitled')
            
            # Skip if no content summary
            if 'content_summary' not in r:
                continue
                
            # Look for code-like content
            content = r['content_summary']
            if any(keyword in content.lower() for keyword in 
                  ['def ', 'class ', 'function', 'import ', 'var ', 'const ',
                   'return', 'public ', 'private ', '#include']):
                   
                output.append(f"📦 {name}")
                output.append(f"Type: {r.get('type', 'unknown')}")
                output.append("Relevant Content:")
                
                # Try to extract code-like sections
                lines = content.split('\n')
                code_lines = []
                for line in lines:
                    if any(keyword in line for keyword in 
                          ['def ', 'class ', 'function', 'import ', 'var ', 'const ',
                           'return', 'public ', 'private ', '#include']):
                        code_lines.append(f"    {line.strip()}")
                
                if code_lines:
                    output.extend(code_lines)
                    
                output.append(f"\nLink: {r.get('link', '#')}")
                output.append("-" * 40 + "\n")
        
        if len(output) == 2:  # Only has header
            output.append("No code-specific content found in the results.")
            
        return "\n".join(output)
    
    def _format_item_interactive(self, item):
        """Format a single item for interactive mode"""
        output = f"  • {item['name']}\n"
        if item.get('modified'):
            output += f"    Modified: {item['modified']}\n"
        if item.get('content_summary'):
            preview = item['content_summary'][:100] + '...' if len(item['content_summary']) > 100 else item['content_summary']
            output += f"    Preview: {preview}\n"
        return output
    
    def _group_by_type(self, results):
        """Group results by document type"""
        groups = {}
        for r in results:
            doc_type = r.get('type', 'other')
            if doc_type not in groups:
                groups[doc_type] = []
            groups[doc_type].append(r)
        return groups
    
    def _create_document_summary(self, doc):
        """Create a detailed summary of a document"""
        summary = f"📄 {doc['name']}\n"
        if doc.get('content_summary'):
            summary += f"   Key Points: {doc['content_summary'][:200]}...\n"
        if doc.get('modified'):
            summary += f"   Last Modified: {doc['modified']}\n"
        return summary
    
    def _find_relationships(self, results):
        """Find relationships between documents"""
        relationships = []
        # Find version sequences
        names = [r.get('name', '') for r in results]
        for i, name1 in enumerate(names):
            for j, name2 in enumerate(names[i+1:], i+1):
                if self._are_related(name1, name2):
                    relationships.append(f"'{name1}' appears to be related to '{name2}'")
        return relationships
    
    def _are_related(self, name1, name2):
        """Check if two documents are related"""
        name1 = name1.lower()
        name2 = name2.lower()
        # Check for version numbers
        return (name1 in name2 or name2 in name1 or
                any(x in name1 and x in name2 
                    for x in ['v1', 'v2', 'draft', 'final']))
    
    def _extract_topics(self, results):
        """Extract key topics from documents"""
        topics = set()
        for r in results:
            if r.get('name'):
                words = r['name'].split()
                topics.update(w for w in words if len(w) > 3)
        return list(topics)
    
    def _is_code_relevant(self, item):
        """Check if item is relevant for code generation"""
        code_extensions = ['.py', '.js', '.java', '.cpp', '.h', '.cs']
        return any(item['name'].endswith(ext) for ext in code_extensions)
    
    def _extract_code_context(self, item):
        """Extract code-relevant context from an item"""
        if item.get('content_summary'):
            # Look for code blocks or patterns
            content = item['content_summary']
            if '```' in content:
                # Extract code blocks
                start = content.find('```') + 3
                end = content.find('```', start)
                return content[start:end] if end > start else content
            return content
        return ""