#!/usr/bin/env python3
"""
RTFC/Carbon Credits Document Summarizer
Downloads and summarizes RTFC, Carbon Credits, and fuel duty documents from Google Drive
"""

import os
import sys
import tempfile
from search_framework import smart_search
from doc_research_gpt.drive_utils import download_file
from doc_research_gpt.pdf_parser import read_pdf_text
from doc_research_gpt.summarizer import summarize_text

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

def download_and_summarize_document(doc_info, temp_dir):
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
        
        # Determine mime type for download
        doc_type = doc_info.get('type', '')
        if 'pdf' in doc_type:
            mime_type = 'application/pdf'
            extension = '.pdf'
        elif 'document' in doc_type:
            mime_type = 'text/plain'
            extension = '.txt'
        else:
            mime_type = 'text/plain'
            extension = '.txt'
        
        # Download to temp directory
        temp_path = os.path.join(temp_dir, f"{file_id}{extension}")
        
        # Use the existing download function
        if mime_type == 'application/pdf':
            downloaded_path = download_file(file_id, mime_type='application/pdf', save_as=temp_path)
        else:
            # For text files, we'll need to use the Google Drive API export
            from googleapiclient.discovery import build
            import pickle
            
            # Load credentials
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if creds:
                service = build('drive', 'v3', credentials=creds)
                request = service.files().export_media(fileId=file_id, mimeType='text/plain')
                
                with open(temp_path, 'wb') as f:
                    import io
                    from googleapiclient.http import MediaIoBaseDownload
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                downloaded_path = temp_path
            else:
                print(f"❌ No valid credentials for downloading text files")
                return None
        
        # Extract text
        if downloaded_path.endswith('.pdf'):
            text = read_pdf_text(downloaded_path)
        else:
            with open(downloaded_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        if not text.strip():
            print(f"⚠️  No text extracted from {filename}")
            return None
        
        print(f"🧠 Summarizing: {filename}")
        
        # Create summary using the existing summarizer
        summary = summarize_text(text)
        
        # Clean up temp file
        if os.path.exists(downloaded_path):
            os.remove(downloaded_path)
        
        return {
            'name': filename,
            'type': doc_type,
            'link': link,
            'summary': summary,
            'text_length': len(text)
        }
        
    except Exception as e:
        print(f"❌ Error processing {doc_info.get('name', 'Unknown')}: {str(e)}")
        return None

def main():
    print("🔍 RTFC/Carbon Credits Document Summarizer")
    print("=" * 60)
    
    # Set up OpenAI API key
    api_key = get_openai_key()
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Update the config file temporarily
    import sys
    sys.path.append('doc_research_gpt')
    
    # Search for RTFC and related documents
    print("\n📋 Searching for RTFC/Carbon Credits/Fuel Duty documents...")
    
    search_queries = [
        'RTFC RTFO Renewable Transport Fuel Certificate',
        'Carbon Credits carbon trading fuel',
        'fuel duty reclaim tax relief'
    ]
    
    all_docs = []
    for query in search_queries:
        print(f"Searching: {query}")
        results = smart_search(query, source='google_drive', max_results=15)
        
        # Filter for relevant documents
        relevant_docs = []
        for doc in results:
            name = doc.get('name', '').lower()
            relevant_keywords = [
                'rtfc', 'rtfo', 'renewable transport fuel', 'carbon credit', 
                'duty', 'fuel', 'greenhouse gas', 'biofuel', 'carbon trading'
            ]
            
            if any(keyword in name for keyword in relevant_keywords):
                # Avoid duplicates
                if not any(existing['name'] == doc.get('name') for existing in all_docs):
                    relevant_docs.append(doc)
        
        all_docs.extend(relevant_docs)
        print(f"Found {len(relevant_docs)} relevant documents")
    
    print(f"\n📊 Total unique documents to summarize: {len(all_docs)}")
    
    if not all_docs:
        print("❌ No relevant documents found")
        return
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        summaries = []
        
        for i, doc in enumerate(all_docs, 1):
            print(f"\n[{i}/{len(all_docs)}] Processing: {doc.get('name', 'Unknown')}")
            
            summary_result = download_and_summarize_document(doc, temp_dir)
            if summary_result:
                summaries.append(summary_result)
            
            # Add a small delay to avoid rate limits
            import time
            time.sleep(1)
    
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
        print(f"   {summary['summary']}")
        print("-" * 60)
    
    print(f"\n✅ Successfully summarized {len(summaries)} out of {len(all_docs)} documents")
    
    # Optionally save results to file
    save_to_file = input("\n💾 Save summaries to file? (y/n): ").strip().lower()
    if save_to_file == 'y':
        import json
        output_file = f"rtfc_summaries_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(summaries, f, indent=2)
        print(f"📁 Summaries saved to: {output_file}")

if __name__ == "__main__":
    main()