from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from search_framework import smart_search, create_gpt_prompt

app = Flask(__name__)
CORS(app)  # Enable CORS for ChatGPT extension

from chatgpt_integration import ChatGPTIntegrator

chatgpt = ChatGPTIntegrator()

@app.route('/search', methods=['POST'])
def search_endpoint():
    try:
        data = request.json
        query = data.get('query')
        if not query:
            return jsonify({"error": "No query provided"}), 400
            
        # Get ChatGPT-specific parameters
        conversation_mode = data.get('conversation_mode', 'auto')
        previous_context = data.get('context_id')

        # Get optional parameters
        file_types = data.get('file_types')
        date_range = None
        if data.get('date_range'):
            from datetime import datetime
            start = datetime.fromisoformat(data['date_range']['start'])
            end = datetime.fromisoformat(data['date_range']['end'])
            date_range = (start, end)
            
        # Enhanced search parameters
        sort_by = data.get('sort_by', 'relevance')
        max_results = int(data.get('max_results', 50))
        owner = data.get('owner')
        shared = data.get('shared', False)
        
        # Validate sort_by parameter
        valid_sort_options = ['relevance', 'modified', 'created', 'name']
        if sort_by not in valid_sort_options:
            return jsonify({"error": f"Invalid sort_by option. Must be one of: {valid_sort_options}"}), 400

        # Perform search
        results = smart_search(
            query=query,
            file_types=file_types,
            date_range=date_range,
            include_content=True
        )

        # Create GPT-ready response
        response = {
            "query": query,
            "results": results,
            "gpt_prompt": create_gpt_prompt(results, query)
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Start the Flask server
    app.run(port=5000)