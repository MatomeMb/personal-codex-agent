# Personal Codex Agent

A context-aware AI chatbot that represents you authentically based on your personal documents and experiences.

## Features

- **Document Processing**: Handles PDF, Markdown, Word, and text files
- **RAG Implementation**: Uses embeddings and vector search for relevant context
- **Multiple Interaction Modes**: Interview, Personal Storytelling, and Fast Facts
- **Conversation Memory**: Maintains context across chat sessions
- **Source Citations**: References specific documents in responses

## Architecture

The system consists of several key components:

### Core Components
- **DocumentProcessor**: Handles file loading and text chunking
- **EmbeddingsSystem**: Generates and searches vector embeddings
- **PromptManager**: Manages conversation modes and prompt generation
- **PersonalCodexAgent**: Orchestrates the entire system

### Technology Stack
- **Backend**: Python with Streamlit
- **Embeddings**: Sentence Transformers
- **Vector Database**: FAISS or ChromaDB
- **LLM Integration**: OpenAI GPT or Anthropic Claude (with mock fallback)

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

3. **Run the Application**
   ```bash
   streamlit run app.py
   ```

4. **Upload Documents**
   - CV/Resume
   - Blog posts
   - Project READMEs
   - Personal notes

5. **Start Chatting**
   - Choose your interaction mode
   - Ask questions about your experience
   - Get personalized responses

## Mock Mode

For demonstration purposes, the system includes a mock LLM client that works without API keys:

```bash
# Set environment variables
export MOCK_MODE=true
export OPENAI_API_KEY=mock_mode

# Run demo
python quick_demo.py
```

## Development

- **Testing**: Run `python test_system.py` to verify all components
- **Documentation**: See `show_your_thinking/` for development details
- **Deployment**: Use `deployment_guide.md` for production setup

## License

MIT License - see LICENSE file for details.
