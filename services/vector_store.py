"""
Vision AI v2.0 - Vector Store Service
======================================
Semantic search and vector database for RAG.
Uses ChromaDB (lightweight, in‑memory, persistent) and sentence-transformers.

Features:
- Document chunking (by tokens or characters)
- Embedding generation with sentence-transformers
- Persistent vector storage with ChromaDB
- Semantic retrieval (top‑K relevant chunks)
- Automatic cleanup and deduplication
"""

import os
import hashlib
import shutil
import asyncio
import functools
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# ==========================================================
# CONFIGURATION
# ==========================================================
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlap between chunks (for continuity)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, accurate, ~384 dimensions
DB_PATH = Path("chroma_db")          # Persistent storage path
COLLECTION_NAME = "vision_ai_docs"
MAX_RETRIES = 3            # Retry count for ChromaDB operations

# ==========================================================
# EMBEDDING ENGINE
# ==========================================================
class LocalEmbeddingFunction:
    """Wrapper for sentence-transformers to work with ChromaDB."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None  # Lazy load the model
        self._embedding_cache = {}  # Cache for frequently used texts
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        # Load the model only once on the first call
        if self._model is None:
            import time
            print(f"⏳ Loading embedding model (first time only)...")
            start = time.time()
            self._model = SentenceTransformer(self.model_name)
            print(f"✅ Embedding model loaded in {time.time() - start:.1f}s")
        
        # Check cache for single texts
        if len(texts) == 1 and texts[0] in self._embedding_cache:
            return [self._embedding_cache[texts[0]]]
        
        # Compute embeddings
        embeddings = self._model.encode(texts, convert_to_numpy=True).tolist()
        
        # Cache for future use (limit cache size)
        for text, emb in zip(texts, embeddings):
            if len(self._embedding_cache) < 1000:
                self._embedding_cache[text] = emb
        
        return embeddings

# Singleton embedding function
embedding_func = LocalEmbeddingFunction()

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================
def run_sync_in_thread(func, *args, **kwargs):
    """Run a synchronous function in a thread to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

# ==========================================================
# CHROMA DB CLIENT
# ==========================================================
class VectorStore:
    """Main vector store manager for RAG."""

    def __init__(self, persist_directory: Path = DB_PATH):
        self.persist_directory = persist_directory
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                persist_directory=str(self.persist_directory)
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )

    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            # Try to break at sentence/paragraph boundary
            if end < len(text):
                # Look for period, newline, or space within last 100 chars
                boundary = text.rfind(". ", start + chunk_size - 100, end)
                if boundary == -1:
                    boundary = text.rfind("\n", start + chunk_size - 100, end)
                if boundary == -1:
                    boundary = text.rfind(" ", start + chunk_size - 100, end)
                if boundary != -1:
                    end = boundary + 1
            chunks.append(text[start:end].strip())
            start = end - overlap
            if start < 0:
                start = 0
        return chunks

    def _normalize_metadata(self, metadata: Dict) -> Dict:
        """Ensure all metadata keys are strings (ChromaDB requirement)."""
        if not metadata:
            return {}
        return {str(k): v for k, v in metadata.items()}

    async def add_document_async(self, text: str, metadata: Dict = None) -> List[str]:
        """Async version of add_document."""
        return await run_sync_in_thread(self.add_document, text, metadata)

    def add_document(self, text: str, metadata: Dict = None) -> List[str]:
        """
        Add a document to the vector store.
        
        Args:
            text: Full document text
            metadata: Optional metadata (filename, user, timestamp, etc.)
            
        Returns:
            List of chunk IDs
        """
        # Normalize metadata
        safe_metadata = self._normalize_metadata(metadata)
        
        # Generate a unique document ID
        doc_id = hashlib.md5(text[:2000].encode()).hexdigest()
        
        # Check if document already exists
        if safe_metadata.get("filename"):
            try:
                existing = self.collection.get(where={"filename": safe_metadata["filename"]})
                if existing and existing["ids"]:
                    return existing["ids"]
            except Exception:
                pass  # If check fails, proceed with adding

        # Chunk the text
        chunks = self._chunk_text(text)
        
        # Generate IDs for each chunk
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        # Prepare metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            m = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": doc_id,
                "chunk_length": len(chunk),
                **safe_metadata
            }
            metadatas.append(m)
        
        # Add to ChromaDB with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                self.collection.add(
                    ids=chunk_ids,
                    documents=chunks,
                    metadatas=metadatas
                )
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise e
                print(f"⚠️ ChromaDB add failed (attempt {attempt+1}), retrying...")
                import time
                time.sleep(1)
        
        return chunk_ids

    async def search_async(self, query: str, top_k: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """Async version of search."""
        return await run_sync_in_thread(self.search, query, top_k, filter_metadata)

    def search(self, query: str, top_k: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """
        Search for relevant document chunks.
        
        Args:
            query: User query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"filename": "doc.pdf"})
            
        Returns:
            List of dicts with text, metadata, and relevance score
        """
        # Normalize filter metadata
        safe_filter = self._normalize_metadata(filter_metadata) if filter_metadata else None
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=safe_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"⚠️ ChromaDB query failed: {e}")
            return []
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # Convert distance to similarity (1 - distance for cosine)
                similarity = 1 - results["distances"][0][i] if results["distances"] else 0.5
                formatted.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": round(similarity, 4),
                    "id": results["ids"][0][i]
                })
        
        return formatted

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document."""
        try:
            self.collection.delete(where={"doc_id": doc_id})
            return True
        except Exception as e:
            print(f"⚠️ Failed to delete document {doc_id}: {e}")
            return False

    def delete_by_filename(self, filename: str) -> bool:
        """Delete all chunks for a specific filename."""
        try:
            self.collection.delete(where={"filename": filename})
            return True
        except Exception as e:
            print(f"⚠️ Failed to delete filename {filename}: {e}")
            return False

    def clear_all(self):
        """Clear all documents from the vector store."""
        try:
            self.collection.delete(where={})
            self.client.delete_collection(COLLECTION_NAME)
            # Recreate collection
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_func
            )
        except Exception as e:
            print(f"⚠️ Failed to clear vector store: {e}")

    def count(self) -> int:
        """Get number of chunks in the store."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def get_document_chunks(self, doc_id: str) -> List[str]:
        """Retrieve all chunk texts for a document."""
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            return results["documents"] if results else []
        except Exception:
            return []

    def get_documents_metadata(self) -> List[Dict]:
        """Get unique document metadata (without chunks)."""
        try:
            results = self.collection.get(include=["metadatas"])
            if not results or not results["metadatas"]:
                return []
            
            seen_docs = set()
            unique_metadata = []
            for m in results["metadatas"]:
                doc_id = m.get("doc_id")
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    unique_metadata.append(m)
            return unique_metadata
        except Exception:
            return []

    def get_stats(self) -> Dict:
        """Get vector store statistics for monitoring."""
        return {
            "total_chunks": self.count(),
            "unique_documents": len(self.get_documents_metadata()),
            "collection_name": COLLECTION_NAME,
            "persist_directory": str(self.persist_directory),
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        }

# ==========================================================
# SINGLETON INSTANCE
# ==========================================================
# Global vector store instance
vector_store = VectorStore()