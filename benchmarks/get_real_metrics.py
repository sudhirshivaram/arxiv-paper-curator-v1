"""
Get REAL metrics from your RAG system for resume/portfolio.

This script queries your actual system to get honest numbers:
- Number of papers indexed
- Number of chunks/documents
- Average query performance
- Storage size
- etc.

NO EXAGGERATION - only real data!
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.opensearch.client import OpenSearchClient
from src.db.factory import create_db_connection

load_dotenv()

# Import config
from src.config import get_settings

settings = get_settings()


async def get_real_metrics():
    """Get actual metrics from your system"""

    print("🔍 Gathering REAL metrics from your RAG system...")
    print("=" * 60)

    metrics = {}

    # 1. OpenSearch metrics (papers indexed)
    try:
        print("\n📊 Checking OpenSearch indices...")
        os_client = OpenSearchClient()

        # Get index stats - use actual index from config
        index_name = f"{settings.opensearch.index_name}-{settings.opensearch.chunk_index_suffix}"
        indices = [index_name]

        for index_name in indices:
            try:
                stats = os_client.client.count(index=index_name)
                count = stats.get("count", 0)
                print(f"   ✓ Index '{index_name}': {count:,} documents")
                metrics[f"{index_name}_count"] = count
            except Exception as e:
                print(f"   ✗ Could not query index '{index_name}': {e}")

        # Get index size
        try:
            index_stats = os_client.client.indices.stats(index=indices[0])
            size_bytes = index_stats['_all']['total']['store']['size_in_bytes']
            size_mb = size_bytes / (1024 * 1024)
            print(f"   ✓ Index size: {size_mb:.2f} MB")
            metrics["index_size_mb"] = size_mb
        except Exception as e:
            print(f"   ✗ Could not get index size: {e}")

    except Exception as e:
        print(f"   ✗ OpenSearch connection failed: {e}")
        print("   → Make sure OpenSearch is running")

    # 2. PostgreSQL metrics (papers metadata)
    try:
        print("\n📚 Checking PostgreSQL database...")
        db = create_db_connection()

        # Count papers in database
        with db.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM papers"))
            paper_count = result.scalar()
            print(f"   ✓ Papers in database: {paper_count:,}")
            metrics["papers_in_db"] = paper_count

            # Get date range
            result = conn.execute(text("""
                SELECT
                    MIN(published_date) as earliest,
                    MAX(published_date) as latest
                FROM papers
            """))
            row = result.fetchone()
            if row:
                print(f"   ✓ Date range: {row[0]} to {row[1]}")
                metrics["date_range"] = f"{row[0]} to {row[1]}"

    except Exception as e:
        print(f"   ✗ PostgreSQL connection failed: {e}")
        print("   → Make sure PostgreSQL is running")

    # 3. Test query performance
    try:
        print("\n⚡ Testing query performance...")
        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        async with httpx.AsyncClient(timeout=30.0) as client:
            import time

            test_queries = [
                "transformer architecture",
                "machine learning",
                "neural networks"
            ]

            latencies = []

            for query in test_queries:
                start = time.time()
                try:
                    response = await client.post(
                        f"{api_url}/hybrid-search/",
                        json={
                            "query": query,
                            "size": 5,
                            "use_hybrid": True,
                        }
                    )
                    latency = (time.time() - start) * 1000
                    latencies.append(latency)
                    print(f"   ✓ Query '{query[:30]}...': {latency:.0f}ms")
                except Exception as e:
                    print(f"   ✗ Query failed: {e}")

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                print(f"   ✓ Average latency: {avg_latency:.0f}ms")
                metrics["avg_latency_ms"] = avg_latency

    except Exception as e:
        print(f"   ✗ API test failed: {e}")
        print("   → Make sure your API is running: uvicorn src.main:app")

    # 4. Estimate query volume (if you have logs/analytics)
    try:
        print("\n📈 Checking usage analytics...")
        # TODO: If you have Langfuse or logging, query it here
        print("   → No analytics configured yet")
        print("   → Add tracking to measure real usage")
        metrics["daily_queries"] = "Not tracked yet"
    except Exception as e:
        pass

    # Print summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY - YOUR REAL METRICS")
    print("=" * 60)

    # Get the index count dynamically
    index_key = f"{settings.opensearch.index_name}-{settings.opensearch.chunk_index_suffix}_count"
    docs_count = metrics.get(index_key, 'Unknown')

    papers_count = metrics.get('papers_in_db', 'Unknown')
    size_mb = metrics.get('index_size_mb', 'Unknown')
    latency = metrics.get('avg_latency_ms', 'Unknown')

    print(f"""
Papers Indexed:        {papers_count if isinstance(papers_count, str) else f'{papers_count:,}'}
Documents in Search:   {docs_count if isinstance(docs_count, str) else f'{docs_count:,}'}
Index Size:            {size_mb if isinstance(size_mb, str) else f'{size_mb:.1f} MB'}
Average Latency:       {latency if isinstance(latency, str) else f'{latency:.0f} ms'}
Daily Queries:         {metrics.get('daily_queries', 'Unknown')}
""")

    # Save to file
    output_file = Path(__file__).parent / "real_metrics.json"
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    print(f"\n💾 Metrics saved to: {output_file}")

    # Generate honest resume bullets
    print("\n" + "=" * 60)
    print("✅ HONEST RESUME BULLETS (based on YOUR data)")
    print("=" * 60)

    papers = papers_count
    docs = docs_count
    latency_val = latency

    # Format for resume bullets
    papers_str = f"{papers:,}" if isinstance(papers, int) else "[YOUR_PAPER_COUNT]"
    docs_str = f"{docs:,}" if isinstance(docs, int) else "[YOUR_DOC_COUNT]"
    latency_str = f"{latency_val:.0f}" if isinstance(latency_val, (int, float)) else "[YOUR_LATENCY]"

    print(f"""
Option 1 (Conservative - Focus on Architecture):
• Developed production-ready RAG system implementing hybrid BM25 + semantic
  search with 4-tier LLM fallback, achieving comprehensive evaluation
  through RAGAS benchmarking framework

Option 2 (With Scale - if you have papers indexed):
• Built hybrid RAG system indexing {papers_str} research papers with
  {latency_str}ms average query latency using FastAPI, OpenSearch,
  and Jina-v3 embeddings (1024-dim)

Option 3 (Once you have benchmark results):
• Architected RAG pipeline achieving [RAGAS_SCORE] evaluation score with
  [HIT_RATE]% Hit Rate@5, indexing {papers_str} papers and serving queries
  at {latency_str}ms average latency

📝 After running benchmarks, fill in the [PLACEHOLDERS] with real numbers!
""")

    print("\n💡 Next Steps:")
    print("1. Run benchmarks: cd benchmarks && python run_benchmark.py")
    print("2. Get RAGAS, MRR, Hit Rate metrics")
    print("3. Update resume bullets with REAL benchmark results")
    print("4. Never exaggerate - let the real numbers speak!")

    return metrics


if __name__ == "__main__":
    # Need to import text for SQL query
    from sqlalchemy import text

    asyncio.run(get_real_metrics())
