"""
Factory for creating SEC EDGAR client instances.

WHY: Follows the factory pattern used throughout the project
WHERE: Used in main.py and scripts to get a configured SEC client
"""

from src.services.sec.client import SECEdgarClient


def make_sec_client(user_agent: str = None) -> SECEdgarClient:
    """
    Create a SEC EDGAR API client.

    Args:
        user_agent: Optional custom user agent. If not provided,
                   uses default identification.

    Returns:
        Configured SECEdgarClient instance

    Example:
        client = make_sec_client()
        filings = await client.fetch_10k_filings("AAPL", count=5)
    """
    return SECEdgarClient(user_agent=user_agent)
