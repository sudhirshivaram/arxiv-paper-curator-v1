# RAG System Benchmarking Framework

Comprehensive evaluation framework for your arXiv Paper Curator RAG system. This framework measures:

- **RAGAS Scores** (0-1 scale): faithfulness, answer relevancy, context precision, context recall
- **MRR** (Mean Reciprocal Rank): How quickly relevant documents appear in results
- **Hit Rate@k**: Percentage of queries with relevant results in top-k
- **Latency Metrics**: Response time analysis (avg, p50, p95, p99)
- **Token Cost Savings**: Track and optimize LLM token usage

## 📦 Installation

First, install the required dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install ragas datasets matplotlib
```

## 🚀 Quick Start

### 1. Start Your RAG System

Make sure your FastAPI server is running:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 2. Create an Evaluation Dataset

You have three options:

#### Option A: Use the Sample Dataset (Quick Test)
```bash
cd benchmarks
cp sample_dataset.json evaluation_dataset.json
```

#### Option B: Generate Synthetic Dataset
```bash
cd benchmarks
python dataset_generator.py --mode synthetic --num-pairs 20 --api-url http://localhost:8000
```

#### Option C: Create Manual Template
```bash
cd benchmarks
python dataset_generator.py --mode template --num-pairs 10
# Then edit evaluation_dataset.json with your questions and answers
```

### 3. Run Benchmarks

```bash
cd benchmarks
python run_benchmark.py
```

Expected output:
```
================================================================================
                        RAG SYSTEM EVALUATION REPORT
================================================================================

📊 EVALUATION SUMMARY
   Samples evaluated: 10
   Failed queries: 0

✅ RAGAS SCORES (0-1 scale, higher is better)
   Overall RAGAS Score:    0.752
   Faithfulness:           0.834
   Answer Relevancy:       0.721
   Context Precision:      0.698
   Context Recall:         0.755

🎯 RANKING METRICS
   MRR (Mean Reciprocal Rank): 0.823
   Hit Rate@1:                 65.0%
   Hit Rate@3:                 90.0%
   Hit Rate@5:                 95.0%
   Hit Rate@10:                100.0%

⚡ LATENCY METRICS (milliseconds)
   Average:       342.5 ms
   P50 (median):  315.2 ms
   P95:           487.3 ms
   P99:           523.1 ms

💰 COST METRICS
   Total tokens:           45,230
   Avg tokens per query:   4,523.0
   Estimated cost:         $0.0678
   Cost per query:         $0.006780
```

### 4. Generate Visualizations

```bash
cd benchmarks
python visualize_results.py results/benchmark_results_*.json
```

This creates:
- `visualizations/ragas_scores.png` - RAGAS metrics bar chart
- `visualizations/ranking_metrics.png` - MRR and Hit Rate charts
- `visualizations/latency_metrics.png` - Latency distribution
- `visualizations/cost_metrics.png` - Token usage and cost analysis
- `visualizations/benchmark_report.html` - **Interactive HTML report**

### 5. View the Report

Open the HTML report in your browser:
```bash
# Linux/Mac
xdg-open benchmarks/results/visualizations/benchmark_report.html

# Or just open the file in your browser
```

## 📊 Understanding the Metrics

### RAGAS Scores (0-1 scale)

| Metric | What It Measures | Good Score |
|--------|------------------|------------|
| **Faithfulness** | Is the answer grounded in the retrieved context? | > 0.7 |
| **Answer Relevancy** | Does the answer directly address the question? | > 0.7 |
| **Context Precision** | Are the retrieved contexts relevant? | > 0.6 |
| **Context Recall** | Did we retrieve all necessary context? | > 0.7 |

### Ranking Metrics

| Metric | What It Measures | Good Score |
|--------|------------------|------------|
| **MRR** | Average position of first relevant result | > 0.7 |
| **Hit Rate@1** | % queries with relevant result in position 1 | > 50% |
| **Hit Rate@3** | % queries with relevant result in top 3 | > 80% |
| **Hit Rate@5** | % queries with relevant result in top 5 | > 90% |

### Latency Metrics

| Metric | What It Measures | Target |
|--------|------------------|--------|
| **Average** | Mean response time | < 500ms |
| **P50** | Median response time | < 400ms |
| **P95** | 95th percentile (handles outliers) | < 800ms |
| **P99** | 99th percentile (worst case) | < 1000ms |

## 🔧 Advanced Usage

### Customize Evaluation Dataset

Edit `evaluation_dataset.json`:

```json
{
  "questions": [
    "What is the attention mechanism in transformers?"
  ],
  "ground_truths": [
    "The attention mechanism allows models to focus on different parts..."
  ],
  "relevant_doc_ids": [
    ["1706.03762", "1409.0473"]
  ],
  "ground_truth_contexts": [
    [
      "An attention function maps a query and key-value pairs to output...",
      "Multi-head attention allows joint attention to information..."
    ]
  ]
}
```

### Run with Custom API URL

```bash
export API_BASE_URL=https://your-production-url.com
python run_benchmark.py
```

### Adjust Cost Calculation

```bash
export COST_PER_1K_TOKENS=0.002  # Adjust based on your LLM pricing
python run_benchmark.py
```

### Compare Multiple Configurations

Run benchmarks with different settings and compare:

```bash
# Test 1: BM25 only
python run_benchmark.py --config bm25_only
# Results saved to: benchmark_results_bm25_1234567890.json

# Test 2: Hybrid search
python run_benchmark.py --config hybrid
# Results saved to: benchmark_results_hybrid_1234567891.json

# Compare
python compare_benchmarks.py results/benchmark_results_*.json
```

## 📁 Project Structure

```
benchmarks/
├── __init__.py              # Package initialization
├── README.md                # This file
├── rag_evaluator.py         # Core evaluation framework
├── run_benchmark.py         # Main benchmark runner
├── dataset_generator.py     # Generate evaluation datasets
├── visualize_results.py     # Create charts and reports
├── sample_dataset.json      # Sample evaluation data
├── evaluation_dataset.json  # Your evaluation dataset (created by you)
└── results/                 # Benchmark results (auto-generated)
    ├── benchmark_results_*.json
    └── visualizations/
        ├── ragas_scores.png
        ├── ranking_metrics.png
        ├── latency_metrics.png
        ├── cost_metrics.png
        └── benchmark_report.html
```

## 🎯 Use Cases

### 1. System Improvement Tracking
Run benchmarks before/after changes to measure impact:
```bash
# Before optimization
python run_benchmark.py
# Results: MRR=0.65, Avg Latency=450ms

# After adding hybrid search
python run_benchmark.py
# Results: MRR=0.82, Avg Latency=380ms
# 🎉 26% improvement in MRR, 15% reduction in latency!
```

### 2. Portfolio Metrics
Generate metrics for your portfolio/resume:
```bash
python run_benchmark.py
python visualize_results.py results/benchmark_results_*.json

# Use the generated metrics:
# - "Achieved 0.82 MRR and 95% Hit Rate@5"
# - "Reduced latency by 30% (450ms → 315ms)"
# - "Optimized costs to $0.007 per query"
```

### 3. A/B Testing
Compare different RAG configurations:
```bash
# Test different embedding models, chunk sizes, retrieval strategies, etc.
# Each test generates separate results for comparison
```

## 🐛 Troubleshooting

### Issue: RAGAS evaluation fails

**Solution**: Make sure you have OpenAI API key set (RAGAS uses OpenAI for evaluation):
```bash
export OPENAI_API_KEY=your-key-here
python run_benchmark.py
```

### Issue: "Connection refused" error

**Solution**: Ensure your FastAPI server is running:
```bash
uvicorn src.main:app --reload
```

### Issue: Low RAGAS scores

**Possible causes**:
- Ground truth answers don't match retrieved contexts
- Retrieved contexts are incomplete
- LLM generation is hallucinating

**Solution**: Check your evaluation dataset quality and retrieval logic.

### Issue: High latency

**Solutions**:
- Enable caching (Redis)
- Optimize OpenSearch queries
- Use smaller embedding models
- Reduce context window size

## 📈 Interpreting Results

### Excellent Performance
- RAGAS scores > 0.8
- MRR > 0.8
- Hit Rate@5 > 95%
- P95 latency < 500ms
- Cost per query < $0.01

### Good Performance
- RAGAS scores > 0.7
- MRR > 0.7
- Hit Rate@5 > 85%
- P95 latency < 800ms
- Cost per query < $0.02

### Needs Improvement
- RAGAS scores < 0.6
- MRR < 0.6
- Hit Rate@5 < 75%
- P95 latency > 1000ms
- Cost per query > $0.05

## 🔗 Integration with Your Multimodal RAG Plan

This benchmarking framework is designed to work with both:
1. **Current system** (text-based RAG)
2. **Future multimodal system** (text + visual)

For multimodal evaluation, extend the framework to include:
- Visual similarity metrics
- Multimodal fusion effectiveness
- Image retrieval precision

## 📚 References

- [RAGAS Framework](https://github.com/explodinggradients/ragas)
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [Mean Reciprocal Rank](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)

## 🤝 Contributing

Found a bug or want to add a feature? Feel free to modify and extend this framework for your needs!

---

**Happy Benchmarking!** 📊✨
