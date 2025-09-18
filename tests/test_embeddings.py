"""
Tests for Embeddings System module
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append('.')

from src.embeddings import EmbeddingsSystem
from src.exceptions import EmbeddingGenerationError, VectorDatabaseError

class TestEmbeddingsSystem:
    """Test suite for EmbeddingsSystem class"""
    
    def test_embeddings_initialization(self):
        """Test embeddings system initialization"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            assert es.model_name == "all-MiniLM-L6-v2"
            assert es.vector_db_type == "faiss"
            assert es.model is not None
            assert es.vector_db is not None
    
    def test_embeddings_initialization_without_model(self):
        """Test embeddings system initialization when model fails to load"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_transformer.side_effect = Exception("Model loading failed")
            
            es = EmbeddingsSystem()
            assert es.model is None
            assert es.vector_db is None
    
    def test_generate_embeddings_without_model(self):
        """Test generating embeddings when model is not available"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_transformer.side_effect = Exception("Model loading failed")
            
            es = EmbeddingsSystem()
            
            with pytest.raises(RuntimeError):
                es.generate_embeddings(["test text"])
    
    def test_generate_embeddings_with_model(self):
        """Test generating embeddings with available model"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            embeddings = es.generate_embeddings(["test text"])
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (1, 3)
            mock_model.encode.assert_called_once_with(["test text"], convert_to_tensor=False)
    
    def test_add_documents_empty(self):
        """Test adding empty document list"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            es.add_documents([])
            
            # Should not call encode for empty list
            mock_model.encode.assert_not_called()
    
    def test_add_documents_with_content(self):
        """Test adding documents with content"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            
            processed_docs = [
                {
                    'chunks': [
                        {'content': 'First chunk', 'metadata': {'filename': 'test1.txt'}},
                        {'content': 'Second chunk', 'metadata': {'filename': 'test2.txt'}}
                    ]
                }
            ]
            
            es.add_documents(processed_docs)
            
            assert len(es.chunk_embeddings) == 2
            assert len(es.chunk_metadata) == 2
            mock_model.encode.assert_called_once()
    
    def test_search_without_model(self):
        """Test search when model is not available"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_transformer.side_effect = Exception("Model loading failed")
            
            es = EmbeddingsSystem()
            
            with pytest.raises(RuntimeError):
                es.search("test query")
    
    def test_search_with_model(self):
        """Test search with available model"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            
            # Add some test data
            es.chunk_embeddings = [np.array([0.1, 0.2, 0.3]), np.array([0.4, 0.5, 0.6])]
            es.chunk_metadata = [
                {'filename': 'test1.txt', 'content': 'First chunk'},
                {'filename': 'test2.txt', 'content': 'Second chunk'}
            ]
            
            # Mock FAISS search
            with patch.object(es.vector_db, 'search') as mock_search:
                mock_search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
                
                results = es.search("test query", top_k=2)
                
                assert len(results) == 2
                assert results[0]['content'] == 'First chunk'
                assert results[1]['content'] == 'Second chunk'
                assert 'score' in results[0]
                assert 'metadata' in results[0]
    
    def test_save_database(self):
        """Test saving database to disk"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            es.chunk_embeddings = [np.array([0.1, 0.2, 0.3])]
            es.chunk_metadata = [{'filename': 'test.txt'}]
            
            with patch('src.embeddings.faiss.write_index') as mock_write:
                with patch('builtins.open', create=True) as mock_open:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = Path(temp_dir) / "test_db"
                        es.save_database(str(file_path))
                        
                        mock_write.assert_called_once()
                        mock_open.assert_called()
    
    def test_load_database(self):
        """Test loading database from disk"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            
            with patch('src.embeddings.faiss.read_index') as mock_read:
                with patch('builtins.open', create=True) as mock_open:
                    with patch('pickle.load') as mock_pickle:
                        mock_pickle.return_value = {
                            'chunk_embeddings': [np.array([0.1, 0.2, 0.3])],
                            'chunk_metadata': [{'filename': 'test.txt'}]
                        }
                        
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = Path(temp_dir) / "test_db"
                            es.load_database(str(file_path))
                            
                            mock_read.assert_called_once()
                            mock_open.assert_called()
    
    def test_get_database_info_not_initialized(self):
        """Test getting database info when not initialized"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_transformer.side_effect = Exception("Model loading failed")
            
            es = EmbeddingsSystem()
            info = es.get_database_info()
            
            assert info['status'] == 'not_initialized'
            assert info['type'] == 'faiss'
    
    def test_get_database_info_initialized(self):
        """Test getting database info when initialized"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            es.chunk_embeddings = [np.array([0.1, 0.2, 0.3])]
            es.chunk_metadata = [{'filename': 'test.txt'}]
            
            info = es.get_database_info()
            
            assert info['type'] == 'faiss'
            assert info['total_vectors'] == 0  # FAISS index is empty
            assert info['total_chunks'] == 1
    
    def test_vector_db_type_fallback(self):
        """Test that unsupported vector DB types fall back to FAISS"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem(vector_db_type="unsupported")
            assert es.vector_db_type == "faiss"
    
    def test_embedding_normalization(self):
        """Test that embeddings are normalized for cosine similarity"""
        with patch('src.embeddings.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            # Return non-normalized embeddings
            mock_model.encode.return_value = np.array([[3.0, 4.0, 0.0]])
            mock_transformer.return_value = mock_model
            
            es = EmbeddingsSystem()
            
            processed_docs = [
                {
                    'chunks': [
                        {'content': 'Test chunk', 'metadata': {'filename': 'test.txt'}}
                    ]
                }
            ]
            
            es.add_documents(processed_docs)
            
            # Check that embeddings are normalized
            assert len(es.chunk_embeddings) == 1
            normalized_embedding = es.chunk_embeddings[0]
            norm = np.linalg.norm(normalized_embedding)
            assert abs(norm - 1.0) < 1e-6  # Should be normalized to unit length

if __name__ == "__main__":
    pytest.main([__file__])
