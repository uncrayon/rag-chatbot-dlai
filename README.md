# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Development

### Setup

```bash
# Install dependencies (including dev tools)
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Quality Checks

```bash
# Format, lint, type-check, and test
./scripts/check-all.sh

# Individual checks
./scripts/format.sh      # Auto-format code
./scripts/lint.sh        # Check code quality
./scripts/typecheck.sh   # Type checking
./scripts/test.sh        # Run tests
```

### Pre-commit Hooks

Git hooks automatically run on commit:
- Code formatting (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- File checks (trailing whitespace, etc.)

To bypass hooks (not recommended):
```bash
git commit --no-verify
```
