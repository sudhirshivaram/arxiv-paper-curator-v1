# Week 1: Infrastructure Setup and Verification

This folder contains the materials for Week 1 of the arXiv Paper Curator project, which focuses on setting up and verifying the complete infrastructure stack.

## Contents

### `week1_setup.ipynb`
A comprehensive Jupyter notebook that guides students through:

1. **System Requirements and Setup**
   - Understanding each technology component and its purpose
   - Cross-platform installation instructions (Windows, macOS, Linux)
   - Prerequisites verification with automated checking

2. **Infrastructure Architecture**
   - Complete overview of the multi-service architecture
   - Understanding how Docker containers communicate
   - Data persistence and volume management concepts

<p align="center">
  <img src="../../static/week1_infra_setup.png" alt="Week 1 Infrastructure Setup" width="700">
</p>

**Architecture Overview:**
- **FastAPI** (Port 8000): REST API with async support and automatic documentation
- **PostgreSQL 16** (Port 5432): Primary database for paper metadata and content storage
- **OpenSearch 2.19** (Ports 9200, 5601): Hybrid search engine with management dashboards
- **Apache Airflow 3.0** (Port 8080): Workflow orchestration with DAGs and PostgreSQL backend
- **Ollama** (Port 11434): Local LLM server for future RAG implementation
- **Docker Network**: All services communicate via `rag-network` with persistent volumes

3. **Service-by-Service Setup**
   - PostgreSQL database for paper metadata storage
   - OpenSearch for full-text search capabilities
   - Apache Airflow for workflow automation
   - Ollama for local LLM inference
   - FastAPI for REST API endpoints

4. **Verification and Testing**
   - Automated health checks for all services
   - Step-by-step verification procedures
   - Modular Ollama testing (4 focused test cells)
   - Common troubleshooting scenarios and solutions

## Learning Objectives

By completing this week's materials, students will:

- Understand containerization and Docker Compose orchestration
- Learn how to set up a production-grade infrastructure stack
- Gain experience with database design and API development
- Master troubleshooting techniques for multi-service applications
- Learn direct HTTP API testing vs service abstraction layers
- Build confidence working with professional development tools

## Quick Start

### 1. Start All Services
```bash
cd ~/arxiv-paper-curator
docker compose up -d
```

### 2. Verify All Services
```bash
# Check service status
docker compose ps

# Expected output: All services should show "running" state
# Note: Some services may show "unhealthy" during startup (30-60 seconds)
```

### 3. Access Web Interfaces

Once all services are healthy, access these URLs:

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Airflow** | http://localhost:8080 | admin / admin | Workflow management |
| **API Docs** | http://localhost:8000/docs | None | FastAPI interactive docs |
| **OpenSearch Dashboards** | http://localhost:5601 | None | Search analytics UI |
| **Langfuse** | http://localhost:3000 | None | LLM observability |
| **pgAdmin** | http://localhost:5050 | admin@admin.com / admin | PostgreSQL web UI |

### 4. Verify Database Connections

**PostgreSQL:**
```bash
# Via Docker
docker compose exec postgres psql -U rag_user -d rag_db

# Or via Python
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5432,
    database='rag_db', user='rag_user', password='rag_password'
)
print("✓ PostgreSQL connected")
conn.close()
```

**Redis:**
```bash
# Via Docker
docker compose exec redis redis-cli ping
# Should return: PONG

# Or via Python
import redis
r = redis.Redis(host='localhost', port=6379)
print(f"✓ Redis connected: {r.ping()}")
```

### 5. Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return: {"status":"ok","version":"0.1.0",...}
```

## Comprehensive Verification Script

The notebook includes a complete verification script that checks:

### Service Health Check
- ✓ Docker containers running
- ✓ Health check status (with smart detection of startup vs actual issues)
- ⚠ Warns about services unhealthy for >2 minutes
- ✓ Distinguishes between services starting up vs misconfigured

### Database Verification
- ✓ PostgreSQL connectivity
- ✓ Table existence check
- ✓ Airflow metadata tables
- ✓ Application tables (papers, users, embeddings)

### API Connectivity
- ✓ REST API health endpoint
- ✓ JSON response validation
- ✓ Dependent service status

### Credentials Management
- ✓ Reads from .env files
- ✓ Airflow admin password retrieval
- ✓ Database connection strings

## Understanding Service Types

**Web-Accessible Services (Use Browser):**
- Airflow, API Docs, OpenSearch Dashboards, Langfuse, pgAdmin

**Programmatic Services (Use Code/CLI):**
- PostgreSQL (port 5432) - Use `psql`, Python, or pgAdmin
- Redis (port 6379) - Use `redis-cli` or Python
- ClickHouse (port 8123) - Use SQL clients

**Important**: PostgreSQL and Redis don't have web UIs by default. Trying to access `localhost:5432` in a browser will fail - this is normal! Use pgAdmin or database clients instead.

## Ollama Testing (Simplified for Week 1)

The notebook includes modular Ollama testing broken into focused cells:

- **Test 3A**: Check available models
- **Test 3B**: Simple model testing (if models installed) 
- **Test 3C**: Performance analysis
- **Test 3D**: Learning notes and setup commands

### Easy Model Installation (Optional for Week 1)
```bash
# Using Makefile (recommended)
make ollama-pull MODEL=llama3.2:1b
make ollama-test MODEL=llama3.2:1b

# Direct HTTP calls for learning
curl -X POST http://localhost:11434/api/pull -d '{"name":"llama3.2:1b"}'
curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.2:1b","prompt":"Hello","stream":false}'
```

### Recommended Models for Course

- **llama3.2:1b** (1.2GB) - Fast, good for testing
- **llama3.2:3b** (2.0GB) - Balance of speed/quality
- **llama3.1:8b** (4.7GB) - Better quality, slower

**Note**: No models are required for Week 1 - service health check works without them.

## Common Issues and Solutions

### Issue: Service Shows "Unhealthy"

**Diagnosis:**
```bash
# Check logs
docker compose logs <service-name> --tail=50

# Example: Check langfuse
docker compose logs langfuse --tail=100
```

**Common Causes:**
1. **Starting up** - Wait 30-60 seconds for services to initialize
2. **Misconfigured health check** - Service works but health check fails (e.g., langfuse)
3. **Missing dependencies** - Check dependent services are healthy

**Solution:**
- If service just started, wait and recheck
- Test service directly (e.g., `curl http://localhost:3000/api/public/health`)
- If service responds correctly, it's working despite "unhealthy" status

### Issue: Can't Access PostgreSQL at localhost:5432 in Browser

**This is normal!** PostgreSQL is not a web service. Use:
- **pgAdmin** web UI: http://localhost:5050
- **Command line**: `docker compose exec postgres psql -U rag_user -d rag_db`
- **Python**: Use `psycopg2` library
- **Desktop clients**: DBeaver, DataGrip, TablePlus

### Issue: Airflow Password Not Found

**Check multiple locations:**
```bash
# Look in week1 .env
cat ~/arxiv-paper-curator/notebooks/week1/.env | grep AIRFLOW_ADMIN_PASSWORD

# Look in project root .env
cat ~/arxiv-paper-curator/.env | grep AIRFLOW_ADMIN_PASSWORD

# Check logs
docker compose logs airflow | grep -i password
```

**Default credentials:** admin / admin

### Issue: API Returns 404

**Wrong endpoint!** The API uses versioned endpoints:
- ✗ http://localhost:8000/health
- ✓ http://localhost:8000/api/v1/health

Check available endpoints at: http://localhost:8000/docs

## Optional: Add pgAdmin for Database Management

Add this to your `docker-compose.yml`:
```yaml
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: rag-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    networks:
      - rag-network
    depends_on:
      - postgres
      - langfuse-postgres
```

Then:
```bash
docker compose up -d pgadmin
# Access at: http://localhost:5050
```

**Connect to databases in pgAdmin:**
- Host: `postgres` (or `langfuse-postgres`)
- Port: 5432
- Database: `rag_db` (or `langfuse`)
- Username: `rag_user` (or `langfuse`)
- Password: `rag_password` (or `langfuse`)

## Target Audience

This material is designed for:
- **Beginners** who want to learn modern software infrastructure
- **Students** looking to understand how real-world applications are built
- **Professionals** transitioning into software development or DevOps
- **Anyone** interested in building their own AI-powered research tools

## Time Commitment

- **Setup**: 2-3 hours (including software installation and downloads)
- **Notebook completion**: 1-2 hours
- **Verification and testing**: 30 minutes
- **Total**: 3-5 hours

## 📖 Additional Resources

**Week 1 Blog Post:** [The Infrastructure That Powers RAG Systems](https://jamwithai.substack.com/p/the-infrastructure-that-powers-rag)
- Deep dive into each infrastructure component
- Production deployment considerations
- Architecture decision explanations

## Support Resources

If you encounter issues:
1. Check the troubleshooting sections in the notebook
2. Review the common problems and solutions above
3. Ensure all prerequisites are properly installed
4. Run the comprehensive verification script
5. Check service logs: `docker compose logs <service-name>`
6. Ask in Jam With AI substack chat channel

## Next Steps

After completing Week 1, you will be ready to:
- Understand how each service contributes to the overall system
- Confidently troubleshoot infrastructure issues
- Modify and extend the infrastructure as needed
- Proceed to Week 2: arXiv Integration and PDF Processing
- Build confidence in working with professional development environments

## Quick Reference Commands
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs <service-name> --tail=50

# Restart a service
docker compose restart <service-name>

# Check service status
docker compose ps

# Access a service shell
docker compose exec <service-name> bash

# Remove everything (including volumes)
docker compose down -v
```
