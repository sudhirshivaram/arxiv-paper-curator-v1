# 🚀 Quick Start - RAG Benchmarking

## Current Status: ⏳ Waiting for Railway Deployment

**Once deployment is done (~10 mins), run this:**

```bash
cd benchmarks

# Set your production URL and OpenAI key
export API_BASE_URL=https://arxiv-paper-curator-v1-production.up.railway.app/api/v1
export OPENAI_API_KEY=sk-your-key-here

# Copy sample dataset
cp sample_dataset.json evaluation_dataset.json

# Run benchmarks (takes ~5 mins)
python run_benchmark.py
```

**You'll get:**
- RAGAS score (0-1)
- MRR (Mean Reciprocal Rank)
- Hit Rate@5 (%)
- Average latency (ms)
- Cost per query ($)

**Use these REAL numbers in your resume!**

---

## Test if Deployment is Ready

```bash
bash test_production.sh
```

✅ **Working** = Returns search results
❌ **Still deploying** = Returns validation error

---

## Resume Bullet Template

**Once you have metrics:**

```
• Architected production RAG system achieving [YOUR_RAGAS] RAGAS
  score with [YOUR_HIT_RATE]% Hit Rate@5, indexing [YOUR_PAPERS]
  research papers at [YOUR_LATENCY]ms average latency using FastAPI,
  OpenSearch, and Jina-v3 embeddings deployed on Railway
```

---

## Keep Git Repos Synced

```bash
# Always push to both repos
git push sushiva main && git push origin main
```

---

That's it! More docs in README.md if you need them.
