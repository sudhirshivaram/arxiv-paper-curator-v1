# Implementation Plan: Adding Financial Documents to arXiv Paper Curator

**Goal**: Extend the RAG system to support both arXiv papers AND financial documents with a unified interface.

---

## 🎯 Architecture Overview

### Dual-Index Design

```
User Interface
    │
    ├─→ Document Type Selector: [arXiv | Financial]
    │
    ▼
FastAPI Backend (/api/v1/ask + document_type parameter)
    │
    ├─→ Index Router
    │   ├─→ arxiv-papers-chunks (existing)
    │   └─→ financial-docs-chunks (new)
    │
    ▼
Same RAG Pipeline (retrieval → generation)
    │
    ▼
OpenAI GPT-4o (with context-aware prompts)
```

**Key Principle**: Minimal code duplication. Same RAG logic, different data sources.

---

## 📋 Phase 1: Data Models (2-3 hours)

### Task 1.1: Create FinancialDocument Model

**File**: `src/models/financial_document.py`

```python
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from src.db.interfaces.postgresql import Base
import uuid

class FinancialDocument(Base):
    __tablename__ = "financial_documents"

    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cik = Column(String, index=True)  # SEC Central Index Key
    ticker_symbol = Column(String, index=True)  # Stock ticker
    company_name = Column(String, nullable=False)

    # Document metadata
    document_type = Column(String, nullable=False)  # "10-K", "10-Q", "8-K", "earnings"
    fiscal_year = Column(String)
    fiscal_period = Column(String)  # "Q1", "Q2", "Q3", "Q4", "FY"
    filing_date = Column(DateTime, nullable=False, index=True)

    # Content
    full_text = Column(Text, nullable=True)
    sections = Column(JSON, nullable=True)  # Parsed sections

    # Source
    source_url = Column(String, nullable=False)  # SEC EDGAR URL

    # Processing metadata
    pdf_processed = Column(Boolean, default=False)
    pdf_processing_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))
```

### Task 1.2: Create Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add financial_documents table"

# Apply migration
alembic upgrade head
```

---

## 📋 Phase 2: Data Ingestion (1 day)

### Task 2.1: SEC EDGAR API Client

**File**: `src/services/sec/client.py`

```python
import httpx
from typing import List, Optional
from datetime import datetime

class SECEdgarClient:
    """
    Client for SEC EDGAR API

    API Docs: https://www.sec.gov/edgar/sec-api-documentation
    Rate Limit: 10 requests/second (with User-Agent header)
    """

    BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "arXiv Paper Curator financial@example.com"
            }
        )

    async def fetch_10k_filings(
        self,
        ticker: str,
        count: int = 5
    ) -> List[dict]:
        """Fetch recent 10-K filings for a company"""
        # Implementation using SEC EDGAR API
        pass

    async def download_filing(self, filing_url: str) -> str:
        """Download filing text from SEC"""
        pass
```

### Task 2.2: Financial Document Ingestion Service

**File**: `src/services/financial/ingestion.py`

```python
from src.services.sec.client import SECEdgarClient
from src.services.pdf_parser.factory import make_pdf_parser_service
from src.repositories.financial_document import FinancialDocumentRepository

class FinancialDocumentIngestion:
    """Orchestrates financial document fetching and storage"""

    async def ingest_company_filings(
        self,
        ticker: str,
        filing_type: str = "10-K",
        count: int = 5
    ):
        """
        Fetch and store financial documents

        1. Fetch from SEC EDGAR
        2. Parse document
        3. Store in PostgreSQL
        4. Index in OpenSearch (financial-docs-chunks)
        """
        pass
```

---

## 📋 Phase 3: OpenSearch Index (2-3 hours)

### Task 3.1: Create Financial Documents Index

**File**: `src/services/opensearch/financial_index_config.py`

```python
FINANCIAL_INDEX_CONFIG = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "company_name": {"type": "text"},
            "ticker": {"type": "keyword"},
            "document_type": {"type": "keyword"},
            "fiscal_period": {"type": "keyword"},
            "filing_date": {"type": "date"},

            # Chunk content
            "chunk_text": {"type": "text"},
            "chunk_index": {"type": "integer"},

            # Vector embedding
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene"
                }
            }
        }
    }
}
```

### Task 3.2: Index Creation Script

```bash
# Create financial documents index
python scripts/create_financial_index.py
```

---

## 📋 Phase 4: API Updates (3-4 hours)

### Task 4.1: Update RAG Endpoint

**File**: `src/routers/ask.py`

```python
from enum import Enum

class DocumentType(str, Enum):
    ARXIV = "arxiv"
    FINANCIAL = "financial"

class AskRequest(BaseModel):
    query: str
    document_type: DocumentType = DocumentType.ARXIV  # Default to arXiv
    top_k: int = 3
    use_hybrid: bool = True

@router.post("/api/v1/ask")
async def ask_question(request: AskRequest):
    """
    RAG endpoint supporting both arXiv and financial documents
    """

    # Route to correct index based on document_type
    if request.document_type == DocumentType.ARXIV:
        index_name = "arxiv-papers-chunks"
        system_prompt = load_prompt("rag_system_arxiv.txt")
    else:
        index_name = "financial-docs-chunks"
        system_prompt = load_prompt("rag_system_financial.txt")

    # Same RAG logic, different index
    chunks = await search_service.hybrid_search(
        query=request.query,
        index_name=index_name,
        top_k=request.top_k
    )

    # Generate answer with context-aware prompt
    answer = await llm_service.generate(
        query=request.query,
        context=chunks,
        system_prompt=system_prompt
    )

    return {"answer": answer, "sources": chunks, "document_type": request.document_type}
```

### Task 4.2: Create Financial-Specific Prompt

**File**: `src/services/ollama/prompts/rag_system_financial.txt`

```
You are a financial analyst assistant helping users understand SEC filings and financial documents.

Your task is to answer questions about companies, earnings, financial performance, and regulatory filings based on the provided context.

Guidelines:
- Focus on financial metrics, risks, and business performance
- Cite specific sections (Item 1A Risk Factors, Item 7 MD&A, etc.)
- Include fiscal periods and dates when relevant
- Be precise with numbers and financial data
- Note when information is from specific quarters or fiscal years

Always cite your sources with company name, document type, and filing date.

Context:
{context}

User Question: {question}

Answer (max 300 words):
```

---

## 📋 Phase 5: UI Updates (2-3 hours)

### Task 5.1: Update Streamlit UI

**File**: `streamlit_app.py`

```python
# Add document type selector
document_type = st.radio(
    "Select Document Type:",
    options=["arXiv Papers", "Financial Documents"],
    horizontal=True
)

# Map to API enum
doc_type_map = {
    "arXiv Papers": "arxiv",
    "Financial Documents": "financial"
}

# Update API call
response = requests.post(
    f"{API_URL}/api/v1/ask",
    json={
        "query": user_query,
        "document_type": doc_type_map[document_type],
        "top_k": top_k,
        "use_hybrid": use_hybrid
    }
)
```

### Task 5.2: Update UI Labels

```python
if document_type == "Financial Documents":
    st.markdown("### 💼 Financial Document Search")
    st.caption("Search SEC 10-K filings, earnings reports, and financial disclosures")
else:
    st.markdown("### 📚 arXiv Paper Search")
    st.caption("Search academic research papers from arXiv")
```

---

## 📋 Phase 6: Testing & Validation (1 day)

### Task 6.1: Test Data Ingestion

```python
# Ingest 10 sample companies
companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "INTC", "AMD"]

for ticker in companies:
    await ingest_service.ingest_company_filings(
        ticker=ticker,
        filing_type="10-K",
        count=1  # Latest 10-K only
    )
```

### Task 6.2: Test RAG Pipeline

```bash
# Test arXiv (should work as before)
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is reinforcement learning?",
    "document_type": "arxiv",
    "top_k": 3
  }'

# Test Financial (new functionality)
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are Apple'\''s main risk factors?",
    "document_type": "financial",
    "top_k": 3
  }'
```

---

## 📊 Storage Impact

**Current (arXiv only):**
- 100 papers, ~100 chunks
- Storage: ~5MB

**After adding Financial:**
- 100 papers + 10 companies (1 10-K each)
- arXiv: 100 chunks (~5MB)
- Financial: ~1,000 chunks (~50MB)
- **Total: ~55MB** (still well within free tier!)

---

## 🚀 Deployment

### Railway Deployment (No changes needed!)

1. Push code to GitHub
2. Railway auto-deploys
3. Run migration: `alembic upgrade head`
4. Ingest financial docs: `python scripts/ingest_financial.py`

**Environment Variables** (add to Railway):
```bash
# No new variables needed! Uses same infrastructure:
- POSTGRES_DATABASE_URL (existing)
- OPENSEARCH__HOST (existing)
- JINA_API_KEY (existing)
- OPENAI_API_KEY (existing)
```

---

## ✅ Success Criteria

- [ ] Users can toggle between arXiv and Financial document types
- [ ] Financial documents indexed in OpenSearch
- [ ] RAG pipeline works for both document types
- [ ] UI shows appropriate labels for each type
- [ ] Railway deployment working with both indices
- [ ] Documentation updated

---

## 📈 Future Enhancements

1. **More document types**:
   - 10-Q (quarterly reports)
   - 8-K (current reports)
   - Earnings call transcripts
   - Analyst reports

2. **Advanced filtering**:
   - Filter by company/ticker
   - Filter by fiscal period
   - Filter by filing date range

3. **Financial-specific features**:
   - Compare companies side-by-side
   - Track metrics over time
   - Financial ratios calculation

---

## 🎯 Timeline

| Phase | Tasks | Time | Status |
|-------|-------|------|--------|
| Phase 1 | Data models | 2-3 hours | Not started |
| Phase 2 | Data ingestion | 1 day | Not started |
| Phase 3 | OpenSearch index | 2-3 hours | Not started |
| Phase 4 | API updates | 3-4 hours | Not started |
| Phase 5 | UI updates | 2-3 hours | Not started |
| Phase 6 | Testing | 1 day | Not started |
| **Total** | **Full implementation** | **3-4 days** | **0% complete** |

---

**Ready to start?** Let's begin with Phase 1: Creating the FinancialDocument model!
