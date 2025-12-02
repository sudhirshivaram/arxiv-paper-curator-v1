#!/bin/bash
# Run Streamlit frontend for arXiv Paper Curator

set -e

echo "Starting arXiv Paper Curator Frontend..."
echo "========================================="
echo ""
echo "API URL: ${API_URL:-https://arxiv-paper-curator-v1-production.up.railway.app}"
echo ""
echo "The app will open in your browser automatically."
echo "If not, navigate to: http://localhost:8501"
echo ""

uv run streamlit run streamlit_app.py
