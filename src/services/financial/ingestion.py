"""
Financial Document Ingestion Service

This service orchestrates fetching and storing financial documents.

Flow:
1. Fetch filings from SEC using SECEdgarClient
2. Parse filing content
3. Save to FinancialDocument table in PostgreSQL
4. Track processing status

Example:
    service = FinancialDocumentIngestionService(sec_client, db_session)
    await service.ingest_company("AAPL", filing_types=["10-K"], count=1)
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.services.sec.client import SECEdgarClient
from src.models.financial_document import FinancialDocument
from src.repositories.financial_document import FinancialDocumentRepository

logger = logging.getLogger(__name__)


class FinancialDocumentIngestionService:
    """
    Service for ingesting financial documents into the database.

    WHY: Connects SEC API client with database storage
    HOW: Fetch → Parse → Store → Track status
    WHERE USED: Scripts and eventual Airflow DAGs
    """

    def __init__(
        self,
        sec_client: SECEdgarClient,
        db_session: Session
    ):
        """
        Initialize the ingestion service.

        Args:
            sec_client: SEC EDGAR API client (for fetching)
            db_session: Database session (for storing)
        """
        self.sec_client = sec_client
        self.repository = FinancialDocumentRepository(db_session)

        logger.info("Financial document ingestion service initialized")

    async def ingest_company(
        self,
        ticker: str,
        filing_types: List[str] = ["10-K"],
        count: int = 1
    ) -> Dict[str, Any]:
        """
        Ingest financial documents for a company.

        This is the main public method users call.

        Args:
            ticker: Stock ticker (e.g., "AAPL", "MSFT")
            filing_types: Types of filings to fetch (e.g., ["10-K", "10-Q"])
            count: Number of each filing type to fetch

        Returns:
            Dict with:
            - ticker: Company ticker
            - company_name: Company name
            - filings_processed: Number of filings successfully stored
            - filings_skipped: Number already in database
            - filings_failed: Number that failed to process
            - documents: List of stored document IDs

        Example:
            result = await service.ingest_company("AAPL", ["10-K"], count=1)
            # Returns: {
            #   "ticker": "AAPL",
            #   "company_name": "Apple Inc.",
            #   "filings_processed": 1,
            #   "filings_skipped": 0,
            #   "filings_failed": 0,
            #   "documents": [UUID("...")]
            # }
        """
        logger.info(f"Starting ingestion for {ticker} - {filing_types} (count: {count})")

        # Track results
        result = {
            "ticker": ticker.upper(),
            "company_name": None,
            "filings_processed": 0,
            "filings_skipped": 0,
            "filings_failed": 0,
            "documents": []
        }

        try:
            # Process each filing type
            for filing_type in filing_types:
                filing_result = await self._ingest_filing_type(
                    ticker,
                    filing_type,
                    count
                )

                # Aggregate results
                if not result["company_name"] and filing_result.get("company_name"):
                    result["company_name"] = filing_result["company_name"]

                result["filings_processed"] += filing_result["filings_processed"]
                result["filings_skipped"] += filing_result["filings_skipped"]
                result["filings_failed"] += filing_result["filings_failed"]
                result["documents"].extend(filing_result["documents"])

            logger.info(
                f"Completed ingestion for {ticker}: "
                f"{result['filings_processed']} processed, "
                f"{result['filings_skipped']} skipped, "
                f"{result['filings_failed']} failed"
            )

            return result

        except Exception as e:
            logger.error(f"Error ingesting {ticker}: {e}")
            result["error"] = str(e)
            return result

    async def _ingest_filing_type(
        self,
        ticker: str,
        filing_type: str,
        count: int
    ) -> Dict[str, Any]:
        """
        Ingest filings of a specific type for a company.

        Internal method called by ingest_company().

        Args:
            ticker: Stock ticker
            filing_type: "10-K", "10-Q", "8-K", etc.
            count: Number of filings to fetch

        Returns:
            Dict with processing results
        """
        logger.info(f"Fetching {filing_type} filings for {ticker} (count: {count})")

        result = {
            "company_name": None,
            "filings_processed": 0,
            "filings_skipped": 0,
            "filings_failed": 0,
            "documents": []
        }

        try:
            # Step 1: Fetch filings from SEC
            if filing_type == "10-K":
                filings = await self.sec_client.fetch_10k_filings(ticker, count=count)
            elif filing_type == "10-Q":
                filings = await self.sec_client.fetch_10q_filings(ticker, count=count)
            else:
                logger.warning(f"Unsupported filing type: {filing_type}")
                return result

            if not filings:
                logger.warning(f"No {filing_type} filings found for {ticker}")
                return result

            result["company_name"] = filings[0]["company_name"]

            # Step 2: Process each filing
            for filing in filings[:count]:  # Limit to requested count
                filing_result = await self._process_filing(filing)

                if filing_result["status"] == "processed":
                    result["filings_processed"] += 1
                    result["documents"].append(filing_result["document_id"])
                elif filing_result["status"] == "skipped":
                    result["filings_skipped"] += 1
                elif filing_result["status"] == "failed":
                    result["filings_failed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error ingesting {filing_type} for {ticker}: {e}")
            result["error"] = str(e)
            return result

    async def _process_filing(self, filing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single filing: download content and save to database.

        Args:
            filing: Filing metadata from SEC client

        Returns:
            Dict with:
            - status: "processed", "skipped", or "failed"
            - document_id: UUID if processed
            - reason: Why skipped/failed
        """
        accession_number = filing["accession_number"]
        ticker = filing["ticker"]
        filing_type = filing["document_type"]

        logger.info(f"Processing {filing_type} for {ticker} - Accession: {accession_number}")

        try:
            # Step 1: Check if already exists
            existing_doc = self.repository.get_by_accession_number(accession_number)
            if existing_doc:
                logger.info(f"Filing already exists: {accession_number} - skipping")
                return {
                    "status": "skipped",
                    "document_id": existing_doc.id,
                    "reason": "already_exists"
                }

            # Step 2: Download filing content
            logger.info(f"Downloading content for {accession_number}...")
            content = await self.sec_client.download_filing_content(filing["filing_url"])

            if not content or len(content) < 100:
                # Content too short or empty
                logger.warning(f"Downloaded content too short for {accession_number}")
                return {
                    "status": "failed",
                    "reason": "content_too_short",
                    "content_length": len(content) if content else 0
                }

            # Step 3: Create document record
            document_data = {
                "ticker_symbol": ticker,
                "company_name": filing["company_name"],
                "cik": filing["cik"],
                "document_type": filing_type,
                "fiscal_year": filing.get("fiscal_year"),
                "fiscal_period": self._infer_fiscal_period(filing_type, filing["filing_date"]),
                "filing_date": filing["filing_date"],
                "accession_number": accession_number,
                "full_text": content,
                "source_url": filing["source_url"],
                "document_size_kb": len(content) // 1024,
                "content_parsed": True,  # We have the text
                "parsing_date": datetime.now(),
                "indexed_in_opensearch": False,  # Not yet indexed
                "chunk_count": 0  # Will be set during indexing
            }

            # Step 4: Save to database
            document = self.repository.create(document_data)

            logger.info(
                f"Successfully stored {filing_type} for {ticker} "
                f"(ID: {document.id}, Size: {document.document_size_kb}KB)"
            )

            return {
                "status": "processed",
                "document_id": document.id,
                "ticker": ticker,
                "filing_type": filing_type,
                "size_kb": document.document_size_kb
            }

        except Exception as e:
            logger.error(f"Error processing filing {accession_number}: {e}")
            return {
                "status": "failed",
                "reason": "exception",
                "error": str(e)
            }

    def _infer_fiscal_period(self, filing_type: str, filing_date: datetime) -> Optional[str]:
        """
        Infer fiscal period from filing type and date.

        10-K = Annual (FY)
        10-Q = Quarterly (Q1, Q2, Q3, Q4)

        Args:
            filing_type: "10-K" or "10-Q"
            filing_date: When the filing was submitted

        Returns:
            "FY" for 10-K, or "Q1"-"Q4" for 10-Q (estimated)
        """
        if filing_type == "10-K":
            return "FY"  # Full year

        elif filing_type == "10-Q":
            # Estimate quarter based on filing month
            # Most companies file: Q1(May), Q2(Aug), Q3(Nov), Q4(Feb)
            month = filing_date.month

            if month in [1, 2, 3]:  # Jan-Mar
                return "Q4"  # Previous year Q4
            elif month in [4, 5, 6]:  # Apr-Jun
                return "Q1"
            elif month in [7, 8, 9]:  # Jul-Sep
                return "Q2"
            else:  # Oct-Dec
                return "Q3"

        return None

    async def bulk_ingest(
        self,
        tickers: List[str],
        filing_types: List[str] = ["10-K"],
        count_per_ticker: int = 1
    ) -> Dict[str, Any]:
        """
        Ingest documents for multiple companies at once.

        WHY: Efficient batch processing
        HOW: Process companies sequentially (respecting rate limits)

        Args:
            tickers: List of stock tickers
            filing_types: Types of filings to fetch for each
            count_per_ticker: How many of each filing type per company

        Returns:
            Dict with:
            - total_companies: Number of companies processed
            - total_documents: Total documents stored
            - results: List of per-company results

        Example:
            result = await service.bulk_ingest(
                tickers=["AAPL", "MSFT", "GOOGL"],
                filing_types=["10-K"],
                count_per_ticker=1
            )
        """
        logger.info(
            f"Starting bulk ingestion for {len(tickers)} companies - "
            f"{filing_types} (count: {count_per_ticker})"
        )

        results = {
            "total_companies": len(tickers),
            "total_documents": 0,
            "total_processed": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "results": []
        }

        for ticker in tickers:
            logger.info(f"Processing {ticker}...")

            company_result = await self.ingest_company(
                ticker,
                filing_types=filing_types,
                count=count_per_ticker
            )

            results["total_documents"] += len(company_result["documents"])
            results["total_processed"] += company_result["filings_processed"]
            results["total_skipped"] += company_result["filings_skipped"]
            results["total_failed"] += company_result["filings_failed"]
            results["results"].append(company_result)

        logger.info(
            f"Bulk ingestion complete: {results['total_documents']} documents stored"
        )

        return results
