#!/usr/bin/env python3
"""
Simple script to ingest arXiv papers into Railway deployment.

This script:
1. Fetches papers from arXiv API
2. Downloads and parses PDFs
3. Chunks the content
4. Stores in PostgreSQL and OpenSearch

Usage:
    python scripts/ingest_papers.py --query "machine learning" --max-results 10
"""

import asyncio
import argparse
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.services.arxiv.client import ArxivClient
from src.services.pdf_parser.client import PDFParserClient
from src.services.indexing.text_chunker import TextChunker
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


async def ingest_papers(query: str, max_results: int = 10):
    """Fetch and ingest papers from arXiv."""

    # Initialize settings and services
    settings = get_settings()
    logger.info(f"Connecting to database: {settings.postgres_database_url[:30]}...")

    # Create database session
    engine = create_engine(settings.postgres_database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Initialize services
        arxiv_client = ArxivClient(settings.arxiv)
        pdf_parser = PDFParserClient(settings.pdf_parser)
        text_chunker = TextChunker(settings.chunking)
        embeddings_service = await make_embeddings_service()
        opensearch_client = make_opensearch_client()

        logger.info(f"Fetching papers with query: '{query}', max_results: {max_results}")

        # Fetch papers from arXiv
        papers_data = arxiv_client.search(
            query=query,
            max_results=max_results,
            sort_by="relevance"
        )

        logger.info(f"Found {len(papers_data)} papers")

        papers_processed = 0

        for paper_data in papers_data:
            try:
                arxiv_id = paper_data.get("arxiv_id")
                logger.info(f"Processing paper: {arxiv_id}")

                # Check if paper already exists
                existing = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
                if existing:
                    logger.info(f"Paper {arxiv_id} already exists, skipping")
                    continue

                # Download and parse PDF
                pdf_path = arxiv_client.download_pdf(paper_data)
                logger.info(f"Downloaded PDF to: {pdf_path}")

                # Parse PDF
                parsed_content = pdf_parser.parse_pdf(str(pdf_path))
                logger.info(f"Parsed {len(parsed_content.get('sections', []))} sections")

                # Create paper object
                paper = Paper(
                    arxiv_id=arxiv_id,
                    title=paper_data.get("title"),
                    authors=paper_data.get("authors", []),
                    abstract=paper_data.get("abstract"),
                    categories=paper_data.get("categories", []),
                    published_date=paper_data.get("published"),
                    pdf_url=paper_data.get("pdf_url"),
                    entry_id=paper_data.get("entry_id"),
                    updated_date=paper_data.get("updated"),
                    comment=paper_data.get("comment"),
                    journal_ref=paper_data.get("journal_ref"),
                    doi=paper_data.get("doi"),
                    primary_category=paper_data.get("primary_category"),
                )

                # Save to database
                db.add(paper)
                db.commit()
                db.refresh(paper)
                logger.info(f"Saved paper to database with ID: {paper.id}")

                # Chunk the content
                chunks = text_chunker.chunk_sections(
                    sections=parsed_content.get("sections", []),
                    metadata={
                        "arxiv_id": arxiv_id,
                        "title": paper_data.get("title"),
                        "authors": paper_data.get("authors", []),
                    }
                )
                logger.info(f"Created {len(chunks)} chunks")

                # Generate embeddings and index to OpenSearch
                for chunk in chunks:
                    # Generate embedding
                    embedding = await embeddings_service.embed_query(chunk["chunk_text"])

                    # Index to OpenSearch
                    opensearch_client.index_chunk(
                        arxiv_id=arxiv_id,
                        chunk_text=chunk["chunk_text"],
                        chunk_index=chunk["chunk_index"],
                        section_title=chunk.get("section_title", ""),
                        embedding=embedding,
                        metadata={
                            "paper_id": paper.id,
                            "title": paper_data.get("title"),
                            "authors": paper_data.get("authors", []),
                            "abstract": paper_data.get("abstract"),
                            "categories": paper_data.get("categories", []),
                        }
                    )

                logger.info(f"✅ Successfully processed paper: {arxiv_id}")
                papers_processed += 1

            except Exception as e:
                logger.error(f"Error processing paper {paper_data.get('arxiv_id')}: {e}")
                continue

        logger.info(f"\n🎉 Ingestion complete! Processed {papers_processed}/{len(papers_data)} papers")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest arXiv papers into Railway deployment")
    parser.add_argument(
        "--query",
        type=str,
        default="machine learning",
        help="Search query for arXiv papers"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of papers to fetch"
    )

    args = parser.parse_args()

    # Run async ingestion
    asyncio.run(ingest_papers(args.query, args.max_results))


if __name__ == "__main__":
    main()
