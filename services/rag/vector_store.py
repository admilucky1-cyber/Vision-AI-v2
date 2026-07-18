import chromadb
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

# Initialize once
CHROMA_PATH = Path("chroma_db")
CHROMA_PATH.mkdir(exist_ok=True)

class VectorStore:
    def __init__(self):
        # Use a lightweight, free embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_or_create_collection(name="documents")
    
    def add_document(self, file_id: str, content: str):
        # Split into chunks (professional chunking)
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk).tolist()
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[f"{file_id}_chunk_{i}"]
            )
    
    def search(self, query: str, top_k: int = 3):
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results['documents'][0] if results['documents'] else []

vector_store = VectorStore()