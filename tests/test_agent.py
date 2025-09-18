"""
Comprehensive tests for Personal Codex Agent

This module tests all major components of the Personal Codex Agent system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
import sys
sys.path.append('.')

from src.agent import PersonalCodexAgent
from src.exceptions import PersonalCodexException, DocumentProcessingError, VectorDatabaseError
from src.config import config

class TestPersonalCodexAgent:
    """Test suite for PersonalCodexAgent class"""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly"""
        agent = PersonalCodexAgent(llm_provider="none")
        assert agent.llm_provider == "none"
        assert agent.current_mode == "interview"
        assert agent.documents_loaded == False
        assert agent.knowledge_base_initialized == False
    
    def test_agent_initialization_with_invalid_provider(self):
        """Test agent initialization with invalid LLM provider"""
        # Should not raise exception, should fall back to mock
        agent = PersonalCodexAgent(llm_provider="invalid")
        assert agent.openai_client is not None  # Should have mock client
    
    def test_mode_switching(self):
        """Test mode switching functionality"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        # Test valid mode switch
        result = agent.switch_mode("fast_facts")
        assert "Fast Facts Mode" in result
        assert agent.current_mode == "fast_facts"
        
        # Test invalid mode switch
        result = agent.switch_mode("invalid_mode")
        assert "Unknown mode" in result
        assert agent.current_mode == "fast_facts"  # Should not change
    
    def test_get_available_modes(self):
        """Test getting available modes"""
        agent = PersonalCodexAgent(llm_provider="none")
        modes = agent.get_available_modes()
        
        expected_modes = ["interview", "personal_storytelling", "fast_facts"]
        assert all(mode in modes for mode in expected_modes)
    
    def test_get_current_mode(self):
        """Test getting current mode"""
        agent = PersonalCodexAgent(llm_provider="none")
        assert agent.get_current_mode() == "interview"
        
        agent.switch_mode("fast_facts")
        assert agent.get_current_mode() == "fast_facts"
    
    def test_search_knowledge_base_no_documents(self):
        """Test searching knowledge base when no documents loaded"""
        agent = PersonalCodexAgent(llm_provider="none")
        results = agent.search_knowledge_base("test query")
        assert results == []
    
    def test_generate_response_no_documents(self):
        """Test generating response when no documents loaded"""
        agent = PersonalCodexAgent(llm_provider="none")
        response = agent.generate_response("test question")
        
        assert "response" in response
        assert "sources" in response
        assert "mode" in response
        assert "confidence" in response
        assert response["mode"] == "interview"
        assert response["confidence"] == "low"
    
    def test_generate_response_with_documents(self):
        """Test generating response with documents loaded"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        # Mock the knowledge base as loaded
        agent.documents_loaded = True
        agent.knowledge_base_initialized = True
        
        # Mock search results
        with patch.object(agent, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    'content': 'Test content about software engineering',
                    'metadata': {'filename': 'test.txt'},
                    'score': 0.9
                }
            ]
            
            response = agent.generate_response("What are your skills?")
            
            assert "response" in response
            assert response["mode"] == "interview"
            assert response["confidence"] in ["high", "medium", "low"]
    
    def test_get_knowledge_base_info(self):
        """Test getting knowledge base information"""
        agent = PersonalCodexAgent(llm_provider="none")
        info = agent.get_knowledge_base_info()
        
        assert isinstance(info, dict)
        assert "type" in info or "status" in info
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary"""
        agent = PersonalCodexAgent(llm_provider="none")
        summary = agent.get_conversation_summary()
        
        assert isinstance(summary, dict)
        assert "total_turns" in summary
        assert "current_mode" in summary
        assert "documents_loaded" in summary
        assert "knowledge_base_initialized" in summary

class TestDocumentProcessing:
    """Test document processing functionality"""
    
    def test_load_documents_nonexistent_directory(self):
        """Test loading documents from non-existent directory"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        with pytest.raises(DocumentProcessingError):
            agent.load_documents("nonexistent_directory")
    
    def test_load_documents_empty_directory(self):
        """Test loading documents from empty directory"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = agent.load_documents(temp_dir)
            assert result == False
    
    def test_load_documents_with_files(self):
        """Test loading documents with actual files"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("This is a test document about software engineering.")
            
            # Mock the embeddings system to avoid actual embedding generation
            with patch.object(agent.embeddings_system, 'add_documents') as mock_add:
                mock_add.return_value = None
                
                result = agent.load_documents(temp_dir)
                assert result == True
                assert agent.documents_loaded == True
                assert agent.knowledge_base_initialized == True

class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_agent_initialization_error(self):
        """Test agent initialization with errors"""
        with patch('src.agent.DocumentProcessor') as mock_processor:
            mock_processor.side_effect = Exception("Test error")
            
            with pytest.raises(PersonalCodexException):
                PersonalCodexAgent(llm_provider="none")
    
    def test_document_processing_error(self):
        """Test document processing error handling"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")
            
            # Mock document processor to raise error
            with patch.object(agent.document_processor, 'process_directory') as mock_process:
                mock_process.side_effect = Exception("Processing error")
                
                with pytest.raises(DocumentProcessingError):
                    agent.load_documents(temp_dir)
    
    def test_vector_database_error(self):
        """Test vector database error handling"""
        agent = PersonalCodexAgent(llm_provider="none")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")
            
            # Mock embeddings system to raise error
            with patch.object(agent.embeddings_system, 'add_documents') as mock_add:
                mock_add.side_effect = Exception("Vector DB error")
                
                with pytest.raises(VectorDatabaseError):
                    agent.load_documents(temp_dir)

class TestMockMode:
    """Test mock mode functionality"""
    
    def test_mock_mode_initialization(self):
        """Test that mock mode initializes correctly"""
        agent = PersonalCodexAgent(llm_provider="none")
        assert agent.openai_client is not None
        assert hasattr(agent.openai_client, 'generate_response')
    
    def test_mock_response_generation(self):
        """Test mock response generation"""
        agent = PersonalCodexAgent(llm_provider="none")
        agent.documents_loaded = True
        agent.knowledge_base_initialized = True
        
        # Mock search results
        with patch.object(agent, 'search_knowledge_base') as mock_search:
            mock_search.return_value = [
                {
                    'content': 'Software engineering skills',
                    'metadata': {'filename': 'cv.txt'},
                    'score': 0.8
                }
            ]
            
            response = agent.generate_response("What are your skills?")
            
            assert "response" in response
            assert len(response["response"]) > 0
            assert response["mode"] == "interview"

class TestConfiguration:
    """Test configuration system"""
    
    def test_config_initialization(self):
        """Test that config initializes correctly"""
        assert config is not None
        assert hasattr(config, 'is_cloud_deployment')
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'is_mock_mode')
    
    def test_config_paths(self):
        """Test configuration path methods"""
        db_path = config.get_database_path()
        assert isinstance(db_path, str)
        assert "knowledge_base" in db_path
        
        processed_path = config.get_processed_documents_path()
        assert isinstance(processed_path, str)
        assert "processed_documents.json" in processed_path
        
        raw_path = config.get_raw_documents_path()
        assert isinstance(raw_path, str)
        assert "raw" in raw_path
    
    def test_config_deployment_info(self):
        """Test deployment information"""
        info = config.get_deployment_info()
        assert isinstance(info, dict)
        assert "is_cloud_deployment" in info
        assert "data_directory" in info
        assert "mock_mode" in info
        assert "llm_provider" in info

if __name__ == "__main__":
    pytest.main([__file__])
