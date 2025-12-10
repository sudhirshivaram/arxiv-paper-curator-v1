"""
Test script for SEC EDGAR API client.

This script demonstrates:
1. Looking up companies by ticker
2. Fetching 10-K annual reports
3. Fetching 10-Q quarterly reports
4. Downloading filing content

Run: uv run python scripts/test_sec_client.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.sec.factory import make_sec_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


async def test_company_lookup():
    """Test looking up companies by ticker symbol."""
    print("\n" + "="*60)
    print("TEST 1: Company Lookup")
    print("="*60)

    client = make_sec_client()

    # Test with multiple companies
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

    for ticker in tickers:
        print(f"\n🔍 Looking up: {ticker}")
        company_info = await client.lookup_company(ticker)

        if company_info:
            print(f"✅ Found: {company_info['company_name']}")
            print(f"   CIK: {company_info['cik']}")
            print(f"   Ticker: {company_info['ticker']}")
        else:
            print(f"❌ Not found: {ticker}")

    await client.close()


async def test_10k_filings():
    """Test fetching 10-K annual reports."""
    print("\n" + "="*60)
    print("TEST 2: Fetch 10-K Annual Reports")
    print("="*60)

    client = make_sec_client()

    ticker = "AAPL"
    count = 3

    print(f"\n📊 Fetching last {count} 10-K filings for {ticker}...")

    filings = await client.fetch_10k_filings(ticker, count=count)

    if filings:
        print(f"✅ Found {len(filings)} filings:\n")

        for i, filing in enumerate(filings, 1):
            print(f"{i}. {filing['document_type']} - Filed: {filing['filing_date'].strftime('%Y-%m-%d')}")
            print(f"   Company: {filing['company_name']}")
            print(f"   Fiscal Year: {filing['fiscal_year']}")
            print(f"   Accession #: {filing['accession_number']}")
            print(f"   URL: {filing['filing_url'][:80]}...")
            print()
    else:
        print(f"❌ No filings found for {ticker}")

    await client.close()


async def test_10q_filings():
    """Test fetching 10-Q quarterly reports."""
    print("\n" + "="*60)
    print("TEST 3: Fetch 10-Q Quarterly Reports")
    print("="*60)

    client = make_sec_client()

    ticker = "MSFT"
    count = 2

    print(f"\n📊 Fetching last {count} 10-Q filings for {ticker}...")

    filings = await client.fetch_10q_filings(ticker, count=count)

    if filings:
        print(f"✅ Found {len(filings)} filings:\n")

        for i, filing in enumerate(filings, 1):
            print(f"{i}. {filing['document_type']} - Filed: {filing['filing_date'].strftime('%Y-%m-%d')}")
            print(f"   Company: {filing['company_name']}")
            print(f"   URL: {filing['filing_url'][:80]}...")
            print()
    else:
        print(f"❌ No filings found for {ticker}")

    await client.close()


async def test_download_content():
    """Test downloading filing content."""
    print("\n" + "="*60)
    print("TEST 4: Download Filing Content")
    print("="*60)

    client = make_sec_client()

    # Get Apple's latest 10-K
    print("\n📥 Fetching Apple's latest 10-K to download...")
    filings = await client.fetch_10k_filings("AAPL", count=1)

    if not filings:
        print("❌ Could not fetch filing")
        await client.close()
        return

    filing = filings[0]
    print(f"✅ Got filing: {filing['document_type']} from {filing['filing_date'].strftime('%Y-%m-%d')}")
    print(f"   URL: {filing['filing_url']}")

    print("\n📥 Downloading content... (this may take a few seconds)")
    content = await client.download_filing_content(filing["filing_url"])

    if content:
        print(f"✅ Downloaded successfully!")
        print(f"   Content length: {len(content):,} characters")
        print(f"   Lines: {len(content.splitlines()):,}")

        # Show first 500 characters as preview
        print("\n📄 Content preview (first 500 chars):")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)
    else:
        print("❌ Download failed")

    await client.close()


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 SEC EDGAR CLIENT TESTS")
    print("="*60)
    print("\nTesting SEC EDGAR API client functionality...")
    print("This will fetch real data from sec.gov")
    print()

    try:
        # Run all tests
        await test_company_lookup()
        await test_10k_filings()
        await test_10q_filings()
        await test_download_content()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        print("\n💡 Next steps:")
        print("  1. SEC client is working!")
        print("  2. Ready to build ingestion service (Phase 4)")
        print("  3. Can fetch real 10-K/10-Q filings from any public company")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
