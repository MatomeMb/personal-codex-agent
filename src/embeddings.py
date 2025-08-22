"""
Embeddings System for Personal Codex Agent
Handles vector embeddings and similarity search for RAG implementation
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import chromadb
    from chromadb.config import Settings
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
        self.chroma_client = None
        self.chroma_collection = None
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
        elif self.vector_db_type == "chroma":
            self._initialize_chroma()
        else:
            raise ValueError(f"Unsupported vector database type: {self.vector_db_type}")
    
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
    
    def _initialize_chroma(self):
        """Initialize ChromaDB vector database"""
        try:
            # Create a persistent client
            db_path = Path("data/processed/chroma_db")
            db_path.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="personal_codex",
                metadata={"description": "Personal Codex Agent Knowledge Base"}
            )
            print("Initialized ChromaDB vector database")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            self.chroma_client = None
            self.chroma_collection = None
    
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
            
            if self.vector_db_type == "faiss":
                self._add_to_faiss(embeddings, all_metadata)
            elif self.vector_db_type == "chroma":
                self._add_to_chroma(all_chunks, embeddings, all_metadata)
            
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
    
    def _add_to_chroma(self, texts: List[str], embeddings: np.ndarray, 
                       metadata: List[Dict[str, Any]]):
        """Add embeddings to ChromaDB"""
        if self.chroma_collection is None:
            raise RuntimeError("ChromaDB not initialized")
        
        # Prepare data for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(texts))]
        
        # Convert embeddings to list format for ChromaDB
        embeddings_list = embeddings.tolist()
        
        # Add to ChromaDB
        self.chroma_collection.add(
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadata,
            ids=ids
        )
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents based on query"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])
            
            if self.vector_db_type == "faiss":
                return self._search_faiss(query_embedding, top_k)
            elif self.vector_db_type == "chroma":
                return self._search_chroma(query, top_k)
            else:
                raise ValueError(f"Unsupported vector database type: {self.vector_db_type}")
                
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
    
    def _search_chroma(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search ChromaDB"""
        if self.chroma_collection is None:
            return []
        
        try:
            # Search in ChromaDB
            results = self.chroma_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['metadatas'] and results['distances']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1.0 - float(results['distances'][0][i])  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []
    
    def save_database(self, file_path: str):
        """Save the vector database to disk"""
        if self.vector_db_type == "faiss":
            self._save_faiss(file_path)
        elif self.vector_db_type == "chroma":
            # ChromaDB is persistent by default
            print("ChromaDB is persistent - no need to save separately")
    
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
        if self.vector_db_type == "faiss":
            self._load_faiss(file_path)
        elif self.vector_db_type == "chroma":
            # ChromaDB loads automatically
            print("ChromaDB loads automatically from persistent storage")
    
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
        if self.vector_db_type == "faiss":
            if self.vector_db is None:
                return {"status": "not_initialized", "type": "faiss"}
            
            return {
                "type": "faiss",
                "total_vectors": self.vector_db.ntotal,
                "dimension": self.vector_db.d,
                "total_chunks": len(self.chunk_metadata)
            }
        
        elif self.vector_db_type == "chroma":
            if self.chroma_collection is None:
                return {"status": "not_initialized", "type": "chroma"}
            
            try:
                count = self.chroma_collection.count()
                return {
                    "type": "chroma",
                    "total_chunks": count,
                    "collection_name": "personal_codex"
                }
            except Exception as e:
                return {"status": "error", "type": "chroma", "error": str(e)}
        
        return {"status": "unknown", "type": "unknown"}
