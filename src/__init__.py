"""
Personal Codex Agent - Source Package
"""

__version__ = "1.0.0"
__author__ = "Personal Codex Agent Team"
__description__ = "AI-powered personal representative system"

# Import main components for easy access
try:
    from .document_processor import DocumentProcessor
    from .embeddings import EmbeddingsSystem
    from .prompts import PromptManager
    from .agent import PersonalCodexAgent
except ImportError:
    # Allow partial imports for testing
    pass
