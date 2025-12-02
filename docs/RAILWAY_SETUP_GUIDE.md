# 🔑 Railway Setup Guide - API Keys & Configuration

## Step-by-Step Guide to Add Your API Keys

### 📝 Before You Start

Get these API keys ready:

1. **OpenAI API Key** → https://platform.openai.com/api-keys
2. **Jina AI API Key** → https://jina.ai/embeddings

---

## 🚀 Deployment Process

### Step 1: Fill in `.env.railway` File (Local)

I created a file called `.env.railway` for you. Fill it in:

```bash
# Edit this file
nano .env.railway

# Or use your favorite editor
code .env.railway
```

**Update these lines:**
```bash
OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-KEY-HERE    ← Paste your OpenAI key
JINA_API_KEY=jina_YOUR-ACTUAL-KEY-HERE         ← Paste your Jina key
```

---

### Step 2: Push to GitHub

```bash
# Make sure .env.railway is in .gitignore (it already is!)
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

---

### Step 3: Deploy to Railway

#### A. Via Web UI (Easiest):

1. **Go to Railway**
   ```
   https://railway.app/new
   ```

2. **Deploy from GitHub**
   - Click "Deploy from GitHub repo"
   - Select `arxiv-paper-curator`
   - Railway starts building

3. **Add PostgreSQL**
   - Click "+ New"
   - Select "Database"
   - Choose "PostgreSQL"
   - Railway auto-configures connection

4. **Add Redis** (Optional but recommended)
   - Click "+ New"
   - Select "Database"
   - Choose "Redis"

5. **Add OpenSearch**
   - Click "+ New"
   - Select "Empty Service"
   - Name it: `opensearch`
   - Click on it → "Settings" → "Source Image"
   - Enter: `opensearchproject/opensearch:2.19.0`
   - Add environment variables:
     ```
     discovery.type=single-node
     OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
     DISABLE_SECURITY_PLUGIN=true
     ```

---

### Step 4: Add Environment Variables

#### Click on Your API Service → "Variables" Tab

Copy these variables from your `.env.railway` file:

**Required Variables (Add Manually):**

```plaintext
LLM_PROVIDER = openai
OPENAI_API_KEY = sk-proj-YOUR-KEY-HERE
OPENAI_MODEL = gpt-4o-mini
JINA_API_KEY = jina_YOUR-KEY-HERE
EMBEDDINGS__MODEL = jina-embeddings-v3
ARXIV__MAX_RESULTS = 25
CHUNKING__CHUNK_SIZE = 600
```

**Auto-Configured by Railway:**

These are automatically set when you add PostgreSQL/Redis:
- `DATABASE_URL` ✅ Auto
- `REDIS_URL` ✅ Auto

**Service URLs (Add These):**

```plaintext
OPENSEARCH_HOST = http://opensearch.railway.internal:9200
OPENSEARCH__HOST = http://opensearch.railway.internal:9200
POSTGRES_DATABASE_URL = ${{Postgres.DATABASE_URL}}
```

---

### Step 5: Deploy & Wait

1. Click "Deploy" in Railway
2. Wait 3-5 minutes for build
3. Check logs for any errors
4. Get your public URL

---

## 🎯 Quick Reference - Copy/Paste Template

When you're in Railway's Variables tab, copy/paste these:

### Core Configuration

```
ENVIRONMENT=production
DEBUG=false
```

### LLM (OpenAI)

```
LLM_PROVIDER=openai
OPENAI_API_KEY=YOUR_KEY_HERE
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
```

### Embeddings (Jina AI)

```
JINA_API_KEY=YOUR_KEY_HERE
EMBEDDINGS__MODEL=jina-embeddings-v3
EMBEDDINGS__TASK=retrieval.passage
EMBEDDINGS__DIMENSIONS=1024
```

### Services

```
OPENSEARCH_HOST=http://opensearch.railway.internal:9200
OPENSEARCH__HOST=http://opensearch.railway.internal:9200
POSTGRES_DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

### arXiv Settings

```
ARXIV__MAX_RESULTS=25
ARXIV__SEARCH_CATEGORY=cs.AI
```

### OpenSearch Settings

```
OPENSEARCH__INDEX_NAME=arxiv-papers
OPENSEARCH__CHUNK_INDEX_SUFFIX=chunks
OPENSEARCH__VECTOR_DIMENSION=1024
```

---

## ✅ Verification Checklist

After deployment, check:

- [ ] Go to your Railway URL: `https://your-app.up.railway.app`
- [ ] Check health: `https://your-app.up.railway.app/api/v1/health`
- [ ] View docs: `https://your-app.up.railway.app/docs`
- [ ] All services showing "healthy" in health endpoint
- [ ] No errors in Railway logs

---

## 🔧 Testing Your Deployment

### 1. Health Check

```bash
curl https://your-app.up.railway.app/api/v1/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "services": {
    "database": {"status": "healthy"},
    "opensearch": {"status": "healthy"}
  }
}
```

### 2. Import Your Data

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Import your 100 papers
railway run psql $DATABASE_URL < railway_backup.sql
```

### 3. Test Hybrid Search

```bash
curl -X POST https://your-app.up.railway.app/api/v1/hybrid-search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "size": 5}'
```

### 4. Test RAG

```bash
curl -X POST https://your-app.up.railway.app/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 2}'
```

---

## 💡 Tips

### Secure Your Keys

- ✅ `.env.railway` is in `.gitignore` - never commit it!
- ✅ Add keys only in Railway dashboard
- ✅ Regenerate keys if exposed

### Save Money

- Use `gpt-4o-mini` instead of `gpt-4` (much cheaper!)
- Set `OPENAI_MAX_TOKENS=500` to limit costs
- Jina AI has generous free tier

### Debugging

Check Railway logs:
```bash
railway logs
```

Or in web UI: Your Service → "Deployments" → Click on deployment → "View Logs"

---

## 📞 Need Help?

1. **Railway Docs**: https://docs.railway.app
2. **Railway Discord**: https://discord.gg/railway
3. **OpenAI Help**: https://help.openai.com
4. **Jina AI Docs**: https://jina.ai/embeddings/

---

## 🎉 Success!

Once everything is green in Railway:

✅ Your RAG system is live!
✅ Share the URL in your resume
✅ Recruiters can try it instantly
✅ Full hybrid search working

**Your Portfolio URL:**
```
https://arxiv-paper-curator-production.up.railway.app/docs
```

Add this to your resume/LinkedIn! 🚀
