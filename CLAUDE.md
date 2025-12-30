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

## Testing

The project includes a comprehensive test suite with 70+ tests covering unit, integration, and API layers.

### Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures for all tests
├── test_ai_generator.py     # Unit tests for Claude API wrapper (23 tests)
├── test_course_search_tool.py # Unit tests for search tools (12 tests)
├── test_rag_system.py       # Integration tests for RAG orchestration (15 tests)
└── test_api_endpoints.py    # API endpoint tests with TestClient (21 tests)
```

### Running Tests

**Always use `uv run pytest` - the pytest configuration is in pyproject.toml.**

```bash
# Run all tests (71 tests, ~0.7s)
uv run pytest

# Run only API endpoint tests (21 tests)
uv run pytest -m api

# Run only unit tests
uv run pytest -m unit

# Run integration tests
uv run pytest -m integration

# Run specific test file
uv run pytest backend/tests/test_api_endpoints.py

# Run with coverage report
uv run pytest --cov=backend --cov-report=term-missing

# Run with HTML coverage report
uv run pytest --cov=backend --cov-report=html
# Then open: htmlcov/index.html

# Verbose output (show all test names)
uv run pytest -vv

# Stop on first failure
uv run pytest -x

# Run tests excluding slow tests
uv run pytest -m "not slow"

# Explicitly target Python 3.13
uv run --python 3.13 pytest
```

### Test Markers

Tests are organized with pytest markers for selective execution:

- `@pytest.mark.unit` - Fast, isolated unit tests for individual components
- `@pytest.mark.integration` - Tests for component interaction
- `@pytest.mark.api` - API endpoint tests using FastAPI TestClient
- `@pytest.mark.slow` - Tests that take significant time to run

### Test Coverage

- **API Layer** (test_api_endpoints.py): All three FastAPI endpoints (/api/query, /api/courses, /api/session/{session_id}), request/response validation, error handling, CORS
- **RAG System** (test_rag_system.py): Query processing, session management, tool orchestration, source tracking
- **AI Generator** (test_ai_generator.py): Tool execution loop, conversation history, multi-round tool calls
- **Search Tools** (test_course_search_tool.py): Course content search, filters, result formatting

### Writing Tests

The test suite uses FastAPI's TestClient for API tests and unittest.mock for mocking dependencies:

```python
import pytest
from fastapi import status

@pytest.mark.api
def test_query_endpoint_success(client, valid_query_request):
    """Test successful query with session ID"""
    response = client.post("/api/query", json=valid_query_request)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "answer" in data
    assert "sources" in data
```

All fixtures are defined in `conftest.py` and automatically available to all tests.
