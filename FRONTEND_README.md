# 🎨 Streamlit Frontend - Quick Start

Beautiful web interface for your arXiv Paper Curator RAG system!

## ✨ Features

- 🔍 **Question Answering**: Ask questions in natural language
- 📚 **Source Citations**: Get links to original papers
- ⚙️ **Configurable**: Adjust search parameters
- 📊 **Health Monitoring**: Real-time API status
- 💡 **Example Questions**: Get started quickly

## 🚀 Quick Start

### Run Locally

```bash
# Option 1: Use the convenience script
./run_frontend.sh

# Option 2: Run directly
uv run streamlit run streamlit_app.py
```

The app will open automatically in your browser at: **http://localhost:8501**

## 🌐 Deploy to Streamlit Cloud (FREE!)

1. **Go to**: [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with GitHub

3. **Click** "New app"

4. **Configure**:
   - Repository: `sudhirshivaram/arxiv-paper-curator-v1`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

5. **Deploy!**

Your app will be live at: `https://[your-app-name].streamlit.app`

## 📸 Screenshot

The interface includes:
- Clean search box for questions
- AI-generated answers with citations
- Source paper links
- System health monitoring
- Example questions

## 🎯 Try These Questions

- "What papers discuss reinforcement learning?"
- "What are the latest advances in transformers?"
- "Tell me about neural network architectures"
- "What research on large language models?"

## 📚 Full Documentation

See [docs/STREAMLIT_FRONTEND.md](docs/STREAMLIT_FRONTEND.md) for:
- Deployment options (Streamlit Cloud, Railway, Docker)
- Customization guide
- Troubleshooting
- Architecture details
- Future enhancements

## 🔧 Current Setup

- **Backend API**: Railway (https://arxiv-paper-curator-v1-production.up.railway.app)
- **Papers Indexed**: 100
- **Search Mode**: Hybrid (BM25 + Vector)
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: Jina AI

## 🎨 Customization

Want to customize the look? Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"  # Change this!
backgroundColor = "#ffffff"
```

## 🐛 Troubleshooting

**API Offline?**
- Check Railway deployment is running
- Visit: https://arxiv-paper-curator-v1-production.up.railway.app/docs

**Slow responses?**
- Normal for complex questions (LLM generation takes time)
- Reduce number of results in sidebar

## 🎉 What's Next?

Now that you have a working frontend:

1. **Deploy to Streamlit Cloud** - Get a public URL to share!
2. **Add more features** - See [docs/STREAMLIT_FRONTEND.md](docs/STREAMLIT_FRONTEND.md)
3. **Deploy Airflow** - Automate paper ingestion (requires Railway $20/month plan)
