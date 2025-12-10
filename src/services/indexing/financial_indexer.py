"""Financial Document Indexing Service

WHAT: Service for chunking and indexing financial documents into OpenSearch
WHY: Enable hybrid search (keyword + semantic) over SEC filings
WHERE: Used by indexing scripts and potentially Airflow DAGs

Flow:
1. Chunk financial document text (600 words per chunk, 100 overlap)
2. Generate embeddings for each chunk (Jina v3)
3. Index chunks with embeddings into financial-docs-chunks index
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.opensearch.financial_client import FinancialOpenSearchClient
from src.services.indexing.text_chunker import TextChunker

logger = logging.getLogger(__name__)


class FinancialDocumentIndexingService:
    """Service for indexing financial documents with chunking and embeddings.

    WHY: Orchestrates chunking → embedding → indexing pipeline for SEC filings
    HOW: Uses TextChunker + Jina + FinancialOpenSearchClient
    WHERE USED: Index scripts and data pipelines
    """

    def __init__(
        self,
        chunker: TextChunker,
        embeddings_client: JinaEmbeddingsClient,
        opensearch_client: FinancialOpenSearchClient
    ):
        """Initialize financial document indexing service.

        Args:
            chunker: Text chunking service
            embeddings_client: Jina embeddings client
            opensearch_client: Financial OpenSearch client
        """
        self.chunker = chunker
        self.embeddings_client = embeddings_client
        self.opensearch_client = opensearch_client

        logger.info("Financial document indexing service initialized")

    async def index_document(
        self,
        document_data: Dict
    ) -> Dict[str, int]:
        """Index a single financial document with chunking and embeddings.

        Args:
            document_data: Document data from FinancialDocument table

        Returns:
            Dictionary with indexing statistics:
            - chunks_created: Number of chunks created
            - chunks_indexed: Number successfully indexed
            - embeddings_generated: Number of embeddings created
            - errors: Number of errors
        """
        document_id = str(document_data.get("id", ""))
        ticker = document_data.get("ticker_symbol", "UNKNOWN")
        doc_type = document_data.get("document_type", "UNKNOWN")

        if not document_id:
            logger.error("Document missing ID")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 1
            }

        try:
            # Step 1: Chunk the document
            # For financial docs, we use simpler chunking (no sections yet)
            full_text = document_data.get("full_text", "")

            if not full_text or len(full_text.strip()) < 100:
                logger.warning(
                    f"Document {ticker} {doc_type} has insufficient text "
                    f"(length: {len(full_text)})"
                )
                return {
                    "chunks_created": 0,
                    "chunks_indexed": 0,
                    "embeddings_generated": 0,
                    "errors": 0
                }

            # Use document_id as both arxiv_id and paper_id for chunker
            # (The chunker expects these fields but we're using it for financial docs)
            chunks = self.chunker.chunk_text(
                text=full_text,
                arxiv_id=document_id,  # Reuse field for document_id
                paper_id=document_id
            )

            if not chunks:
                logger.warning(
                    f"No chunks created for {ticker} {doc_type}"
                )
                return {
                    "chunks_created": 0,
                    "chunks_indexed": 0,
                    "embeddings_generated": 0,
                    "errors": 0
                }

            logger.info(
                f"Created {len(chunks)} chunks for {ticker} {doc_type} "
                f"(Document ID: {document_id})"
            )

            # Step 2: Generate embeddings for chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self.embeddings_client.embed_passages(
                texts=chunk_texts,
                batch_size=50  # Process in batches
            )

            if len(embeddings) != len(chunks):
                logger.error(
                    f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}"
                )
                return {
                    "chunks_created": len(chunks),
                    "chunks_indexed": 0,
                    "embeddings_generated": len(embeddings),
                    "errors": 1
                }

            # Step 3: Prepare chunks with embeddings for indexing
            chunks_with_embeddings = []

            for chunk, embedding in zip(chunks, embeddings):
                # Prepare chunk data for OpenSearch
                chunk_data = {
                    "document_id": document_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "chunk_text": chunk.text,
                    "chunk_word_count": chunk.metadata.word_count,
                    "start_char": chunk.metadata.start_char,
                    "end_char": chunk.metadata.end_char,
                    "section_title": chunk.metadata.section_title,
                    "embedding_model": "jina-embeddings-v3",

                    # Denormalized document metadata for efficient search
                    "ticker_symbol": document_data.get("ticker_symbol", ""),
                    "company_name": document_data.get("company_name", ""),
                    "cik": document_data.get("cik", ""),
                    "document_type": document_data.get("document_type", ""),
                    "fiscal_year": document_data.get("fiscal_year"),
                    "fiscal_period": document_data.get("fiscal_period"),
                    "filing_date": document_data.get("filing_date"),
                    "accession_number": document_data.get("accession_number", ""),

                    # Timestamps
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }

                chunks_with_embeddings.append({
                    "chunk_data": chunk_data,
                    "embedding": embedding
                })

            # Step 4: Index chunks into OpenSearch
            results = self.opensearch_client.bulk_index_chunks(
                chunks_with_embeddings
            )

            logger.info(
                f"Indexed {ticker} {doc_type}: "
                f"{results['success']} chunks successful, "
                f"{results['failed']} failed"
            )

            return {
                "chunks_created": len(chunks),
                "chunks_indexed": results["success"],
                "embeddings_generated": len(embeddings),
                "errors": results["failed"]
            }

        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 1
            }

    async def index_documents_batch(
        self,
        documents: List[Dict],
        replace_existing: bool = False
    ) -> Dict[str, int]:
        """Index multiple financial documents in batch.

        Args:
            documents: List of document data from database
            replace_existing: If True, delete existing chunks before indexing

        Returns:
            Aggregated statistics
        """
        total_stats = {
            "documents_processed": 0,
            "total_chunks_created": 0,
            "total_chunks_indexed": 0,
            "total_embeddings_generated": 0,
            "total_errors": 0,
        }

        for document in documents:
            document_id = str(document.get("id", ""))

            # Optionally delete existing chunks
            if replace_existing and document_id:
                self.opensearch_client.delete_document_chunks(document_id)

            # Index the document
            stats = await self.index_document(document)

            # Update totals
            total_stats["documents_processed"] += 1
            total_stats["total_chunks_created"] += stats["chunks_created"]
            total_stats["total_chunks_indexed"] += stats["chunks_indexed"]
            total_stats["total_embeddings_generated"] += stats["embeddings_generated"]
            total_stats["total_errors"] += stats["errors"]

        logger.info(
            f"Batch indexing complete: "
            f"{total_stats['documents_processed']} documents, "
            f"{total_stats['total_chunks_indexed']} chunks indexed"
        )

        return total_stats

    async def reindex_document(
        self,
        document_id: str,
        document_data: Dict
    ) -> Dict[str, int]:
        """Reindex a document by deleting old chunks and creating new ones.

        Args:
            document_id: UUID of the financial document
            document_data: Updated document data

        Returns:
            Indexing statistics
        """
        # Delete existing chunks
        deleted = self.opensearch_client.delete_document_chunks(document_id)
        if deleted:
            logger.info(f"Deleted existing chunks for document {document_id}")

        # Index with new data
        return await self.index_document(document_data)
