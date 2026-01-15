# 🐛 Debugging Your RAG System - Step by Step

## How to Start Debugging

### Step 1: Start Debug Mode in VS Code

1. Press `F5` or click "Run and Debug" in sidebar
2. Select "Debug FastAPI App"
3. Wait for server to start (you'll see "Application startup complete")

### Step 2: Set Your Breakpoints

Click in the left margin (next to line numbers) to set breakpoints at these key locations:

---

## 🎯 Essential Breakpoints (Place These First!)

### Breakpoint 1: Request Entry Point
**File:** `src/routers/ask.py`
**Line:** 171 (the `async def ask_question` function)

**Why:** This is where every RAG request starts. You'll see:
- The user's query
- All request parameters (top_k, use_hybrid, document_type)
- What model is being used

**What to inspect:**
```python
# In VS Code Debug Console, type:
request.query           # The user's question
request.top_k          # How many chunks to retrieve
request.use_hybrid     # BM25 only or hybrid search?
request.document_type  # "arxiv" or "financial"
```

---

### Breakpoint 2: Cache Check
**File:** `src/routers/ask.py`
**Line:** 191 (inside the cache check)

**Why:** See if this is a cached response (instant return) or needs processing

**What to inspect:**
```python
cached_response  # Will be None if cache miss, AskResponse if cache hit
```

---

### Breakpoint 3: Embedding Generation
**File:** `src/routers/ask.py`
**Line:** 42 (inside `_prepare_chunks_and_sources_arxiv`)

**Why:** This is where your query becomes a 1024-dim vector for semantic search

**What to inspect:**
```python
request.query         # The text query
query_embedding      # Will be a list of 1024 floats (Jina-v3 embeddings)
```

---

### Breakpoint 4: Search Execution
**File:** `src/routers/ask.py`
**Line:** 51 (just before `search_unified`)

**Why:** This is where hybrid search (BM25 + semantic) happens

**What to inspect:**
```python
request.query              # Search query
query_embedding           # Vector (if hybrid mode)
request.top_k             # How many results
request.use_hybrid        # True/False
```

**Step Over** this line, then inspect:
```python
search_results            # See what papers were found
search_results["hits"]    # List of matching papers
len(search_results["hits"])  # How many results
```

---

### Breakpoint 5: Chunk Preparation
**File:** `src/routers/ask.py`
**Line:** 66 (inside the for loop building chunks)

**Why:** See how search results are converted to chunks for the LLM

**What to inspect:**
```python
hit                    # Current search result
hit["arxiv_id"]       # Paper ID
hit["chunk_text"]     # The actual text going to LLM
hit.get("score", 0)   # Search relevance score
```

---

### Breakpoint 6: Prompt Construction
**File:** `src/routers/ask.py`
**Line:** 236 (after prompt creation)

**Why:** See the EXACT prompt sent to the LLM

**What to inspect:**
```python
final_prompt      # The complete prompt with context
len(chunks)       # How many chunks were used
request.query     # Original question
```

**Pro tip:** Copy `final_prompt` and paste in a text editor to see the full context!

---

### Breakpoint 7: LLM Generation
**File:** `src/routers/ask.py`
**Line:** 253 (before `generate_rag_answer`)

**Why:** This is where the magic happens - LLM generates the answer

**What to inspect:**
```python
request.query    # Question
chunks           # Context chunks
request.model    # Which LLM
```

**Step Over** this line (might take 1-2 seconds), then inspect:
```python
rag_response              # The LLM's response
answer                    # The generated answer
```

---

### Breakpoint 8: Fallback Logic (If Primary Fails)
**File:** `src/routers/ask.py`
**Line:** 264 (Tier 1 fallback warning)

**Why:** See the 4-tier fallback in action

**What to inspect:**
```python
primary_error     # Why did primary LLM fail?
```

Then step through to see which tier succeeds:
- Line 276: Tier 2 (Gemini Pro)
- Line 295: Tier 3 (Claude)
- Line 315: Tier 4 (OpenAI)

---

### Breakpoint 9: Response Building
**File:** `src/routers/ask.py`
**Line:** 341 (creating AskResponse)

**Why:** See the final response before it's sent to user

**What to inspect:**
```python
response.query         # Original question
response.answer        # Generated answer
response.sources       # List of PDF URLs
response.chunks_used   # How many chunks
response.search_mode   # "hybrid" or "bm25"
```

---

## 🔥 Understanding the Flow - Step by Step

### Scenario 1: Simple Query (Cache Miss)

1. **Set breakpoints 1, 3, 4, 5, 6, 7, 9**
2. Press `F5` to start debugging
3. In another terminal, run:
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is attention mechanism?",
    "top_k": 5,
    "use_hybrid": true
  }'
```

4. **Watch the flow:**
   - BP1: Request arrives ✅
   - BP2: Cache miss (cached_response = None)
   - BP3: Embedding created (1024 floats) ✅
   - BP4: Hybrid search executes ✅
   - BP5: Chunks extracted ✅
   - BP6: Prompt built ✅
   - BP7: LLM generates answer ✅
   - BP9: Response ready ✅

---

### Scenario 2: Cache Hit

1. Run the same query twice
2. First time: Goes through full pipeline
3. Second time: Stops at BP2 with cached_response populated!

---

### Scenario 3: LLM Fallback

1. **Set breakpoint 8** (the fallback logic)
2. Disconnect internet or use invalid API key to trigger fallback
3. Watch it try: Gemini → Claude → GPT-4 → GPT-3.5

---

## 🎓 What Each Variable Tells You

### In Debug Console, Try These:

```python
# See the full request
request.__dict__

# See search results structure
search_results.keys()
search_results["total"]
search_results["hits"][0]

# See chunks going to LLM
[c["chunk_text"][:100] for c in chunks]  # First 100 chars of each

# See final prompt length
len(final_prompt)
final_prompt[:500]  # First 500 chars

# See answer
answer
len(answer)
```

---

## 🚀 Advanced Debugging Tips

### 1. Conditional Breakpoints

Right-click on a breakpoint → "Edit Breakpoint" → Add condition:

```python
# Only break when query contains "transformer"
"transformer" in request.query.lower()

# Only break when hybrid search is used
request.use_hybrid == True

# Only break when more than 3 chunks found
len(chunks) > 3
```

### 2. Watch Expressions

In Debug sidebar → "Watch" section → Add:
```
request.query
len(chunks)
search_results["total"]
answer
```

These values update automatically as you step through!

### 3. Debug Console Magic

While paused at a breakpoint, try:
```python
# Modify variables on the fly!
request.top_k = 10  # Change to retrieve more chunks

# Test functions
await embeddings_service.embed_query("test")

# Pretty print
import json
print(json.dumps(search_results, indent=2))
```

---

## 📊 Understanding Your Metrics While Debugging

Watch these to understand your RAGAS scores:

### Faithfulness (Your score: 1.0)
- **Check:** All text in `chunks` comes from retrieved documents
- **Breakpoint 5:** Verify chunk_text is from actual papers

### Context Precision (Your score: 1.0)
- **Check:** All retrieved chunks are relevant
- **Breakpoint 4:** Look at search scores - higher = more relevant

### Context Recall (Your score: 0.925)
- **Check:** Are all necessary chunks retrieved?
- **Breakpoint 5:** Count how many chunks vs. top_k

### MRR (Your score: 1.0)
- **Check:** Most relevant result is ranked first
- **Breakpoint 4:** Look at search_results["hits"][0] - should be most relevant

---

## 🎯 Quick Debug Workflows

### "Why is this answer wrong?"
1. BP6: Check `final_prompt` - is the context good?
2. BP5: Check `chunks` - are relevant papers included?
3. BP4: Check `search_results` - did search find right papers?

### "Why is search not finding papers?"
1. BP3: Check `query_embedding` - is it None? (means hybrid failed)
2. BP4: Check `search_results["total"]` - how many matches?
3. BP1: Check `request.categories` - too restrictive?

### "Why is it slow?"
1. Add `time.time()` watch expression
2. Step through and see which line takes longest
3. Usually BP7 (LLM) or BP4 (search)

---

## 💡 Pro Tips

1. **Use Step Over (F10)** not Step Into (F11) to avoid diving into library code
2. **Use Continue (F5)** to jump between breakpoints
3. **Hover over variables** to see values instantly
4. **Right-click variable → View Value** for long strings
5. **Copy as Expression** to reuse variable inspection

---

## 🎬 Your First Debug Session

**Try this right now:**

1. Set BP1, BP4, BP6, BP7, BP9
2. Press F5
3. Run this test query:
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain transformers",
    "top_k": 3,
    "use_hybrid": true
  }'
```

4. At each breakpoint, inspect the variables
5. Watch your RAG system come to life!

---

**Happy Debugging! You'll understand your system 10x better after one debug session.** 🚀
