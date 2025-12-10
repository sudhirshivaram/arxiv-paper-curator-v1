"""
SEC EDGAR API Client

This client fetches financial documents from the SEC's EDGAR system.

Key Features:
- Company lookup by ticker symbol
- Fetch 10-K and 10-Q filings
- Download filing content
- Automatic rate limiting (10 requests/second as required by SEC)

SEC EDGAR Documentation: https://www.sec.gov/edgar/sec-api-documentation
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SECEdgarClient:
    """
    Client for accessing SEC EDGAR filings.

    The SEC requires:
    1. User-Agent header identifying who you are
    2. Rate limit: Maximum 10 requests per second

    Example:
        client = SECEdgarClient(user_agent="MyApp contact@example.com")
        filings = await client.fetch_10k_filings("AAPL", count=5)
    """

    # SEC EDGAR API endpoints
    BASE_URL = "https://www.sec.gov"
    COMPANY_SEARCH_URL = f"{BASE_URL}/cgi-bin/browse-edgar"

    # SEC requires identifying yourself
    DEFAULT_USER_AGENT = "arXiv-Paper-Curator financial.curator@example.com"

    def __init__(
        self,
        user_agent: Optional[str] = None,
        rate_limit_per_second: int = 10
    ):
        """
        Initialize the SEC EDGAR client.

        Args:
            user_agent: Your identification (email). SEC requires this!
            rate_limit_per_second: Max requests per second (SEC limit is 10)
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.rate_limit_per_second = rate_limit_per_second

        # Calculate delay between requests to stay under rate limit
        # Example: 10 req/sec = 0.1 seconds between requests
        self._request_delay = 1.0 / rate_limit_per_second
        self._last_request_time = 0.0

        # HTTP client with proper headers
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/json",
            },
            timeout=30.0,
            follow_redirects=True
        )

        logger.info(f"SEC EDGAR client initialized with user agent: {self.user_agent}")

    async def _rate_limit(self):
        """
        Enforce rate limiting.

        WHY: SEC requires max 10 requests/second
        HOW: Wait if needed before making next request
        """
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._request_delay:
            # Need to wait before next request
            wait_time = self._request_delay - time_since_last_request
            await asyncio.sleep(wait_time)

        self._last_request_time = asyncio.get_event_loop().time()

    async def lookup_company(self, ticker: str) -> Optional[Dict[str, str]]:
        """
        Look up company information by ticker symbol.

        Args:
            ticker: Stock ticker (e.g., "AAPL", "MSFT")

        Returns:
            Dict with:
            - ticker: Stock ticker
            - cik: SEC Central Index Key (unique company ID)
            - company_name: Official company name

        Example:
            info = await client.lookup_company("AAPL")
            # Returns: {
            #   "ticker": "AAPL",
            #   "cik": "0000320193",
            #   "company_name": "Apple Inc."
            # }
        """
        await self._rate_limit()

        ticker = ticker.upper().strip()
        logger.info(f"Looking up company: {ticker}")

        try:
            # SEC provides a company tickers JSON file
            # This is the easiest way to map ticker → CIK
            url = f"{self.BASE_URL}/files/company_tickers.json"
            response = await self.client.get(url)
            response.raise_for_status()

            # Parse the JSON
            companies = response.json()

            # Search for our ticker
            for key, company_data in companies.items():
                if company_data.get("ticker") == ticker:
                    # Found it!
                    cik = str(company_data["cik_str"]).zfill(10)  # Pad to 10 digits

                    result = {
                        "ticker": ticker,
                        "cik": cik,
                        "company_name": company_data["title"]
                    }

                    logger.info(f"Found company: {result['company_name']} (CIK: {cik})")
                    return result

            logger.warning(f"Company not found: {ticker}")
            return None

        except Exception as e:
            logger.error(f"Error looking up company {ticker}: {e}")
            return None

    async def fetch_10k_filings(
        self,
        ticker: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent 10-K annual reports for a company.

        10-K = Annual report (filed once per year)
        Contains: Financial statements, risks, business description, etc.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            count: Number of recent filings to fetch (default: 5)

        Returns:
            List of filings with:
            - accession_number: Unique filing ID
            - filing_date: When it was filed
            - document_url: URL to download the filing
            - fiscal_year: Which year the report covers

        Example:
            filings = await client.fetch_10k_filings("AAPL", count=2)
            # Returns last 2 annual reports
        """
        return await self._fetch_filings(ticker, filing_type="10-K", count=count)

    async def fetch_10q_filings(
        self,
        ticker: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent 10-Q quarterly reports for a company.

        10-Q = Quarterly report (filed 4 times per year)
        Contains: Quarterly financial statements (less detail than 10-K)

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            count: Number of recent filings to fetch (default: 5)

        Returns:
            List of filings (same format as fetch_10k_filings)
        """
        return await self._fetch_filings(ticker, filing_type="10-Q", count=count)

    async def _fetch_filings(
        self,
        ticker: str,
        filing_type: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Internal method to fetch filings of any type.

        HOW IT WORKS:
        1. Look up company CIK from ticker
        2. Query SEC for recent filings of this type
        3. Parse HTML response to extract filing info
        4. Return structured data
        """
        # Step 1: Get company CIK
        company_info = await self.lookup_company(ticker)
        if not company_info:
            logger.error(f"Cannot fetch filings: Company {ticker} not found")
            return []

        cik = company_info["cik"]
        logger.info(f"Fetching {count} {filing_type} filings for {ticker} (CIK: {cik})")

        await self._rate_limit()

        try:
            # Step 2: Query SEC EDGAR for filings
            params = {
                "action": "getcompany",
                "CIK": cik,
                "type": filing_type,
                "dateb": "",  # Empty = get all dates
                "owner": "exclude",
                "count": str(count),
                "output": "atom"  # Get data in Atom XML format (easier to parse)
            }

            response = await self.client.get(
                self.COMPANY_SEARCH_URL,
                params=params
            )
            response.raise_for_status()

            # Step 3: Parse the response
            filings = self._parse_filings_response(
                response.text,
                filing_type,
                company_info
            )

            logger.info(f"Found {len(filings)} {filing_type} filings for {ticker}")
            return filings

        except Exception as e:
            logger.error(f"Error fetching {filing_type} filings for {ticker}: {e}")
            return []

    def _parse_filings_response(
        self,
        response_text: str,
        filing_type: str,
        company_info: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Parse SEC EDGAR Atom XML response into structured data.

        WHY: SEC returns data in XML format, we need Python dicts
        """
        filings = []

        try:
            # Parse XML using BeautifulSoup
            soup = BeautifulSoup(response_text, "xml")

            # Each filing is an <entry> in the XML
            entries = soup.find_all("entry")

            for entry in entries:
                # Extract filing information
                filing_date_str = entry.find("filing-date").text if entry.find("filing-date") else None
                accession_number = entry.find("accession-number").text if entry.find("accession-number") else None

                # Get the document URL
                # SEC provides a filing-href link to the main page
                filing_href = entry.find("filing-href").text if entry.find("filing-href") else None

                if not all([filing_date_str, accession_number, filing_href]):
                    continue

                # Parse filing date
                try:
                    filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
                except:
                    filing_date = None

                # Determine fiscal year from filing date
                fiscal_year = str(filing_date.year) if filing_date else None

                filing_info = {
                    "ticker": company_info["ticker"],
                    "cik": company_info["cik"],
                    "company_name": company_info["company_name"],
                    "document_type": filing_type,
                    "accession_number": accession_number.replace("-", ""),  # Remove dashes
                    "filing_date": filing_date,
                    "fiscal_year": fiscal_year,
                    "filing_url": filing_href,  # URL to filing details page
                    "source_url": filing_href
                }

                filings.append(filing_info)

            return filings

        except Exception as e:
            logger.error(f"Error parsing filings response: {e}")
            return []

    async def download_filing_content(self, filing_url: str) -> Optional[str]:
        """
        Download the actual text content of a filing.

        Args:
            filing_url: URL from fetch_10k_filings or fetch_10q_filings

        Returns:
            Full text content of the filing (can be 100+ pages)

        NOTE: This is a simplified version. Real filings can be complex
        with multiple documents, exhibits, etc. We'll enhance this in Phase 4.
        """
        await self._rate_limit()

        try:
            logger.info(f"Downloading filing from: {filing_url}")

            response = await self.client.get(filing_url)
            response.raise_for_status()

            # Parse the HTML page
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract text (simple version - removes HTML tags)
            text = soup.get_text(separator="\n", strip=True)

            logger.info(f"Downloaded filing content ({len(text)} characters)")
            return text

        except Exception as e:
            logger.error(f"Error downloading filing content: {e}")
            return None

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("SEC EDGAR client closed")

    async def __aenter__(self):
        """Context manager support."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        await self.close()
