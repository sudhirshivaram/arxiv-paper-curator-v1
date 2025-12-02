# 🚂 Railway.app Deployment Guide

Deploy your arXiv Paper Curator RAG system to Railway.app with full hybrid search support!

## 💰 Cost Estimate

- **Starter Plan**: $5/month (500 hours included)
- **Usage beyond**: ~$5-10/month total
- **Free Trial**: $5 credit to start

## 📋 Prerequisites

1. **Railway.app account** (sign up at https://railway.app)
2. **GitHub account** (to connect your repo)
3. **API Keys:**
   - OpenAI API key (or Anthropic)
   - Jina AI API key (for embeddings)

## 🚀 Quick Deployment (5 Steps)

### Step 1: Prepare Your Repository

```bash
# Make sure you're in the project directory
cd /home/bhargav/arxiv-paper-curator

# Commit all changes
git add .
git commit -m "Prepare for Railway deployment"

# Push to GitHub (create repo if needed)
git push origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your `arxiv-paper-curator` repository
4. Railway will auto-detect the `railway.json` config

### Step 3: Add Services

Railway will create these services automatically:

#### A. API Service (Main App)
- Automatically created from your repo
- Uses `Dockerfile`
- Exposed on public URL

#### B. Add PostgreSQL Database
1. Click "New Service" → "Database" → "PostgreSQL"
2. Railway auto-configures connection
3. Note: Free tier = 500MB storage

#### C. Add Redis (Optional)
1. Click "New Service" → "Database" → "Redis"
2. Free tier = 100MB memory
3. Used for caching

#### D. Add OpenSearch (Docker)
1. Click "New Service" → "Empty Service"
2. Name it "opensearch"
3. Add these environment variables:
   ```
   discovery.type=single-node
   OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
   DISABLE_SECURITY_PLUGIN=true
   ```
4. Deploy from Docker image: `opensearchproject/opensearch:2.19.0`

### Step 4: Configure Environment Variables

Click on your API service → "Variables" → Add these:

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Database (Auto-filled by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}
POSTGRES_DATABASE_URL=${{Postgres.DATABASE_URL}}

# Services (Use Railway internal URLs)
OPENSEARCH_HOST=http://opensearch.railway.internal:9200
OPENSEARCH__HOST=http://opensearch.railway.internal:9200
REDIS__HOST=${{Redis.REDIS_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# LLM Configuration (Use OpenAI)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500

# Embeddings (Jina AI)
JINA_API_KEY=jina_your-api-key-here
EMBEDDINGS__MODEL=jina-embeddings-v3
EMBEDDINGS__TASK=retrieval.passage
EMBEDDINGS__DIMENSIONS=1024

# arXiv Configuration
ARXIV__MAX_RESULTS=25
ARXIV__SEARCH_CATEGORY=cs.AI

# Chunking
CHUNKING__CHUNK_SIZE=600
CHUNKING__OVERLAP_SIZE=100

# OpenSearch
OPENSEARCH__INDEX_NAME=arxiv-papers
OPENSEARCH__CHUNK_INDEX_SUFFIX=chunks
OPENSEARCH__VECTOR_DIMENSION=1024
```

### Step 5: Deploy & Initialize

1. Railway will auto-deploy after you add variables
2. Wait for deployment (2-3 minutes)
3. Get your public URL from Railway dashboard
4. Visit `https://your-app.up.railway.app/docs`

---

## 📊 Loading Your Existing Data

You have 100 papers locally. Let's export and import them:

### Option 1: Export Database (Recommended)

```bash
# Export PostgreSQL data
docker exec rag-postgres pg_dump -U rag_user -d rag_db > railway_backup.sql

# After Railway deployment, import:
# 1. Get Railway PostgreSQL connection string from dashboard
# 2. Import the dump
psql $RAILWAY_DATABASE_URL < railway_backup.sql
```

### Option 2: Trigger Fresh Ingestion

Once deployed, trigger the ingestion via API:

```bash
# Your Railway URL
RAILWAY_URL="https://your-app.up.railway.app"

# Health check
curl $RAILWAY_URL/api/v1/health

# This will trigger background paper fetching
# (Note: Without Airflow, you'll need to fetch via API)
```

---

## 🎯 What Gets Deployed

### ✅ Services Deployed:
- **FastAPI** - Your main API
- **PostgreSQL** - Managed by Railway (500MB free)
- **OpenSearch** - Hybrid search engine
- **Redis** - Caching layer (optional)

### ✅ Features Working:
- **Hybrid Search** (BM25 + Vector + RRF)
- **RAG Endpoints** (ask, stream)
- **API Documentation** (/docs)
- **Health Checks**

### ❌ Not Deployed (Not Needed):
- **Airflow** - Data pipeline (manual trigger instead)
- **Ollama** - Using OpenAI API instead
- **Gradio UI** - Can be added separately

---

## 🔧 Alternative: Deploy WITHOUT OpenSearch

If you want even simpler deployment (and lower cost):

### Use PostgreSQL Full-Text Search Instead

1. Remove OpenSearch service
2. Update code to use PostgreSQL's built-in search
3. Saves ~$2-3/month in resources

**Trade-off:** Simpler search, but still works for demos!

---

## 📈 Monitoring & Maintenance

### Check Deployment Status
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Check status
railway status
```

### Update Deployment
```bash
# Push changes to GitHub
git push origin main

# Railway auto-deploys on push!
```

---

## 💡 Cost Optimization Tips

### 1. Use Railway's Free Trial
- $5 free credit
- Test everything first

### 2. Sleep Services When Not Using
```bash
# Scale down when not needed
railway down

# Wake up when needed
railway up
```

### 3. Optimize OpenSearch
- Use smaller heap size (512MB)
- Limit index size to essentials

### 4. Use OpenAI API Efficiently
- Cache responses (Redis)
- Use gpt-4o-mini (cheaper)
- Limit max_tokens

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] API is accessible at Railway URL
- [ ] `/api/v1/health` returns healthy status
- [ ] `/docs` shows API documentation
- [ ] PostgreSQL is connected (check logs)
- [ ] OpenSearch is running (check health endpoint)
- [ ] Hybrid search works (`/api/v1/hybrid-search/`)
- [ ] RAG endpoint works (`/api/v1/ask`)
- [ ] Papers are indexed (check counts)

---

## 🆘 Troubleshooting

### Issue: OpenSearch won't start
**Solution:** Increase memory allocation in Railway settings

### Issue: Database connection errors
**Solution:** Check `DATABASE_URL` is set correctly (Railway auto-fills this)

### Issue: API is slow
**Solution:**
- Check Railway plan (upgrade if needed)
- Enable Redis caching
- Optimize queries

### Issue: Out of memory
**Solution:**
- Reduce OpenSearch heap size
- Process fewer papers at once
- Upgrade Railway plan

---

## 📞 Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Your GitHub Issues**: Open an issue in your repo

---

## 🎓 What to Tell Recruiters

Your deployed Railway app showcases:

1. **Production Deployment Skills**
   - Docker containerization
   - Cloud platform (Railway)
   - Environment configuration
   - Database management

2. **RAG System Implementation**
   - Hybrid search (BM25 + Vector)
   - LLM integration (OpenAI)
   - Embeddings (Jina AI)
   - RESTful API design

3. **Best Practices**
   - Health checks
   - Error handling
   - Documentation (OpenAPI)
   - Scalable architecture

**Share this URL in your resume:**
```
Live Demo: https://your-app.up.railway.app/docs
GitHub: https://github.com/your-username/arxiv-paper-curator
```

---

## 🚀 Next Steps After Deployment

1. **Add Gradio UI** - Deploy Gradio app to Hugging Face Spaces, connect to Railway API
2. **Add Authentication** - Secure your endpoints
3. **Add Monitoring** - Use Railway's built-in metrics
4. **Add More Features** - Week 6 content (Langfuse monitoring)

---

**Ready to deploy?** Follow the steps above and you'll have your RAG system live in 30 minutes! 🎉
