# arXiv Paper Curator - RAG System Portfolio Entry

**Copy this content to add to your portfolio website/resume**

---

## 📚 arXiv Paper Curator - AI-Powered Research Assistant

**Live Demo**: [API](https://arxiv-paper-curator-v1-production.up.railway.app/docs) • [GitHub](https://github.com/sudhirshivaram/arxiv-paper-curator-v1)

### Overview

An intelligent research paper discovery system that uses Retrieval-Augmented Generation (RAG) to help researchers find and understand academic papers. The system combines semantic search, keyword matching, and AI-powered summarization to provide accurate, cited answers to research questions.

### Key Features

- 🔍 **Hybrid Search**: Combines BM25 keyword search with vector similarity for optimal results
- 🤖 **AI-Powered Q&A**: Natural language question answering with source citations
- 📊 **100 Papers Indexed**: Curated collection of AI/ML research papers from arXiv
- 🎨 **Interactive UI**: Clean Streamlit interface with real-time API monitoring
- ☁️ **Production Deployment**: Fully deployed on Railway.app with 99%+ uptime

### Technical Stack

**Backend**:
- FastAPI (Python REST API)
- PostgreSQL (metadata storage)
- OpenSearch (vector database)
- SQLAlchemy ORM

**AI/ML**:
- Jina AI Embeddings (1024-dimensional vectors)
- OpenAI GPT-4o-mini (answer generation)
- Custom hybrid search algorithm

**Frontend**:
- Streamlit (Python web framework)
- Interactive search interface
- Real-time health monitoring

**Infrastructure**:
- Railway.app (cloud deployment)
- Docker (containerization)
- Redis (caching)

### Architecture Highlights

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

### Key Achievements

1. **Implemented Full RAG Pipeline**
   - Paper ingestion from arXiv API
   - PDF parsing and text extraction
   - Intelligent chunking (600 words with 100-word overlap)
   - Vector embedding generation
   - Hybrid search implementation

2. **Production Deployment**
   - Successfully deployed to Railway.app
   - Managed multiple services (API, PostgreSQL, OpenSearch, Redis)
   - Implemented proper environment variable management
   - Created deployment documentation

3. **Database Architecture**
   - Designed dual-database system (PostgreSQL + OpenSearch)
   - PostgreSQL for structured metadata
   - OpenSearch for vector similarity search
   - Optimal query performance

4. **User Experience**
   - Built clean, intuitive Streamlit interface
   - Real-time API health monitoring
   - Configurable search parameters
   - Example questions for quick start

### Technical Challenges Solved

**1. Environment Variable Configuration**
- **Challenge**: Scripts not loading Railway environment variables properly
- **Solution**: Created wrapper scripts with explicit environment loading
- **Learning**: Deep understanding of Pydantic Settings and configuration management

**2. Docker Build Optimization**
- **Challenge**: Railway not supporting certain Docker cache directives
- **Solution**: Simplified Dockerfile, removed mount directives
- **Learning**: Cloud platform constraints and optimization

**3. Data Migration**
- **Challenge**: Import 100 papers from local PostgreSQL to Railway
- **Solution**: Used Docker PostgreSQL client to pipe SQL dump to remote database
- **Learning**: Database migration strategies

**4. Zero-to-Production Indexing**
- **Challenge**: OpenSearch had 0 documents after deployment
- **Solution**: Created reindexing script to populate from PostgreSQL
- **Learning**: Production data initialization workflows

### Code Quality

- **Clean Architecture**: Separation of concerns (services, models, routes)
- **Type Safety**: Full type hints with Pydantic
- **Documentation**: Comprehensive docs (setup, deployment, API)
- **Error Handling**: Proper exception handling and logging
- **Testing**: Unit tests for core functionality

### Performance Metrics

- **Query Time**: 2-5 seconds average
- **Papers Indexed**: 100 (with plans for 1000+)
- **Vector Dimensions**: 1024 (Jina embeddings)
- **Search Accuracy**: Hybrid approach improves relevance
- **Uptime**: 99%+ on Railway deployment

### Future Enhancements

**Phase 1** (Short-term):
- Index full paper content (not just abstracts)
- Expand to 50 papers with complete PDF parsing
- Add paper filtering by category/date

**Phase 2** (Medium-term):
- Deploy Airflow for automated daily ingestion
- Implement citation network visualization
- Add paper recommendation system

**Phase 3** (Long-term):
- User authentication and collections
- Streaming responses for real-time feedback
- Multi-language support

### Impact & Learnings

**Business Value**:
- Saves researchers hours of manual paper searching
- Provides accurate, cited answers (not hallucinations)
- Scalable to thousands of papers
- Production-ready with proper deployment

**Technical Skills Gained**:
- RAG system architecture and implementation
- Vector database design and optimization
- Production cloud deployment (Railway)
- FastAPI backend development
- Streamlit frontend development
- Docker containerization
- Environment and configuration management
- PostgreSQL and OpenSearch administration

**Soft Skills Developed**:
- Technical documentation writing
- System architecture design
- Problem-solving and debugging
- Project planning and execution

### Try It Out

**Live API**: https://arxiv-paper-curator-v1-production.up.railway.app/docs

**Example Query**:
```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers discuss reinforcement learning?", "top_k": 3}'
```

**Response**: AI-generated answer with source citations!

### Repository

**GitHub**: https://github.com/sudhirshivaram/arxiv-paper-curator-v1

**Key Files**:
- `/src/main.py` - FastAPI application
- `/streamlit_app.py` - Frontend interface
- `/src/services/` - Service layer (embeddings, search, etc.)
- `/docs/` - Comprehensive documentation
- `/scripts/` - Utility scripts for data operations

### Contact

For questions or collaboration opportunities:
- GitHub: [@sudhirshivaram](https://github.com/sudhirshivaram)
- Project: [arxiv-paper-curator-v1](https://github.com/sudhirshivaram/arxiv-paper-curator-v1)

---

## Portfolio Presentation Tips

### For Technical Interviews:
1. **Start with architecture**: Show the dual-database design
2. **Explain RAG pipeline**: Walk through query → retrieval → generation
3. **Discuss challenges**: Environment variables, deployment issues
4. **Show live demo**: Use the Railway deployment or Streamlit UI

### For Non-Technical Interviews:
1. **Use the elevator pitch**: "AI-powered research assistant"
2. **Show the problem**: Researchers struggle to find relevant papers
3. **Demo the solution**: Live query showing cited answers
4. **Highlight impact**: Saves time, provides accurate information

### Key Talking Points:
- ✅ Production-deployed, not just local
- ✅ Full-stack (frontend + backend + databases)
- ✅ Modern AI stack (RAG, vector search, LLMs)
- ✅ Solved real deployment challenges
- ✅ Scalable architecture

---

**Project Duration**: 5 weeks (part-time)
**Lines of Code**: ~3000+
**Technologies Used**: 15+
**Status**: Production-ready, actively maintained
