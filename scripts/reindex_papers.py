#!/usr/bin/env python3
"""
Re-index existing papers from PostgreSQL to OpenSearch.

This script:
1. Reads papers from PostgreSQL
2. Reads parsed content from backups (if available) or generates chunks
3. Generates embeddings
4. Indexes to OpenSearch

Usage:
    python scripts/reindex_papers.py
"""

import asyncio
import logging
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.services.embeddings.factory import make_embeddings_service
from src.services.opensearch.factory import make_opensearch_client
from src.models.paper import Paper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def reindex_papers():
    """Re-index all papers from PostgreSQL to OpenSearch."""

    # Initialize settings and services
    settings = get_settings()

    # Debug: Print settings
    logger.info(f"PostgreSQL URL: {settings.postgres_database_url[:50]}...")
    logger.info(f"OpenSearch Host: {settings.opensearch.host}")

    logger.info(f"Connecting to database...")

    # Create database session
    engine = create_engine(settings.postgres_database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Initialize services
        logger.info("Initializing embeddings service...")
        embeddings_service = make_embeddings_service()

        logger.info("Initializing OpenSearch client...")
        opensearch_client = make_opensearch_client()

        # Get all papers from database
        papers = db.query(Paper).all()
        logger.info(f"Found {len(papers)} papers in database")

        if not papers:
            logger.warning("No papers found in database!")
            return

        indexed_count = 0
        error_count = 0

        for i, paper in enumerate(papers, 1):
            try:
                logger.info(f"[{i}/{len(papers)}] Processing paper: {paper.arxiv_id}")

                # Create chunks from abstract (since we don't have the full content)
                # In a real scenario, you'd chunk the full paper content
                chunks = []

                # Chunk 1: Title + Abstract
                if paper.abstract:
                    chunk_text = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
                    chunks.append({
                        "chunk_text": chunk_text,
                        "chunk_index": 0,
                        "section_title": "Abstract"
                    })

                if not chunks:
                    logger.warning(f"No content available for {paper.arxiv_id}, skipping")
                    continue

                # Index each chunk
                for chunk in chunks:
                    try:
                        # Generate embedding
                        logger.info(f"  Generating embedding for chunk {chunk['chunk_index']}...")
                        embedding = await embeddings_service.embed_query(chunk["chunk_text"])

                        # Prepare chunk data for OpenSearch
                        chunk_data = {
                            "arxiv_id": paper.arxiv_id,
                            "chunk_text": chunk["chunk_text"],
                            "chunk_index": chunk["chunk_index"],
                            "section_title": chunk.get("section_title", ""),
                            "paper_id": paper.id,
                            "title": paper.title,
                            "authors": paper.authors or [],
                            "abstract": paper.abstract,
                            "categories": paper.categories or [],
                            "published_date": paper.published_date.isoformat() if paper.published_date else None,
                        }

                        # Index to OpenSearch
                        success = opensearch_client.index_chunk(
                            chunk_data=chunk_data,
                            embedding=embedding
                        )

                        if success:
                            logger.info(f"  ✅ Indexed chunk {chunk['chunk_index']}")
                        else:
                            logger.error(f"  ❌ Failed to index chunk {chunk['chunk_index']}")
                            error_count += 1

                    except Exception as e:
                        logger.error(f"  ❌ Error indexing chunk {chunk['chunk_index']}: {e}")
                        error_count += 1
                        continue

                indexed_count += 1
                logger.info(f"✅ Successfully indexed paper {i}/{len(papers)}: {paper.arxiv_id}")

            except Exception as e:
                logger.error(f"❌ Error processing paper {paper.arxiv_id}: {e}")
                error_count += 1
                continue

        logger.info(f"\n🎉 Indexing complete!")
        logger.info(f"  ✅ Successfully indexed: {indexed_count} papers")
        logger.info(f"  ❌ Errors: {error_count}")

        # Verify indexing
        logger.info("\nVerifying OpenSearch index...")
        try:
            health = opensearch_client.health_check()
            logger.info(f"OpenSearch health: {health}")
        except Exception as e:
            logger.error(f"Failed to check OpenSearch health: {e}")

    finally:
        db.close()
        logger.info("Database connection closed")


def main():
    logger.info("=" * 80)
    logger.info("Re-indexing papers from PostgreSQL to OpenSearch")
    logger.info("=" * 80)

    # Run async indexing
    asyncio.run(reindex_papers())

    logger.info("=" * 80)
    logger.info("Done!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
