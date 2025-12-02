#!/bin/bash
# Wrapper script to run reindex_papers.py with environment variables loaded

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "Loading environment variables from .env..."
    set -a
    source "$PROJECT_DIR/.env"
    set +a
else
    echo "Error: .env file not found at $PROJECT_DIR/.env"
    exit 1
fi

# Run the reindexing script
cd "$PROJECT_DIR"
uv run python scripts/reindex_papers.py
