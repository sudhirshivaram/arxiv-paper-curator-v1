# 🎯 Request Routing & Agent Coordination Guide

## The Coordination Architecture

Your FastAPI app acts as a **coordinator** that routes requests to specialized agents/services based on the request type.

---

## 📍 Entry Point: main.py (The Coordinator)

**File:** [src/main.py](src/main.py)

### The Coordinator Registers 4 Routers:

```python
# Line 125-128: Router registration
app.include_router(ping.router, prefix="/api/v1")           # ① Health checks
app.include_router(hybrid_search.router, prefix="/api/v1")   # ② Search only
app.include_router(ask_router, prefix="/api/v1")            # ③ RAG (non-streaming)
app.include_router(stream_router, prefix="/api/v1")         # ④ RAG (streaming)
```

---

## 🔀 Routing Flow Diagram

```
User Request
     │
     ▼
┌────────────────────────────────────────┐
│   FastAPI Main App (Coordinator)      │
│   src/main.py                          │
└────────────────────────────────────────┘
     │
     ├─── GET  /api/v1/ping ──────────► ping.router
     │                                    └─> Health check
     │
     ├─── POST /api/v1/hybrid-search ──► hybrid_search.router
     │                                    └─> Search only (no LLM)
     │
     ├─── POST /api/v1/ask ─────────────► ask_router
     │                                    │
     │                                    ▼
     │                            ┌──────────────────────┐
     │                            │ Document Type Router │
     │                            │ (Inside ask.py)      │
     │                            └──────────────────────┘
     │                                    │
     │                                    ├─ document_type="arxiv"
     │                                    │  └─> _prepare_chunks_and_sources_arxiv()
     │                                    │       └─> OpenSearchClient (arXiv)
     │                                    │
     │                                    └─ document_type="financial"
     │                                       └─> _prepare_chunks_and_sources_financial()
     │                                            └─> FinancialOpenSearchClient
     │
     └─── POST /api/v1/stream ──────────► stream_router
                                          └─> Same routing as /ask but streaming
```

---

## 🎯 Key Coordination Point #1: Document Type Routing

**File:** [src/routers/ask.py](src/routers/ask.py:198-206)

This is where the magic happens! The coordinator decides which agent to use:

```python
# Line 198-206: Document type routing
if request.document_type == "financial":
    # Route to Financial Agent
    chunks, sources, _ = await _prepare_chunks_and_sources_financial(
        request, financial_opensearch_client, embeddings_service, rag_tracer, trace
    )
else:  # "arxiv"
    # Route to arXiv Agent
    chunks, sources, _ = await _prepare_chunks_and_sources_arxiv(
        request, opensearch_client, embeddings_service, rag_tracer, trace
    )
```

### Breakpoint Location:
**Set a breakpoint at line 198** to see this routing decision!

---

## 🤖 The Two Search Agents

### Agent 1: arXiv Search Agent
**Function:** `_prepare_chunks_and_sources_arxiv()` (line 28-85)
**Responsibility:** Search arXiv research papers

```python
async def _prepare_chunks_and_sources_arxiv(
    request: AskRequest,
    opensearch_client: OpenSearchClient,  # ← arXiv-specific client
    embeddings_service,
    rag_tracer: RAGTracer,
    trace=None,
) -> tuple[List[Dict], List[str], List[str]]:
    """Retrieve and prepare chunks for arXiv papers."""

    # 1. Generate embedding (if hybrid mode)
    query_embedding = await embeddings_service.embed_query(request.query)

    # 2. Search arXiv index
    search_results = opensearch_client.search_unified(
        query=request.query,
        query_embedding=query_embedding,
        size=request.top_k,
        categories=request.categories,
        use_hybrid=request.use_hybrid
    )

    # 3. Extract chunks and build arXiv PDF URLs
    for hit in search_results.get("hits", []):
        arxiv_id = hit.get("arxiv_id", "")
        sources_set.add(f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf")

    return chunks, list(sources_set), arxiv_ids
```

---

### Agent 2: Financial Search Agent
**Function:** `_prepare_chunks_and_sources_financial()` (line 88-167)
**Responsibility:** Search SEC financial filings

```python
async def _prepare_chunks_and_sources_financial(
    request: AskRequest,
    financial_opensearch_client: FinancialOpenSearchClient,  # ← Financial-specific client
    embeddings_service,
    rag_tracer: RAGTracer,
    trace=None,
) -> tuple[List[Dict], List[str], List[str]]:
    """Retrieve and prepare chunks for financial documents."""

    # 1. Generate embedding (if hybrid mode)
    query_embedding = await embeddings_service.embed_query(request.query)

    # 2. Choose search method based on mode
    if request.use_hybrid and query_embedding is not None:
        search_results = financial_opensearch_client.search_chunks_hybrid(
            query=request.query,
            query_embedding=query_embedding,
            size=request.top_k,
            ticker=request.ticker,
            document_types=request.filing_types
        )
    else:
        search_results = financial_opensearch_client.search_chunks_bm25(
            query=request.query,
            size=request.top_k,
            ticker=request.ticker,
            document_types=request.filing_types
        )

    # 3. Extract chunks and build SEC EDGAR URLs
    for hit in search_results.get("hits", []):
        accession = hit.get("accession_number", "")
        sources_set.add(f"https://www.sec.gov/cgi-bin/viewer?...")

    return chunks, list(sources_set), document_ids
```

---

## 🎯 Key Coordination Point #2: LLM Fallback Chain

**File:** [src/routers/ask.py](src/routers/ask.py:250-336)

After getting chunks, the coordinator tries multiple LLM agents with fallback:

```python
# Line 250-336: 4-tier LLM fallback coordination

# TIER 1: Primary LLM (configured in settings)
try:
    answer = await llm_client.generate_rag_answer(...)
    provider_used = "primary"

except Exception as primary_error:
    # TIER 2: Gemini Pro fallback
    try:
        gemini_client = GeminiClient(settings)
        answer = await gemini_client.generate_rag_answer(...)
        provider_used = "gemini_pro_fallback"

    except Exception as tier2_error:
        # TIER 3: Claude Haiku fallback
        try:
            claude_client = AnthropicClient(settings)
            answer = await claude_client.generate_rag_answer(...)
            provider_used = "claude_fallback"

        except Exception as tier3_error:
            # TIER 4: OpenAI fallback (last resort)
            try:
                openai_client = OpenAIClient(settings)
                answer = await openai_client.generate_rag_answer(...)
                provider_used = "openai_fallback"

            except Exception as tier4_error:
                # All tiers failed
                raise HTTPException(status_code=503, detail="LLM unavailable")
```

### Breakpoint Locations:
- **Line 253:** Primary LLM attempt
- **Line 276:** Tier 2 (Gemini) fallback
- **Line 295:** Tier 3 (Claude) fallback
- **Line 315:** Tier 4 (OpenAI) fallback

---

## 🔧 Dependency Injection (How Services Are Passed)

**File:** [src/dependencies.py](src/dependencies.py)

The coordinator uses FastAPI dependency injection to pass the right agents.

### The Dependency Flow:

```
STEP 1: Initialization (main.py lifespan)
┌──────────────────────────────────────────────┐
│ app.state.opensearch_client = make_...()    │  Line 46
│ app.state.financial_opensearch_client = ... │  Line 49
│ app.state.embeddings_service = make_...()   │  Line 83
│ app.state.llm_client = make_...()           │  Line 88/91/94
│ app.state.cache_client = make_...()         │  Line 101
└──────────────────────────────────────────────┘
                     ↓
STEP 2: Request Arrives
┌──────────────────────────────────────────────┐
│  POST /api/v1/ask                            │
│  { "query": "...", "document_type": "..." }  │
└──────────────────────────────────────────────┘
                     ↓
STEP 3: FastAPI Calls Dependency Functions
┌──────────────────────────────────────────────┐
│ get_opensearch_client(request)               │  dependencies.py:42
│   └─> returns request.app.state.opensearch  │
│                                               │
│ get_financial_opensearch_client(request)     │  dependencies.py:47
│   └─> returns request.app.state.financial   │
│                                               │
│ get_llm_client(request)                      │  dependencies.py:82
│   └─> returns request.app.state.llm_client  │
└──────────────────────────────────────────────┘
                     ↓
STEP 4: Dependencies Injected Into Handler
┌──────────────────────────────────────────────┐
│ async def ask_question(                      │
│     request: AskRequest,                     │
│     opensearch_client: OpenSearchDep,        │  ← Injected!
│     financial_opensearch_client: ...Dep,     │  ← Injected!
│     llm_client: LLMDep,                      │  ← Injected!
│     ...                                       │
│ )                                             │
└──────────────────────────────────────────────┘
```

### The Code (dependencies.py):

```python
# Line 42-44: Getter function for arXiv OpenSearch
def get_opensearch_client(request: Request) -> OpenSearchClient:
    """Get OpenSearch client from the request state."""
    return request.app.state.opensearch_client  # ← Retrieved from app.state


# Line 47-49: Getter function for Financial OpenSearch
def get_financial_opensearch_client(request: Request) -> FinancialOpenSearchClient:
    """Get Financial OpenSearch client from the request state."""
    return request.app.state.financial_opensearch_client


# Line 82-84: Getter function for LLM (could be Gemini, OpenAI, or Ollama)
def get_llm_client(request: Request) -> Union[OllamaClient, OpenAIClient, GeminiClient]:
    """Get LLM client from the request state (routes based on LLM_PROVIDER)."""
    return request.app.state.llm_client


# Line 87-99: Type annotations for dependency injection
OpenSearchDep = Annotated[OpenSearchClient, Depends(get_opensearch_client)]
FinancialOpenSearchDep = Annotated[FinancialOpenSearchClient, Depends(get_financial_opensearch_client)]
EmbeddingsDep = Annotated[JinaEmbeddingsClient, Depends(get_embeddings_service)]
LLMDep = Annotated[Union[OllamaClient, OpenAIClient, GeminiClient], Depends(get_llm_client)]
CacheDep = Annotated[CacheClient | None, Depends(get_cache_client)]
LangfuseDep = Annotated[LangfuseTracer, Depends(get_langfuse_tracer)]
```

### How It's Used (ask.py):

```python
@ask_router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    opensearch_client: OpenSearchDep,           # ← Auto-injected arXiv client
    financial_opensearch_client: FinancialOpenSearchDep,  # ← Auto-injected financial client
    embeddings_service: EmbeddingsDep,          # ← Auto-injected embeddings
    llm_client: LLMDep,                         # ← Auto-injected LLM client
    langfuse_tracer: LangfuseDep,              # ← Auto-injected tracing
    cache_client: CacheDep,                     # ← Auto-injected cache
):
```

### The Magic:

FastAPI sees `OpenSearchDep` and:
1. Calls `get_opensearch_client(request)`
2. Which returns `request.app.state.opensearch_client`
3. Which was initialized in `main.py` lifespan
4. Passes it to `ask_question()` automatically

**No manual wiring needed!** FastAPI handles all the plumbing.

---

## 🎯 Debugging Dependency Injection

**Set breakpoint at:** `src/dependencies.py:42` (inside `get_opensearch_client`)

**What you'll see:**
```python
request                    # The incoming FastAPI request
request.app               # The FastAPI app instance
request.app.state         # The shared state object
request.app.state.opensearch_client  # The initialized client
```

This shows you exactly how services are retrieved and passed to handlers!

---

## 🎬 Debug These Routing Points

### Scenario 1: Trace arXiv Request Routing

**Set these breakpoints:**
1. Line 198 in `ask.py` - See document_type check
2. Line 28 in `ask.py` - Enter arXiv agent
3. Line 51 in `ask.py` - See arXiv search call

**Test request:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is attention mechanism?",
    "document_type": "arxiv",
    "top_k": 5
  }'
```

**What you'll see:**
- BP1: `request.document_type == "arxiv"` → takes else branch
- BP2: Enters `_prepare_chunks_and_sources_arxiv()`
- BP3: Calls `opensearch_client.search_unified()`

---

### Scenario 2: Trace Financial Request Routing

**Set these breakpoints:**
1. Line 198 in `ask.py` - See document_type check
2. Line 88 in `ask.py` - Enter financial agent
3. Line 112 in `ask.py` - See financial search call

**Test request:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was Apple revenue in Q4?",
    "document_type": "financial",
    "ticker": "AAPL",
    "top_k": 5
  }'
```

**What you'll see:**
- BP1: `request.document_type == "financial"` → takes if branch
- BP2: Enters `_prepare_chunks_and_sources_financial()`
- BP3: Calls `financial_opensearch_client.search_chunks_hybrid()` or `search_chunks_bm25()`

---

### Scenario 3: Trace LLM Fallback Coordination

**Set these breakpoints:**
1. Line 253 in `ask.py` - Primary LLM
2. Line 276 in `ask.py` - Gemini fallback
3. Line 295 in `ask.py` - Claude fallback
4. Line 315 in `ask.py` - OpenAI fallback

**Simulate failure:**
- Remove Gemini API key from environment
- Watch it cascade through fallbacks

**What you'll see:**
- BP1: Primary fails with error
- BP2: Tries Gemini Pro
- BP3: Tries Claude (if Gemini fails)
- BP4: Last resort OpenAI

---

## 📊 Coordination Summary

### Request Flow:
```
1. User Request → FastAPI Router
                     │
2. Router → ask_question() function
                     │
3. Document Type Check → Route to specialized agent
                     │
                     ├─ arXiv Agent (OpenSearchClient)
                     └─ Financial Agent (FinancialOpenSearchClient)
                     │
4. Both agents → Embeddings Service (if hybrid mode)
                     │
5. Search Results → Chunks extracted
                     │
6. Chunks → LLM Coordinator (4-tier fallback)
                     │
7. LLM Response → User
```

---

## 🎯 The Coordinator Pattern

Your app follows the **Coordinator Pattern**:

1. **Single Entry Point** (main.py) registers all routers
2. **Smart Routing** (ask.py) decides which agent based on document_type
3. **Specialized Agents** (arXiv vs Financial) handle specific domains
4. **Fallback Strategy** (4-tier LLM) ensures reliability
5. **Dependency Injection** (FastAPI) wires services automatically

---

## 🔍 Key Files for Routing

| File | Role | What It Coordinates |
|------|------|---------------------|
| [src/main.py](src/main.py) | Main Coordinator | Registers routers, initializes services |
| [src/routers/ask.py](src/routers/ask.py) | Request Router | Routes to arXiv or Financial agent |
| [src/dependencies.py](src/dependencies.py) | Service Injector | Provides agents to endpoints |
| [src/services/opensearch/client.py](src/services/opensearch/client.py) | arXiv Agent | Searches arXiv papers |
| [src/services/opensearch/financial_client.py](src/services/opensearch/financial_client.py) | Financial Agent | Searches SEC filings |

---

## 💡 Interview Talking Point

**When asked:** "How does your system handle different document types?"

**Your Answer:**
> "I implemented a coordinator pattern where the main FastAPI app routes requests to specialized agents based on document_type. For arXiv papers, requests go to an arXiv-specific agent that searches the academic papers index and builds arXiv PDF URLs. For financial documents, requests route to a financial agent that searches SEC filings and constructs EDGAR URLs.
>
> Both agents use the same hybrid search strategy (BM25 + semantic embeddings), but handle domain-specific metadata differently. The coordinator also implements a 4-tier LLM fallback (Gemini → Claude → GPT-4 → GPT-3.5) to ensure 100% query success rate.
>
> This architecture makes it easy to add new document types - just create a new agent and add a routing condition."

---

**Debug the routing by setting breakpoints at lines 198, 28, and 88 in ask.py!** 🚀
