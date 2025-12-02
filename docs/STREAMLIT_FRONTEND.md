# Streamlit Frontend for arXiv Paper Curator

Beautiful, interactive web interface for searching and querying research papers.

## Features

- **🔍 Question Answering**: Ask natural language questions about research papers
- **📚 Source Citations**: Every answer includes links to source papers
- **⚙️ Configurable Search**: Adjust number of results
- **📊 System Stats**: Real-time API health monitoring
- **💡 Example Questions**: Helpful suggestions to get started

## Quick Start

### Local Development

1. **Install dependencies** (already done if you ran `uv add streamlit`):
   ```bash
   uv add streamlit requests python-dotenv
   ```

2. **Run the app**:
   ```bash
   uv run streamlit run streamlit_app.py
   ```

3. **Open in browser**:
   - Local: http://localhost:8501
   - Network: Check terminal for network URL

### Configure API URL

By default, the app connects to your Railway deployment:
```
https://arxiv-paper-curator-v1-production.up.railway.app
```

To use a different API:
```bash
export API_URL="http://localhost:8000"
uv run streamlit run streamlit_app.py
```

## Deployment Options

### Option 1: Streamlit Cloud (Free, Recommended)

1. **Push code to GitHub** (already done!)

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Deploy**:
   - Click "New app"
   - Select your repository: `sudhirshivaram/arxiv-paper-curator-v1`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

4. **Set environment variables** (if needed):
   - Go to App settings → Secrets
   - Add: `API_URL = "your-railway-url"`

5. **Done!** Your app will be live at: `https://[your-app-name].streamlit.app`

### Option 2: Railway (Paid)

Add to your existing Railway project:

1. **Create new service** in Railway
2. **Connect to GitHub** repo
3. **Set build command**: `pip install -r requirements.txt` (or use uv)
4. **Set start command**: `streamlit run streamlit_app.py --server.port $PORT`
5. **Set environment variables**:
   ```
   API_URL=https://your-api-url.railway.app
   ```

### Option 3: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy app
COPY streamlit_app.py ./
COPY .streamlit .streamlit

# Expose port
EXPOSE 8501

# Run
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Usage

### Ask Questions

1. Navigate to the "Ask Questions" tab
2. Type your question in the text area
3. Click "Search"
4. View:
   - AI-generated answer
   - Number of chunks used
   - Search mode (hybrid)
   - Source paper links

### Example Questions

- "What papers discuss reinforcement learning?"
- "What are the latest advances in transformers?"
- "Tell me about neural network architectures for computer vision"
- "What research has been done on large language models?"

## Customization

### Change Theme

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#your-color"
backgroundColor = "#your-bg-color"
```

### Modify UI

Edit `streamlit_app.py`:
- Add more tabs
- Change layout
- Add filters
- Customize styling in the CSS section

## Troubleshooting

### API Connection Failed

**Problem**: "❌ API Offline" in sidebar

**Solutions**:
1. Check API is running: Visit `https://your-api-url.up.railway.app/docs`
2. Verify `API_URL` environment variable
3. Check CORS settings in FastAPI

### Slow Response

**Problem**: Queries take a long time

**Causes**:
- LLM generation is slow (normal for complex questions)
- API cold start (first request after inactivity)

**Solutions**:
- Use streaming endpoint (future enhancement)
- Reduce `top_k` parameter
- Upgrade Railway plan for better performance

### Deployment Issues

**Problem**: App crashes on Streamlit Cloud

**Solutions**:
1. Check Python version compatibility
2. Verify all dependencies in `pyproject.toml`
3. Check Streamlit Cloud logs

## Architecture

```
User Browser
     ↓
Streamlit Frontend (Port 8501)
     ↓
HTTP POST /api/v1/ask
     ↓
FastAPI Backend (Railway)
     ↓
PostgreSQL + OpenSearch + Jina API
     ↓
Return answer + sources
```

## Next Steps

### Enhancements

- [ ] Add paper browsing (list all papers)
- [ ] Add filtering by category/date/author
- [ ] Add streaming responses for real-time feedback
- [ ] Add chat history
- [ ] Add export functionality (PDF, Markdown)
- [ ] Add paper recommendation
- [ ] Add visualization of search results

### Advanced Features

- [ ] User authentication
- [ ] Save favorite papers
- [ ] Custom collections
- [ ] Collaborative features
- [ ] Analytics dashboard

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Cloud](https://streamlit.io/cloud)
- [Streamlit Gallery](https://streamlit.io/gallery)
