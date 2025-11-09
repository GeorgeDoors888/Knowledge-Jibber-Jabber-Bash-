import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = 'elexon_keyword_index.pkl'
model = SentenceTransformer('all-MiniLM-L6-v2')


def search_documents(query, top_n=5):
    with open(INDEX_PATH, 'rb') as f:
        index = pickle.load(f)
    query_emb = model.encode([query])[0]
    results = []
    for doc, data in index.items():
        doc_embs = data['embeddings']
        sims = np.dot(doc_embs, query_emb) / (np.linalg.norm(doc_embs, axis=1) * np.linalg.norm(query_emb) + 1e-8)
        best_score = np.max(sims)
        best_kw = data['keywords'][np.argmax(sims)]
        results.append((doc, best_score, best_kw))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]

if __name__ == '__main__':
    query = input('Enter your search query: ')
    results = search_documents(query)
    print('\nTop matching documents:')
    for doc, score, kw in results:
        print(f"{doc} | Score: {score:.3f} | Matched keyword: {kw}")
