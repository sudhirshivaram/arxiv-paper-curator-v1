"""Factory for creating Financial OpenSearch client.

WHAT: Factory function for financial document OpenSearch client
WHY: Consistent initialization pattern across the codebase
WHERE: Used in scripts and services that need to index/search financial docs
"""

from functools import lru_cache
from typing import Optional

from src.config import Settings, get_settings

from .financial_client import FinancialOpenSearchClient


@lru_cache(maxsize=1)
def make_financial_opensearch_client(
    settings: Optional[Settings] = None
) -> FinancialOpenSearchClient:
    """Factory function to create cached Financial OpenSearch client.

    Uses lru_cache to maintain a singleton instance for efficiency.

    :param settings: Optional settings instance
    :returns: Cached FinancialOpenSearchClient instance
    """
    if settings is None:
        settings = get_settings()

    return FinancialOpenSearchClient(
        host=settings.opensearch.host,
        settings=settings
    )


def make_financial_opensearch_client_fresh(
    settings: Optional[Settings] = None,
    host: Optional[str] = None
) -> FinancialOpenSearchClient:
    """Factory function to create a fresh Financial OpenSearch client (not cached).

    Use this when you need a new client instance (e.g., for testing
    or when connection issues occur).

    :param settings: Optional settings instance
    :param host: Optional host override
    :returns: New FinancialOpenSearchClient instance
    """
    if settings is None:
        settings = get_settings()

    # Use provided host or settings host
    opensearch_host = host or settings.opensearch.host

    return FinancialOpenSearchClient(
        host=opensearch_host,
        settings=settings
    )
