#!/bin/bash

# Setup script for RAG benchmarking framework
# This script installs dependencies and sets up the benchmarking environment

set -e

echo "🚀 Setting up RAG Benchmarking Framework"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

echo ""
echo "📦 Installing dependencies..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv sync
else
    echo "uv not found, using pip..."
    pip install ragas datasets matplotlib
fi

echo ""
echo "✅ Dependencies installed!"

# Create results directory
echo ""
echo "📁 Creating results directory..."
mkdir -p benchmarks/results/visualizations
echo "✅ Results directory created"

# Check for OpenAI API key (required for RAGAS)
echo ""
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "RAGAS evaluation requires OpenAI API key. Set it with:"
    echo "export OPENAI_API_KEY=your-key-here"
    echo ""
    echo "Or add it to your .env file:"
    echo "echo 'OPENAI_API_KEY=your-key-here' >> .env"
else
    echo "✅ OpenAI API key found"
fi

echo ""
echo "🎯 Setup complete! Next steps:"
echo ""
echo "1. Start your RAG system:"
echo "   uvicorn src.main:app --reload"
echo ""
echo "2. Create an evaluation dataset:"
echo "   cd benchmarks"
echo "   python dataset_generator.py --mode synthetic --num-pairs 10"
echo ""
echo "3. Run benchmarks:"
echo "   python run_benchmark.py"
echo ""
echo "4. Generate visualizations:"
echo "   python visualize_results.py results/benchmark_results_*.json"
echo ""
echo "📚 For detailed instructions, see benchmarks/README.md"
echo ""
echo "Happy benchmarking! 📊✨"
