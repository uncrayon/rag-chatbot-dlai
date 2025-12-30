#!/bin/bash
# Format code with Ruff

set -e

echo "🎨 Formatting Python code with Ruff..."
uv run ruff format backend/

echo "📦 Sorting imports with Ruff..."
uv run ruff check --select I --fix backend/

echo "✅ Formatting complete!"
