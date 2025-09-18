"""
Configuration Management for Personal Codex Agent

Handles environment-aware configuration for both local and cloud deployments.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    """Environment-aware configuration manager"""
    
    def __init__(self):
        self.is_cloud_deployment = self._detect_cloud_deployment()
        self.data_dir = self._setup_data_directory()
        self.log_level = self._get_log_level()
        self._setup_logging()
    
    def _detect_cloud_deployment(self) -> bool:
        """Detect if running in cloud deployment (Streamlit Cloud)"""
        return (
            os.getenv('STREAMLIT_SHARING_MODE', '').lower() == 'true' or
            os.getenv('STREAMLIT_SERVER_HEADLESS', '').lower() == 'true' or
            'streamlit.app' in os.getenv('STREAMLIT_SERVER_ADDRESS', '')
        )
    
    def _setup_data_directory(self) -> Path:
        """Setup data directory with cloud deployment compatibility"""
        if self.is_cloud_deployment:
            # Use relative paths for cloud deployment
            data_dir = Path('./data')
        else:
            # Use absolute paths for local development
            data_dir = Path('data')
        
        # Ensure directories exist
        data_dir.mkdir(exist_ok=True)
        (data_dir / 'raw').mkdir(exist_ok=True)
        (data_dir / 'processed').mkdir(exist_ok=True)
        
        return data_dir
    
    def _get_log_level(self) -> str:
        """Get log level from environment or default"""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('personal_codex.log', mode='a')
            ]
        )
    
    def get_database_path(self, base_name: str = "knowledge_base") -> str:
        """Get database path with cloud compatibility"""
        return str(self.data_dir / 'processed' / base_name)
    
    def get_processed_documents_path(self) -> str:
        """Get processed documents path"""
        return str(self.data_dir / 'processed' / 'processed_documents.json')
    
    def get_raw_documents_path(self) -> str:
        """Get raw documents path"""
        return str(self.data_dir / 'raw')
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'
        api_key = os.getenv('OPENAI_API_KEY', '')
        return (
            mock_mode or 
            not api_key or 
            api_key in ['your_openai_api_key_here', 'mock_mode']
        )
    
    def get_llm_provider(self) -> str:
        """Get preferred LLM provider based on available API keys"""
        openai_key = os.getenv('OPENAI_API_KEY', '')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if openai_key and openai_key not in ['your_openai_api_key_here', 'mock_mode']:
            return 'openai'
        elif anthropic_key and anthropic_key not in ['your_anthropic_api_key_here', 'mock_mode']:
            return 'anthropic'
        else:
            return 'none'
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information for debugging"""
        return {
            'is_cloud_deployment': self.is_cloud_deployment,
            'data_directory': str(self.data_dir),
            'log_level': self.log_level,
            'mock_mode': self.is_mock_mode(),
            'llm_provider': self.get_llm_provider(),
            'environment_variables': {
                'STREAMLIT_SHARING_MODE': os.getenv('STREAMLIT_SHARING_MODE'),
                'STREAMLIT_SERVER_HEADLESS': os.getenv('STREAMLIT_SERVER_HEADLESS'),
                'STREAMLIT_SERVER_ADDRESS': os.getenv('STREAMLIT_SERVER_ADDRESS'),
            }
        }

# Global config instance
config = Config()
