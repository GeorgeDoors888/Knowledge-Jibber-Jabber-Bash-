from flask import jsonify
import json
from datetime import datetime, timedelta

class DriveExtensionHandler:
    def __init__(self):
        self.chat_context = {}
        
    def format_response_for_extension(self, results, query, analysis_mode='auto'):
        """Format search results specifically for the ChatGPT extension"""
        
        # Track conversation context
        conversation_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.chat_context[conversation_id] = {
            'query': query,
            'timestamp': datetime.now(),
            'result_count': len(results),
            'file_types': list(set(r.get('type') for r in results))
        }
        
        # Generate different prompt styles based on analysis mode
        prompts = {
            'summary': self._generate_summary_prompt(results, query),
            'detailed': self._generate_detailed_prompt(results, query),
            'quick': self._generate_quick_prompt(results, query)
        }
        
        # Format response for the extension
        response = {
            'success': True,
            'conversation_id': conversation_id,
            'query': query,
            'results': results,
            'prompts': prompts,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'result_count': len(results),
                'file_types': list(set(r.get('type') for r in results)),
                'conversation_context': self.chat_context[conversation_id]
            },
            'suggestions': self._generate_suggestions(results)
        }
        
        return response
    
    def _generate_quick_prompt(self, results, query):
        """Generate a concise prompt for quick questions"""
        prompt = f"I found {len(results)} items in Google Drive about '{query}'. "
        prompt += "Here are the key documents:\n\n"
        
        for i, r in enumerate(results[:3], 1):
            prompt += f"{i}. {r['name']} ({r['type']})\n"
        
        if len(results) > 3:
            prompt += f"\n...and {len(results) - 3} more items. "
        
        prompt += "\nWhat would you like to know about these documents?"
        return prompt
    
    def _generate_suggestions(self, results):
        """Generate context-aware suggestions for the extension"""
        suggestions = []
        
        # Add file-type specific suggestions
        file_types = set(r.get('type') for r in results)
        if 'document' in file_types:
            suggestions.append("Summarize the main points from the documents")
        if 'spreadsheet' in file_types:
            suggestions.append("Analyze numerical data and trends")
        if len(file_types) > 1:
            suggestions.append("Compare information across different file types")
            
        # Add time-based suggestions
        dates = [r.get('modified') for r in results if r.get('modified')]
        if dates:
            date_range = max(dates) - min(dates)
            if date_range > timedelta(days=30):
                suggestions.append("Show how the content has evolved over time")
                
        return suggestions

    def clean_up_old_contexts(self, max_age_hours=24):
        """Remove old conversation contexts"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        self.chat_context = {
            k: v for k, v in self.chat_context.items()
            if v['timestamp'] > cutoff
        }