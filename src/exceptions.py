"""
Custom Exceptions for Personal Codex Agent

This module defines specific exception types for better error handling
and debugging throughout the application.
"""

class PersonalCodexException(Exception):
    """Base exception for Personal Codex Agent"""
    pass

class DocumentProcessingError(PersonalCodexException):
    """Raised when document processing fails"""
    pass

class EmbeddingGenerationError(PersonalCodexException):
    """Raised when embedding generation fails"""
    pass

class VectorDatabaseError(PersonalCodexException):
    """Raised when vector database operations fail"""
    pass

class LLMClientError(PersonalCodexException):
    """Raised when LLM client operations fail"""
    pass

class ConfigurationError(PersonalCodexException):
    """Raised when configuration is invalid"""
    pass

class DeploymentError(PersonalCodexException):
    """Raised when deployment-specific issues occur"""
    pass
