### Repository: Personal Codex Agent — Guidance for AI coding agents

This file gives concise, actionable tips to AI coding agents (Copilot-like assistants) so they can be productive quickly in this repo.

Key goals for edits:
- Preserve the RAG architecture and mock-mode-first deployment model.
- Keep FAISS as the canonical vector DB for Streamlit Cloud compatibility.
- Avoid reintroducing heavy external deps (ChromaDB) unless there's a clear reason.

Quick architecture overview
- app.py — Streamlit UI and session-state orchestration. Handles agent initialization, file uploads, mode selection, chat UI, and session-state variables (`st.session_state.agent`, `chat_history`, `documents_loaded`, `knowledge_base_info`).
- src/agent.py — Core orchestration: document loading, RAG flow, LLM client selection (OpenAI/Anthropic/Mock), mode switching, and response formatting.
- src/embeddings.py — Embedding model wrapper + FAISS-based vector store. Implements embedding generation, FAISS indexing, search, and save/load logic.
- src/document_processor.py — Document parsing & chunking (used by `PersonalCodexAgent.document_processor`).
- src/mock_llm.py — Deterministic mock LLM client used when `MOCK_MODE` is true or API keys are missing.

Patterns and conventions (do not change lightly)
- Mock-first design: The code often falls back to `MockLLMClient` when environment variables are missing. Preserve this behavior when refactoring tests or CI flows.
- FAISS-only vector DB in `src/embeddings.py`: Chroma-related code has been intentionally removed. If you add Chroma back, keep separate feature-flagged paths and update `requirements.txt`.
- Session-state-driven UI: `app.py` expects `st.session_state.agent` to be an initialized `PersonalCodexAgent`. Any changes to agent initialization must keep that contract.
- File IO paths: Processed artifacts live under `data/processed/` and raw files under `data/raw/`. Keep save/load filename conventions (e.g., knowledge base base path `data/processed/knowledge_base`) to preserve compatibility with tests and the Streamlit UI.

Developer workflows & commands
- Run the Streamlit app locally (Windows / cmd.exe):
```
streamlit run app.py
```
- Run quick system tests (mock mode recommended):
```
set MOCK_MODE=true
set OPENAI_API_KEY=mock_mode
pip install -r requirements.txt
python quick_demo.py
python test_mock_llm.py
python test_system.py
```
- If adding or restoring heavy deps (faiss/chroma/sentence-transformers), update `requirements.txt` and prefer pinned versions.

Where to look for examples and patterns
- Mode handling: `PersonalCodexAgent.switch_mode` and `app.py`'s sidebar mode selector. Keep UI strings and `modes` metadata in sync.
- RAG flow: `PersonalCodexAgent.load_documents` -> `EmbeddingsSystem.add_documents` -> `EmbeddingsSystem._add_to_faiss` -> `PersonalCodexAgent.generate_response` -> LLM call. Edits that alter the data shape must update the intermediate consumers.
- Mock examples: `test_mock_llm.py` sets `MOCK_MODE` and exercises `MockLLMClient`. Use this file as a template for unit tests that must run offline.
- Tests and smoke checks: `test_system.py` contains simple import and integration checks; keep its expectations (FAISS presence, Mock fallback) intact.

Common pitfalls and how to avoid them
- Changing vector dimensions: `EmbeddingsSystem._initialize_faiss()` infers dimension from `model_name`. If you change the model, update index creation and serialization.
- Session state resets: Streamlit reruns can clear transient variables. Persist agent state by storing necessary metadata in `st.session_state` and avoid re-creating heavy objects on every rerun.
- API key handling: Code treats missing or placeholder API keys as `mock_mode`. Don't remove this guard without adding an explicit migration path for CI and production secrets.

Small targeted examples to use in patches
- Initialize agent (app.py pattern):
```py
agent = PersonalCodexAgent(
    llm_provider='openai',
    vector_db_type='faiss',
    chunk_size=1000,
    chunk_overlap=200
)
```
- Save/load knowledge base (keep file path conventions):
```py
agent.save_knowledge_base('data/processed/knowledge_base')
agent.load_knowledge_base('data/processed/knowledge_base')
```
- Search flow example (unit-tests):
```py
agent = PersonalCodexAgent(llm_provider='none')
agent.load_documents('data/raw')
results = agent.search_knowledge_base('machine learning', top_k=3)
```

Edit guidance for contributors (AI and humans)
- Prefer minimal, well-tested edits. When modifying the RAG pipeline, add a small unit test to `test_system.py` or a new test file demonstrating the new shape.
- Keep mock-mode behavior intact: update `test_mock_llm.py` if you change `MockLLMClient` APIs.
- When adding external services (ChromaDB, cloud stores), gate them behind explicit config and document changes in `README.md`.

Files of highest relevance (quick references)
- `app.py` — UI and user flows
- `src/agent.py` — core orchestration and LLM switching
- `src/embeddings.py` — FAISS index and embedding operations
- `src/document_processor.py` — chunking and parsing
- `src/mock_llm.py` — offline LLM behavior used by tests and demos
- `test_system.py`, `test_mock_llm.py` — integration & mock tests

If you see something unclear or missing, ask the repo owner for:
- Intent on reintroducing ChromaDB or other vector DBs
- Preferred production deployment (Streamlit Cloud vs containerized app)
- Any secrets/CI instructions that differ from local `.env` usage

---
If you want me to iterate on this file, say which section to expand (workflows, architecture, tests, or edit policies).
