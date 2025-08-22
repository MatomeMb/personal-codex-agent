"""
Mock LLM Client for Personal Codex Agent
Provides realistic responses for testing and demonstration without API keys
"""

class MockLLMClient:
    """Mock LLM client for testing without API keys"""
    
    def __init__(self):
        self.mock_responses = {
            "interview": {
                "technical_skills": "Based on the documents provided, I'm a full-stack developer with strong expertise in Python, JavaScript, and modern web frameworks. My experience spans backend development with Django/Flask, frontend work with React, and cloud deployment on AWS. I'm particularly skilled at building scalable APIs and have a solid foundation in database design and optimization.",
                
                "engineer_type": "I'm a software engineer who thrives at the intersection of problem-solving and user experience. I enjoy building robust, scalable systems while keeping the end-user in mind. My approach combines technical depth with practical application - I love diving deep into algorithms and architecture, but always with a focus on delivering real value.",
                
                "projects_proud": "I'm most proud of a real-time collaboration platform I built that handled 10,000+ concurrent users. The technical challenges included implementing WebSocket architecture, optimizing database queries for sub-100ms response times, and designing a conflict resolution system for simultaneous edits. What made it special was seeing teams actually improve their productivity using something I created."
            },
            
            "personal_storytelling": {
                "learning_approach": "My learning style is very hands-on and project-driven. When I encounter something new, I start by building a small prototype to understand the core concepts. For example, when learning React, I didn't just read documentation - I rebuilt a familiar interface from scratch. I find that debugging my own mistakes teaches me more than following tutorials perfectly. I also believe in the power of teaching others - explaining concepts to teammates often reveals gaps in my own understanding.",
                
                "team_culture": "I thrive in environments that balance autonomy with collaboration. I love having the freedom to dive deep into problems and explore creative solutions, but I also value regular check-ins and knowledge sharing. The best teams I've worked with had a culture of curiosity - where asking 'why' and 'what if' was encouraged, not seen as challenging authority. I appreciate when technical decisions are made transparently and everyone's input is valued regardless of seniority.",
                
                "debugging_approach": "My debugging philosophy is methodical but creative. I start by reproducing the issue consistently, then work backwards from the symptom to the root cause. I love using print statements and logs strategically - not randomly. When stuck, I often explain the problem out loud to a rubber duck (or patient colleague). Sometimes the breakthrough comes from taking a walk and thinking about the problem differently. I've learned that the most elegant fixes often involve understanding the 'why' behind the bug, not just the 'how' to patch it."
            },
            
            "fast_facts": {
                "skills_summary": "• Languages: Python, JavaScript, TypeScript, SQL\n• Frameworks: React, Django, Flask, Node.js\n• Cloud: AWS (EC2, S3, RDS, Lambda)\n• Databases: PostgreSQL, Redis, MongoDB\n• Tools: Docker, Git, GitHub Actions, Pytest\n• Specialties: API design, real-time systems, performance optimization",
                
                "experience_overview": "• 3+ years full-stack development\n• Led 2 major product launches\n• Built systems handling 10K+ concurrent users\n• Reduced API response times by 60%\n• Mentored 3 junior developers\n• Open source contributor (5 repos, 200+ stars)",
                
                "values_quick": "• Code quality over speed\n• User experience drives technical decisions\n• Continuous learning and knowledge sharing\n• Transparent communication\n• Data-driven decision making\n• Work-life balance and sustainable pace"
            }
        }
    
    def generate_response(self, prompt, mode="interview", context=""):
        """Generate a mock response based on mode and prompt content"""
        
        prompt_lower = prompt.lower()
        mode_responses = self.mock_responses.get(mode, self.mock_responses["interview"])
        
        if any(word in prompt_lower for word in ["skill", "technical", "technology", "programming"]):
            if mode == "fast_facts":
                return mode_responses.get("skills_summary", "Technical skills include Python, JavaScript, and cloud platforms.")
            else:
                return mode_responses.get("technical_skills", "I have strong technical skills in full-stack development.")
        
        elif any(word in prompt_lower for word in ["engineer", "developer", "what kind"]):
            return mode_responses.get("engineer_type", "I'm a software engineer focused on building scalable solutions.")
        
        elif any(word in prompt_lower for word in ["project", "proud", "experience"]):
            if mode == "fast_facts":
                return mode_responses.get("experience_overview", "• 3+ years experience\n• Multiple successful projects")
            else:
                return mode_responses.get("projects_proud", "I'm proud of several projects that solved real user problems.")
        
        elif any(word in prompt_lower for word in ["learn", "debug", "approach"]):
            return mode_responses.get("learning_approach", "I learn by building and debugging real projects.")
        
        elif any(word in prompt_lower for word in ["team", "culture", "collaborate"]):
            if mode == "fast_facts":
                return mode_responses.get("values_quick", "• Collaboration\n• Quality code\n• Continuous learning")
            else:
                return mode_responses.get("team_culture", "I value collaborative environments with clear communication.")
        
        else:
            # Default response based on mode
            if mode == "interview":
                return "I'm a passionate software engineer with experience in full-stack development, focusing on building scalable and user-friendly applications."
            elif mode == "personal_storytelling":
                return "Let me tell you about my journey as a developer. I started coding because I loved the idea of building things that could help people solve real problems..."
            elif mode == "fast_facts":
                return "• Software Engineer\n• Full-stack development\n• 3+ years experience\n• Focus on scalable systems"

    def chat_completion(self, messages, model="gpt-3.5-turbo", **kwargs):
        """Mock the OpenAI chat completion interface"""
        
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        mode = "interview"
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "").lower()
                if "storytelling" in content:
                    mode = "personal_storytelling"
                elif "fast facts" in content or "bullet" in content:
                    mode = "fast_facts"
                break
        
        response_content = self.generate_response(user_message, mode)
        
        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
                self.usage = {"total_tokens": len(content.split())}
        
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.role = "assistant"
        
        return MockResponse(response_content)
