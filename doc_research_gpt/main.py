from sheets_utils import load_sheet, update_summary
from summarizer import summarize_text
from config import SEARCH_KEYWORDS
from drive_utils import download_file
from pdf_parser import read_pdf_text
import time
import os

EXPORT_MIME_TYPE = 'application/pdf'

sheet_urls = [
    # Add your Google Sheet URLs here
]

for url in sheet_urls:
    df, ws = load_sheet(url)

    for idx, row in df.iterrows():
        filename = row.get("File Name", "")
        link = row.get("Drive Link", "")
        if not link or not any(k.lower() in filename.lower() for k in SEARCH_KEYWORDS):
            continue

        try:
            file_id = link.split("/d/")[1].split("/")[0]
        except Exception:
            continue

        print(f"📥 Downloading: {filename}")
        try:
            local_path = download_file(file_id, mime_type=EXPORT_MIME_TYPE)
        except Exception:
            continue

        try:
            text = read_pdf_text(local_path)
            if not text.strip():
                continue
        except Exception:
            continue

        print(f"🧠 Summarizing {filename}")
        try:
            summary = summarize_text(text)
            update_summary(ws, idx+2, summary, ", ".join(SEARCH_KEYWORDS))
        except Exception:
            continue

        if os.path.exists(local_path):
            os.remove(local_path)

        time.sleep(1)
