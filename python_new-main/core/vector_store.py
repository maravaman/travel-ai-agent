from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim=384):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []

    def add(self, text: str):
        vec = self.model.encode([text])[0].astype('float32')
        self.index.add(np.array([vec]))
        self.texts.append(text)

    def search(self, query: str, k=5):
        vec = self.model.encode([query])[0].astype('float32')
        D, I = self.index.search(np.array([vec]), k)
        return [self.texts[i] for i in I[0]]
