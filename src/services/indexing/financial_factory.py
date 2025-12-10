"""Factory for creating Financial Document Indexing Service.

WHAT: Factory function to create configured indexing service
WHY: Encapsulates dependency creation and wiring
WHERE: Used in scripts that need to index financial documents
"""

from src.services.embeddings.factory import make_embeddings_client
from src.services.opensearch.financial_factory import make_financial_opensearch_client
from src.services.indexing.text_chunker import TextChunker
from src.services.indexing.financial_indexer import FinancialDocumentIndexingService


def make_financial_indexing_service() -> FinancialDocumentIndexingService:
    """Create a fully configured financial document indexing service.

    Returns:
        Configured FinancialDocumentIndexingService instance with:
        - TextChunker (600 words, 100 overlap)
        - Jina embeddings client
        - Financial OpenSearch client

    Example:
        service = make_financial_indexing_service()
        stats = await service.index_document(document_data)
    """
    # Create chunker (reuse from arXiv - same chunking logic)
    chunker = TextChunker(
        chunk_size=600,      # 600 words per chunk
        overlap_size=100,    # 100 words overlap
        min_chunk_size=100   # Minimum 100 words
    )

    # Create embeddings client (shared with arXiv)
    embeddings_client = make_embeddings_client()

    # Create financial-specific OpenSearch client
    opensearch_client = make_financial_opensearch_client()

    # Wire them together
    return FinancialDocumentIndexingService(
        chunker=chunker,
        embeddings_client=embeddings_client,
        opensearch_client=opensearch_client
    )
