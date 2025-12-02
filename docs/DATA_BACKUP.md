# Data Backup & Restore Guide

## Where is Data Stored?

### PostgreSQL (Primary Data Storage)
- **Location**: Docker volume `postgres_data`
- **Contains**:
  - Paper metadata (title, authors, abstract, arxiv_id, etc.)
  - Parsed PDF content in `raw_text` field
  - Chunks for RAG pipeline
- **Tables**: `papers`, `chunks`

### OpenSearch (Search Indexes)
- **Location**: Docker volume `opensearch_data`
- **Contains**:
  - Full-text search index: `arxiv-papers`
  - Vector embeddings index: `arxiv-papers-chunks` (with Jina AI embeddings)
- **Can be recreated**: Yes, by re-running the DAG indexing task from PostgreSQL data

## Quick Backup

```bash
# Run the backup script
./backup_data.sh

# This creates a timestamped backup in ./backups/YYYYMMDD_HHMMSS/
```

## What Gets Backed Up?

1. **PostgreSQL dump** (`postgres_backup.sql`) - All paper data and chunks
2. **OpenSearch documents** (`opensearch_papers.json`, `opensearch_chunks.json`) - Search data
3. **OpenSearch mappings** (`papers_mapping.json`, `chunks_mapping.json`) - Index schemas

## Restore from Backup

```bash
# Restore PostgreSQL data
./restore_data.sh ./backups/20251128_185500

# Re-index to OpenSearch (run from Airflow UI or trigger manually)
docker exec -i rag-airflow airflow dags trigger arxiv_paper_ingestion --conf '{"skip_fetch": true}'
```

## Manual Backup (PostgreSQL only)

```bash
# Backup
docker exec rag-postgres pg_dump -U rag_user -d rag_db > my_backup.sql

# Restore
docker exec -i rag-postgres psql -U rag_user -d rag_db < my_backup.sql
```

## Important Notes

- **PostgreSQL is the source of truth** - Always backup this first
- **OpenSearch can be rebuilt** - Re-run the indexing task from the DAG
- **Docker volumes persist** - Data survives container restarts (but not `docker compose down -v`)
- **.env is NOT in git** - Backup your `.env` file separately if needed
- **Backups are local** - Consider copying to cloud storage for production use

## Current Configuration (Week 4 Stable)

- `process_pdfs=False` in `airflow/dags/arxiv_ingestion/fetching.py`
- Using abstracts as `raw_text` substitute
- Airflow memory: 8GB (compose.yml)
- Max results: 3 papers (`.env`)