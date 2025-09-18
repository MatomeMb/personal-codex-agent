"""
Tests for Mock LLM Client module
"""

import pytest
import sys
sys.path.append('.')

from src.mock_llm import MockLLMClient

class TestMockLLMClient:
    """Test suite for MockLLMClient class"""
    
    def test_mock_client_initialization(self):
        """Test mock client initialization"""
        client = MockLLMClient()
        assert client is not None
        assert hasattr(client, 'mock_responses')
        assert hasattr(client, 'generate_response')
        assert hasattr(client, 'chat_completion')
    
    def test_mock_responses_structure(self):
        """Test that mock responses have expected structure"""
        client = MockLLMClient()
        
        # Check that all modes are present
        assert 'interview' in client.mock_responses
        assert 'personal_storytelling' in client.mock_responses
        assert 'fast_facts' in client.mock_responses
        
        # Check that each mode has expected response types
        for mode in client.mock_responses:
            mode_responses = client.mock_responses[mode]
            assert isinstance(mode_responses, dict)
            assert len(mode_responses) > 0
    
    def test_generate_response_technical_skills(self):
        """Test response generation for technical skills questions"""
        client = MockLLMClient()
        
        # Test interview mode
        response = client.generate_response("What are your technical skills?", "interview")
        assert "technical" in response.lower() or "skills" in response.lower()
        assert len(response) > 10
        
        # Test fast facts mode
        response = client.generate_response("What are your technical skills?", "fast_facts")
        assert "•" in response or "Languages:" in response
        assert len(response) > 10
    
    def test_generate_response_engineer_type(self):
        """Test response generation for engineer type questions"""
        client = MockLLMClient()
        
        response = client.generate_response("What kind of engineer are you?", "interview")
        assert "engineer" in response.lower()
        assert len(response) > 10
    
    def test_generate_response_projects(self):
        """Test response generation for project questions"""
        client = MockLLMClient()
        
        # Test interview mode
        response = client.generate_response("What projects are you proud of?", "interview")
        assert "project" in response.lower() or "built" in response.lower()
        assert len(response) > 10
        
        # Test fast facts mode
        response = client.generate_response("What projects are you proud of?", "fast_facts")
        assert "•" in response or "experience" in response.lower()
        assert len(response) > 10
    
    def test_generate_response_learning(self):
        """Test response generation for learning questions"""
        client = MockLLMClient()
        
        response = client.generate_response("How do you learn new things?", "personal_storytelling")
        assert "learn" in response.lower() or "approach" in response.lower()
        assert len(response) > 10
    
    def test_generate_response_team_culture(self):
        """Test response generation for team culture questions"""
        client = MockLLMClient()
        
        # Test personal storytelling mode
        response = client.generate_response("What do you value in team culture?", "personal_storytelling")
        assert "team" in response.lower() or "culture" in response.lower()
        assert len(response) > 10
        
        # Test fast facts mode
        response = client.generate_response("What do you value in team culture?", "fast_facts")
        assert "•" in response or "collaboration" in response.lower()
        assert len(response) > 10
    
    def test_generate_response_default(self):
        """Test default response generation for unrecognized queries"""
        client = MockLLMClient()
        
        # Test interview mode default
        response = client.generate_response("Random question", "interview")
        assert "software engineer" in response.lower() or "development" in response.lower()
        assert len(response) > 10
        
        # Test personal storytelling mode default
        response = client.generate_response("Random question", "personal_storytelling")
        assert "developer" in response.lower() or "journey" in response.lower()
        assert len(response) > 10
        
        # Test fast facts mode default
        response = client.generate_response("Random question", "fast_facts")
        assert "•" in response or "engineer" in response.lower()
        assert len(response) > 10
    
    def test_chat_completion_interface(self):
        """Test OpenAI chat completion interface"""
        client = MockLLMClient()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What are your skills?"}
        ]
        
        response = client.chat_completion(messages)
        
        # Check response structure
        assert hasattr(response, 'choices')
        assert hasattr(response, 'usage')
        assert len(response.choices) == 1
        assert hasattr(response.choices[0], 'message')
        assert hasattr(response.choices[0].message, 'content')
        assert hasattr(response.choices[0].message, 'role')
        
        # Check content
        assert len(response.choices[0].message.content) > 0
        assert response.choices[0].message.role == "assistant"
    
    def test_chat_completion_mode_detection(self):
        """Test mode detection from system messages"""
        client = MockLLMClient()
        
        # Test storytelling mode detection
        messages = [
            {"role": "system", "content": "You are in personal storytelling mode."},
            {"role": "user", "content": "Tell me about yourself"}
        ]
        
        response = client.chat_completion(messages)
        content = response.choices[0].message.content
        
        # Should contain storytelling-style content
        assert len(content) > 10
    
    def test_chat_completion_fast_facts_detection(self):
        """Test fast facts mode detection from system messages"""
        client = MockLLMClient()
        
        messages = [
            {"role": "system", "content": "You are in fast facts mode with bullet points."},
            {"role": "user", "content": "What are your skills?"}
        ]
        
        response = client.chat_completion(messages)
        content = response.choices[0].message.content
        
        # Should contain bullet points or structured format
        assert "•" in content or "Languages:" in content
    
    def test_chat_completion_no_user_message(self):
        """Test chat completion with no user message"""
        client = MockLLMClient()
        
        messages = [
            {"role": "system", "content": "System message only"}
        ]
        
        response = client.chat_completion(messages)
        
        # Should still return a response
        assert hasattr(response, 'choices')
        assert len(response.choices) == 1
        assert len(response.choices[0].message.content) > 0
    
    def test_response_consistency(self):
        """Test that responses are consistent for similar queries"""
        client = MockLLMClient()
        
        # Same query should return similar response structure
        response1 = client.generate_response("What are your skills?", "interview")
        response2 = client.generate_response("What are your technical skills?", "interview")
        
        # Both should be substantial responses
        assert len(response1) > 10
        assert len(response2) > 10
        
        # Both should contain skill-related content
        assert any(word in response1.lower() for word in ["skill", "technical", "development"])
        assert any(word in response2.lower() for word in ["skill", "technical", "development"])
    
    def test_all_modes_have_responses(self):
        """Test that all conversation modes have appropriate responses"""
        client = MockLLMClient()
        
        test_queries = [
            "What are your skills?",
            "Tell me about your projects",
            "How do you work in teams?",
            "What do you value?",
            "Random question"
        ]
        
        for mode in ["interview", "personal_storytelling", "fast_facts"]:
            for query in test_queries:
                response = client.generate_response(query, mode)
                assert len(response) > 10
                assert isinstance(response, str)

if __name__ == "__main__":
    pytest.main([__file__])
