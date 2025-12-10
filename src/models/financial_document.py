import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from src.db.interfaces.postgresql import Base


class FinancialDocument(Base):
    """
    Model for financial documents (10-K, 10-Q, 8-K, earnings reports, etc.)

    Stores metadata and content from SEC EDGAR filings and other financial sources.
    """
    __tablename__ = "financial_documents"

    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company identification
    cik = Column(String, index=True, nullable=True)  # SEC Central Index Key (e.g., "0000320193" for Apple)
    ticker_symbol = Column(String, index=True, nullable=False)  # Stock ticker (e.g., "AAPL")
    company_name = Column(String, nullable=False)  # Full company name

    # Document metadata
    document_type = Column(String, nullable=False, index=True)  # "10-K", "10-Q", "8-K", "earnings", "proxy"
    fiscal_year = Column(String, nullable=True)  # e.g., "2024"
    fiscal_period = Column(String, nullable=True)  # "Q1", "Q2", "Q3", "Q4", "FY"
    filing_date = Column(DateTime, nullable=False, index=True)  # When the document was filed

    # Document identifiers
    accession_number = Column(String, unique=True, nullable=True, index=True)  # SEC accession number (unique per filing)

    # Content
    full_text = Column(Text, nullable=True)  # Full document text (for smaller docs)
    sections = Column(JSON, nullable=True)  # Parsed sections (e.g., {"risk_factors": "...", "md_a": "..."})

    # Source and metadata
    source_url = Column(String, nullable=False)  # URL to original filing (SEC EDGAR or other)
    document_size_kb = Column(Integer, nullable=True)  # Size of original document

    # Processing status
    content_parsed = Column(Boolean, default=False, nullable=False)
    parsing_date = Column(DateTime, nullable=True)
    parser_metadata = Column(JSON, nullable=True)  # Metadata from parsing process

    # Indexing status
    indexed_in_opensearch = Column(Boolean, default=False, nullable=False)
    indexing_date = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)  # Number of chunks created from this document

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<FinancialDocument(ticker={self.ticker_symbol}, type={self.document_type}, date={self.filing_date})>"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": str(self.id),
            "cik": self.cik,
            "ticker_symbol": self.ticker_symbol,
            "company_name": self.company_name,
            "document_type": self.document_type,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "accession_number": self.accession_number,
            "source_url": self.source_url,
            "document_size_kb": self.document_size_kb,
            "content_parsed": self.content_parsed,
            "indexed_in_opensearch": self.indexed_in_opensearch,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
