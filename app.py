"""
Personal Codex Agent - Streamlit Application

File purpose:
    Main Streamlit UI for the Personal Codex Agent. Orchestrates the app lifecycle
    (initialization, file uploads, mode selection, chat flow) and holds minimal
    session-state wiring required by the UI.

Key components:
    - Streamlit configuration and custom CSS
    - Session state initialization helpers
    - Agent creation and document upload handling
    - Chat display and interaction flow
    - Comprehensive error handling and cloud deployment support

Dependencies:
    - streamlit
    - src.agent.PersonalCodexAgent
    - src.document_processor.DocumentProcessor
    - src.config.Config
    - src.exceptions

Usage:
    Run locally (Windows cmd.exe):

    ```
    streamlit run app.py
    ```

Design notes:
    - The UI stores the heavy `PersonalCodexAgent` instance in `st.session_state.agent`
      to avoid recreating large objects on every rerun. Keep that contract when
      refactoring.
    - The app intentionally presents a mock-mode warning when API keys are absent.
    - Enhanced with comprehensive error handling and cloud deployment compatibility.
"""

import streamlit as st
import os
import sys
import tempfile
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Import our custom modules
try:
    from src.agent import PersonalCodexAgent
    from src.document_processor import DocumentProcessor
    from src.config import config
    from src.exceptions import PersonalCodexException, DeploymentError
    from src.performance import get_performance_dashboard, performance_monitor, cache_manager
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please ensure all dependencies are installed and the src directory is accessible.")
    st.stop()

# Setup logging
logger = logging.getLogger(__name__)

# Mock mode detection using config
IS_MOCK = config.is_mock_mode()

# Page configuration
st.set_page_config(
    page_title="Personal Codex Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .mode-selector {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .agent-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .source-info {
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .confidence-high { background-color: #c8e6c9; color: #2e7d32; }
    .confidence-medium { background-color: #fff3e0; color: #f57c00; }
    .confidence-low { background-color: #ffcdd2; color: #c62828; }
</style>
""", unsafe_allow_html=True)

def display_debug_info():
    """Display debugging information for troubleshooting deployment issues"""
    with st.expander("🔧 Debug Information", expanded=False):
        st.write("**Python Version:**", sys.version)
        st.write("**Working Directory:**", str(Path.cwd()))
        st.write("**Data Directory:**", str(config.data_dir))
        st.write("**Cloud Deployment:**", config.is_cloud_deployment)
        st.write("**Mock Mode:**", IS_MOCK)
        st.write("**LLM Provider:**", config.get_llm_provider())
        
        # Environment variables (filtered for security)
        env_vars = {
            'STREAMLIT_SHARING_MODE': os.getenv('STREAMLIT_SHARING_MODE'),
            'STREAMLIT_SERVER_HEADLESS': os.getenv('STREAMLIT_SERVER_HEADLESS'),
            'STREAMLIT_SERVER_ADDRESS': os.getenv('STREAMLIT_SERVER_ADDRESS'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL'),
        }
        st.write("**Environment Variables:**", env_vars)
        
        # File system check
        try:
            files = list(Path('.').glob('**/*'))
            st.write(f"**Available Files:** {len(files)} files found")
            if st.checkbox("Show file list"):
                for file in files[:20]:  # Show first 20 files
                    st.write(f"- {file}")
        except Exception as e:
            st.write(f"**File System Error:** {e}")

def initialize_session_state():
    """
    Initialize Streamlit `st.session_state` keys used by the app.

    Args:
        None

    Returns:
        None: Mutates `st.session_state` in-place to ensure keys exist:
            - agent: Optional[PersonalCodexAgent]
            - chat_history: List of chat messages
            - documents_loaded: bool flag
            - current_mode: str currently selected mode
            - knowledge_base_info: metadata about the loaded KB
            - error_count: int for tracking errors
            - last_error: str for displaying last error

    Example:
        >>> initialize_session_state()
        # after call: st.session_state.agent may be None or an agent instance
    """
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = "interview"
    if 'knowledge_base_info' not in st.session_state:
        st.session_state.knowledge_base_info = {}
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None

def create_agent() -> Optional[PersonalCodexAgent]:
    """
    Create and initialize a `PersonalCodexAgent` using environment keys.

    The function reads `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` to decide the
    default `llm_provider`. If no API key is present, it will choose `none` and
    the agent will operate in mock/fallback mode.

    Returns:
        PersonalCodexAgent | None: Initialized agent or `None` on error.

    Example:
        >>> agent = create_agent()
        >>> assert agent is not None
    """
    try:
        logger.info("Creating Personal Codex Agent...")
        
        # Get LLM provider from config
        llm_provider = config.get_llm_provider()
        
        if llm_provider == "none":
            st.warning("⚠️ No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables.")
            st.info("The agent will work with limited functionality using fallback responses.")
        
        # Create agent with error handling
        agent = PersonalCodexAgent(
            llm_provider=llm_provider,
            vector_db_type="faiss",  # Use FAISS for better performance
            chunk_size=1000,
            chunk_overlap=200
        )
        
        logger.info(f"Agent created successfully with provider: {llm_provider}")
        return agent
        
    except PersonalCodexException as e:
        logger.error(f"Personal Codex error creating agent: {e}")
        st.error(f"❌ Agent creation failed: {e}")
        st.session_state.error_count += 1
        st.session_state.last_error = str(e)
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error creating agent: {e}")
        logger.error(traceback.format_exc())
        st.error(f"❌ Unexpected error creating agent: {e}")
        st.session_state.error_count += 1
        st.session_state.last_error = str(e)
        return None

def load_documents(agent: PersonalCodexAgent, uploaded_files: List[Any]) -> bool:
    """
    Save uploaded files to a temporary directory, run document processing, and
    add results to the agent's knowledge base.

    Args:
        agent (PersonalCodexAgent): Agent used to process and index documents
        uploaded_files (List[Any]): List of Streamlit uploaded file objects

    Returns:
        bool: True on success, False on failure

    Notes:
        - Files are written to a temporary directory and passed to
          `PersonalCodexAgent.load_documents` which expects a directory path.
        - On success the knowledge base is saved and `st.session_state.knowledge_base_info`
          is updated so the sidebar can display metadata.

    Example:
        >>> success = load_documents(agent, uploaded_files)
    """
    if not uploaded_files:
        st.warning("No files uploaded")
        return False
    
    try:
        logger.info(f"Processing {len(uploaded_files)} uploaded files...")
        
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files to temporary directory
            for uploaded_file in uploaded_files:
                try:
                    file_path = temp_path / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    logger.info(f"Saved uploaded file: {uploaded_file.name}")
                except Exception as e:
                    logger.error(f"Error saving file {uploaded_file.name}: {e}")
                    st.error(f"Error saving file {uploaded_file.name}: {e}")
                    continue
            
            # Process documents
            success = agent.load_documents(str(temp_path))
            
            if success:
                # Save knowledge base
                try:
                    agent.save_knowledge_base()
                    logger.info("Knowledge base saved successfully")
                except Exception as e:
                    logger.warning(f"Could not save knowledge base: {e}")
                    st.warning(f"Could not save knowledge base: {e}")
                
                # Update session state
                try:
                    st.session_state.knowledge_base_info = agent.get_knowledge_base_info()
                    logger.info("Session state updated with knowledge base info")
                except Exception as e:
                    logger.warning(f"Could not update session state: {e}")
                
                return True
            else:
                logger.error("Document processing failed")
                return False
                
    except PersonalCodexException as e:
        logger.error(f"Personal Codex error processing documents: {e}")
        st.error(f"❌ Document processing failed: {e}")
        st.session_state.error_count += 1
        st.session_state.last_error = str(e)
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error processing documents: {e}")
        logger.error(traceback.format_exc())
        st.error(f"❌ Unexpected error processing documents: {e}")
        st.session_state.error_count += 1
        st.session_state.last_error = str(e)
        return False

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """
    Render one chat message in the main UI column using the CSS classes defined
    at the top of the module.

    Args:
        message (Dict[str, Any]): Message dictionary with keys like `content`,
            `mode`, `confidence`, `sources`.
        is_user (bool): If True, render the message as a user message style.

    Returns:
        None: Uses `st.markdown` to render HTML fragments.

    Example:
        >>> display_chat_message({'content': 'Hello'}, is_user=True)
    """
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {message['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Determine confidence badge styling
        confidence_class = f"confidence-{message.get('confidence', 'medium')}"
        confidence_text = message.get('confidence', 'medium').title()
        
        st.markdown(f"""
        <div class="chat-message agent-message">
            <strong>Personal Codex Agent ({message.get('mode', 'Unknown').title()} Mode):</strong><br>
            {message['content']}
            <div class="source-info">
                <span class="confidence-badge {confidence_class}">Confidence: {confidence_text}</span>
                {f" | Sources: {', '.join(message.get('sources', []))}" if message.get('sources') else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """
    Streamlit application entrypoint. Boots session state, renders sidebar
    configuration, initializes/loads the `PersonalCodexAgent`, and drives the
    chat interaction loop.

    Key responsibilities:
        - Initialize session state
        - Offer agent/config controls in the sidebar
        - Process document uploads and initialize knowledge base
        - Manage chat input and display conversation history
        - Handle errors gracefully with comprehensive error reporting

    Returns:
        None

    Example:
        Run the app:
        >>> streamlit run app.py
    """
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Header
        st.markdown('<h1 class="main-header">🧠 Personal Codex Agent</h1>', unsafe_allow_html=True)
        
        # Mock mode display
        if IS_MOCK:
            st.warning("🎭 Running in Mock Mode - No API key required for demonstration")
            st.info("Add your OpenAI API key to .env file for full functionality")
        
        # Cloud deployment info
        if config.is_cloud_deployment:
            st.info("☁️ Running in Streamlit Cloud - Enhanced error handling enabled")
        
        st.markdown("""
        <p style="text-align: center; font-size: 1.1rem; color: #666;">
            Your AI-powered personal representative, trained on your documents and experiences
        </p>
        """, unsafe_allow_html=True)
        
        # Error display
        if st.session_state.error_count > 0:
            st.error(f"⚠️ {st.session_state.error_count} error(s) occurred. Last error: {st.session_state.last_error}")
            if st.button("Clear Errors"):
                st.session_state.error_count = 0
                st.session_state.last_error = None
                st.rerun()
        
        # Debug information (collapsible)
        display_debug_info()
        
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        logger.error(traceback.format_exc())
        st.error(f"❌ Critical application error: {e}")
        st.error("Please check the debug information below and try refreshing the page.")
        display_debug_info()
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # LLM Provider Selection
        st.subheader("AI Provider")
        llm_provider = st.selectbox(
            "Choose your AI provider:",
            ["openai", "anthropic"],
            index=0,
            help="Select which AI service to use for generating responses"
        )
        
        # Vector Database Selection
        st.subheader("Vector Database")
        vector_db_type = st.selectbox(
            "Choose vector database:",
            ["faiss", "chroma"],
            index=0,
            help="FAISS is faster, ChromaDB is more feature-rich"
        )
        
        # Document Processing Settings
        st.subheader("Document Processing")
        chunk_size = st.slider(
            "Chunk Size:",
            min_value=500,
            max_value=2000,
            value=1000,
            step=100,
            help="Size of text chunks for processing"
        )
        
        chunk_overlap = st.slider(
            "Chunk Overlap:",
            min_value=100,
            max_value=500,
            value=200,
            step=50,
            help="Overlap between text chunks"
        )
        
        # Initialize/Create Agent Button
        if st.button("🔄 Initialize Agent", type="primary"):
            with st.spinner("Initializing Personal Codex Agent..."):
                try:
                    st.session_state.agent = PersonalCodexAgent(
                        llm_provider=llm_provider,
                        vector_db_type=vector_db_type,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    st.success("✅ Agent initialized successfully!")
                    st.session_state.error_count = 0  # Reset error count on success
                    st.session_state.last_error = None
                    logger.info("Agent initialized successfully via UI")
                except PersonalCodexException as e:
                    logger.error(f"Personal Codex error initializing agent: {e}")
                    st.error(f"❌ Agent initialization failed: {e}")
                    st.session_state.error_count += 1
                    st.session_state.last_error = str(e)
                except Exception as e:
                    logger.error(f"Unexpected error initializing agent: {e}")
                    logger.error(traceback.format_exc())
                    st.error(f"❌ Unexpected error initializing agent: {e}")
                    st.session_state.error_count += 1
                    st.session_state.last_error = str(e)
        
        # Agent Status
        if st.session_state.agent:
            st.subheader("🤖 Agent Status")
            st.info("✅ Agent Ready")
            
            # Knowledge Base Info
            if st.session_state.knowledge_base_info:
                st.subheader("📚 Knowledge Base")
                kb_info = st.session_state.knowledge_base_info
                st.write(f"**Type:** {kb_info.get('type', 'Unknown')}")
                st.write(f"**Total Chunks:** {kb_info.get('total_chunks', 0)}")
                if kb_info.get('type') == 'faiss':
                    st.write(f"**Vectors:** {kb_info.get('total_vectors', 0)}")
                    st.write(f"**Dimension:** {kb_info.get('dimension', 0)}")
        
        # Document Upload Section
        st.header("📁 Document Upload")
        st.info("Upload your personal documents to train the agent")
        
        uploaded_files = st.file_uploader(
            "Choose files to upload:",
            type=['pdf', 'docx', 'md', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, Word, Markdown, Text"
        )
        
        if uploaded_files and st.button("📥 Process Documents"):
            if st.session_state.agent:
                with st.spinner("Processing documents..."):
                    try:
                        success = load_documents(st.session_state.agent, uploaded_files)
                        if success:
                            st.session_state.documents_loaded = True
                            st.success(f"✅ Successfully processed {len(uploaded_files)} documents!")
                            st.session_state.error_count = 0  # Reset error count on success
                            st.session_state.last_error = None
                            logger.info(f"Successfully processed {len(uploaded_files)} documents")
                        else:
                            st.error("❌ Failed to process documents")
                            logger.error("Document processing failed")
                    except Exception as e:
                        logger.error(f"Error in document processing UI: {e}")
                        st.error(f"❌ Error processing documents: {e}")
                        st.session_state.error_count += 1
                        st.session_state.last_error = str(e)
            else:
                st.error("Please initialize the agent first")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Mode Selector
        if st.session_state.agent:
            st.subheader("🎭 Interaction Mode")
            
            mode_options = {
                "interview": "🎯 Interview Mode",
                "personal_storytelling": "📖 Personal Storytelling Mode", 
                "fast_facts": "⚡ Fast Facts Mode"
            }
            
            selected_mode = st.selectbox(
                "Choose your interaction style:",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(st.session_state.current_mode)
            )
            
            if selected_mode != st.session_state.current_mode:
                # Delegate mode switching to the agent to keep UI logic thin.
                mode_switch_msg = st.session_state.agent.switch_mode(selected_mode)
                st.session_state.current_mode = selected_mode
                st.info(mode_switch_msg)
            
            # Mode description
            mode_descriptions = {
                "interview": "Professional, concise responses suitable for job interviews and networking",
                "personal_storytelling": "Reflective, narrative responses that showcase personality and values",
                "fast_facts": "Quick, scannable information in bullet-point format"
            }
            st.info(f"**{mode_options[selected_mode]}**: {mode_descriptions[selected_mode]}")
        
        # Chat Interface
        st.subheader("💬 Chat with Your Personal Codex Agent")
        
        if not st.session_state.agent:
            st.info("👈 Please initialize the agent in the sidebar first")
        elif not st.session_state.documents_loaded:
            st.info("📁 Please upload and process some documents to start chatting")
        else:
            # Display chat history
            for message in st.session_state.chat_history:
                if message['type'] == 'user':
                    display_chat_message({'content': message['content']}, is_user=True)
                else:
                    display_chat_message(message)
            
            # Chat input
            user_input = st.chat_input("Ask me anything about your experience, skills, or background...")
            
            if user_input:
                try:
                    # Add user message to history
                    st.session_state.chat_history.append({
                        'type': 'user',
                        'content': user_input,
                        'timestamp': None
                    })
                    
                    # Generate agent response
                    with st.spinner("🤔 Thinking..."):
                        try:
                            # Core RAG flow: agent searches the KB, formats prompts, and
                            # calls the configured LLM (or mock) to generate a response.
                            response = st.session_state.agent.generate_response(user_input)
                            
                            # Add agent response to history
                            st.session_state.chat_history.append({
                                'type': 'agent',
                                'content': response['response'],
                                'mode': response['mode'],
                                'confidence': response['confidence'],
                                'sources': response.get('sources', []),
                                'timestamp': None
                            })
                            
                            logger.info(f"Generated response for query: {user_input[:50]}...")
                            
                        except PersonalCodexException as e:
                            logger.error(f"Personal Codex error generating response: {e}")
                            error_response = {
                                'type': 'agent',
                                'content': f"❌ Error generating response: {e}",
                                'mode': 'error',
                                'confidence': 'low',
                                'sources': [],
                                'timestamp': None
                            }
                            st.session_state.chat_history.append(error_response)
                            st.session_state.error_count += 1
                            st.session_state.last_error = str(e)
                            
                        except Exception as e:
                            logger.error(f"Unexpected error generating response: {e}")
                            logger.error(traceback.format_exc())
                            error_response = {
                                'type': 'agent',
                                'content': f"❌ Unexpected error: {e}",
                                'mode': 'error',
                                'confidence': 'low',
                                'sources': [],
                                'timestamp': None
                            }
                            st.session_state.chat_history.append(error_response)
                            st.session_state.error_count += 1
                            st.session_state.last_error = str(e)
                    
                    # Rerun to display new messages
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Error in chat interface: {e}")
                    st.error(f"❌ Error in chat interface: {e}")
                    st.session_state.error_count += 1
                    st.session_state.last_error = str(e)
    
    with col2:
        # Quick Actions Panel
        st.subheader("🚀 Quick Actions")
        
        if st.session_state.agent and st.session_state.documents_loaded:
            # Sample Questions
            st.subheader("💡 Sample Questions")
            sample_questions = [
                "What kind of engineer are you?",
                "What are your strongest technical skills?",
                "What projects are you most proud of?",
                "What do you value in team culture?",
                "How do you approach learning new things?",
                "What tasks energize you?",
                "How do you collaborate with others?"
            ]
            
            for question in sample_questions:
                if st.button(question, key=f"sample_{hash(question)}"):
                    # Add to chat input (this would need to be handled differently in a real app)
                    st.info("Click the sample question to see how the agent responds!")
            
            # Conversation Stats
            st.subheader("📊 Conversation Stats")
            if st.session_state.agent:
                summary = st.session_state.agent.get_conversation_summary()
                st.write(f"**Total Turns:** {summary['total_turns']}")
                st.write(f"**Current Mode:** {summary['current_mode'].title()}")
                st.write(f"**Documents Loaded:** {'✅' if summary['documents_loaded'] else '❌'}")
                st.write(f"**Knowledge Base:** {'✅' if summary['knowledge_base_initialized'] else '❌'}")
        
        # Performance Dashboard
        if st.session_state.agent:
            st.subheader("📊 Performance Dashboard")
            
            if st.button("🔄 Refresh Performance Data"):
                st.rerun()
            
            try:
                dashboard = get_performance_dashboard()
                
                # Performance Stats
                perf_stats = dashboard.get('performance_stats', {})
                if perf_stats:
                    st.write("**Function Performance:**")
                    for func_name, stats in list(perf_stats.items())[:5]:  # Show top 5
                        st.write(f"• {func_name}: {stats['avg_time']:.2f}s avg ({stats['call_count']} calls)")
                
                # Cache Stats
                cache_stats = dashboard.get('cache_stats', {})
                if cache_stats:
                    st.write(f"**Cache Hit Rate:** {cache_stats.get('hit_rate', 0):.1%}")
                    st.write(f"**Cache Size:** {cache_stats.get('size', 0)}/{cache_stats.get('max_size', 0)}")
                
                # Error Rate
                error_rate = performance_monitor.get_error_rate()
                if error_rate > 0:
                    st.warning(f"**Error Rate:** {error_rate:.1%}")
                else:
                    st.success("**Error Rate:** 0%")
                
                # Recent Metrics
                recent_metrics = dashboard.get('recent_metrics', [])
                if recent_metrics:
                    st.write("**Recent Operations:**")
                    for metric in recent_metrics[-3:]:  # Show last 3
                        status = "✅" if metric['success'] else "❌"
                        st.write(f"{status} {metric['function_name']}: {metric['execution_time']:.2f}s")
                
            except Exception as e:
                st.error(f"Error loading performance data: {e}")
        
        # Help and Information
        st.subheader("❓ Help")
        st.info("""
        **How to use:**
        1. Initialize the agent in the sidebar
        2. Upload your personal documents
        3. Choose an interaction mode
        4. Start chatting!
        
        **Supported file types:**
        - PDF (CVs, resumes)
        - Word documents
        - Markdown files
        - Text files
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <p style="text-align: center; color: #666;">
        Personal Codex Agent - Your AI-powered personal representative
    </p>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()