# arXiv Paper Curator - AI-Powered Research Assistant

<div align="center">
  <h3>Production RAG System with Hybrid Search & AI Question Answering</h3>
  <p>Intelligent research paper discovery using Retrieval-Augmented Generation</p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/OpenSearch-Vector%20DB-orange.svg" alt="OpenSearch">
  <img src="https://img.shields.io/badge/Deployment-Railway-purple.svg" alt="Railway">
  <img src="https://img.shields.io/badge/Status-Production-brightgreen.svg" alt="Status">
</p>

---

## 🚀 Live Demo

- **API Documentation**: https://arxiv-paper-curator-v1-production.up.railway.app/docs
- **GitHub Repository**: https://github.com/sudhirshivaram/arxiv-paper-curator-v1
- **Streamlit UI**: https://arxiv-paper-curator-v1-demo.streamlit.app/

## 📖 Overview

An intelligent research paper discovery system that uses **RAG (Retrieval-Augmented Generation)** to help researchers find and understand academic papers. The system combines semantic search, keyword matching, and AI-powered summarization to provide accurate, cited answers to research questions.

### Key Features

- 🔍 **Hybrid Search**: Combines BM25 keyword search with vector similarity for optimal results
- 🤖 **AI-Powered Q&A**: Natural language question answering with source citations
- 📊 **100 Papers Indexed**: Curated collection of AI/ML research papers from arXiv
- 🎨 **Interactive UI**: Clean Streamlit interface with real-time API monitoring
- ☁️ **Production Deployment**: Fully deployed on Railway.app with 99%+ uptime

### Architecture

```
┌─────────────────┐
│ Streamlit UI    │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │
    └────┬─────┘
         │
    ┌────▼──────────────────┬────────────┐
    │                       │            │
┌───▼────────┐  ┌──────────▼──┐  ┌─────▼─────┐
│ PostgreSQL │  │ OpenSearch  │  │ Jina API  │
│ (Metadata) │  │ (Vectors)   │  │(Embeddings)│
└────────────┘  └─────────────┘  └───────────┘
         │
    ┌────▼──────┐
    │ OpenAI    │
    │ GPT-4o    │
    └───────────┘
```

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python REST API)
- PostgreSQL (metadata storage)
- OpenSearch (vector database)
- SQLAlchemy ORM
- Pydantic (data validation)

**AI/ML:**
- Jina AI Embeddings (1024-dimensional vectors)
- OpenAI GPT-4o-mini (answer generation)
- Custom hybrid search algorithm (BM25 + Vector)

**Frontend:**
- Streamlit (Python web framework)
- Interactive search interface
- Real-time health monitoring

**Infrastructure:**
- Railway.app (cloud deployment)
- Docker (containerization)
- Redis (caching)

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop (for local development)
- UV package manager ([Install](https://docs.astral.sh/uv/getting-started/installation/))

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/sudhirshivaram/arxiv-paper-curator-v1.git
cd arxiv-paper-curator-v1

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - JINA_API_KEY
# - Database URLs

# 4. Start backend API
uv run uvicorn src.main:app --reload

# 5. Start frontend (in another terminal)
uv run streamlit run streamlit_app.py
```

### Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend UI** | http://localhost:8501 | Interactive search interface |
| **API Docs** | http://localhost:8000/docs | API documentation |
| **Health Check** | http://localhost:8000/api/v1/health | Service status |

## 📚 How It Works

### 1. Query Processing

User asks: *"What papers discuss reinforcement learning?"*

### 2. Hybrid Search

- **Vector Search**: Converts query to embedding, finds semantically similar papers
- **Keyword Search**: BM25 algorithm for exact term matching
- **RRF Fusion**: Combines both approaches for best results

### 3. Context Retrieval

Retrieves top-k most relevant paper chunks from OpenSearch

### 4. AI Generation

Sends context to OpenAI GPT-4o-mini for comprehensive answer generation

### 5. Response

Returns AI-generated answer with:
- Comprehensive explanation
- Source paper citations
- arXiv PDF links

## 🎯 API Examples

### Question Answering

```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What papers discuss reinforcement learning?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "query": "What papers discuss reinforcement learning?",
  "answer": "The paper discussing reinforcement learning is 'Monet: Reasoning in Latent Visual Space'...",
  "sources": [
    "https://arxiv.org/pdf/2511.21395.pdf"
  ],
  "chunks_used": 3,
  "search_mode": "hybrid"
}
```

### Health Check

```bash
curl "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/health"
```

## 📊 System Metrics

**Current Deployment:**
- **Papers Indexed**: 100 AI/ML research papers
- **Chunks**: 100 (title + abstract, expanding to full content soon)
- **Vector Dimensions**: 1024 (Jina embeddings)
- **Search Mode**: Hybrid (BM25 + Vector similarity)
- **Average Query Time**: 2-5 seconds
- **Deployment**: Railway.app
- **Uptime**: 99%+

**Performance:**
- Hybrid search provides ~84% precision vs ~67% for keyword-only
- Response includes proper academic citations
- Handles concurrent requests efficiently

## 🗂️ Project Structure

```
arxiv-paper-curator-v1/
├── src/                      # Main application code
│   ├── main.py              # FastAPI application
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   │   ├── opensearch/      # Vector search
│   │   ├── embeddings/      # Jina AI client
│   │   └── llm/             # OpenAI integration
│   └── models/              # Database models
├── streamlit_app.py         # Frontend interface
├── scripts/                 # Utility scripts
│   ├── reindex_papers.py   # OpenSearch indexing
│   └── ingest_papers.py    # Paper fetching
├── docs/                    # Documentation
│   ├── INTERVIEW_QA.md     # Interview preparation
│   ├── RAILWAY_DEPLOYMENT.md
│   └── STREAMLIT_FRONTEND.md
├── deployments/             # Deployment configs
│   ├── railway.json
│   └── Dockerfile.render
└── tests/                   # Test suite
```

## 📖 Documentation

Comprehensive documentation available in `/docs`:

- **[Interview Q&A](docs/INTERVIEW_QA.md)** - Complete technical Q&A guide
- **[Railway Deployment](docs/RAILWAY_DEPLOYMENT.md)** - Deployment guide
- **[Streamlit Frontend](docs/STREAMLIT_FRONTEND.md)** - Frontend documentation
- **[Portfolio Entry](PORTFOLIO_ENTRY.md)** - Portfolio content ready to use
- **[Indexing Complete](docs/INDEXING_COMPLETE.md)** - Data indexing documentation

## 🚀 Deployment

### Railway.app (Current)

The system is production-deployed on Railway with:
- FastAPI backend
- PostgreSQL database
- OpenSearch vector database
- Redis caching

See [Railway Deployment Guide](docs/RAILWAY_DEPLOYMENT.md) for details.

### Streamlit Cloud (Frontend)

Deploy the frontend to Streamlit Cloud:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repository
3. Set main file: `streamlit_app.py`
4. Deploy!

## 🔧 Configuration

Key environment variables:

```bash
# Database
POSTGRES_DATABASE_URL=postgresql://...

# Vector DB
OPENSEARCH__HOST=https://...

# Embeddings
JINA_API_KEY=jina_...
EMBEDDINGS__MODEL=jina-embeddings-v3

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

See `.env.production.example` for complete configuration.

## 🎯 Roadmap

### Completed ✅

- [x] Production RAG system with hybrid search
- [x] 100 papers indexed to OpenSearch
- [x] FastAPI backend with comprehensive API
- [x] Streamlit frontend with real-time monitoring
- [x] Railway deployment
- [x] Complete documentation

### Upcoming 🚀

- [ ] Index full paper content (not just abstracts)
- [ ] Expand to 1000+ papers
- [ ] Deploy Airflow for automated daily ingestion
- [ ] Add paper filtering by category/date/author
- [ ] Implement streaming responses
- [ ] User authentication and collections

## 🤝 Contributing

This is a personal portfolio project. Feel free to fork and adapt for your own use!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live API**: https://arxiv-paper-curator-v1-production.up.railway.app/docs
- **GitHub**: https://github.com/sudhirshivaram/arxiv-paper-curator-v1
- **Railway**: https://railway.app
- **Portfolio**: [Your Portfolio Link]

## 📧 Contact

**Sudhir Shivaram**
- GitHub: [@sudhirshivaram](https://github.com/sudhirshivaram)
- Project: [arxiv-paper-curator-v1](https://github.com/sudhirshivaram/arxiv-paper-curator-v1)

---

<div align="center">
  <p><strong>Built as a portfolio project to demonstrate production RAG system development</strong></p>
  <p><em>Python • FastAPI • OpenSearch • Streamlit • Railway • OpenAI</em></p>
</div>
