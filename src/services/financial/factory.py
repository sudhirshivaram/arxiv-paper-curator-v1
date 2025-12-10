"""
Factory for creating financial document ingestion service.

WHY: Follows the factory pattern used throughout the project
WHERE: Used in scripts and main app to get configured service
"""

from sqlalchemy.orm import Session
from src.services.sec.client import SECEdgarClient
from src.services.financial.ingestion import FinancialDocumentIngestionService


def make_financial_ingestion_service(
    sec_client: SECEdgarClient,
    db_session: Session
) -> FinancialDocumentIngestionService:
    """
    Create a financial document ingestion service.

    Args:
        sec_client: SEC EDGAR API client (for fetching)
        db_session: Database session (for storing)

    Returns:
        Configured FinancialDocumentIngestionService instance

    Example:
        from src.services.sec.factory import make_sec_client
        from src.db.factory import make_database

        sec_client = make_sec_client()
        db = make_database()

        with db.get_session() as session:
            service = make_financial_ingestion_service(sec_client, session)
            await service.ingest_company("AAPL", ["10-K"], count=1)
    """
    return FinancialDocumentIngestionService(
        sec_client=sec_client,
        db_session=db_session
    )
