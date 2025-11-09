import os
import pickle
from sentence_transformers import SentenceTransformer

INDEX_PATH = 'elexon_keyword_index.pkl'
KEYWORD_SHEET_PATH = 'elexon_keywords.csv'  # You can export from Google Sheets as CSV

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_keywords_from_csv(path):
    import csv
    docs = {}
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = row['Document Name']
            kw = row['Keyword/Keyphrase']
            if doc not in docs:
                docs[doc] = []
            docs[doc].append(kw)
    return docs

def build_index():
    docs = load_keywords_from_csv(KEYWORD_SHEET_PATH)
    index = {}
    for doc, keywords in docs.items():
        embeddings = model.encode(keywords)
        index[doc] = {
            'keywords': keywords,
            'embeddings': embeddings
        }
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump(index, f)
    print(f"Index built and saved to {INDEX_PATH}")

if __name__ == '__main__':
    build_index()
