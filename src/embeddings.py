"""
Embeddings System for Personal Codex Agent
Handles vector embeddings and similarity search for RAG implementation

UPDATED FOR MOCK MODE DEPLOYMENT:
- ChromaDB dependencies removed to reduce installation weight
- FAISS-only operation for Streamlit Cloud compatibility
- Simplified codebase for mock mode functionality
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError as e:
    print(f"Warning: Some embedding libraries not available: {e}")

class EmbeddingsSystem:
    """Handles text embeddings and vector similarity search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 vector_db_type: str = "faiss"):
        """
        Initialize the embeddings system
        
        Args:
            model_name: Sentence transformer model to use
            vector_db_type: Type of vector database ('faiss' or 'chroma')
        """
        self.model_name = model_name
        self.vector_db_type = vector_db_type
        self.model = None
        self.vector_db = None
        self.chunk_embeddings = []
        self.chunk_metadata = []
        
        self._initialize_model()
        self._initialize_vector_db()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Fallback to a simpler approach if needed
            self.model = None
    
    def _initialize_vector_db(self):
        """Initialize the vector database"""
        if self.vector_db_type == "faiss":
            self._initialize_faiss()
        else:
            # Force FAISS for mock mode - ChromaDB removed for cloud deployment
            print(f"Warning: {self.vector_db_type} not supported, using FAISS instead")
            self.vector_db_type = "faiss"
            self._initialize_faiss()
    
    def _initialize_faiss(self):
        """Initialize FAISS vector database"""
        try:
            # Start with an empty index
            dimension = 384 if "MiniLM" in self.model_name else 768
            self.vector_db = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            print("Initialized FAISS vector database")
        except Exception as e:
            print(f"Error initializing FAISS: {e}")
            self.vector_db = None
    
    # ChromaDB initialization removed for mock mode deployment
    # This reduces dependencies and ensures FAISS-only operation
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings
        except Exception as e:
            raise Exception(f"Error generating embeddings: {e}")
    
    def add_documents(self, processed_documents: List[Dict[str, Any]]):
        """Add processed documents to the vector database"""
        if not processed_documents:
            return
        
        all_chunks = []
        all_metadata = []
        
        # Extract all chunks from processed documents
        for doc in processed_documents:
            for chunk in doc['chunks']:
                all_chunks.append(chunk['content'])
                all_metadata.append(chunk['metadata'])
        
        if not all_chunks:
            return
        
        # Generate embeddings
        try:
            embeddings = self.generate_embeddings(all_chunks)
            
            # FAISS only for mock mode deployment
            self._add_to_faiss(embeddings, all_metadata)
            
            print(f"Added {len(all_chunks)} chunks to vector database")
            
        except Exception as e:
            print(f"Error adding documents to vector database: {e}")
    
    def _add_to_faiss(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """Add embeddings to FAISS database"""
        if self.vector_db is None:
            raise RuntimeError("FAISS database not initialized")
        
        # Normalize embeddings for cosine similarity
        embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS
        self.vector_db.add(embeddings_normalized.astype('float32'))
        
        # Store metadata
        self.chunk_embeddings.extend(embeddings_normalized)
        self.chunk_metadata.extend(metadata)
    
    # ChromaDB add method removed for mock mode deployment
    # FAISS-only operation reduces dependencies and ensures cloud compatibility
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents based on query"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])
            
            # FAISS only for mock mode deployment
            return self._search_faiss(query_embedding, top_k)
                
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    def _search_faiss(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search FAISS database"""
        if self.vector_db is None:
            return []
        
        # Normalize query embedding
        query_normalized = query_embedding / np.linalg.norm(query_embedding)
        
        # Search
        scores, indices = self.vector_db.search(
            query_normalized.astype('float32'), 
            min(top_k, len(self.chunk_metadata))
        )
        
        # Prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunk_metadata):
                results.append({
                    'content': self.chunk_metadata[idx].get('content', ''),
                    'metadata': self.chunk_metadata[idx],
                    'score': float(score)
                })
        
        return results
    
    # ChromaDB search method removed for mock mode deployment
    # FAISS-only operation ensures cloud compatibility
    
    def save_database(self, file_path: str):
        """Save the vector database to disk"""
        # FAISS only for mock mode deployment
        self._save_faiss(file_path)
    
    def _save_faiss(self, file_path: str):
        """Save FAISS database to disk"""
        if self.vector_db is None:
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.vector_db, f"{file_path}.faiss")
            
            # Save metadata
            with open(f"{file_path}_metadata.pkl", 'wb') as f:
                pickle.dump({
                    'chunk_embeddings': self.chunk_embeddings,
                    'chunk_metadata': self.chunk_metadata
                }, f)
            
            print(f"Saved FAISS database to {file_path}")
        except Exception as e:
            print(f"Error saving FAISS database: {e}")
    
    def load_database(self, file_path: str):
        """Load the vector database from disk"""
        # FAISS only for mock mode deployment
        self._load_faiss(file_path)
    
    def _load_faiss(self, file_path: str):
        """Load FAISS database from disk"""
        try:
            # Load FAISS index
            self.vector_db = faiss.read_index(f"{file_path}.faiss")
            
            # Load metadata
            with open(f"{file_path}_metadata.pkl", 'rb') as f:
                data = pickle.load(f)
                self.chunk_embeddings = data['chunk_embeddings']
                self.chunk_metadata = data['chunk_metadata']
            
            print(f"Loaded FAISS database from {file_path}")
        except Exception as e:
            print(f"Error loading FAISS database: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the current database"""
        # FAISS only for mock mode deployment
        if self.vector_db is None:
            return {"status": "not_initialized", "type": "faiss"}
        
        return {
            "type": "faiss",
            "total_vectors": self.vector_db.ntotal,
            "dimension": self.vector_db.d,
            "total_chunks": len(self.chunk_metadata)
        }
