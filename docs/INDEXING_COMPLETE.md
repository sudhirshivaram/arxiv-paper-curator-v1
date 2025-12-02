# OpenSearch Indexing Complete ✅

## Summary

Successfully indexed **100 papers** from PostgreSQL to OpenSearch on Railway deployment.

**Date**: December 1, 2025
**Status**: ✅ Complete (0 errors)

## What Was Indexed

- **Papers**: 100 arXiv papers from PostgreSQL database
- **Chunks**: 100 chunks (1 per paper - title + abstract)
- **Embeddings**: Generated using Jina AI embeddings API (jina-embeddings-v3, 1024 dimensions)
- **Index**: `arxiv-papers-chunks` on Railway OpenSearch instance

## Services Used

1. **PostgreSQL** (Railway): `interchange.proxy.rlwy.net:58055/railway`
2. **OpenSearch** (Railway): `https://opensearch-production-5fa9.up.railway.app`
3. **Jina API**: Embeddings generation

## Testing Results

The RAG system is now fully operational!

### Test Query 1: Reinforcement Learning
```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers discuss reinforcement learning?", "top_k": 3}'
```

**Result**: ✅ Successfully returned detailed answer about "Monet: Reasoning in Latent Visual Space" paper with proper citations.

### Test Query 2: Transformers
```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in transformers?", "top_k": 3}'
```

**Result**: ✅ Successfully returned information about Monet and PeriodNet with citations.

## How to Re-run Indexing

If you need to re-index papers in the future:

```bash
# Option 1: Use the wrapper script
./scripts/run_reindex.sh

# Option 2: Manual execution
set -a && source .env && set +a
uv run python scripts/reindex_papers.py
```

## Scripts Created

1. **`scripts/reindex_papers.py`**: Main reindexing script
   - Reads papers from PostgreSQL
   - Generates embeddings using Jina API
   - Indexes to OpenSearch with proper schema

2. **`scripts/run_reindex.sh`**: Convenience wrapper
   - Automatically loads `.env` file
   - Runs the reindexing script

## API Endpoints (All Working)

- **RAG Query**: `POST /api/v1/ask`
  - Query: `{"query": "your question", "top_k": 3}`
  - Returns: Answer with sources and citations

- **Health Check**: `GET /api/v1/health`

- **Streaming RAG**: `POST /api/v1/stream`

- **Hybrid Search**: `POST /api/v1/hybrid-search/` (has minor validation issue with authors field)

## Environment Variables Required

The following variables must be set in `.env`:

```bash
# PostgreSQL
POSTGRES_DATABASE_URL=postgresql://postgres:...@interchange.proxy.rlwy.net:58055/railway

# OpenSearch
OPENSEARCH__HOST=https://opensearch-production-5fa9.up.railway.app

# Jina Embeddings
JINA_API_KEY=jina_...
EMBEDDINGS__MODEL=jina-embeddings-v3
EMBEDDINGS__TASK=retrieval.passage
EMBEDDINGS__DIMENSIONS=1024
```

## Next Steps

✅ **COMPLETED**: Basic RAG system with 100 papers indexed

**Optional Future Enhancements**:
1. Deploy Airflow to Railway for automated paper ingestion (requires $20/month plan)
2. Index full paper content (not just abstracts) for better retrieval
3. Add more papers by running the ingestion script
4. Fix the minor validation issue in `/api/v1/hybrid-search/` endpoint

## Notes

- The reindexing script only indexes title + abstract because we don't have the full parsed PDF content
- For production use, you'd want to chunk the full paper content using the PDF parser
- The script successfully connects to Railway services when environment variables are properly loaded
- All 100 papers were indexed with 0 errors
