"""
Tests for Configuration module
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.append('.')

from src.config import Config, config

class TestConfig:
    """Test suite for Config class"""
    
    def test_config_initialization(self):
        """Test config initialization"""
        test_config = Config()
        assert test_config is not None
        assert hasattr(test_config, 'is_cloud_deployment')
        assert hasattr(test_config, 'data_dir')
        assert hasattr(test_config, 'log_level')
        assert isinstance(test_config.data_dir, Path)
    
    def test_cloud_deployment_detection(self):
        """Test cloud deployment detection"""
        # Test local deployment
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.is_cloud_deployment == False
        
        # Test Streamlit Cloud deployment
        with patch.dict(os.environ, {'STREAMLIT_SHARING_MODE': 'true'}):
            test_config = Config()
            assert test_config.is_cloud_deployment == True
        
        # Test headless mode
        with patch.dict(os.environ, {'STREAMLIT_SERVER_HEADLESS': 'true'}):
            test_config = Config()
            assert test_config.is_cloud_deployment == True
        
        # Test streamlit.app domain
        with patch.dict(os.environ, {'STREAMLIT_SERVER_ADDRESS': 'https://app.streamlit.app'}):
            test_config = Config()
            assert test_config.is_cloud_deployment == True
    
    def test_data_directory_setup(self):
        """Test data directory setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    test_config = Config()
                    
                    # Check that data directory exists
                    assert test_config.data_dir.exists()
                    assert (test_config.data_dir / 'raw').exists()
                    assert (test_config.data_dir / 'processed').exists()
    
    def test_log_level_configuration(self):
        """Test log level configuration"""
        # Test default log level
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.log_level == 'INFO'
        
        # Test custom log level
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            test_config = Config()
            assert test_config.log_level == 'DEBUG'
        
        # Test case insensitive
        with patch.dict(os.environ, {'LOG_LEVEL': 'error'}):
            test_config = Config()
            assert test_config.log_level == 'ERROR'
    
    def test_mock_mode_detection(self):
        """Test mock mode detection"""
        # Test explicit mock mode
        with patch.dict(os.environ, {'MOCK_MODE': 'true'}):
            test_config = Config()
            assert test_config.is_mock_mode() == True
        
        # Test no API key
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.is_mock_mode() == True
        
        # Test placeholder API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'your_openai_api_key_here'}):
            test_config = Config()
            assert test_config.is_mock_mode() == True
        
        # Test mock_mode API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock_mode'}):
            test_config = Config()
            assert test_config.is_mock_mode() == True
        
        # Test real API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-real-api-key'}):
            test_config = Config()
            assert test_config.is_mock_mode() == False
    
    def test_llm_provider_selection(self):
        """Test LLM provider selection"""
        # Test OpenAI provider
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-real-key'}):
            test_config = Config()
            assert test_config.get_llm_provider() == 'openai'
        
        # Test Anthropic provider (no OpenAI key)
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'real-key'}):
            test_config = Config()
            assert test_config.get_llm_provider() == 'anthropic'
        
        # Test no provider (fallback to none)
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            assert test_config.get_llm_provider() == 'none'
        
        # Test preference for OpenAI over Anthropic
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-real-key',
            'ANTHROPIC_API_KEY': 'real-key'
        }):
            test_config = Config()
            assert test_config.get_llm_provider() == 'openai'
    
    def test_database_path_generation(self):
        """Test database path generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    test_config = Config()
                    
                    db_path = test_config.get_database_path()
                    assert isinstance(db_path, str)
                    assert 'knowledge_base' in db_path
                    assert test_config.data_dir.name in db_path
                    
                    # Test custom base name
                    custom_path = test_config.get_database_path("custom_db")
                    assert 'custom_db' in custom_path
    
    def test_processed_documents_path(self):
        """Test processed documents path generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    test_config = Config()
                    
                    path = test_config.get_processed_documents_path()
                    assert isinstance(path, str)
                    assert 'processed_documents.json' in path
                    assert test_config.data_dir.name in path
    
    def test_raw_documents_path(self):
        """Test raw documents path generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    test_config = Config()
                    
                    path = test_config.get_raw_documents_path()
                    assert isinstance(path, str)
                    assert 'raw' in path
                    assert test_config.data_dir.name in path
    
    def test_deployment_info(self):
        """Test deployment information generation"""
        with patch.dict(os.environ, {
            'STREAMLIT_SHARING_MODE': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            test_config = Config()
            info = test_config.get_deployment_info()
            
            assert isinstance(info, dict)
            assert 'is_cloud_deployment' in info
            assert 'data_directory' in info
            assert 'log_level' in info
            assert 'mock_mode' in info
            assert 'llm_provider' in info
            assert 'environment_variables' in info
            
            assert info['is_cloud_deployment'] == True
            assert info['log_level'] == 'DEBUG'
            assert info['mock_mode'] == True  # No API key set
    
    def test_global_config_instance(self):
        """Test that global config instance works"""
        assert config is not None
        assert hasattr(config, 'is_cloud_deployment')
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'is_mock_mode')
        assert hasattr(config, 'get_llm_provider')
    
    def test_path_consistency(self):
        """Test that paths are consistent across calls"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    test_config = Config()
                    
                    # Multiple calls should return same paths
                    path1 = test_config.get_database_path()
                    path2 = test_config.get_database_path()
                    assert path1 == path2
                    
                    # Different base names should return different paths
                    path3 = test_config.get_database_path("different")
                    assert path1 != path3
                    assert "different" in path3
    
    def test_directory_creation(self):
        """Test that directories are created if they don't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {}, clear=True):
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    # Remove directories if they exist
                    data_dir = Path(temp_dir) / 'data'
                    if data_dir.exists():
                        import shutil
                        shutil.rmtree(data_dir)
                    
                    test_config = Config()
                    
                    # Directories should be created
                    assert test_config.data_dir.exists()
                    assert (test_config.data_dir / 'raw').exists()
                    assert (test_config.data_dir / 'processed').exists()

if __name__ == "__main__":
    pytest.main([__file__])
