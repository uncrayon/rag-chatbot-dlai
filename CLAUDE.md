# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) chatbot for answering questions about course materials. Uses ChromaDB for vector storage, Anthropic Claude for AI generation, and a vanilla JS frontend.

## Commands

**Always use `uv` for package management and running Python - never use `pip` directly.**

```bash
# Add a dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Run a Python file
uv run python <file.py>
```

```bash
# Install dependencies
uv sync

# Run the server (from project root)
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000

# Access points
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Architecture

### Tool-Based RAG Pattern

This system uses a **tool-based RAG** approach rather than traditional forced retrieval:

1. User query arrives at `/api/query`
2. Claude receives the query with a `search_course_content` tool definition
3. Claude **decides** whether to search (not every query triggers retrieval)
4. If search is used, results are returned to Claude for synthesis
5. Two LLM calls: first for tool decision, second for final answer

### Key Components

```
backend/
├── app.py              # FastAPI endpoints, serves frontend
├── rag_system.py       # Main orchestrator connecting all components
├── ai_generator.py     # Claude API wrapper with tool execution loop
├── vector_store.py     # ChromaDB with two collections
├── search_tools.py     # Tool definitions and ToolManager
├── document_processor.py # Parses course docs, chunks text
├── session_manager.py  # Conversation history (last 2 exchanges)
└── config.py           # Settings from .env

frontend/               # Vanilla JS, served as static files
docs/                   # Course .txt files loaded on startup
```

### Data Flow

**Document Ingestion (on startup):**
```
docs/*.txt → DocumentProcessor (parse + chunk 800 chars) → VectorStore (embed + store)
```

**Query Processing:**
```
Frontend POST → RAGSystem.query() → AIGenerator (Claude + tools) → CourseSearchTool → VectorStore.search() → Claude synthesizes → Response with sources
```

### Two ChromaDB Collections

| Collection | Purpose |
|------------|---------|
| `course_catalog` | Course metadata for fuzzy name resolution |
| `course_content` | Text chunks with course/lesson metadata |

Course name resolution uses vector similarity, so "prompt course" matches "Prompt Compression and Query Optimization".

### Configuration (config.py)

- `CHUNK_SIZE`: 800 characters
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation exchanges
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2

## Environment

Requires `.env` with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Code Quality

This project uses modern Python quality tools:

**Tools:**
- `ruff` - Fast linter and formatter (replaces Black, isort, Flake8)
- `mypy` - Static type checking
- `pytest` - Testing with coverage
- `pre-commit` - Git hooks

**Commands:**

```bash
# Format code
./scripts/format.sh

# Lint code
./scripts/lint.sh

# Type check
./scripts/typecheck.sh

# Run tests
./scripts/test.sh

# Run all checks
./scripts/check-all.sh

# Install git hooks (one-time setup)
uv run pre-commit install

# Run pre-commit on all files
uv run pre-commit run --all-files
```

**Configuration files:**
- `pyproject.toml` - Tool configurations
- `.pre-commit-config.yaml` - Git hooks
