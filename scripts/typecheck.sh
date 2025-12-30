#!/bin/bash
# Type check with mypy (informational - does not fail build)

set -e

echo "🔬 Type checking with mypy (informational)..."
uv run mypy backend/ || {
    echo "⚠️  Type checking found issues (non-fatal)"
    echo "    These are informational and don't block the build"
    exit 0
}

echo "✅ Type checking complete with no issues!"
