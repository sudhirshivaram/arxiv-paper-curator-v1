# Financial Documents Implementation Guide

**Purpose**: This guide explains WHAT we built, WHY we built it, and WHERE it fits in the architecture for adding financial documents to the RAG system.

---

## 📋 Table of Contents

1. [Overall Architecture](#overall-architecture)
2. [Phase 1: Database Models](#phase-1-database-models)
3. [Phase 2: Table Creation & Testing](#phase-2-table-creation--testing)
4. [Phase 3: SEC EDGAR API Client](#phase-3-sec-edgar-api-client-upcoming)
5. [Phase 4: Data Ingestion](#phase-4-data-ingestion-upcoming)
6. [Phase 5: OpenSearch Indexing](#phase-5-opensearch-indexing-upcoming)
7. [Phase 6: API & UI Updates](#phase-6-api--ui-updates-upcoming)

---

## Overall Architecture

### The Big Picture: What Are We Building?

We're **extending** the existing arXiv paper curator to also handle financial documents (like 10-K filings, earnings reports) **without breaking** the current system.

**Before (Current System):**
```
User → Streamlit UI → FastAPI → OpenSearch (arxiv-papers) → OpenAI → Answer
```

**After (Dual-Index System):**
```
User → Streamlit UI → [Select: arXiv or Financial]
              ↓
         FastAPI (routes to correct index)
              ↓
         ┌────────────────┬─────────────────┐
         ↓                ↓                 ↓
    arxiv-papers   financial-docs      Same RAG
    (existing)        (new)           Pipeline
         └────────────────┴─────────────────┘
                          ↓
                      OpenAI LLM
                          ↓
                       Answer
```

**Key Principle**: Same RAG logic, different data sources. User chooses which dataset to search.

---

## Phase 1: Database Models

**Status**: ✅ COMPLETED

### What We Built

We created two new Python files:

1. **[src/models/financial_document.py](../src/models/financial_document.py)** - Database model
2. **[src/repositories/financial_document.py](../src/repositories/financial_document.py)** - Database operations

### Why We Need This

**Problem**: The existing `Paper` model is designed for academic papers (arXiv):
```python
class Paper:
    arxiv_id       # Paper identifier (e.g., "2401.12345")
    title          # Paper title
    authors        # List of authors
    abstract       # Paper abstract
    categories     # ["cs.AI", "cs.LG"]
```

Financial documents are completely different:
```python
class FinancialDocument:
    ticker_symbol  # Stock ticker (e.g., "AAPL")
    company_name   # "Apple Inc."
    document_type  # "10-K", "10-Q", "earnings"
    fiscal_year    # "2024"
    fiscal_period  # "Q4", "FY"
```

**Solution**: Create a separate model for financial documents with appropriate fields.

### Where It Fits

```
Project Structure:

src/
├── models/
│   ├── paper.py                    ← Existing (arXiv papers)
│   └── financial_document.py       ← NEW (Financial docs)
│
├── repositories/
│   ├── paper.py                    ← Existing (arXiv queries)
│   └── financial_document.py       ← NEW (Financial queries)
```

### What Each File Does

#### 1. Model: `src/models/financial_document.py`

**What**: Defines the database table structure (blueprint)

**Why**: SQLAlchemy needs a Python class to create database tables

**Key Fields Explained**:
```python
class FinancialDocument(Base):
    __tablename__ = "financial_documents"  # Table name in PostgreSQL

    # Company Identification
    ticker_symbol = Column(String, index=True)
    # Why indexed: Fast lookup by ticker ("give me all AAPL filings")

    company_name = Column(String)
    # Why: Human-readable company name

    cik = Column(String, index=True)
    # What: SEC's Central Index Key (unique company ID)
    # Why: Official SEC identifier (more reliable than ticker)

    # Document Metadata
    document_type = Column(String, index=True)
    # What: "10-K" (annual), "10-Q" (quarterly), "8-K" (current events)
    # Why indexed: Fast filtering ("show me all 10-Ks")

    fiscal_year = Column(String)
    fiscal_period = Column(String)
    # What: "2024", "Q3"
    # Why: Track which period the filing covers

    filing_date = Column(DateTime, index=True)
    # Why indexed: Sort by date, filter by date range

    accession_number = Column(String, unique=True)
    # What: SEC's unique document identifier (e.g., "0000320193-24-000123")
    # Why unique: Prevents duplicate filings

    # Content Storage
    full_text = Column(Text, nullable=True)
    # What: Complete document text
    # Why nullable: Some docs might be too large

    sections = Column(JSON, nullable=True)
    # What: Structured sections (e.g., {"risk_factors": "...", "md_a": "..."})
    # Why JSON: Flexible structure for different doc types

    # Processing Status
    content_parsed = Column(Boolean, default=False)
    # What: Has the PDF been parsed yet?
    # Why: Track processing pipeline

    indexed_in_opensearch = Column(Boolean, default=False)
    # What: Has this doc been indexed for search?
    # Why: Track which docs are searchable

    chunk_count = Column(Integer, default=0)
    # What: How many chunks created from this doc?
    # Why: Understand document size, verify indexing
```

**Analogy**: Think of this like a spreadsheet template. Before you can enter data, you need to define the columns (ticker, company name, etc.). This model defines those columns.

#### 2. Repository: `src/repositories/financial_document.py`

**What**: Functions to interact with the database (CRUD operations)

**Why**: Instead of writing raw SQL queries everywhere, we use clean Python functions

**Key Methods Explained**:

```python
class FinancialDocumentRepository:

    def get_by_ticker(self, ticker: str) -> List[FinancialDocument]:
        """Get all documents for a company"""
        # WHY: When user asks "what are Apple's risks?", fetch all AAPL docs
        # WHERE USED: In the RAG pipeline to retrieve context

    def get_by_document_type(self, document_type: str):
        """Get all 10-Ks, or all 10-Qs"""
        # WHY: Filter by document type for specific analysis
        # WHERE USED: API endpoints, UI filters

    def get_unindexed_documents(self):
        """Find docs that need to be indexed in OpenSearch"""
        # WHY: After ingesting new docs, find which ones to index
        # WHERE USED: Indexing scripts (Phase 5)

    def mark_as_indexed(self, document_id, chunk_count):
        """Mark a doc as successfully indexed"""
        # WHY: Track processing status, avoid re-indexing
        # WHERE USED: After successful OpenSearch indexing

    def get_stats(self):
        """Get statistics (total docs, parsed, indexed, etc.)"""
        # WHY: Health dashboard, monitoring
        # WHERE USED: /health endpoint, admin UI
```

**Analogy**: If the Model is the spreadsheet template, the Repository is the set of tools to work with the spreadsheet (filter rows, add data, count entries, etc.).

---

## Phase 2: Table Creation & Testing

**Status**: ✅ COMPLETED

### What We Built

1. **Table Creation**: `financial_documents` table automatically created on Railway PostgreSQL
2. **Test Script**: [scripts/test_financial_model.py](../scripts/test_financial_model.py)

### Why We Need This

**Problem**: The model is just Python code. We need to actually create the table in the database.

**How It Works**:
```python
# In src/db/interfaces/postgresql.py (existing file):

def startup(self):
    # This line creates ALL tables defined in models/
    Base.metadata.create_all(bind=self.engine)
```

**What Happens**:
1. App starts (either locally or on Railway)
2. Code imports `FinancialDocument` model
3. SQLAlchemy sees: "Oh, there's a new model I haven't seen before"
4. Creates `financial_documents` table automatically
5. If table already exists, does nothing (safe to run multiple times)

### Where It Happens

```
Application Startup Flow:

src/main.py (line 38)
    ↓
make_database()
    ↓
PostgreSQLDatabase.startup() (line 55)
    ↓
Base.metadata.create_all()  ← Creates ALL tables from models/
    ↓
financial_documents table created ✅
```

### The Test Script Explained

**File**: `scripts/test_financial_model.py`

**What It Does**:
1. Connects to Railway database (same as production)
2. Lists all tables
3. Verifies `financial_documents` table exists
4. Shows table structure (21 columns)
5. Tests creating a sample document (without saving)
6. Tests repository methods

**Why We Need It**:
- Verify table was created correctly
- Test before production use
- Catch errors early

**Test Results** (from our run):
```
✅ financial_documents table exists!
✅ 21 columns created correctly
✅ Repository methods working
✅ Model instantiation successful
```

---

## Database Tables: Side-by-Side Comparison

### Current State of Railway Database

```
Railway PostgreSQL Database
├── papers                      ← Existing (arXiv papers)
│   ├── id, arxiv_id, title
│   ├── authors, abstract
│   ├── categories, published_date
│   └── (13 columns total)
│
└── financial_documents         ← NEW (Financial docs)
    ├── id, ticker_symbol, company_name
    ├── document_type, fiscal_year
    ├── filing_date, accession_number
    ├── full_text, sections
    ├── content_parsed, indexed_in_opensearch
    └── (21 columns total)
```

**Key Insight**: Both tables exist side-by-side. They don't interfere with each other.

---

## How Data Flows (Complete Picture)

### For arXiv Papers (Existing):
```
1. arXiv API → Papers
2. PDF Parsing → Papers.full_text
3. Chunking → OpenSearch (arxiv-papers-chunks)
4. User Query → Search arxiv-papers-chunks → RAG → Answer
```

### For Financial Documents (What We're Building):
```
1. SEC EDGAR API → FinancialDocuments         ← Phase 3 (Next!)
2. PDF Parsing → FinancialDocuments.full_text ← Phase 4
3. Chunking → OpenSearch (financial-docs-chunks) ← Phase 5
4. User Query → Search financial-docs-chunks → RAG → Answer ← Phase 6
```

**User Experience**:
```
User Interface:
┌────────────────────────────────────┐
│ Select Document Type:              │
│ ○ arXiv Papers                     │
│ ○ Financial Documents              │  ← User picks one
│                                    │
│ Question: What are Apple's risks?  │
│ [Ask Question]                     │
└────────────────────────────────────┘
         ↓
   Routes to correct index
         ↓
      Same RAG logic
         ↓
       Answer!
```

---

## Files Created So Far

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `src/models/financial_document.py` | Database model definition | ~80 lines |
| `src/repositories/financial_document.py` | Database query methods | ~200 lines |
| `scripts/test_financial_model.py` | Test & verification | ~100 lines |
| `IMPLEMENTATION_PLAN_FINANCIAL.md` | Overall roadmap | 600+ lines |

**Total Code**: ~380 lines (actual implementation)
**Total Docs**: ~600 lines (planning)

---

## Key Concepts Explained

### 1. Why Separate Tables?

**Option A** (Bad): Add columns to `papers` table
```python
# This would be messy:
class Paper:
    arxiv_id = Column(String)      # For papers
    ticker_symbol = Column(String) # For financial docs (?)
    # Which fields are used when? Confusing!
```

**Option B** (Good): Separate tables
```python
class Paper:
    arxiv_id = Column(String)      # Only for papers

class FinancialDocument:
    ticker_symbol = Column(String) # Only for financial docs
    # Clear separation of concerns!
```

### 2. Why Repository Pattern?

**Without Repository** (Bad):
```python
# Everywhere in the code:
from sqlalchemy import select
stmt = select(FinancialDocument).where(FinancialDocument.ticker == "AAPL")
results = session.execute(stmt).scalars().all()
# Repeat this SQL logic 50+ times across codebase
```

**With Repository** (Good):
```python
# Everywhere in the code:
repo = FinancialDocumentRepository(session)
results = repo.get_by_ticker("AAPL")
# Clean, reusable, testable!
```

### 3. Why Automatic Table Creation?

**Alternative** (Manual SQL):
```sql
-- Write and run manually:
CREATE TABLE financial_documents (
    id UUID PRIMARY KEY,
    ticker_symbol VARCHAR,
    ...
);
```

**Our Approach** (Automatic):
```python
# Just define the model, table is created automatically:
class FinancialDocument(Base):
    ticker_symbol = Column(String)
    # SQLAlchemy handles CREATE TABLE for us!
```

---

## What's Next?

### Phase 3: SEC EDGAR API Client (Upcoming)

**What**: Build a client to fetch 10-K filings from SEC.gov

**Why**: Need to get financial documents from somewhere!

**Where**: `src/services/sec/client.py` (new file)

**What It Will Do**:
```python
# Example usage:
client = SECEdgarClient()
filings = await client.fetch_10k_filings("AAPL", count=1)
# Returns: Latest Apple 10-K filing with URL and metadata
```

**Difficulty**: Medium (SEC API is well-documented)
**Time Estimate**: 2-3 hours

---

## Questions & Answers

### Q: Why not use Alembic migrations?

**A**: This project uses automatic table creation via `Base.metadata.create_all()`. For this use case, it's simpler and works well. Alembic is more for complex production systems with schema versioning needs.

### Q: Will this break the existing arXiv functionality?

**A**: No! The tables are completely separate. arXiv papers continue to work exactly as before.

### Q: What happens if I run the app twice?

**A**: `create_all()` is idempotent - if tables exist, it does nothing. Safe to run multiple times.

### Q: How do I see the table in Railway?

**A**:
1. Go to Railway dashboard
2. Click on PostgreSQL service
3. Click "Data" tab
4. You'll see `financial_documents` table alongside `papers`

### Q: Can I query both tables in one search?

**A**: Not in the current design. User picks one dataset at a time. This keeps queries fast and results focused.

---

## Summary: Progress So Far

**Completed**:
- ✅ Database model (what to store)
- ✅ Repository (how to query)
- ✅ Table created on Railway (where to store)
- ✅ Tests passing (verification)

**Total Progress**: 30% of full implementation

**Remaining**:
- ⏳ SEC API client (fetch docs)
- ⏳ Ingestion service (process docs)
- ⏳ OpenSearch index (search docs)
- ⏳ API updates (route queries)
- ⏳ UI updates (user selection)

---

## Visual Reference: The Stack

```
┌─────────────────────────────────────────┐
│           Streamlit UI                  │  Phase 6
│        (Document selector)              │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│           FastAPI Backend               │  Phase 6
│        (/ask with document_type)        │
└────────┬───────────────────┬────────────┘
         ↓                   ↓
┌────────────────┐  ┌────────────────────┐
│ arxiv-papers   │  │ financial-docs     │  Phase 5
│ (OpenSearch)   │  │ (OpenSearch)       │
└────────────────┘  └──────────┬─────────┘
                               ↓
                    ┌──────────────────────┐
                    │ FinancialDocuments   │  Phase 1 ✅
                    │ (PostgreSQL Table)   │  Phase 2 ✅
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ SEC EDGAR API        │  Phase 3 ⏳
                    │ (Data Source)        │
                    └──────────────────────┘
```

---

**Next Step**: Build the SEC EDGAR API client to fetch real 10-K filings!

**Estimated Time**: 2-3 hours
**Difficulty**: Medium
**Fun Factor**: High (real financial data!)
