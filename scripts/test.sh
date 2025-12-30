#!/bin/bash
# Run tests with coverage

set -e

echo "🧪 Running tests with coverage..."
cd backend && uv run pytest

echo ""
echo "📊 Coverage report available in backend/htmlcov/index.html"
echo "✅ Testing complete!"
