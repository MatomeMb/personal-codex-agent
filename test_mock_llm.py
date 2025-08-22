#!/usr/bin/env python3
"""
Test Mock LLM Client
Simple test to verify mock responses work correctly
"""

import os
import sys
from pathlib import Path

# Set mock mode for testing
os.environ['MOCK_MODE'] = 'true'
os.environ['OPENAI_API_KEY'] = 'mock_mode'

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_mock_llm():
    """Test the mock LLM client"""
    print("🧪 Testing Mock LLM Client")
    print("=" * 40)
    
    try:
        from src.mock_llm import MockLLMClient
        
        # Create mock client
        mock_client = MockLLMClient()
        print("✅ Mock LLM client created successfully")
        
        # Test different modes and queries
        test_cases = [
            ("interview", "What are your technical skills?"),
            ("personal_storytelling", "How do you learn new things?"),
            ("fast_facts", "What projects are you proud of?"),
            ("interview", "What kind of engineer are you?"),
        ]
        
        print("\n🔍 Testing Mock Responses:")
        for mode, query in test_cases:
            print(f"\nMode: {mode}")
            print(f"Query: {query}")
            response = mock_client.generate_response(query, mode)
            print(f"Response: {response[:100]}...")
        
        # Test OpenAI interface compatibility
        print("\n🔍 Testing OpenAI Interface Compatibility:")
        messages = [
            {"role": "system", "content": "You are in interview mode"},
            {"role": "user", "content": "What are your strongest skills?"}
        ]
        
        mock_response = mock_client.chat_completion(messages)
        print(f"✅ Chat completion response: {mock_response.choices[0].message.content[:100]}...")
        print(f"✅ Usage info: {mock_response.usage}")
        
        print("\n🎉 Mock LLM client test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mock_llm()
