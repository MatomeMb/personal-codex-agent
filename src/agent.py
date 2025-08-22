"""
Core Agent Logic for Personal Codex Agent

File purpose:
    Implements the `PersonalCodexAgent` which orchestrates the RAG pipeline:
    - Document processing via `DocumentProcessor`
    - Embedding and FAISS indexing via `EmbeddingsSystem`
    - Prompt templating and conversation history via `PromptManager`
    - LLM client selection (OpenAI / Anthropic / Mock)

Key responsibilities:
    - Loading and indexing documents into the knowledge base
    - Searching the knowledge base
    - Formatting prompts and generating LLM responses
    - Mode switching and simple conversation state

Dependencies:
    - openai or anthropic SDKs (optional)
    - src.document_processor.DocumentProcessor
    - src.embeddings.EmbeddingsSystem
    - src.prompts.PromptManager
    - src.mock_llm.MockLLMClient

Usage example:
    >>> agent = PersonalCodexAgent(llm_provider='none')
    >>> agent.load_documents('data/raw')
    >>> resp = agent.generate_response('Tell me about your projects')
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None

from .document_processor import DocumentProcessor
from .embeddings import EmbeddingsSystem
from .prompts import PromptManager
from .mock_llm import MockLLMClient

class PersonalCodexAgent:
    """
    Main agent class that orchestrates the Personal Codex system.

    Purpose and responsibility:
        - Glue together document processing, embedding indexing, prompt
          management, and LLM interaction.

    Key attributes:
        - llm_provider (str): Selected LLM provider ('openai', 'anthropic', 'none')
        - document_processor (DocumentProcessor): Parser & chunker instance
        - embeddings_system (EmbeddingsSystem): Embedding & vector DB manager
        - prompt_manager (PromptManager): Template and context utilities
        - openai_client / anthropic_client: Optional SDK clients or MockLLMClient

    Example:
        >>> agent = PersonalCodexAgent()
        >>> agent.switch_mode('fast_facts')
        'Switched to Fast Facts Mode: ...'
    """
    
    def __init__(self, 
                 llm_provider: str = "openai",
                 vector_db_type: str = "faiss",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the Personal Codex Agent
        
        Args:
            llm_provider: Which LLM to use ('openai' or 'anthropic')
            vector_db_type: Type of vector database ('faiss' or 'chroma')
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.llm_provider = llm_provider
        self.vector_db_type = vector_db_type
        
        # Initialize components
        self.document_processor = DocumentProcessor(chunk_size, chunk_overlap)
        self.embeddings_system = EmbeddingsSystem(vector_db_type=vector_db_type)
        self.prompt_manager = PromptManager()
        
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_llm_clients()
        
        # State management
        self.conversation_history = []
        self.current_mode = "interview"
        self.documents_loaded = False
        self.knowledge_base_initialized = False
        
        # Mode configurations
        self.modes = {
            "interview": {
                "name": "Interview Mode",
                "description": "Professional, concise responses for job interviews and networking",
                "max_tokens": 150
            },
            "personal_storytelling": {
                "name": "Personal Storytelling Mode", 
                "description": "Reflective, narrative responses that showcase personality",
                "max_tokens": 300
            },
            "fast_facts": {
                "name": "Fast Facts Mode",
                "description": "Quick, scannable information in bullet-point format",
                "max_tokens": 200
            }
        }
    
    def _initialize_llm_clients(self):
        """
        Initialize LLM clients (OpenAI, Anthropic) or fall back to `MockLLMClient`.

        Behavior:
            - If `MOCK_MODE` is set or no API key is available the agent will use
                `MockLLMClient` to avoid external dependencies.
            - When a real API key is present and the corresponding SDK is
                importable, the appropriate client is constructed.
        """
        # Check for mock mode
        mock_mode = os.getenv('MOCK_MODE', 'false').lower() == 'true'
        api_key = os.getenv("OPENAI_API_KEY")
        
        if mock_mode or not api_key or api_key == "your_openai_api_key_here" or api_key == "mock_mode":
            print("🎭 Using mock LLM client for demonstration")
            self.openai_client = MockLLMClient()
            self.anthropic_client = None
            return
        
        if self.llm_provider == "openai":
            if api_key and openai:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    print("Initialized OpenAI client")
                except Exception as e:
                    print(f"Warning: OpenAI client initialization failed: {e}")
                    self.openai_client = MockLLMClient()
                    print("🎭 Falling back to mock LLM client")
            else:
                print("Warning: OpenAI API key not found or client not available")
                self.openai_client = MockLLMClient()
                print("🎭 Using mock LLM client")
        
        elif self.llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key and anthropic:
                try:
                    self.anthropic_client = Anthropic(api_key=api_key)
                    print("Initialized Anthropic client")
                except Exception as e:
                    print(f"Warning: Anthropic client initialization failed: {e}")
                    self.anthropic_client = None
            else:
                print("Warning: Anthropic API key not found or client not available")
        
        if not self.openai_client and not self.anthropic_client:
            print("🎭 No LLM client available - using mock client for demonstration")
            self.openai_client = MockLLMClient()
    
    def load_documents(self, directory_path: str = "data/raw") -> bool:
        """
        Load and process documents from disk, index them in the embeddings system,
        and save a small processed summary to `data/processed/processed_documents.json`.

        Args:
            directory_path (str): Path containing raw documents

        Returns:
            bool: True on success, False on failure

        Example:
            >>> success = agent.load_documents('data/raw')
        """
        try:
            print(f"Loading documents from {directory_path}...")
            
            # Check if directory exists and has files
            if not Path(directory_path).exists():
                print(f"Directory {directory_path} does not exist")
                return False
            
            # Process documents
            processed_docs = self.document_processor.process_directory(directory_path)
            
            if not processed_docs:
                print("No documents found to process")
                return False
            
            print(f"Processed {len(processed_docs)} documents")
            
            # Add to vector database
            self.embeddings_system.add_documents(processed_docs)
            
            # Save processed documents for reference
            self._save_processed_documents(processed_docs)
            
            self.documents_loaded = True
            self.knowledge_base_initialized = True
            
            print("Documents loaded and knowledge base initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
    
    def _save_processed_documents(self, processed_docs: List[Dict[str, Any]]):
        """
        Persist a trimmed JSON summary of processed documents to
        `data/processed/processed_documents.json` for debugging and inspection.

        This method truncates chunk text to keep the saved file small.
        """
        try:
            output_path = Path("data/processed/processed_documents.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for JSON serialization
            serializable_docs = []
            for doc in processed_docs:
                serializable_doc = {
                    'metadata': doc['document']['metadata'],
                    'total_chunks': doc['total_chunks'],
                    'chunks': [
                        {
                            'content': chunk['content'][:500] + "..." if len(chunk['content']) > 500 else chunk['content'],
                            'metadata': chunk['metadata']
                        }
                        for chunk in doc['chunks']
                    ]
                }
                serializable_docs.append(serializable_doc)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_docs, f, indent=2, ensure_ascii=False)
            
            print(f"Saved processed documents summary to {output_path}")
            
        except Exception as e:
            print(f"Warning: Could not save processed documents summary: {e}")
    
    def switch_mode(self, new_mode: str) -> str:
        """
        Switch the conversational mode used to generate responses.

        Args:
            new_mode (str): Mode key (e.g. 'interview', 'personal_storytelling')

        Returns:
            str: Human-readable status message about the switch.
        """
        if new_mode not in self.modes:
            return f"Unknown mode: {new_mode}. Available modes: {', '.join(self.modes.keys())}"
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        mode_info = self.modes[new_mode]
        return f"Switched to {mode_info['name']}: {mode_info['description']}"
    
    def get_available_modes(self) -> Dict[str, Dict[str, str]]:
        """Get information about available modes"""
        return self.modes
    
    def get_current_mode(self) -> str:
        """Get the current interaction mode"""
        return self.current_mode
    
    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the embeddings-backed knowledge base for relevant chunks.

        Args:
            query (str): Natural language search query
            top_k (int): Number of results to return

        Returns:
            List[Dict[str, Any]]: Search results from `EmbeddingsSystem.search`
        """
        if not self.knowledge_base_initialized:
            return []
        
        try:
            results = self.embeddings_system.search(query, top_k)
            return results
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    def generate_response(self, user_question: str, 
                         include_sources: bool = True) -> Dict[str, Any]:
        """
        Generate an answer to the user's question using the RAG pipeline.

        Steps:
            1. Validate that documents are loaded
            2. Search the knowledge base for relevant chunks
            3. Format system and mode prompts via `PromptManager`
            4. Call the configured LLM (OpenAI/Anthropic) or fallback logic
            5. Optionally attach source citations and store conversation history

        Args:
            user_question (str): The user's input question
            include_sources (bool): Attach source filenames to the response

        Returns:
            Dict[str, Any]: Response dictionary with keys: 'response', 'sources',
                'mode', 'confidence'
        """
        
        # Check if we have documents loaded
        if not self.documents_loaded:
            return {
                'response': self.prompt_manager.get_document_upload_prompt(),
                'sources': [],
                'mode': self.current_mode,
                'confidence': 'low'
            }
        
        # Search for relevant context
        search_results = self.search_knowledge_base(user_question)
        
        # Generate response using LLM
        if self.openai_client or self.anthropic_client:
            response = self._generate_llm_response(user_question, search_results)
        else:
            # Fallback response without LLM
            response = self._generate_fallback_response(user_question, search_results)
        
        # Add to conversation history
        self.prompt_manager.add_to_conversation_history(user_question, response['response'])
        
        # Format response with sources if requested
        if include_sources and response.get('sources'):
            response['response'] = self.prompt_manager.format_response_with_sources(
                response['response'], 
                response['sources']
            )
        
        return response
    
    def _generate_llm_response(self, user_question: str, 
                              search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Orchestrate prompt creation and call the configured LLM client.

        This method isolates prompt construction from provider-specific calls
        (`_generate_openai_response` and `_generate_anthropic_response`). If an
        LLM call fails the method falls back to `_generate_fallback_response`.
        """
        
        # Prepare context and prompts
        conversation_context = self.prompt_manager.get_conversation_context()
        relevant_context = self.prompt_manager.format_context(search_results)
        
        system_prompt = self.prompt_manager.get_system_prompt(
            conversation_context, relevant_context
        )
        
        mode_prompt = self.prompt_manager.get_mode_prompt(
            self.current_mode, user_question
        )
        
        # Combine prompts
        full_prompt = f"{system_prompt}\n\n{mode_prompt}"
        
        try:
            if self.openai_client:
                return self._generate_openai_response(full_prompt, user_question, search_results)
            elif self.anthropic_client:
                return self._generate_anthropic_response(full_prompt, user_question, search_results)
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_fallback_response(user_question, search_results)
    
    def _generate_openai_response(self, full_prompt: str, user_question: str,
                                 search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make an OpenAI chat completion call and package the result.

        Notes:
            - The code expects `self.openai_client` to be a client object with
              `chat.completions.create(...)` semantics (the OpenAI SDK wrapper
              used in this repo).
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=self.modes[self.current_mode]["max_tokens"],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            return {
                'response': response_text,
                'sources': [result.get('metadata', {}).get('filename', 'Unknown') 
                           for result in search_results],
                'mode': self.current_mode,
                'confidence': 'high' if search_results else 'medium'
            }
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(user_question, search_results)
    
    def _generate_anthropic_response(self, full_prompt: str, user_question: str,
                                    search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a request to Anthropic Claude and return a standardized response
        dict.
        """
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=self.modes[self.current_mode]["max_tokens"],
                messages=[
                    {"role": "user", "content": f"{full_prompt}\n\nQuestion: {user_question}"}
                ]
            )
            
            response_text = response.content[0].text
            
            return {
                'response': response_text,
                'sources': [result.get('metadata', {}).get('filename', 'Unknown') 
                           for result in search_results],
                'mode': self.current_mode,
                'confidence': 'high' if search_results else 'medium'
            }
            
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return self._generate_fallback_response(user_question, search_results)
    
    def _generate_fallback_response(self, user_question: str,
                                   search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Produce a lightweight fallback response when no LLM client is
        available. The method uses simple templates per mode and provides
        basic source attribution when search results are available.
        """
        
        if not search_results:
            return {
                'response': "I don't have enough information to answer that question accurately. Please ask me something more specific about my documented experience.",
                'sources': [],
                'mode': self.current_mode,
                'confidence': 'low'
            }
        
        # Simple template-based response
        mode_templates = {
            "interview": "Based on my experience, I can tell you that {context}. This demonstrates my {skill} and {achievement}.",
            "personal_storytelling": "From my personal experience, I remember {context}. This taught me {lesson} and shaped my approach to {topic}.",
            "fast_facts": "Key points about this:\n• {context}\n• {skill}\n• {achievement}"
        }
        
        # Extract key information from search results
        context = search_results[0].get('content', '')[:100] + "..."
        skill = "relevant skills"
        achievement = "professional achievements"
        
        template = mode_templates.get(self.current_mode, mode_templates["interview"])
        response_text = template.format(context=context, skill=skill, achievement=achievement)
        
        return {
            'response': response_text,
            'sources': [result.get('metadata', {}).get('filename', 'Unknown') 
                       for result in search_results],
            'mode': self.current_mode,
            'confidence': 'medium'
        }
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """
        Return a small metadata dictionary describing the knowledge base
        currently loaded in the embeddings system.
        """
        return self.embeddings_system.get_database_info()
    
    def save_knowledge_base(self, file_path: str = "data/processed/knowledge_base"):
        """
        Save the knowledge base to disk.
        """
        try:
            self.embeddings_system.save_database(file_path)
            print(f"Knowledge base saved to {file_path}")
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def load_knowledge_base(self, file_path: str = "data/processed/knowledge_base"):
        """
        Load the knowledge base from disk.
        """
        try:
            self.embeddings_system.load_database(file_path)
            self.knowledge_base_initialized = True
            print(f"Knowledge base loaded from {file_path}")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation.
        """
        return {
            'total_turns': len(self.conversation_history),
            'current_mode': self.current_mode,
            'documents_loaded': self.documents_loaded,
            'knowledge_base_initialized': self.knowledge_base_initialized,
            'recent_topics': [turn['user'][:50] + "..." for turn in self.conversation_history[-3:]]
        }
