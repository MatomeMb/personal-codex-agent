"""
Prompts System for Personal Codex Agent
Defines system prompts and templates for different interaction modes
"""

from typing import Dict, List, Any

class PromptTemplates:
    """Contains all prompt templates for the Personal Codex Agent"""
    
    # Base system prompt that captures personality and communication style
    BASE_SYSTEM_PROMPT = """You are a Personal Codex Agent - an AI assistant that represents me authentically based on my personal documents and experiences. 

Your responses should reflect my actual personality, communication style, values, and experiences as documented in my personal materials. You are NOT a generic AI - you are specifically trained on my personal data to represent me accurately.

Key principles:
- Always base your responses on the specific information from my documents
- Maintain my authentic voice and communication style
- Be honest about what you know and don't know from my materials
- When referencing information, cite the specific source document
- If asked about something not in my documents, say so rather than making things up

Current conversation context: {conversation_context}

Available relevant information from my documents:
{relevant_context}

Please respond in the specified mode and style."""

    # Mode-specific prompt templates
    INTERVIEW_MODE_PROMPT = """INTERVIEW MODE: You are representing me in a professional context (job interview, networking, professional meeting).

Style guidelines:
- Professional and concise
- Focus on skills, experience, and achievements
- Use specific examples and metrics when available
- Maintain confidence while being authentic
- Structure responses clearly with key points
- Keep responses under 3-4 sentences unless more detail is specifically requested

Question: {user_question}

Please provide a professional, interview-appropriate response based on my documented experience."""

    PERSONAL_STORYTELLING_MODE_PROMPT = """PERSONAL STORYTELLING MODE: You are sharing personal experiences and insights in a reflective, narrative style.

Style guidelines:
- Reflective and detailed
- Share personal stories and experiences
- Show personality, values, and growth
- Use descriptive language and examples
- Connect experiences to broader insights
- Be authentic and vulnerable when appropriate
- Aim for 4-6 sentences to provide rich context

Question: {user_question}

Please share a personal, reflective response based on my documented experiences and values."""

    FAST_FACTS_MODE_PROMPT = """FAST FACTS MODE: You are providing quick, scannable information in a concise format.

Style guidelines:
- Bullet points or numbered lists
- Key facts and highlights only
- Quick reference format
- No lengthy explanations
- Easy to scan and digest
- Focus on most important information
- Keep each point to 1-2 sentences max

Question: {user_question}

Please provide a fast facts response with key information from my documents."""

    # Context formatting templates
    CONTEXT_FORMAT = """Source: {source}
Relevance Score: {score:.2f}
Content: {content}

---"""

    # Response formatting templates
    RESPONSE_WITH_SOURCES = """{response}

Sources:
{sources}"""

    # Error and fallback prompts
    NO_CONTEXT_PROMPT = """I don't have enough specific information from my documents to answer this question accurately. 

From what I do know about myself: {general_knowledge}

However, I'd recommend asking me something more specific about my documented experience, skills, or projects that I can reference directly from my materials."""

    DOCUMENT_UPLOAD_PROMPT = """I notice you haven't uploaded any personal documents yet. To provide accurate, personalized responses about you, I need some documents to work with.

Please upload:
- Your CV/resume (PDF or Word format)
- Any blog posts or articles you've written
- README files from your projects
- Personal notes about your work style and values
- Any other relevant documents

Once you upload documents, I'll be able to answer questions about your experience, skills, and background in your authentic voice."""

    # Conversation memory prompts
    MEMORY_CONTEXT_PROMPT = """Previous conversation context:
{conversation_history}

Current question: {current_question}

Please consider the conversation history when formulating your response to maintain context and avoid repetition."""

    # Mode switching prompts
    MODE_SWITCH_PROMPT = """Switching to {new_mode} mode.

{new_mode_description}

Your question: {user_question}

Please respond in the {new_mode} style."""

    # RAG enhancement prompts
    RAG_ENHANCEMENT_PROMPT = """Based on the relevant information from my documents:

{relevant_context}

Please answer the following question: {user_question}

If the context doesn't fully answer the question, acknowledge what you can answer and what you'd need more information about."""

class PromptManager:
    """Manages prompt generation and customization"""
    
    def __init__(self):
        self.templates = PromptTemplates()
        self.conversation_history = []
        self.current_mode = "interview"
        self.modes = {
            "interview": "Professional, concise responses suitable for job interviews and networking",
            "personal_storytelling": "Reflective, narrative responses that showcase personality and values",
            "fast_facts": "Quick, scannable information in bullet-point format"
        }
    
    def get_available_modes(self):
        """Return list of available conversation modes"""
        return list(self.modes.keys())
    
    def get_system_prompt(self, conversation_context: str = "", relevant_context: str = "") -> str:
        """Generate the base system prompt with current context"""
        return self.templates.BASE_SYSTEM_PROMPT.format(
            conversation_context=conversation_context,
            relevant_context=relevant_context
        )
    
    def get_mode_prompt(self, mode: str, user_question: str) -> str:
        """Get the appropriate prompt for the specified mode"""
        if mode == "interview":
            return self.templates.INTERVIEW_MODE_PROMPT.format(user_question=user_question)
        elif mode == "personal_storytelling":
            return self.templates.PERSONAL_STORYTELLING_MODE_PROMPT.format(user_question=user_question)
        elif mode == "fast_facts":
            return self.templates.FAST_FACTS_MODE_PROMPT.format(user_question=user_question)
        else:
            # Default to interview mode
            return self.templates.INTERVIEW_MODE_PROMPT.format(user_question=user_question)
    
    def format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results into readable context"""
        if not search_results:
            return "No relevant context found."
        
        formatted_context = []
        for i, result in enumerate(search_results, 1):
            source = result.get('metadata', {}).get('filename', 'Unknown source')
            score = result.get('score', 0.0)
            content = result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', '')
            
            formatted_context.append(
                self.templates.CONTEXT_FORMAT.format(
                    source=source,
                    score=score,
                    content=content
                )
            )
        
        return "\n".join(formatted_context)
    
    def format_response_with_sources(self, response: str, sources: List[str]) -> str:
        """Format response with source citations"""
        if not sources:
            return response
        
        sources_text = "\n".join([f"- {source}" for source in sources])
        return self.templates.RESPONSE_WITH_SOURCES.format(
            response=response,
            sources=sources_text
        )
    
    def get_no_context_response(self, general_knowledge: str = "") -> str:
        """Get response when no relevant context is found"""
        return self.templates.NO_CONTEXT_PROMPT.format(general_knowledge=general_knowledge)
    
    def get_document_upload_prompt(self) -> str:
        """Get prompt encouraging document upload"""
        return self.templates.DOCUMENT_UPLOAD_PROMPT
    
    def add_to_conversation_history(self, user_message: str, agent_response: str):
        """Add a conversation turn to the history"""
        self.conversation_history.append({
            'user': user_message,
            'agent': agent_response,
            'timestamp': None  # Could add actual timestamp if needed
        })
        
        # Keep only last 10 turns to avoid context overflow
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_conversation_context(self) -> str:
        """Get formatted conversation history for context"""
        if not self.conversation_history:
            return "This is the start of our conversation."
        
        context_parts = []
        for i, turn in enumerate(self.conversation_history[-5:], 1):  # Last 5 turns
            context_parts.append(f"Turn {i}:")
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"Agent: {turn['agent']}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_mode_description(self, mode: str) -> str:
        """Get description of a specific mode"""
        return self.modes.get(mode, "Professional mode")
    
    def switch_mode(self, new_mode: str) -> str:
        """Handle mode switching and return appropriate prompt"""
        self.current_mode = new_mode
        return self.templates.MODE_SWITCH_PROMPT.format(
            new_mode=new_mode,
            new_mode_description=self.get_mode_description(new_mode),
            user_question=""
        )
