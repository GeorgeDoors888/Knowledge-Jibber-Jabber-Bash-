class ChatGPTIntegrator:
    def __init__(self):
        self.conversation_memory = {}
        self.current_context = None
        
    def create_contextual_prompt(self, results, query, mode='auto'):
        """
        Creates a ChatGPT-optimized prompt that follows GPT's conversation style
        """
        system_prompt = (
            "You are an AI assistant with access to Google Drive documents. "
            "You can analyze, summarize, and answer questions about these documents "
            "while maintaining context across the conversation."
        )
        
        content_summary = self._create_content_summary(results)
        document_context = self._create_document_context(results)
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Document Context:\n{document_context}"},
                {"role": "assistant", "content": f"I've accessed your Google Drive and found {len(results)} relevant documents for '{query}'. {content_summary}\n\nHow can I help you analyze these documents?"}
            ],
            "contextId": self._generate_context_id(results)
        }
    
    def _create_content_summary(self, results):
        """Creates a GPT-friendly summary of document contents"""
        summary = "Here's what I found:\n\n"
        
        # Group by document type
        by_type = {}
        for r in results:
            doc_type = r.get('type', 'other')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(r)
        
        # Summarize each type
        for doc_type, docs in by_type.items():
            summary += f"📎 {doc_type.upper()} ({len(docs)} items):\n"
            for doc in docs[:3]:  # Show first 3 of each type
                title = doc.get('name', 'Untitled')
                modified = doc.get('modified', 'Unknown date')
                preview = doc.get('content_summary', '')[:100] + '...' if doc.get('content_summary') else ''
                
                summary += f"  • {title} (Modified: {modified})\n"
                if preview:
                    summary += f"    Preview: {preview}\n"
            
            if len(docs) > 3:
                summary += f"    ...and {len(docs) - 3} more {doc_type} files\n"
            summary += "\n"
        
        return summary
    
    def _create_document_context(self, results):
        """Creates structured context for GPT to understand the documents"""
        context = {
            "document_count": len(results),
            "document_types": list(set(r.get('type') for r in results)),
            "date_range": self._get_date_range(results),
            "key_topics": self._extract_key_topics(results),
            "relationships": self._find_document_relationships(results)
        }
        
        return json.dumps(context, indent=2)
    
    def _get_date_range(self, results):
        """Extracts the date range of documents"""
        dates = [r.get('modified') for r in results if r.get('modified')]
        if dates:
            return {
                "earliest": min(dates),
                "latest": max(dates),
                "span_days": (max(dates) - min(dates)).days
            }
        return None
    
    def _extract_key_topics(self, results):
        """Extracts potential key topics from document titles and content"""
        topics = []
        for r in results:
            # Add words from title
            if r.get('name'):
                topics.extend(r['name'].split())
            # Add key terms from content summary
            if r.get('content_summary'):
                # Add most frequent meaningful words
                words = r['content_summary'].split()
                # (implement frequency analysis here)
        return list(set(topics))
    
    def _find_document_relationships(self, results):
        """Identifies potential relationships between documents"""
        relationships = []
        
        # Find documents with similar names
        names = [(r.get('name', ''), i) for i, r in enumerate(results)]
        for i, (name1, idx1) in enumerate(names):
            for name2, idx2 in names[i+1:]:
                if self._are_related_names(name1, name2):
                    relationships.append({
                        "type": "similar_names",
                        "docs": [idx1, idx2]
                    })
        
        # Find documents modified in similar timeframes
        times = [(r.get('modified'), i) for i, r in enumerate(results) if r.get('modified')]
        times.sort()
        for i in range(len(times)-1):
            if (times[i+1][0] - times[i][0]).seconds < 3600:  # Within an hour
                relationships.append({
                    "type": "modified_together",
                    "docs": [times[i][1], times[i+1][1]]
                })
        
        return relationships
    
    def _are_related_names(self, name1, name2):
        """Checks if two document names are related"""
        # Remove common prefixes/suffixes and compare
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Check for version numbers
        if name1 in name2 or name2 in name1:
            return True
            
        # Check for common patterns (v1, v2, draft, final, etc.)
        patterns = ['v1', 'v2', 'draft', 'final', 'copy', 'rev']
        for p in patterns:
            if (p in name1 and p in name2):
                return True
                
        return False
    
    def _generate_context_id(self, results):
        """Generates a unique context ID for this set of documents"""
        import hashlib
        content = json.dumps([r.get('id') for r in results])
        return hashlib.md5(content.encode()).hexdigest()