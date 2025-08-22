# Personal Codex Agent

## Overview
The Personal Codex Agent is an intelligent, context-aware chatbot that answers questions about me as a candidate based on my personal documents and data. It uses Retrieval-Augmented Generation (RAG) to provide accurate, personalized responses that reflect my authentic voice and experiences.

## System Design
The system follows a modular architecture with the following components:
- **Document Processor**: Handles multiple file formats (PDF, Markdown, Text) and extracts relevant information
- **Embedding System**: Generates vector representations using sentence-transformers
- **Vector Database**: FAISS for efficient similarity search (ChromaDB support removed for Streamlit Cloud compatibility)
- **Agent Core**: Manages conversation flow, mode switching, and response generation with mock mode support
- **Web Interface**: Streamlit-based UI with multiple interaction modes

## Setup Instructions

### Prerequisites
- Python 3.8+ (tested with Python 3.8, 3.9, and 3.13)
- OpenAI API key or Anthropic API key (optional for mock mode)
- Git installed on your system

### Installation

#### Initial Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/MatomeMb/personal-codex-agent.git
   cd personal-codex-agent
   ```

2. Create and activate a virtual environment:

   Windows CMD:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

   Windows PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Linux/macOS:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Option 1: Full Mode (with API keys)
3. Create a `.env` file with your API keys:
   ```ini
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```
4. Create the required data directory structure:
   ```bash
   mkdir -p data/raw data/processed
   ```

5. Place your personal documents in the `data/raw/` folder:
   - PDF files (CV/resume)
   - Markdown files (blog posts, project descriptions)
   - Text files (personal statements, skills summaries)

6. Run the application:
   ```bash
   # Windows CMD
   streamlit run app.py

   # Windows PowerShell / Linux / macOS
   streamlit run app.py
   ```

#### Option 2: Mock Mode (no API keys required)
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables for mock mode:

   **Temporary (Current Session):**

   Windows CMD:
   ```cmd
   set MOCK_MODE=true
   set OPENAI_API_KEY=mock_mode
   ```

   Windows PowerShell:
   ```powershell
   $env:MOCK_MODE='true'
   $env:OPENAI_API_KEY='mock_mode'
   ```

   Linux/macOS:
   ```bash
   export MOCK_MODE=true
   export OPENAI_API_KEY=mock_mode
   ```

   **Permanent Setup:**

   Windows (System Settings):
   1. Open System Properties → Advanced → Environment Variables
   2. Add new System Variables:
      - MOCK_MODE = true
      - OPENAI_API_KEY = mock_mode

   Linux/macOS (add to shell profile):
   ```bash
   # Add to ~/.bashrc, ~/.zshrc, or appropriate shell config
   export MOCK_MODE=true
   export OPENAI_API_KEY=mock_mode
   ```

4. Test the system:
   ```bash
   # Windows CMD/PowerShell
   python test_mock_llm.py      # Test mock responses
   python test_system.py        # Full system test
   python quick_demo.py         # Quick system test

   # Linux/macOS
   python3 test_mock_llm.py    # Test mock responses
   python3 test_system.py      # Full system test
   python3 quick_demo.py       # Quick system test
   ```

5. Run the application:
   ```bash
   # Windows CMD/PowerShell
   streamlit run app.py

   # Linux/macOS
   streamlit run app.py
   ```

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
- **RAG**: sentence-transformers + FAISS
- **LLM**: OpenAI GPT-3.5/4 or Anthropic Claude (with mock fallback)
- **Document Processing**: pypdf, python-docx, markdown
- **Vector Store**: FAISS (optimized for Streamlit Cloud deployment)
- **Mock Mode**: Built-in mock LLM client for demonstration
- **Environment Support**: Windows, Linux, macOS compatible

## Troubleshooting

### Common Issues

1. **ImportError: No module found**
   - Ensure you've activated the virtual environment
   - Verify all dependencies are installed: `pip list`
   - Try reinstalling requirements: `pip install -r requirements.txt`

2. **Environment Variables Not Recognized**
   - Check if variables are set: 
     - Windows CMD: `echo %MOCK_MODE%`
     - PowerShell: `echo $env:MOCK_MODE`
     - Linux/macOS: `echo $MOCK_MODE`
   - Try restarting your terminal after setting variables
   - Verify virtual environment is activated

3. **Streamlit App Issues**
   - Clear Streamlit cache: `streamlit cache clear`
   - Check Streamlit is installed: `streamlit --version`
   - Verify port 8501 is available

4. **Data Loading Issues**
   - Ensure data directory structure exists
   - Check file permissions
   - Verify file formats are supported

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
