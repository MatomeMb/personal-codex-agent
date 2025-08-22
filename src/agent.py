"""
Core Agent Logic for Personal Codex Agent
Manages conversation flow, mode switching, and response generation
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
    """Main agent class that orchestrates the Personal Codex system"""
    
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
        """Initialize LLM API clients based on provider"""
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
        """Load and process documents from the specified directory"""
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
        """Save processed documents to disk for reference"""
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
        """Switch to a different interaction mode"""
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
        """Search the knowledge base for relevant information"""
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
        """Generate a response to the user's question"""
        
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
        """Generate response using the configured LLM"""
        
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
        """Generate response using OpenAI"""
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
        """Generate response using Anthropic Claude"""
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
        """Generate a fallback response when LLM is not available"""
        
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
        """Get information about the current knowledge base"""
        return self.embeddings_system.get_database_info()
    
    def save_knowledge_base(self, file_path: str = "data/processed/knowledge_base"):
        """Save the knowledge base to disk"""
        try:
            self.embeddings_system.save_database(file_path)
            print(f"Knowledge base saved to {file_path}")
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def load_knowledge_base(self, file_path: str = "data/processed/knowledge_base"):
        """Load the knowledge base from disk"""
        try:
            self.embeddings_system.load_database(file_path)
            self.knowledge_base_initialized = True
            print(f"Knowledge base loaded from {file_path}")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            'total_turns': len(self.conversation_history),
            'current_mode': self.current_mode,
            'documents_loaded': self.documents_loaded,
            'knowledge_base_initialized': self.knowledge_base_initialized,
            'recent_topics': [turn['user'][:50] + "..." for turn in self.conversation_history[-3:]]
        }
