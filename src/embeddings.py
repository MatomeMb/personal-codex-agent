"""
Embeddings System for Personal Codex Agent

File purpose:
    Provide a thin wrapper around sentence-transformers for embedding
    generation and FAISS for efficient nearest-neighbour search. The class
    accepts processed document chunks and indexes them for later retrieval by
    the RAG pipeline.

Key components:
    - SentenceTransformer model loader (lightweight default model)
    - FAISS IndexFlatIP index used as an inner-product index for cosine similarity
    - Serialization helpers to save/load the FAISS index and metadata

Design notes:
    - This repository favors FAISS-only operation for Streamlit Cloud
      compatibility; ChromaDB support has been intentionally removed.
    - The module normalizes embeddings before adding to FAISS so inner-product
      search behaves like cosine similarity.

Usage example:
    >>> es = EmbeddingsSystem()
    >>> es.add_documents(processed_documents)
    >>> hits = es.search('machine learning', top_k=3)
"""

import os
import pickle
import numpy as np
import logging
from typing import List, Dict, Any
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError as e:
    print(f"Warning: Some embedding libraries not available: {e}")

from .exceptions import EmbeddingGenerationError, VectorDatabaseError


class EmbeddingsSystem:
    """
    Handles text embeddings and vector similarity search.

    Purpose and responsibility:
        - Maintain an embedding model and FAISS index
        - Normalize and add chunk embeddings to the index
        - Perform similarity search and return chunk metadata and scores

    Key attributes:
        - model_name (str): SentenceTransformer model identifier
        - vector_db_type (str): 'faiss' (only supported option)
        - model: Loaded SentenceTransformer model instance or None
        - vector_db: FAISS index object
        - chunk_embeddings: list of stored embeddings (normalized)
        - chunk_metadata: list of metadata dicts corresponding to stored chunks

    Example:
        >>> es = EmbeddingsSystem(model_name='all-MiniLM-L6-v2')
        >>> es.generate_embeddings(['hello world'])
        array([...])
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2",
                 vector_db_type: str = "faiss"):
        """
        Initialize the embeddings system

        Args:
            model_name: Sentence transformer model to use
            vector_db_type: Type of vector database ('faiss' or 'chroma')
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.vector_db_type = vector_db_type
        self.model = None
        self.vector_db = None
        self.chunk_embeddings = []
        self.chunk_metadata = []

        try:
            self._initialize_model()
            self._initialize_vector_db()
            self.logger.info("EmbeddingsSystem initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing EmbeddingsSystem: {e}")
            raise EmbeddingGenerationError(f"Failed to initialize embeddings system: {e}")

    def _initialize_model(self):
        """
        Initialize the sentence transformer model.

        Notes:
            - When running in CI or mock modes the import may fail; this method
              sets `self.model` to None on error. Callers should handle a None
              model (the rest of the repo expects a working model in normal
              operation).
        """
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Fallback to a simpler approach if needed
            self.model = None

    def _initialize_vector_db(self):
        """
        Initialize the vector database backend. Currently only FAISS is
        supported; attempts to use other backends will force the system to
        FAISS with a warning.
        """
        if self.vector_db_type == "faiss":
            self._initialize_faiss()
        else:
            # Force FAISS for mock mode - ChromaDB removed for cloud deployment
            print(f"Warning: {self.vector_db_type} not supported, using FAISS instead")
            self.vector_db_type = "faiss"
            self._initialize_faiss()

    def _initialize_faiss(self):
        """
        Initialize FAISS vector database.

        - Chooses an index dimension heuristic based on the model name.
        - Uses IndexFlatIP (inner-product) and relies on normalized vectors
          so IP behaves like cosine similarity.
        """
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
        """
        Generate embeddings for a list of texts using the sentence-transformers model.

        Args:
            texts (List[str]): List of text strings to embed.

        Returns:
            np.ndarray: Array of embeddings shaped (len(texts), dimension).

        Raises:
            EmbeddingGenerationError: If the model is not initialized or generation fails.
        """
        if self.model is None:
            self.logger.error("Embedding model not initialized")
            raise EmbeddingGenerationError("Embedding model not initialized")

        if not texts:
            self.logger.warning("Empty text list provided for embedding generation")
            return np.array([])

        try:
            self.logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            self.logger.info(f"Successfully generated embeddings with shape {embeddings.shape}")
            return embeddings
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embeddings: {e}")

    def add_documents(self, processed_documents: List[Dict[str, Any]]):
        """
        Add processed documents (from `DocumentProcessor`) to the vector database.

        Args:
            processed_documents (List[Dict[str, Any]]): Each document must include
                a 'chunks' list where each chunk is a dict with 'content' and 'metadata'.

        Returns:
            None

        Side effects:
            - Generates embeddings for each chunk and adds them to FAISS
            - Appends metadata to `self.chunk_metadata` for later retrieval
        """
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

        # Generate embeddings and add to FAISS. Keep errors local to avoid
        # crashing the caller; failures are surfaced via printed warnings.
        try:
            embeddings = self.generate_embeddings(all_chunks)

            # FAISS only for mock mode deployment
            self._add_to_faiss(embeddings, all_metadata)

            print(f"Added {len(all_chunks)} chunks to vector database")

        except Exception as e:
            print(f"Error adding documents to vector database: {e}")

    def _add_to_faiss(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Add embeddings to the FAISS index and store metadata.

        Args:
            embeddings (np.ndarray): Raw embeddings (not necessarily normalized)
            metadata (List[Dict[str, Any]]): Metadata entries corresponding to rows

        Returns:
            None

        Notes:
            - Normalizes embeddings to unit length so IndexFlatIP returns cosine-like
              similarity scores.
        """
        if self.vector_db is None:
            raise RuntimeError("FAISS database not initialized")

        # Normalize embeddings for cosine similarity
        embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Add to FAISS index (FAISS expects float32)
        self.vector_db.add(embeddings_normalized.astype('float32'))

        # Persist embeddings and metadata in-memory for easy lookup by index
        self.chunk_embeddings.extend(embeddings_normalized)
        self.chunk_metadata.extend(metadata)

    # ChromaDB add method removed for mock mode deployment
    # FAISS-only operation reduces dependencies and ensures cloud compatibility

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for chunks similar to the provided query.

        Args:
            query (str): Natural language query string
            top_k (int): Number of top results to return

        Returns:
            List[Dict[str, Any]]: List of result dicts with keys 'content',
                'metadata', and 'score'. Empty list on error.
        """
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
        """
        Internal FAISS search implementation.

        Args:
            query_embedding (np.ndarray): Shape (1, dim) query embedding
            top_k (int): Number of results to retrieve

        Returns:
            List[Dict[str, Any]]: List of result dicts
        """
        if self.vector_db is None:
            return []

        # Normalize query embedding to match stored vector norms
        query_normalized = query_embedding / np.linalg.norm(query_embedding)

        # Perform the FAISS search. The `min` protects against requesting more
        # results than exist in the index.
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
        """
        Save the FAISS index and metadata to disk using the provided base file path.

        The FAISS index will be written to `{file_path}.faiss` and the metadata to
        `{file_path}_metadata.pkl`.
        """
        # FAISS only for mock mode deployment
        self._save_faiss(file_path)

    def _save_faiss(self, file_path: str):
        """
        Save FAISS index and metadata to disk. Metadata includes chunk embeddings
        and chunk metadata to enable reloading state.
        """
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
        """
        Load FAISS index and metadata from disk. Expects the same filenames used
        in `_save_faiss`.
        """
        # FAISS only for mock mode deployment
        self._load_faiss(file_path)

    def _load_faiss(self, file_path: str):
        """
        Internal FAISS load routine. Restores `self.vector_db`, `self.chunk_embeddings`,
        and `self.chunk_metadata`.
        """
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
        """
        Return lightweight information about the currently loaded vector DB.

        Returns:
            Dict[str, Any]: Fields include 'type', 'total_vectors', 'dimension',
                and 'total_chunks'. If uninitialized returns status accordingly.
        """
        # FAISS only for mock mode deployment
        if self.vector_db is None:
            return {"status": "not_initialized", "type": "faiss"}

        return {
            "type": "faiss",
            "total_vectors": self.vector_db.ntotal,
            "dimension": self.vector_db.d,
            "total_chunks": len(self.chunk_metadata)
        }
