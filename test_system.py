#!/usr/bin/env python3
"""
Test Script for Personal Codex Agent
Simple test to verify system components are working correctly
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from src.document_processor import DocumentProcessor
        print("✅ DocumentProcessor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DocumentProcessor: {e}")
        return False
    
    try:
        from src.embeddings import EmbeddingsSystem
        print("✅ EmbeddingsSystem imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import EmbeddingsSystem: {e}")
        return False
    
    try:
        from src.prompts import PromptManager
        print("✅ PromptManager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PromptManager: {e}")
        return False
    
    try:
        from src.agent import PersonalCodexAgent
        print("✅ PersonalCodexAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PersonalCodexAgent: {e}")
        return False
    
    return True

def test_document_processor():
    """Test document processor functionality"""
    print("\n📄 Testing DocumentProcessor...")
    
    try:
        from src.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        print("✅ DocumentProcessor initialized successfully")
        
        # Test chunking
        test_text = "This is a test document. " * 50  # Create long text
        chunks = processor.chunk_text(test_text, chunk_size=100, chunk_overlap=20)
        print(f"✅ Text chunking works: {len(chunks)} chunks created")
        
        return True
    except Exception as e:
        print(f"❌ DocumentProcessor test failed: {e}")
        return False

def test_prompt_manager():
    """Test prompt manager functionality"""
    print("\n💬 Testing PromptManager...")
    
    try:
        from src.prompts import PromptManager
        pm = PromptManager()
        print("✅ PromptManager initialized successfully")
        
        # Test mode switching
        modes = pm.get_available_modes()
        print(f"✅ Available modes: {modes}")
        
        # Test prompt generation
        system_prompt = pm.get_system_prompt()
        print(f"✅ System prompt generated: {len(system_prompt)} characters")
        
        return True
    except Exception as e:
        print(f"❌ PromptManager test failed: {e}")
        return False

def test_embeddings_system():
    """Test embeddings system functionality"""
    print("\n🔍 Testing EmbeddingsSystem...")
    
    try:
        from src.embeddings import EmbeddingsSystem
        # Test with FAISS (should work without external dependencies)
        embeddings = EmbeddingsSystem(vector_db_type="faiss")
        print("✅ EmbeddingsSystem initialized successfully")
        
        # Get database info
        info = embeddings.get_database_info()
        print(f"✅ Database info: {info}")
        
        return True
    except Exception as e:
        print(f"❌ EmbeddingsSystem test failed: {e}")
        return False

def test_agent():
    """Test agent functionality"""
    print("\n🤖 Testing PersonalCodexAgent...")
    
    try:
        from src.agent import PersonalCodexAgent
        # Test agent creation (without LLM clients)
        agent = PersonalCodexAgent(llm_provider="none")
        print("✅ PersonalCodexAgent initialized successfully")
        
        # Test mode switching
        modes = agent.get_available_modes()
        print(f"✅ Available modes: {list(modes.keys())}")
        
        # Test conversation summary
        summary = agent.get_conversation_summary()
        print(f"✅ Conversation summary: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ PersonalCodexAgent test failed: {e}")
        return False

def test_streamlit_app():
    """Test Streamlit app import"""
    print("\n🌐 Testing Streamlit app...")
    
    try:
        # Try to import the main app
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Check if app.py can be imported
        try:
            import app
            print("✅ Main app module imported successfully")
        except ImportError:
            print("⚠️ Main app module import failed (this is normal if not running in Streamlit)")
        
        return True
    except ImportError:
        print("❌ Streamlit not available - install with: pip install streamlit")
        return False

def main():
    """Run all tests"""
    print("🚀 Personal Codex Agent - System Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Document Processor", test_document_processor),
        ("Prompt Manager", test_prompt_manager),
        ("Embeddings System", test_embeddings_system),
        ("Agent", test_agent),
        ("Streamlit App", test_streamlit_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Set up your API keys in a .env file")
        print("2. Run: streamlit run app.py")
        print("3. Upload your documents and start chatting!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check Python version (3.8+ required)")
        print("3. Verify file permissions and paths")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
