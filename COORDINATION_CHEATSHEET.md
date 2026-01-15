# 🎯 Coordination Debugging Cheat Sheet

## Quick Reference: Where to Set Breakpoints to See Agent Coordination

---

## 🚀 The Complete Coordination Flow

### Step 1️⃣: App Initialization
**File:** [src/main.py](src/main.py:30-114)

**Breakpoints:**
- Line 46: `app.state.opensearch_client = make_opensearch_client()`
- Line 49: `app.state.financial_opensearch_client = make_financial_opensearch_client()`
- Line 88: `app.state.llm_client = make_openai_client()` (if OpenAI)
- Line 91: `app.state.llm_client = make_gemini_client()` (if Gemini)

**What happens:** The coordinator initializes all agents and stores them in `app.state`

---

### Step 2️⃣: Request Arrives at Coordinator
**File:** [src/routers/ask.py](src/routers/ask.py:170-179)

**Breakpoint:**
- Line 171: `async def ask_question(...)`

**What happens:** FastAPI receives the request and prepares to route it

**Inspect:**
```python
request.query           # User's question
request.document_type   # "arxiv" or "financial"
request.top_k          # How many chunks
request.use_hybrid     # BM25 only or hybrid?
```

---

### Step 3️⃣: Dependency Injection (Behind the Scenes)
**File:** [src/dependencies.py](src/dependencies.py:42-84)

**Breakpoints:**
- Line 42: `def get_opensearch_client(request: Request)`
- Line 47: `def get_financial_opensearch_client(request: Request)`
- Line 82: `def get_llm_client(request: Request)`

**What happens:** FastAPI calls these functions to get the agents

**Inspect:**
```python
request.app.state.opensearch_client         # arXiv search agent
request.app.state.financial_opensearch_client  # Financial search agent
request.app.state.llm_client                # LLM agent (Gemini/OpenAI/etc)
```

---

### Step 4️⃣: Document Type Routing Decision
**File:** [src/routers/ask.py](src/routers/ask.py:198-206)

**Breakpoint:**
- Line 198: `if request.document_type == "financial":`

**What happens:** Coordinator decides which search agent to use

**Inspect:**
```python
request.document_type   # Check the value
# Then step through to see which branch it takes
```

**Decision Tree:**
```
if document_type == "financial":
    ↓
    Route to Financial Agent (line 200-202)
else:
    ↓
    Route to arXiv Agent (line 204-206)
```

---

### Step 5️⃣: arXiv Agent Execution
**File:** [src/routers/ask.py](src/routers/ask.py:28-85)

**Breakpoints:**
- Line 42: `query_embedding = await embeddings_service.embed_query(request.query)`
- Line 51: `search_results = opensearch_client.search_unified(...)`
- Line 66: `for hit in search_results.get("hits", []):`

**What happens:** arXiv agent processes the request

**Flow:**
```
1. Generate embedding (if hybrid mode)
   ↓
2. Search arXiv index with hybrid search
   ↓
3. Extract chunks from search results
   ↓
4. Build arXiv PDF URLs
```

**Inspect:**
```python
query_embedding           # 1024-dim vector (or None if BM25-only)
search_results["total"]   # How many papers found
search_results["hits"]    # List of matching papers
chunks                    # Extracted text chunks for LLM
```

---

### Step 6️⃣: Financial Agent Execution
**File:** [src/routers/ask.py](src/routers/ask.py:88-167)

**Breakpoints:**
- Line 102: `query_embedding = await embeddings_service.embed_query(request.query)`
- Line 112: `search_results = financial_opensearch_client.search_chunks_hybrid(...)`
- Line 133: `for hit in search_results.get("hits", []):`

**What happens:** Financial agent processes the request

**Flow:**
```
1. Generate embedding (if hybrid mode)
   ↓
2. Choose search method (hybrid vs BM25)
   ↓
3. Search financial index
   ↓
4. Extract chunks from search results
   ↓
5. Build SEC EDGAR URLs
```

**Inspect:**
```python
query_embedding           # 1024-dim vector (or None)
request.ticker           # Stock ticker (e.g., "AAPL")
request.filing_types     # Document types (e.g., ["10-K", "10-Q"])
search_results["hits"]    # Matching financial documents
chunks                    # Extracted text chunks
```

---

### Step 7️⃣: LLM Coordinator (4-Tier Fallback)
**File:** [src/routers/ask.py](src/routers/ask.py:250-336)

**Breakpoints:**
- Line 253: Primary LLM attempt
- Line 264: Tier 1 failed (entering fallback)
- Line 276: Tier 2 (Gemini Pro)
- Line 295: Tier 3 (Claude)
- Line 315: Tier 4 (OpenAI)

**What happens:** Coordinator tries multiple LLM agents with fallback

**Flow:**
```
Try Tier 1: Primary LLM (configured in settings)
   ↓ (if fails)
Try Tier 2: Gemini Pro
   ↓ (if fails)
Try Tier 3: Claude Haiku
   ↓ (if fails)
Try Tier 4: OpenAI GPT
   ↓ (if all fail)
Return 503 error
```

**Inspect:**
```python
primary_error      # Why did Tier 1 fail?
tier2_error        # Why did Tier 2 fail?
provider_used      # Which tier succeeded?
answer             # The generated answer
```

---

### Step 8️⃣: Response Assembly
**File:** [src/routers/ask.py](src/routers/ask.py:341-358)

**Breakpoint:**
- Line 341: `response = AskResponse(...)`

**What happens:** Coordinator assembles the final response

**Inspect:**
```python
response.query         # Original question
response.answer        # LLM-generated answer
response.sources       # List of source URLs
response.chunks_used   # Number of chunks used
response.search_mode   # "hybrid" or "bm25"
```

---

## 🎬 Quick Debug Scenarios

### Scenario A: Trace Full arXiv Request

**Breakpoints to set:**
1. Line 171 (ask.py) - Request entry
2. Line 198 (ask.py) - Routing decision
3. Line 42 (ask.py) - Embedding generation
4. Line 51 (ask.py) - Search execution
5. Line 253 (ask.py) - LLM generation
6. Line 341 (ask.py) - Response assembly

**Run this:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is attention mechanism?",
    "document_type": "arxiv",
    "top_k": 5,
    "use_hybrid": true
  }'
```

**Step through and watch the flow!**

---

### Scenario B: Trace Full Financial Request

**Breakpoints to set:**
1. Line 171 (ask.py) - Request entry
2. Line 198 (ask.py) - Routing decision
3. Line 102 (ask.py) - Embedding generation
4. Line 112 (ask.py) - Search execution
5. Line 253 (ask.py) - LLM generation
6. Line 341 (ask.py) - Response assembly

**Run this:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was Apple revenue?",
    "document_type": "financial",
    "ticker": "AAPL",
    "top_k": 5,
    "use_hybrid": true
  }'
```

---

### Scenario C: Trace Dependency Injection

**Breakpoints to set:**
1. Line 42 (dependencies.py) - get_opensearch_client
2. Line 47 (dependencies.py) - get_financial_opensearch_client
3. Line 82 (dependencies.py) - get_llm_client

**Run any request and watch FastAPI inject dependencies automatically!**

---

### Scenario D: Trace LLM Fallback

**Breakpoints to set:**
1. Line 253 (ask.py) - Primary LLM
2. Line 264 (ask.py) - Fallback triggered
3. Line 276 (ask.py) - Tier 2
4. Line 295 (ask.py) - Tier 3
5. Line 315 (ask.py) - Tier 4

**To trigger fallback:**
- Remove API key from environment to simulate failure
- Watch it cascade through tiers

---

## 📊 Visual Summary

```
┌─────────────────────────────────────────────────────────┐
│  1. App Startup (main.py:30)                            │
│     └─> Initialize all agents → app.state              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. Request Arrives (ask.py:171)                        │
│     └─> FastAPI receives POST /api/v1/ask              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Dependency Injection (dependencies.py:42,47,82)     │
│     └─> FastAPI injects agents from app.state          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. Routing Decision (ask.py:198)                       │
│     ├─> if "financial" → Financial Agent (line 200)    │
│     └─> else → arXiv Agent (line 204)                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  5. Search Agent Execution (ask.py:28 or 88)            │
│     ├─> Generate embedding (if hybrid)                 │
│     ├─> Search OpenSearch index                        │
│     └─> Extract chunks                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  6. LLM Coordination (ask.py:250)                       │
│     ├─> Try Tier 1 (Primary)                           │
│     ├─> Try Tier 2 (Gemini) if Tier 1 fails           │
│     ├─> Try Tier 3 (Claude) if Tier 2 fails           │
│     └─> Try Tier 4 (OpenAI) if Tier 3 fails           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  7. Response Assembly (ask.py:341)                      │
│     └─> Build AskResponse with answer & sources        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  8. Return to User                                       │
│     └─> JSON response with answer                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Files Reference

| File | What It Coordinates | Key Lines |
|------|---------------------|-----------|
| [src/main.py](src/main.py) | Initializes all agents | 30-114 |
| [src/dependencies.py](src/dependencies.py) | Injects agents into handlers | 42, 47, 82 |
| [src/routers/ask.py](src/routers/ask.py) | Routes requests & coordinates LLM fallback | 171, 198, 250 |

---

**Pro Tip:** Set all breakpoints from Scenario A, then step through once. You'll understand the entire coordination flow in 5 minutes! 🚀
