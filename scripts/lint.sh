#!/bin/bash
# Lint code with Ruff

set -e

echo "🔍 Linting Python code with Ruff..."

# Show what would be fixed
echo "Preview of auto-fixable issues:"
uv run ruff check backend/ --diff

echo ""
echo "Running linter with auto-fix..."
uv run ruff check backend/ --fix

# Show remaining issues
echo ""
echo "Remaining issues (manual fixes needed):"
uv run ruff check backend/ || {
    echo "❌ Linting found issues that need manual fixes"
    exit 1
}

echo "✅ Linting complete!"
