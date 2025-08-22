# Personal Codex Agent

## Overview
The Personal Codex Agent is an intelligent, context-aware chatbot that answers questions about me as a candidate based on my personal documents and data. It uses Retrieval-Augmented Generation (RAG) to provide accurate, personalized responses that reflect my authentic voice and experiences.

## System Design
The system follows a modular architecture with the following components:
- **Document Processor**: Handles multiple file formats (PDF, Markdown, Text) and extracts relevant information
- **Embedding System**: Generates vector representations using sentence-transformers
- **Vector Database**: FAISS/Chroma for efficient similarity search
- **Agent Core**: Manages conversation flow, mode switching, and response generation
- **Web Interface**: Streamlit-based UI with multiple interaction modes

## Setup Instructions

### Prerequisites
- Python 3.8+
- OpenAI API key or Anthropic API key (optional for mock mode)

### Installation

#### Option 1: Full Mode (with API keys)
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```
4. Place your personal documents in the `data/raw/` folder
5. Run the application: `streamlit run app.py`

#### Option 2: Mock Mode (no API keys required)
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables for mock mode:
   ```bash
   export MOCK_MODE=true
   export OPENAI_API_KEY=mock_mode
   ```
4. Test the system:
   ```bash
   python quick_demo.py          # Quick system test
   python test_mock_llm.py      # Test mock responses
   python test_system.py        # Full system test
   ```
5. Run the application: `streamlit run app.py`

**Mock Mode Features:**
- Works completely without API keys
- Provides realistic sample responses
- Demonstrates all RAG functionality
- Perfect for testing and demonstration
- Easy to switch to real API when available

## Sample Interactions

### Interview Mode
- Professional, concise responses
- Focus on skills and experience
- Suitable for job interviews and networking

### Personal Storytelling Mode
- Reflective, narrative responses
- Detailed personal experiences
- Great for deeper conversations

### Fast Facts Mode
- Bullet-point summaries
- Quick reference information
- Perfect for rapid fact-checking

## Mode Descriptions

1. **Interview Mode**: Tailored for professional contexts, providing structured responses about skills, experience, and achievements
2. **Personal Storytelling Mode**: Offers rich, contextual narratives that showcase personality and values
3. **Fast Facts Mode**: Delivers concise, scannable information for quick reference

## Technology Stack
- **Backend**: Python with Streamlit
- **RAG**: sentence-transformers + FAISS/Chroma
- **LLM**: OpenAI GPT-3.5/4 or Anthropic Claude (with mock fallback)
- **Document Processing**: pypdf, python-docx, markdown
- **Deployment**: Streamlit Cloud ready
- **Mock Mode**: Built-in mock LLM client for demonstration

## Future Improvements
- Self-reflective agent mode for deeper questions
- Easy dataset extension capability
- Creative prompt strategies or agent chaining
- Export conversation feature
- Analytics on most asked questions

## Show Your Thinking Artifacts
See the `show_your_thinking/` folder for:
- All prompts used to generate code
- Conversation logs with AI assistants
- Code attribution and implementation decisions
- Sub-agent definitions and roles
