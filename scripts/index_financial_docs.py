"""
Index Financial Documents into OpenSearch

This script demonstrates:
1. Creating the financial-docs-chunks index
2. Fetching unindexed documents from PostgreSQL
3. Chunking and embedding financial documents
4. Indexing into OpenSearch for hybrid search

Run: uv run python scripts/index_financial_docs.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.factory import make_database
from src.repositories.financial_document import FinancialDocumentRepository
from src.services.opensearch.financial_factory import make_financial_opensearch_client
from src.services.indexing.financial_factory import make_financial_indexing_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


def print_separator(char="=", length=70):
    """Print a separator line."""
    print(f"\n{char * length}")


async def setup_index():
    """Setup the financial-docs-chunks index."""
    print_separator()
    print("STEP 1: Setup OpenSearch Index")
    print_separator()

    client = make_financial_opensearch_client()

    # Check health
    print("\n🏥 Checking OpenSearch health...")
    if not client.health_check():
        print("❌ OpenSearch is not healthy!")
        return False

    print("✅ OpenSearch is healthy")

    # Setup indices
    print("\n📊 Setting up financial-docs-chunks index...")
    results = client.setup_indices(force=False)

    if results.get("financial_index"):
        print("✅ Created financial-docs-chunks index")
    else:
        print("ℹ️  Index already exists")

    if results.get("rrf_pipeline"):
        print("✅ Created RRF search pipeline")
    else:
        print("ℹ️  RRF pipeline already exists")

    # Get stats
    stats = client.get_index_stats()
    print(f"\n📈 Index Statistics:")
    print(f"   Index name: {stats['index_name']}")
    print(f"   Exists: {stats['exists']}")
    print(f"   Document count: {stats.get('document_count', 0)}")

    return True


async def index_documents():
    """Index unindexed financial documents."""
    print_separator()
    print("STEP 2: Index Financial Documents")
    print_separator()

    db = make_database()

    try:
        with db.get_session() as session:
            repo = FinancialDocumentRepository(session)

            # Get unindexed documents
            print("\n🔍 Fetching unindexed documents from database...")
            unindexed_docs = repo.get_unindexed_documents()

            if not unindexed_docs:
                print("ℹ️  No unindexed documents found!")
                return

            print(f"✅ Found {len(unindexed_docs)} unindexed documents:\n")

            for i, doc in enumerate(unindexed_docs, 1):
                print(f"   {i}. {doc.company_name} ({doc.ticker_symbol})")
                print(f"      Type: {doc.document_type}")
                print(f"      Filed: {doc.filing_date.strftime('%Y-%m-%d')}")
                print(f"      Size: {doc.document_size_kb} KB")
                print()

            # Create indexing service
            print("🔧 Creating indexing service...")
            service = make_financial_indexing_service()

            # Convert SQLAlchemy objects to dicts
            print("\n📦 Preparing documents for indexing...")
            documents = []
            for doc in unindexed_docs:
                documents.append({
                    "id": doc.id,
                    "ticker_symbol": doc.ticker_symbol,
                    "company_name": doc.company_name,
                    "cik": doc.cik,
                    "document_type": doc.document_type,
                    "fiscal_year": doc.fiscal_year,
                    "fiscal_period": doc.fiscal_period,
                    "filing_date": doc.filing_date,
                    "accession_number": doc.accession_number,
                    "full_text": doc.full_text,
                })

            # Index documents
            print("\n🚀 Starting indexing process...")
            print("   This will:")
            print("   1. Chunk each document (600 words, 100 overlap)")
            print("   2. Generate embeddings using Jina AI")
            print("   3. Index into OpenSearch")
            print()

            stats = await service.index_documents_batch(
                documents=documents,
                replace_existing=False
            )

            print_separator("=")
            print("✅ INDEXING COMPLETE!")
            print_separator("=")

            print(f"\n📊 Statistics:")
            print(f"   Documents processed: {stats['documents_processed']}")
            print(f"   Total chunks created: {stats['total_chunks_created']}")
            print(f"   Total chunks indexed: {stats['total_chunks_indexed']}")
            print(f"   Total embeddings generated: {stats['total_embeddings_generated']}")
            print(f"   Errors: {stats['total_errors']}")

            if stats['total_errors'] == 0:
                # Mark documents as indexed in database
                print("\n✅ Marking documents as indexed in database...")
                for doc in unindexed_docs:
                    # Calculate chunk count for this document
                    doc_stats = [d for d in documents if d["id"] == doc.id]
                    chunk_count = stats['total_chunks_created'] // len(documents)

                    repo.mark_as_indexed(
                        document_id=doc.id,
                        chunk_count=chunk_count
                    )

                print("✅ Database updated!")

    finally:
        db.teardown()


async def verify_indexing():
    """Verify that documents were indexed correctly."""
    print_separator()
    print("STEP 3: Verify Indexing")
    print_separator()

    client = make_financial_opensearch_client()
    db = make_database()

    try:
        # Check OpenSearch stats
        print("\n📊 OpenSearch Index Statistics:")
        stats = client.get_index_stats()
        print(f"   Total chunks: {stats.get('document_count', 0)}")
        print(f"   Size: {stats.get('size_in_bytes', 0) / 1024 / 1024:.2f} MB")

        # Check database stats
        print("\n💾 Database Statistics:")
        with db.get_session() as session:
            repo = FinancialDocumentRepository(session)
            db_stats = repo.get_stats()

            print(f"   Total documents: {db_stats['total_documents']}")
            print(f"   Indexed documents: {db_stats['indexed_documents']}")
            print(f"   Unindexed documents: {db_stats['total_documents'] - db_stats['indexed_documents']}")

            if db_stats['documents_by_type']:
                print(f"\n   By document type:")
                for doc_type, count in db_stats['documents_by_type'].items():
                    print(f"     - {doc_type}: {count}")

    finally:
        db.teardown()


async def main():
    """Run all steps."""
    print_separator("=")
    print("🧪 FINANCIAL DOCUMENTS INDEXING")
    print_separator("=")

    print("\nThis will:")
    print("  1. Create financial-docs-chunks OpenSearch index")
    print("  2. Fetch unindexed documents from PostgreSQL")
    print("  3. Chunk and embed documents (Jina AI)")
    print("  4. Index into OpenSearch for hybrid search")
    print()

    input("Press Enter to continue (or Ctrl+C to cancel)...")

    try:
        # Step 1: Setup index
        success = await setup_index()
        if not success:
            print("\n❌ Failed to setup index. Exiting.")
            return

        # Step 2: Index documents
        await index_documents()

        # Step 3: Verify
        await verify_indexing()

        print_separator("=")
        print("✅ ALL STEPS COMPLETED!")
        print_separator("=")

        print("\n💡 What we accomplished:")
        print("  1. ✅ Created financial-docs-chunks OpenSearch index")
        print("  2. ✅ Indexed financial documents with embeddings")
        print("  3. ✅ Ready for hybrid search (BM25 + vector)")
        print("  4. ✅ Database updated with indexing status")
        print()
        print("🎯 Next steps:")
        print("  - Phase 6: Update /ask endpoint to support financial docs")
        print("  - Phase 7: Create financial-specific RAG prompt")
        print("  - Phase 8: Add document type selector to UI")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Indexing cancelled by user")
    except Exception as e:
        print(f"\n❌ Indexing failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
