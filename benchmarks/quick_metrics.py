#!/usr/bin/env python3
"""
Quick script to get your REAL metrics without needing all dependencies.
Just tells you what you have so you can write honest resume bullets.
"""

import os
import sys
from pathlib import Path

# Try to get database count
def get_paper_count():
    """Get actual paper count from database"""
    try:
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv

        load_dotenv()

        db_url = os.getenv('POSTGRES_DATABASE_URL')
        if not db_url:
            return None, "DATABASE_URL not set"

        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT COUNT(*) FROM papers'))
            count = result.scalar()

            # Get date range
            result = conn.execute(text(
                'SELECT MIN(published_date), MAX(published_date) FROM papers'
            ))
            dates = result.fetchone()

            return {
                'count': count,
                'date_range': f"{dates[0]} to {dates[1]}" if dates else None
            }, None

    except Exception as e:
        return None, str(e)

def main():
    print("🔍 Getting YOUR Real Metrics")
    print("=" * 60)

    # 1. Check papers in database
    print("\n📚 Checking PostgreSQL database...")
    papers_info, error = get_paper_count()

    if papers_info:
        paper_count = papers_info['count']
        date_range = papers_info['date_range']
        print(f"   ✓ Papers indexed: {paper_count:,}")
        print(f"   ✓ Date range: {date_range}")
    else:
        print(f"   ✗ Could not connect: {error}")
        print("   → Make sure .env has POSTGRES_DATABASE_URL set")
        paper_count = None

    # 2. Check if OpenSearch is running (simple check)
    print("\n📊 Checking OpenSearch...")
    try:
        import requests
        response = requests.get('http://localhost:9200/_cat/indices?format=json', timeout=5)
        if response.ok:
            indices = response.json()
            for idx in indices:
                if 'arxiv' in idx.get('index', ''):
                    print(f"   ✓ Index: {idx['index']}")
                    print(f"   ✓ Documents: {idx.get('docs.count', 'Unknown')}")
        else:
            print("   ✗ OpenSearch not responding")
    except Exception as e:
        print(f"   ✗ Could not connect: {e}")
        print("   → Make sure OpenSearch is running on port 9200")

    # 3. Print honest resume bullets
    print("\n" + "=" * 60)
    print("✅ HONEST RESUME BULLETS")
    print("=" * 60)

    if paper_count:
        print(f"""
📝 Option 1 (With Your Actual Numbers):
• Built hybrid RAG system indexing {paper_count:,} research papers with
  hybrid BM25 + semantic search using FastAPI, OpenSearch, and Jina-v3
  embeddings (1024-dim)

📝 Option 2 (Focus on Engineering Quality):
• Developed production-ready RAG system for {paper_count:,} research papers
  achieving comprehensive evaluation through RAGAS benchmarking framework,
  measuring faithfulness, answer relevancy, MRR, and Hit Rate@k

📝 Option 3 (After Running Benchmarks):
• Architected RAG pipeline indexing {paper_count:,} papers achieving
  [RAGAS_SCORE] evaluation score with [HIT_RATE]% Hit Rate@5 and
  [LATENCY]ms average latency through optimized hybrid retrieval
""")
    else:
        print("""
📝 Option 1 (No Numbers Yet - Focus on Architecture):
• Architected production-grade RAG system implementing hybrid BM25 +
  semantic search with 4-tier LLM fallback (Gemini → Claude → GPT),
  comprehensive RAGAS benchmarking, and Redis caching

📝 Option 2 (Focus on Methodology):
• Developed RAG evaluation framework measuring RAGAS scores (faithfulness,
  answer relevancy, context precision/recall), MRR, Hit Rate@k, latency
  percentiles, and cost metrics to drive data-driven optimization

📝 Option 3 (After Indexing Papers):
• Built hybrid search system combining lexical (BM25) and semantic
  retrieval using Jina-v3 embeddings with reciprocal rank fusion,
  achieving measurable quality improvements through systematic benchmarking
""")

    print("\n💡 Next Steps:")
    print("1. If you haven't indexed papers yet:")
    print("   → Index some papers first")
    print("   → Then run this script again")
    print("")
    print("2. Run benchmarks to get quality metrics:")
    print("   cd benchmarks")
    print("   python run_benchmark.py")
    print("")
    print("3. Use YOUR real numbers in resume bullets")
    print("   → No exaggeration needed!")
    print("")

    if paper_count:
        print(f"✨ You have {paper_count:,} papers indexed - that's real and verifiable!")
        print("   Focus on the engineering quality, not just the scale.")

if __name__ == "__main__":
    main()
