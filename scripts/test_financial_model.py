"""
Test script to verify FinancialDocument model and table creation.

This script:
1. Imports the FinancialDocument model
2. Connects to the database
3. Creates the financial_documents table if it doesn't exist
4. Verifies the table structure
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect
from src.db.factory import make_database
from src.models import Paper, FinancialDocument

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test financial document model and database setup"""

    logger.info("🔍 Testing FinancialDocument model...")

    # 1. Verify imports
    logger.info(f"✅ Imported FinancialDocument: {FinancialDocument.__tablename__}")

    # 2. Initialize database (same way as main.py)
    db = make_database()
    logger.info(f"📊 Database initialized")

    # 4. Inspect tables
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    logger.info(f"\n📋 Existing tables in database:")
    for table in existing_tables:
        logger.info(f"  - {table}")

    # 5. Check if financial_documents table exists
    if "financial_documents" in existing_tables:
        logger.info("\n✅ SUCCESS: 'financial_documents' table exists!")

        # Show columns
        columns = inspector.get_columns("financial_documents")
        logger.info(f"\n📊 Table structure ({len(columns)} columns):")
        for col in columns:
            logger.info(f"  - {col['name']}: {col['type']}")

    else:
        logger.error("\n❌ FAILED: 'financial_documents' table was not created!")
        logger.info("This might happen if the model wasn't imported before Base.metadata.create_all()")
        sys.exit(1)

    # 6. Test creating a sample document (without committing)
    logger.info("\n🧪 Testing FinancialDocument instantiation...")
    from datetime import datetime

    test_doc = FinancialDocument(
        ticker_symbol="AAPL",
        company_name="Apple Inc.",
        document_type="10-K",
        fiscal_year="2024",
        fiscal_period="FY",
        filing_date=datetime(2024, 10, 31),
        source_url="https://sec.gov/test",
        accession_number="0000320193-24-000123"
    )

    logger.info(f"✅ Created test document: {test_doc}")
    logger.info(f"   Ticker: {test_doc.ticker_symbol}")
    logger.info(f"   Company: {test_doc.company_name}")
    logger.info(f"   Type: {test_doc.document_type}")

    # 7. Test repository
    logger.info("\n🧪 Testing FinancialDocumentRepository...")
    from src.repositories import FinancialDocumentRepository

    with db.get_session() as session:
        repo = FinancialDocumentRepository(session)
        count = repo.get_count()
        logger.info(f"✅ Repository initialized. Current document count: {count}")

        stats = repo.get_stats()
        logger.info(f"\n📊 Financial Documents Statistics:")
        for key, value in stats.items():
            logger.info(f"  - {key}: {value}")

    # Cleanup
    db.teardown()

    logger.info("\n🎉 All tests passed! FinancialDocument model is ready to use.")
    logger.info("\n💡 Next steps:")
    logger.info("  1. Build SEC EDGAR API client to fetch real 10-K filings")
    logger.info("  2. Create ingestion service to store documents")
    logger.info("  3. Index documents in OpenSearch")


if __name__ == "__main__":
    main()
