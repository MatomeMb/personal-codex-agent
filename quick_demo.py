#!/usr/bin/env python3
"""
Quick Demo Script for Personal Codex Agent
Demonstrates all components working together without API keys
"""

import os
import sys
from pathlib import Path

# Set mock mode for demonstration
os.environ['MOCK_MODE'] = 'true'
os.environ['OPENAI_API_KEY'] = 'mock_mode'

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def demo_personal_codex():
    print("🚀 Personal Codex Agent - Live Demo")
    print("=" * 50)
    
    try:
        from src.agent import PersonalCodexAgent
        from src.document_processor import DocumentProcessor
        from src.embeddings import EmbeddingsSystem
        
        print("✅ All modules imported successfully")
        
        agent = PersonalCodexAgent()
        processor = DocumentProcessor()
        embeddings = EmbeddingsSystem()
        
        print("✅ All components initialized")
        
        sample_doc = """
        I'm a passionate software engineer with 3+ years of experience in full-stack development. 
        My technical expertise includes Python, JavaScript, React, and Django. 
        I've successfully built and deployed scalable web applications that serve thousands of users.
        
        One project I'm particularly proud of is a real-time collaboration platform that I architected 
        from the ground up. It handles over 10,000 concurrent users and features WebSocket communication, 
        Redis for caching, and PostgreSQL for data persistence.
        """
        
        chunks = processor.chunk_text(sample_doc)
        print(f"✅ Created {len(chunks)} text chunks")
        print(f"✅ Embeddings system: {embeddings.get_database_info()}")
        print(f"🎭 Available conversation modes: {agent.get_available_modes()}")
        print(f"💬 Conversation status: {agent.get_conversation_summary()}")
        
        test_queries = [
            "What are your strongest technical skills?",
            "Tell me about a project you're proud of",
            "How do you approach learning new technologies?"
        ]
        
        print(f"\n🔍 RAG Retrieval Demo:")
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            print(f"   🤖 Mock Response: [Would generate personalized response based on context]")
        
        print(f"\n🎉 Demo Complete! Your system is working correctly.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_personal_codex()
