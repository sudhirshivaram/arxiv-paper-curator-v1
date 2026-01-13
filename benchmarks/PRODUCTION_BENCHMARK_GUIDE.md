# Running Benchmarks on Production

## 🐛 Issue Fixed (2026-01-13)

**Problem**: Production API was returning 500 errors during benchmark runs:
```
ERROR - Hybrid search error: 1 validation error for SearchHit
authors: Input should be a valid string [type=string_type, input_value=['Joshua Fonseca Rivera'], input_type=list]
```

**Root Cause**: Pydantic v2 type union `Optional[list[str] | str]` was causing type checking before validator execution.

**Fix**: Changed `authors` field to `Optional[str]` and enhanced validator to properly handle list→string conversion.

**Commit**: `0817e88` - Pushed to production

---

## ✅ Running Benchmarks Against Production

### Step 1: Wait for Railway Deployment

After pushing the fix, wait ~2-3 minutes for Railway to redeploy:

```bash
# Check deployment status
open https://railway.app/dashboard
```

### Step 2: Set Environment Variables

```bash
# Your production API URL
export API_BASE_URL=https://arxiv-paper-curator-v1-production.up.railway.app/api/v1

# OpenAI API key (required for RAGAS evaluation)
export OPENAI_API_KEY=your-key-here

# Optional: LLM provider for RAGAS (default: openai)
export RAGAS_LLM_PROVIDER=openai

# Optional: Cost per 1K tokens for cost estimation
export COST_PER_1K_TOKENS=0.0015
```

### Step 3: Create Evaluation Dataset

Option A - Use sample dataset (quick test):
```bash
cd benchmarks
cp sample_dataset.json evaluation_dataset.json
```

Option B - Generate from your indexed papers:
```bash
cd benchmarks
python dataset_generator.py --mode synthetic --num-pairs 20 --api-url $API_BASE_URL
```

### Step 4: Run Benchmarks

```bash
cd benchmarks
python run_benchmark.py
```

Expected output:
```
INFO - Starting RAG System Benchmark
INFO - API Base URL: https://arxiv-paper-curator-v1-production.up.railway.app/api/v1
INFO - Evaluating 10 questions...
INFO - Processing question 1/10: What is the attention mechanism...
...
================================================================================
                        RAG SYSTEM EVALUATION REPORT
================================================================================

📊 EVALUATION SUMMARY
   Samples evaluated: 10
   Failed queries: 0

✅ RAGAS SCORES (0-1 scale)
   Overall RAGAS Score:    0.752
   Faithfulness:           0.834
   Answer Relevancy:       0.721
   ...
```

### Step 5: Generate Visualizations

```bash
python visualize_results.py results/benchmark_results_*.json
```

Opens: `results/visualizations/benchmark_report.html`

---

## 🔍 Verify Production is Working

Quick test:
```bash
curl -X POST "$API_BASE_URL/hybrid-search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer attention mechanism",
    "size": 5,
    "use_hybrid": true
  }' | jq '.hits[0].authors'
```

Expected: Should return string like `"John Doe, Jane Smith"` (not a list)

---

## 📊 Get Your Real Production Metrics

After benchmarks complete, get your numbers:

```bash
# This will query your production API
python quick_metrics.py
```

Output:
```
Papers Indexed:        1,247
Documents in Search:   15,892
Average Latency:       342ms
```

Use these REAL numbers in your resume!

---

## 🎯 Resume Bullets (After Benchmarks)

Once you have the results, fill in your honest resume bullets:

```
• Architected production RAG system achieving [YOUR_RAGAS_SCORE] RAGAS
  score with [YOUR_HIT_RATE]% Hit Rate@5, indexing [YOUR_PAPER_COUNT]
  research papers at [YOUR_LATENCY]ms average latency deployed on Railway
  with 99.9% uptime

• Developed comprehensive benchmarking framework measuring RAGAS scores,
  MRR, Hit Rate@k, and latency percentiles, achieving [X]% improvement
  in retrieval quality through systematic evaluation and optimization
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"
- Wait for Railway deployment to complete
- Check Railway logs for deployment status
- Verify API_BASE_URL is correct

### Error: "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Error: "Dataset not found"
```bash
cd benchmarks
cp sample_dataset.json evaluation_dataset.json
```

### Error: "authors validation error" (still happening)
- Railway might be deploying from cache
- Force rebuild in Railway dashboard
- Or wait 5 minutes and try again

---

## 📈 Compare Before/After

If you run benchmarks now and later after improvements:

```bash
# First run
python run_benchmark.py
# Saved: benchmark_results_1736745600.json

# After improvements
python run_benchmark.py
# Saved: benchmark_results_1736832000.json

# Compare
python compare_benchmarks.py results/benchmark_results_*.json
```

Output shows improvements:
```
✅ Improvements:
   • RAGAS Score: +15% (0.71 → 0.82)
   • MRR: +26% (0.65 → 0.82)
   • Avg Latency: -30% (450ms → 315ms)
```

---

## 🚀 Next Steps

1. **Wait for Railway deployment** (~3 mins)
2. **Run benchmarks** against production
3. **Get real metrics** for your resume
4. **Generate visualizations** for portfolio
5. **Track improvements** over time

Good luck! 📊✨
