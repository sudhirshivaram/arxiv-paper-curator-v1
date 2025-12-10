"""OpenSearch index configuration for financial documents (hybrid search).

This configuration supports both keyword search (BM25) and vector similarity search
for financial documents (10-K, 10-Q filings).

WHAT: Index structure for financial document chunks with embeddings
WHY: Enable hybrid search over SEC filings (keyword + semantic)
WHERE: Used by OpenSearch client when creating financial-docs-chunks index
"""

FINANCIAL_DOCS_CHUNKS_INDEX = "financial-docs-chunks"

# Index mapping for chunked financial documents with vector embeddings
FINANCIAL_DOCS_CHUNKS_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.knn": True,  # Enable k-NN search
        "index.knn.space_type": "cosinesimil",  # Cosine similarity for embeddings
        "analysis": {
            "analyzer": {
                "standard_analyzer": {"type": "standard", "stopwords": "_english_"},
                "text_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                },
            }
        },
    },
    "mappings": {
        "dynamic": "strict",  # Prevent accidental field creation
        "properties": {
            # Chunk identification
            "chunk_id": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
            "chunk_text": {
                "type": "text",
                "analyzer": "text_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "chunk_word_count": {"type": "integer"},
            "start_char": {"type": "integer"},
            "end_char": {"type": "integer"},

            # Vector embedding
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,  # Jina v3 embeddings dimension
                "method": {
                    "name": "hnsw",  # Hierarchical Navigable Small World
                    "space_type": "cosinesimil",  # Cosine similarity
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 512,  # Higher = better recall, slower indexing
                        "m": 16,  # Number of bi-directional links
                    },
                },
            },

            # Financial document metadata (denormalized for search)
            "document_id": {"type": "keyword"},  # UUID in financial_documents table
            "ticker_symbol": {
                "type": "keyword",  # Exact match for ticker
                "fields": {
                    "text": {"type": "text", "analyzer": "standard_analyzer"}
                }
            },
            "company_name": {
                "type": "text",
                "analyzer": "text_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "cik": {"type": "keyword"},  # SEC Central Index Key
            "document_type": {"type": "keyword"},  # "10-K", "10-Q", etc.
            "fiscal_year": {"type": "keyword"},  # "2024", "2025", etc.
            "fiscal_period": {"type": "keyword"},  # "FY", "Q1", "Q2", "Q3", "Q4"
            "filing_date": {"type": "date"},
            "accession_number": {"type": "keyword"},  # SEC accession number

            # Section information (if available)
            "section_title": {"type": "keyword"},

            # Embedding metadata
            "embedding_model": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        },
    },
}

# We can reuse the same RRF pipeline from arXiv (it's index-agnostic)
# The pipeline is created once and works for any index
FINANCIAL_HYBRID_RRF_PIPELINE = {
    "id": "hybrid-rrf-pipeline",  # Shared with arXiv
    "description": "Post processor for hybrid RRF search",
    "phase_results_processors": [
        {
            "score-ranker-processor": {
                "combination": {
                    "technique": "rrf",  # Reciprocal Rank Fusion
                    "rank_constant": 60,  # Default k=60 for RRF formula: 1/(k+rank)
                }
            }
        }
    ],
}
