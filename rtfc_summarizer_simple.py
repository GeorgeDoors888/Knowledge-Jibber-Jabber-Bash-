#!/usr/bin/env python3
"""
RTFC/Carbon Credits Document Summarizer
Downloads and summarizes RTFC, Carbon Credits, and fuel duty documents from Google Drive
"""

import os
import sys
import tempfile
import pickle
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PyPDF2 import PdfReader
from search_framework import smart_search

def get_openai_key():
    """Get OpenAI API key from environment or user input"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not found in environment variables.")
        api_key = input("Please enter your OpenAI API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            sys.exit(1)
    return api_key

def summarize_with_openai(text, api_key):
    """Summarize text using OpenAI API"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Truncate text to avoid token limits
        max_chars = 7000
        truncated_text = text[:max_chars]
        if len(text) > max_chars:
            truncated_text += "\n\n[Document truncated for summarization]"
        
        prompt = f"""Summarize this document focusing on:
- Key points and main topics related to RTFCs, carbon credits, or fuel duty
- Important regulations or requirements
- Financial implications or costs
- Compliance requirements
- Any deadlines or timeframes mentioned

Document text:
{truncated_text}"""
        
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
        
    except Exception as e:
        print(f"❌ Error with OpenAI API: {str(e)}")
        return None

def get_drive_service():
    """Get authenticated Google Drive service"""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials_2.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def read_pdf_content(file_path):
    """Extract text from PDF file"""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def download_and_summarize_document(doc_info, service, temp_dir, api_key):
    """Download a document and create a summary"""
    try:
        # Extract file ID from Google Drive link
        link = doc_info.get('link', '')
        if '/d/' not in link:
            print(f"⚠️  Invalid Google Drive link for {doc_info.get('name', 'Unknown')}")
            return None
            
        file_id = link.split("/d/")[1].split("/")[0]
        filename = doc_info.get('name', 'Unknown')
        
        print(f"📥 Downloading: {filename}")
        
        # Determine download method based on file type
        doc_type = doc_info.get('type', '')
        
        if 'pdf' in doc_type:
            # Download PDF directly
            request = service.files().get_media(fileId=file_id)
            temp_path = os.path.join(temp_dir, f"{file_id}.pdf")
            
            with open(temp_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            # Extract text from PDF
            text = read_pdf_content(temp_path)
            
        else:
            # Export as plain text
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
            temp_path = os.path.join(temp_dir, f"{file_id}.txt")
            
            with open(temp_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            # Read text file
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        if not text.strip():
            print(f"⚠️  No text extracted from {filename}")
            return None
        
        print(f"🧠 Summarizing: {filename} ({len(text):,} characters)")
        
        # Create summary
        summary = summarize_with_openai(text, api_key)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if summary:
            return {
                'name': filename,
                'type': doc_type,
                'link': link,
                'summary': summary,
                'text_length': len(text)
            }
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error processing {doc_info.get('name', 'Unknown')}: {str(e)}")
        return None

def main():
    print("🔍 RTFC/Carbon Credits Document Summarizer using OpenAI")
    print("=" * 70)
    
    # Set up OpenAI API key
    api_key = get_openai_key()
    
    # Get Google Drive service
    try:
        service = get_drive_service()
        print("✅ Google Drive authentication successful")
    except Exception as e:
        print(f"❌ Error authenticating with Google Drive: {e}")
        return
    
    # Search for RTFC and related documents
    print("\n📋 Searching for RTFC/Carbon Credits/Fuel Duty documents...")
    
    search_queries = [
        'RTFO compliance',
        'RTFO recycled carbon fuels',
        'renewable transport fuel obligations',
        'motor fuel greenhouse gas'
    ]
    
    all_docs = []
    for query in search_queries:
        print(f"Searching: {query}")
        results = smart_search(query, source='google_drive', max_results=5)
        
        # Filter for relevant documents and avoid duplicates
        for doc in results:
            name = doc.get('name', '').lower()
            if any(keyword in name for keyword in ['rtfo', 'rtfc', 'renewable', 'motor fuel', 'greenhouse']):
                # Check for duplicates
                if not any(existing['name'] == doc.get('name') for existing in all_docs):
                    all_docs.append(doc)
        
        print(f"Found {len([d for d in results if any(k in d.get('name', '').lower() for k in ['rtfo', 'rtfc', 'renewable', 'motor fuel', 'greenhouse'])])} relevant documents")
    
    print(f"\n📊 Total unique documents to summarize: {len(all_docs)}")
    
    if not all_docs:
        print("❌ No relevant documents found")
        return
    
    # Show documents to be processed
    print("\nDocuments to process:")
    for i, doc in enumerate(all_docs, 1):
        print(f"{i}. {doc.get('name', 'Unknown')} ({doc.get('type', 'Unknown type')})")
    
    proceed = input(f"\nProceed with summarizing {len(all_docs)} documents? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Operation cancelled")
        return
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        summaries = []
        
        for i, doc in enumerate(all_docs, 1):
            print(f"\n[{i}/{len(all_docs)}] Processing: {doc.get('name', 'Unknown')}")
            
            summary_result = download_and_summarize_document(doc, service, temp_dir, api_key)
            if summary_result:
                summaries.append(summary_result)
            
            # Add delay to avoid rate limits
            import time
            time.sleep(2)
    
    # Display results
    print("\n" + "=" * 80)
    print("📄 DOCUMENT SUMMARIES")
    print("=" * 80)
    
    for i, summary in enumerate(summaries, 1):
        print(f"\n{i}. 📄 {summary['name']}")
        print(f"   Type: {summary['type']}")
        print(f"   Text Length: {summary['text_length']:,} characters")
        print(f"   Link: {summary['link']}")
        print(f"\n   📋 SUMMARY:")
        # Format summary with proper line breaks
        summary_lines = summary['summary'].split('\n')
        for line in summary_lines:
            if line.strip():
                print(f"   {line}")
        print("-" * 60)
    
    print(f"\n✅ Successfully summarized {len(summaries)} out of {len(all_docs)} documents")
    
    # Save results to file
    if summaries:
        import json
        import time
        output_file = f"rtfc_summaries_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(summaries, f, indent=2)
        print(f"📁 Summaries saved to: {output_file}")

if __name__ == "__main__":
    main()