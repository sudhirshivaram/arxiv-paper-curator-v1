"""OpenSearch client for financial documents (hybrid search).

WHAT: Client for indexing and searching financial document chunks
WHY: Separate client for financial docs with specific field mappings
WHERE: Used by financial indexing service and API endpoints
"""

import logging
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch
from src.config import Settings

from .financial_index_config import (
    FINANCIAL_DOCS_CHUNKS_MAPPING,
    FINANCIAL_HYBRID_RRF_PIPELINE,
)

logger = logging.getLogger(__name__)


class FinancialOpenSearchClient:
    """OpenSearch client for financial documents with hybrid search support."""

    def __init__(self, host: str, settings: Settings):
        self.host = host
        self.settings = settings
        self.index_name = "financial-docs-chunks"

        self.client = OpenSearch(
            hosts=[host],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )

        logger.info(f"Financial OpenSearch client initialized with host: {host}")

    def health_check(self) -> bool:
        """Check if OpenSearch cluster is healthy."""
        try:
            health = self.client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics for the financial docs index."""
        try:
            if not self.client.indices.exists(index=self.index_name):
                return {
                    "index_name": self.index_name,
                    "exists": False,
                    "document_count": 0
                }

            stats_response = self.client.indices.stats(index=self.index_name)
            index_stats = stats_response["indices"][self.index_name]["total"]

            return {
                "index_name": self.index_name,
                "exists": True,
                "document_count": index_stats["docs"]["count"],
                "deleted_count": index_stats["docs"]["deleted"],
                "size_in_bytes": index_stats["store"]["size_in_bytes"],
            }

        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                "index_name": self.index_name,
                "exists": False,
                "document_count": 0,
                "error": str(e)
            }

    def setup_indices(self, force: bool = False) -> Dict[str, bool]:
        """Setup the financial docs index and RRF pipeline."""
        results = {}
        results["financial_index"] = self._create_index(force)
        results["rrf_pipeline"] = self._create_rrf_pipeline(force)
        return results

    def _create_index(self, force: bool = False) -> bool:
        """Create financial docs index for hybrid search.

        :param force: If True, recreate index even if it exists
        :returns: True if created, False if already exists
        """
        try:
            if force and self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted existing financial index: {self.index_name}")

            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(
                    index=self.index_name,
                    body=FINANCIAL_DOCS_CHUNKS_MAPPING
                )
                logger.info(f"Created financial index: {self.index_name}")
                return True

            logger.info(f"Financial index already exists: {self.index_name}")
            return False

        except Exception as e:
            logger.error(f"Error creating financial index: {e}")
            raise

    def _create_rrf_pipeline(self, force: bool = False) -> bool:
        """Create RRF search pipeline for native hybrid search.

        Note: This is shared with arXiv, so it might already exist.

        :param force: If True, recreate pipeline even if it exists
        :returns: True if created, False if already exists
        """
        try:
            pipeline_id = FINANCIAL_HYBRID_RRF_PIPELINE["id"]

            if force:
                try:
                    self.client.ingest.get_pipeline(id=pipeline_id)
                    self.client.ingest.delete_pipeline(id=pipeline_id)
                    logger.info(f"Deleted existing RRF pipeline: {pipeline_id}")
                except Exception:
                    pass

            try:
                self.client.ingest.get_pipeline(id=pipeline_id)
                logger.info(f"RRF pipeline already exists: {pipeline_id}")
                return False
            except Exception:
                pass

            pipeline_body = {
                "description": FINANCIAL_HYBRID_RRF_PIPELINE["description"],
                "phase_results_processors": FINANCIAL_HYBRID_RRF_PIPELINE["phase_results_processors"],
            }

            self.client.transport.perform_request(
                "PUT",
                f"/_search/pipeline/{pipeline_id}",
                body=pipeline_body
            )

            logger.info(f"Created RRF search pipeline: {pipeline_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating RRF pipeline: {e}")
            raise

    def index_chunk(self, chunk_data: Dict[str, Any], embedding: List[float]) -> bool:
        """Index a single chunk with its embedding.

        :param chunk_data: Chunk data dictionary
        :param embedding: Embedding vector
        :returns: True if successful
        """
        try:
            chunk_data["embedding"] = embedding

            response = self.client.index(
                index=self.index_name,
                body=chunk_data,
                refresh=True
            )

            return response["result"] in ["created", "updated"]

        except Exception as e:
            logger.error(f"Error indexing chunk: {e}")
            return False

    def bulk_index_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk index multiple chunks with embeddings.

        :param chunks: List of dicts with 'chunk_data' and 'embedding'
        :returns: Statistics
        """
        from opensearchpy import helpers

        try:
            actions = []
            for chunk in chunks:
                chunk_data = chunk["chunk_data"].copy()
                chunk_data["embedding"] = chunk["embedding"]

                action = {
                    "_index": self.index_name,
                    "_source": chunk_data
                }
                actions.append(action)

            success, failed = helpers.bulk(self.client, actions, refresh=True)

            logger.info(f"Bulk indexed {success} financial chunks, {len(failed)} failed")
            return {"success": success, "failed": len(failed)}

        except Exception as e:
            logger.error(f"Bulk financial chunk indexing error: {e}")
            raise

    def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a specific financial document.

        :param document_id: UUID of the financial document
        :returns: True if deletion was successful
        """
        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"document_id": document_id}}},
                refresh=True
            )

            deleted = response.get("deleted", 0)
            logger.info(f"Deleted {deleted} chunks for document {document_id}")
            return deleted > 0

        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific financial document.

        :param document_id: UUID of the financial document
        :returns: List of chunks sorted by chunk_index
        """
        try:
            search_body = {
                "query": {"term": {"document_id": document_id}},
                "size": 1000,
                "sort": [{"chunk_index": "asc"}],
                "_source": {"excludes": ["embedding"]},
            }

            response = self.client.search(index=self.index_name, body=search_body)

            chunks = []
            for hit in response["hits"]["hits"]:
                chunk = hit["_source"]
                chunk["chunk_id"] = hit["_id"]
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(f"Error getting chunks: {e}")
            return []

    def search_chunks_hybrid(
        self,
        query: str,
        query_embedding: List[float],
        size: int = 10,
        ticker: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> Dict[str, Any]:
        """Hybrid search combining BM25 and vector similarity using native RRF.

        :param query: Text query for search
        :param query_embedding: Query embedding vector
        :param size: Number of results to return
        :param ticker: Optional ticker filter (e.g., "AAPL")
        :param document_types: Optional document type filter (e.g., ["10-K"])
        :param min_score: Minimum score threshold
        :returns: Search results
        """
        try:
            # Build BM25 query
            bm25_query = {
                "bool": {
                    "should": [
                        {"match": {"chunk_text": {"query": query, "boost": 2.0}}},
                        {"match": {"company_name": {"query": query, "boost": 1.5}}},
                        {"match": {"section_title": {"query": query, "boost": 1.0}}},
                    ]
                }
            }

            # Add filters if provided
            filter_clause = []
            if ticker:
                filter_clause.append({"term": {"ticker_symbol": ticker.upper()}})
            if document_types:
                filter_clause.append({"terms": {"document_type": document_types}})

            if filter_clause:
                bm25_query["bool"]["filter"] = filter_clause

            # Build hybrid query (BM25 + vector)
            hybrid_query = {
                "hybrid": {
                    "queries": [
                        bm25_query,
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": size * 2
                                }
                            }
                        }
                    ]
                }
            }

            search_body = {
                "size": size,
                "query": hybrid_query,
                "_source": {"excludes": ["embedding"]},
                "highlight": {
                    "fields": {
                        "chunk_text": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }

            # Execute search with RRF pipeline
            response = self.client.search(
                index=self.index_name,
                body=search_body,
                params={"search_pipeline": FINANCIAL_HYBRID_RRF_PIPELINE["id"]}
            )

            results = {"total": response["hits"]["total"]["value"], "hits": []}

            for hit in response["hits"]["hits"]:
                if hit["_score"] < min_score:
                    continue

                chunk = hit["_source"]
                chunk["score"] = hit["_score"]
                chunk["chunk_id"] = hit["_id"]

                if "highlight" in hit:
                    chunk["highlights"] = hit["highlight"]

                results["hits"].append(chunk)

            results["total"] = len(results["hits"])
            logger.info(
                f"Financial hybrid search for '{query[:50]}...' "
                f"returned {results['total']} results"
            )
            return results

        except Exception as e:
            logger.error(f"Financial hybrid search error: {e}")
            return {"total": 0, "hits": []}

    def search_chunks_bm25(
        self,
        query: str,
        size: int = 10,
        ticker: Optional[str] = None,
        document_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Pure BM25 keyword search.

        :param query: Text query for search
        :param size: Number of results to return
        :param ticker: Optional ticker filter
        :param document_types: Optional document type filter
        :returns: Search results
        """
        try:
            # Build query
            query_body = {
                "bool": {
                    "should": [
                        {"match": {"chunk_text": {"query": query, "boost": 2.0}}},
                        {"match": {"company_name": {"query": query, "boost": 1.5}}},
                        {"match": {"section_title": {"query": query, "boost": 1.0}}},
                    ]
                }
            }

            # Add filters
            filter_clause = []
            if ticker:
                filter_clause.append({"term": {"ticker_symbol": ticker.upper()}})
            if document_types:
                filter_clause.append({"terms": {"document_type": document_types}})

            if filter_clause:
                query_body["bool"]["filter"] = filter_clause

            search_body = {
                "size": size,
                "query": query_body,
                "_source": {"excludes": ["embedding"]},
                "highlight": {
                    "fields": {
                        "chunk_text": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }

            response = self.client.search(index=self.index_name, body=search_body)

            results = {"total": response["hits"]["total"]["value"], "hits": []}

            for hit in response["hits"]["hits"]:
                chunk = hit["_source"]
                chunk["score"] = hit["_score"]
                chunk["chunk_id"] = hit["_id"]

                if "highlight" in hit:
                    chunk["highlights"] = hit["highlight"]

                results["hits"].append(chunk)

            logger.info(
                f"Financial BM25 search for '{query[:50]}...' "
                f"returned {results['total']} results"
            )
            return results

        except Exception as e:
            logger.error(f"Financial BM25 search error: {e}")
            return {"total": 0, "hits": []}
