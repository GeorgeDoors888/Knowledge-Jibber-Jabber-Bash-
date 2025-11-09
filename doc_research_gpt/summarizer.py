import openai
import os
from config import OPENAI_API_KEY

# Set API key from config or environment
api_key = OPENAI_API_KEY if OPENAI_API_KEY != "sk-..." else os.getenv('OPENAI_API_KEY')
if api_key:
    openai.api_key = api_key

def summarize_text(text):
    """Summarize document text using OpenAI GPT"""
    
    # Use environment variable if config doesn't have real key
    current_api_key = openai.api_key or os.getenv('OPENAI_API_KEY')
    if not current_api_key or current_api_key == "sk-...":
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    
    # Truncate text to avoid token limits
    max_chars = 7000
    truncated_text = text[:max_chars]
    if len(text) > max_chars:
        truncated_text += "\n\n[Document truncated for summarization]"
    
    prompt = f"""Summarize this document focusing on:
- Key points and main topics
- Important regulations or requirements
- Financial implications or costs
- Compliance requirements
- Any deadlines or timeframes mentioned

Document text:
{truncated_text}"""
    
    try:
        # Try new OpenAI client format first
        from openai import OpenAI
        client = OpenAI(api_key=current_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert document analyzer specializing in regulatory and policy documents, particularly those related to renewable transport fuels, carbon credits, and tax policy."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content
        
    except ImportError:
        # Fallback to legacy format
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert document analyzer specializing in regulatory and policy documents, particularly those related to renewable transport fuels, carbon credits, and tax policy."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']
