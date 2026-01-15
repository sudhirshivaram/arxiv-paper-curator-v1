# 🎯 How to Establish Baseline Metrics for RAG Systems

## The Problem

You have **RAGAS 0.88, MRR 1.0, Hit Rate 100%** - but what's the baseline?

Without a baseline, you can't claim improvement. This guide shows you how to establish honest, verifiable baselines.

---

## 🔬 Three Types of Baselines

### 1. Ablation Baseline (Remove Features)
**Concept:** Turn off your improvements to see their impact

### 2. Naive Baseline (Simplest Approach)
**Concept:** Compare to the most basic implementation

### 3. Component Baseline (Weaker Parts)
**Concept:** Replace sophisticated components with simpler ones

---

## 🚀 Practical Experiments for Your System

### Experiment 1: Hybrid Search vs BM25-Only

**Current System:** Hybrid (BM25 + Semantic embeddings)
**Baseline:** BM25 only (no embeddings)

**How to run:**

```bash
# 1. Run with hybrid search (your current system)
python run_benchmark.py \
  --api-url https://your-api.railway.app/api/v1 \
  --use-hybrid true \
  --output-file results/hybrid_system.json

# 2. Run with BM25 only (baseline)
python run_benchmark.py \
  --api-url https://your-api.railway.app/api/v1 \
  --use-hybrid false \
  --output-file results/bm25_baseline.json
```

**Expected Results:**
- Hybrid: RAGAS ~0.88, MRR ~1.0
- BM25-only: RAGAS ~0.70-0.75, MRR ~0.80-0.85

**Resume Bullet:**
> "Implemented hybrid search (BM25 + semantic) improving RAGAS from **0.73 baseline** to **0.88** (+21%)"

---

### Experiment 2: Top-K Optimization

**Current System:** top_k = 5
**Baselines:** top_k = 3, 7, 10

**How to run:**

```python
# Modify run_benchmark.py temporarily:

# Test different top_k values
for k in [3, 5, 7, 10]:
    request_data = {
        "query": question,
        "top_k": k,  # ← Change this
        "use_hybrid": True
    }
    # Run and save results
```

**Expected Results:**
- top_k=3: RAGAS ~0.83, lower recall
- top_k=5: RAGAS ~0.88 (optimal)
- top_k=7: RAGAS ~0.86, noise increases
- top_k=10: RAGAS ~0.82, too much noise

**Resume Bullet:**
> "Optimized retrieval chunk count to **top-5** through ablation testing, achieving **0.88 RAGAS** vs **0.83** (top-3 baseline)"

---

### Experiment 3: LLM Provider Comparison

**Current System:** 4-tier fallback (Gemini → Claude → GPT-4 → GPT-3.5)
**Baseline:** Single GPT-3.5 (no fallback)

**How to run:**

```bash
# 1. Current system (4-tier fallback)
# (Your normal setup - uses Gemini primary with fallbacks)
python run_benchmark.py

# 2. Single LLM baseline
# Temporarily set in .env:
# LLM_PROVIDER=openai
# OPENAI_MODEL=gpt-3.5-turbo
# Comment out fallback logic in ask.py (lines 264-336)
python run_benchmark.py --output-file results/gpt35_baseline.json
```

**Expected Results:**
- 4-tier fallback: 100% success rate, RAGAS ~0.88
- GPT-3.5 only: 95% success rate, RAGAS ~0.68-0.72

**Resume Bullet:**
> "Designed 4-tier LLM fallback strategy achieving **100% query success** vs **95% baseline** (single model), improving RAGAS from **0.70** to **0.88** (+26%)"

---

### Experiment 4: No Caching vs Redis Cache

**Current System:** Redis caching enabled
**Baseline:** No caching

**How to run:**

```bash
# 1. With caching (current)
# REDIS enabled in environment
python run_benchmark.py --measure-latency

# 2. Without caching (baseline)
# Disable Redis in .env or stop Redis service
python run_benchmark.py --measure-latency --output-file results/no_cache_baseline.json
```

**Expected Results:**
- With cache: Avg latency ~500ms (50% cache hit)
- No cache: Avg latency ~1200ms

**Resume Bullet:**
> "Implemented Redis caching reducing average query latency from **1.2s baseline** to **500ms** (58% improvement)"

---

## 📊 Complete Baseline Testing Script

Create this file: `benchmarks/run_ablation_tests.sh`

```bash
#!/bin/bash

API_URL="https://your-api.railway.app/api/v1"
RESULTS_DIR="benchmarks/ablation_results"

mkdir -p $RESULTS_DIR

echo "🔬 Running Ablation Tests..."
echo ""

# Test 1: Hybrid vs BM25-only
echo "Test 1: Hybrid Search Impact"
python run_benchmark.py \
  --api-url $API_URL \
  --use-hybrid true \
  --output-file $RESULTS_DIR/1_hybrid.json

python run_benchmark.py \
  --api-url $API_URL \
  --use-hybrid false \
  --output-file $RESULTS_DIR/1_bm25_baseline.json

echo "✅ Test 1 complete"
echo ""

# Test 2: Top-K optimization
echo "Test 2: Top-K Impact"
for k in 3 5 7 10; do
  python run_benchmark.py \
    --api-url $API_URL \
    --top-k $k \
    --output-file $RESULTS_DIR/2_topk_${k}.json
done

echo "✅ Test 2 complete"
echo ""

# Test 3: Compare results
echo "📊 Results Summary:"
python compare_benchmarks.py $RESULTS_DIR/*.json

echo ""
echo "✅ All ablation tests complete!"
echo "Results saved to: $RESULTS_DIR/"
```

**Run it:**
```bash
chmod +x benchmarks/run_ablation_tests.sh
./benchmarks/run_ablation_tests.sh
```

---

## 🎯 Quick Baseline Identification Guide

### For Each Feature, Ask:

**Question:** What happens if I remove this feature?

**If RAGAS drops from 0.88 to 0.73 when you remove hybrid search:**
- Hybrid search contributes +15% (21% relative improvement)
- 0.73 is your BM25-only baseline

**If latency increases from 500ms to 1200ms without caching:**
- Caching reduces latency by 700ms (58% improvement)
- 1200ms is your no-cache baseline

**If success rate drops from 100% to 95% with single LLM:**
- Fallback strategy adds +5% reliability
- 95% is your single-LLM baseline

---

## 📝 Honest Resume Writing Formula

```
"[Action] achieving [Your Score] vs [Baseline Score] ([Improvement])"
```

**Examples:**

✅ **Good (Honest):**
> "Implemented hybrid search achieving **0.88 RAGAS** vs **0.73 BM25-only baseline** (+21%)"

✅ **Good (Specific):**
> "Optimized top-k retrieval to 5 chunks, improving context recall from **0.85** (top-3 baseline) to **0.925** (+8.8%)"

❌ **Bad (No baseline):**
> "Achieved 0.88 RAGAS score" (compared to what?)

❌ **Bad (Vague):**
> "Significantly improved RAG performance" (how much?)

---

## 🔍 Verification: How to Validate Your Baselines

### Rule 1: Baseline Must Be Runnable
You should be able to reproduce the baseline score:

```bash
# Anyone should be able to run this and get ~0.73
python run_benchmark.py --use-hybrid false
```

### Rule 2: Baseline Must Be Realistic
Don't compare to a strawman:

❌ **Bad baseline:** "Random ranking" (RAGAS 0.10)
✅ **Good baseline:** "BM25-only search" (RAGAS 0.73)

### Rule 3: Baseline Must Be Fair
Compare similar systems:

❌ **Bad:** Compare your 5-chunk hybrid to 1-chunk BM25
✅ **Good:** Compare your 5-chunk hybrid to 5-chunk BM25

---

## 🎓 Interview Talking Points

### Question: "What was your baseline?"

**Weak Answer:**
> "I compared to some other systems online."

**Strong Answer:**
> "I established baselines through ablation testing. For hybrid search, I ran benchmarks with BM25-only (no embeddings), which scored 0.73 RAGAS. My hybrid implementation achieved 0.88, a 21% improvement. I also tested different top-k values (3, 5, 7, 10) and found 5 was optimal. Each baseline is reproducible - anyone can run the same benchmarks with features disabled to verify my improvements."

**Shows:**
- ✅ Scientific methodology
- ✅ Reproducible results
- ✅ Systematic optimization
- ✅ Honest comparison

---

## 📊 Example Ablation Results Table

After running all tests, create a comparison:

| Configuration | RAGAS | MRR | Hit@5 | Latency | Notes |
|---------------|-------|-----|-------|---------|-------|
| **Full System** | **0.88** | **1.0** | **100%** | **1.2s** | Production config |
| BM25-only (no hybrid) | 0.73 | 0.85 | 92% | 0.9s | Baseline 1 |
| Top-3 chunks | 0.83 | 0.95 | 98% | 1.0s | Baseline 2 |
| GPT-3.5 single | 0.70 | 0.95 | 98% | 0.8s | Baseline 3 |
| No caching | 0.88 | 1.0 | 100% | 3.5s | Baseline 4 |

**Insights:**
- Hybrid search: +21% RAGAS (0.88 vs 0.73)
- Top-5 chunks: +6% RAGAS (0.88 vs 0.83)
- 4-tier LLM: +26% RAGAS (0.88 vs 0.70)
- Redis cache: -66% latency (1.2s vs 3.5s)

---

## 🚨 Common Mistakes to Avoid

### Mistake 1: No Baseline
❌ "I achieved 0.88 RAGAS score"
✅ "I achieved 0.88 RAGAS, improving 21% from 0.73 BM25-only baseline"

### Mistake 2: Unrealistic Baseline
❌ "Improved from random retrieval (RAGAS 0.1)"
✅ "Improved from BM25-only search (RAGAS 0.73)"

### Mistake 3: Unfair Comparison
❌ "My hybrid top-5 (0.88) vs BM25 top-1 (0.45)"
✅ "My hybrid top-5 (0.88) vs BM25 top-5 (0.73)"

### Mistake 4: Can't Reproduce
❌ "I think the baseline was around 0.6 or something"
✅ "Baseline: 0.73 (run with --use-hybrid false, results in ablation_results/)"

---

## 🎯 Action Items

**To establish your baselines:**

1. **Run BM25-only test** (30 mins)
   ```bash
   python run_benchmark.py --use-hybrid false
   ```

2. **Run top-k variations** (1 hour)
   ```bash
   for k in 3 5 7 10; do
     python run_benchmark.py --top-k $k
   done
   ```

3. **Document results** (15 mins)
   - Save JSON outputs
   - Create comparison table
   - Calculate improvement percentages

4. **Update resume** (15 mins)
   - Replace "achieved X" with "achieved X vs Y baseline"
   - Add improvement percentages
   - Make claims verifiable

---

## 💡 The Golden Rule

**Every improvement claim needs three things:**

1. **Your score:** 0.88 RAGAS
2. **Baseline score:** 0.73 RAGAS (BM25-only)
3. **How to reproduce:** `python run_benchmark.py --use-hybrid false`

**If you can't provide all three, don't claim the improvement.**

---

**Now go establish those baselines! 🚀**
