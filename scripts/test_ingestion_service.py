"""
Test script for Financial Document Ingestion Service.

This script demonstrates:
1. Ingesting a single company's 10-K filing
2. Ingesting multiple filing types
3. Bulk ingestion for multiple companies
4. Checking database for stored documents

Run: uv run python scripts/test_ingestion_service.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.sec.factory import make_sec_client
from src.services.financial.factory import make_financial_ingestion_service
from src.db.factory import make_database
from src.repositories.financial_document import FinancialDocumentRepository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


async def test_single_company_ingestion():
    """Test ingesting a single company's 10-K."""
    print("\n" + "="*70)
    print("TEST 1: Ingest Single Company (Apple 10-K)")
    print("="*70)

    sec_client = make_sec_client()
    db = make_database()

    try:
        with db.get_session() as session:
            service = make_financial_ingestion_service(sec_client, session)

            print("\n📥 Ingesting Apple's latest 10-K...")
            print("   This will:")
            print("   1. Fetch from SEC EDGAR")
            print("   2. Download content")
            print("   3. Save to PostgreSQL\n")

            result = await service.ingest_company(
                ticker="AAPL",
                filing_types=["10-K"],
                count=1
            )

            print(f"\n✅ Ingestion Complete!")
            print(f"   Company: {result['company_name']}")
            print(f"   Ticker: {result['ticker']}")
            print(f"   Processed: {result['filings_processed']}")
            print(f"   Skipped: {result['filings_skipped']}")
            print(f"   Failed: {result['filings_failed']}")
            print(f"   Documents stored: {len(result['documents'])}")

            if result['documents']:
                print(f"\n   Document IDs:")
                for doc_id in result['documents']:
                    print(f"     - {doc_id}")

    finally:
        await sec_client.close()
        db.teardown()


async def test_multiple_filing_types():
    """Test ingesting both 10-K and 10-Q for a company."""
    print("\n" + "="*70)
    print("TEST 2: Ingest Multiple Filing Types (Microsoft 10-K + 10-Q)")
    print("="*70)

    sec_client = make_sec_client()
    db = make_database()

    try:
        with db.get_session() as session:
            service = make_financial_ingestion_service(sec_client, session)

            print("\n📥 Ingesting Microsoft's filings...")
            print("   - 1 10-K (annual report)")
            print("   - 2 10-Q (quarterly reports)\n")

            result = await service.ingest_company(
                ticker="MSFT",
                filing_types=["10-K", "10-Q"],
                count=1  # 1 of each type
            )

            print(f"\n✅ Ingestion Complete!")
            print(f"   Company: {result['company_name']}")
            print(f"   Total documents: {len(result['documents'])}")
            print(f"   Processed: {result['filings_processed']}")
            print(f"   Skipped: {result['filings_skipped']}")

    finally:
        await sec_client.close()
        db.teardown()


async def test_bulk_ingestion():
    """Test bulk ingestion for multiple companies."""
    print("\n" + "="*70)
    print("TEST 3: Bulk Ingest Multiple Companies")
    print("="*70)

    sec_client = make_sec_client()
    db = make_database()

    try:
        with db.get_session() as session:
            service = make_financial_ingestion_service(sec_client, session)

            companies = ["GOOGL", "TSLA", "NVDA"]

            print(f"\n📥 Bulk ingesting {len(companies)} companies...")
            print(f"   Companies: {', '.join(companies)}")
            print(f"   Filing types: 10-K")
            print(f"   Count: 1 per company\n")

            result = await service.bulk_ingest(
                tickers=companies,
                filing_types=["10-K"],
                count_per_ticker=1
            )

            print(f"\n✅ Bulk Ingestion Complete!")
            print(f"   Total companies: {result['total_companies']}")
            print(f"   Total documents: {result['total_documents']}")
            print(f"   Processed: {result['total_processed']}")
            print(f"   Skipped: {result['total_skipped']}")
            print(f"   Failed: {result['total_failed']}\n")

            print("   Per-company results:")
            for company_result in result['results']:
                print(f"     - {company_result['ticker']}: "
                      f"{len(company_result['documents'])} docs")

    finally:
        await sec_client.close()
        db.teardown()


async def check_database_contents():
    """Check what's stored in the database."""
    print("\n" + "="*70)
    print("TEST 4: Check Database Contents")
    print("="*70)

    db = make_database()

    try:
        with db.get_session() as session:
            repo = FinancialDocumentRepository(session)

            # Get statistics
            stats = repo.get_stats()

            print(f"\n📊 Database Statistics:")
            print(f"   Total documents: {stats['total_documents']}")
            print(f"   Parsed documents: {stats['parsed_documents']}")
            print(f"   Indexed documents: {stats['indexed_documents']}")
            print(f"   Unique companies: {stats['unique_companies']}")

            if stats['documents_by_type']:
                print(f"\n   Documents by type:")
                for doc_type, count in stats['documents_by_type'].items():
                    print(f"     - {doc_type}: {count}")

            # Get all documents
            all_docs = repo.get_all(limit=50)

            if all_docs:
                print(f"\n📄 Recent Documents (showing first {min(len(all_docs), 10)}):")
                for i, doc in enumerate(all_docs[:10], 1):
                    print(f"\n   {i}. {doc.company_name} ({doc.ticker_symbol})")
                    print(f"      Type: {doc.document_type}")
                    print(f"      Filed: {doc.filing_date.strftime('%Y-%m-%d')}")
                    print(f"      Size: {doc.document_size_kb:,} KB")
                    print(f"      Accession: {doc.accession_number}")
                    print(f"      Parsed: {'Yes' if doc.content_parsed else 'No'}")
                    print(f"      Indexed: {'Yes' if doc.indexed_in_opensearch else 'No'}")

    finally:
        db.teardown()


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 FINANCIAL DOCUMENT INGESTION SERVICE TESTS")
    print("="*70)
    print("\nThis will:")
    print("  1. Fetch real filings from SEC.gov")
    print("  2. Store them in your Railway PostgreSQL database")
    print("  3. Show what's been stored\n")

    input("Press Enter to continue (or Ctrl+C to cancel)...")

    try:
        # Run tests
        await test_single_company_ingestion()
        await test_multiple_filing_types()
        await test_bulk_ingestion()
        await check_database_contents()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        print("\n💡 What we accomplished:")
        print("  1. ✅ Fetched real 10-K/10-Q filings from SEC")
        print("  2. ✅ Stored them in PostgreSQL (Railway)")
        print("  3. ✅ Tracked processing status")
        print("  4. ✅ Ready for indexing in OpenSearch (Phase 5)")
        print()
        print("🎯 Next step: Phase 5 - Index documents in OpenSearch")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
