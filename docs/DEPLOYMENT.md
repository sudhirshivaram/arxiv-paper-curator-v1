# 🚀 Cloud Deployment Guide - Digital Ocean

Complete guide to deploy your arXiv Paper Curator RAG system to Digital Ocean.

## 📋 Prerequisites

- Digital Ocean account
- Domain name (optional but recommended)
- Jina AI API key (for embeddings)
- OpenAI/Anthropic API key (optional - for external LLM)

## 💰 Cost Estimation

**Recommended Droplet:** Basic - 8GB RAM / 4 vCPUs / 160GB SSD
- **Cost:** $48/month
- **Good for:** 10,000+ requests/month, testing & small production

**Production Droplet:** General Purpose - 16GB RAM / 4 vCPUs / 320GB SSD
- **Cost:** $96/month
- **Good for:** High traffic, full PDF processing

## 🚀 Deployment Steps

### Step 1: Create Digital Ocean Droplet

```bash
# Option A: Via Digital Ocean Dashboard
1. Go to https://cloud.digitalocean.com/droplets/new
2. Choose: Ubuntu 24.04 LTS
3. Size: Basic ($48/mo) or General Purpose ($96/mo)
4. Choose datacenter region (closest to your users)
5. Select "Docker" from Marketplace Apps (pre-installed Docker)
6. Add SSH key for secure access
7. Create Droplet

# Option B: Via doctl CLI
doctl compute droplet create arxiv-rag \
  --image docker-20-04 \
  --size s-4vcpu-8gb \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID
```

### Step 2: Connect to Your Droplet

```bash
# Get your droplet IP
doctl compute droplet list

# SSH into droplet
ssh root@YOUR_DROPLET_IP
```

### Step 3: Prepare the Server

```bash
# Update system
apt update && apt upgrade -y

# Install required tools
apt install -y git curl

# Verify Docker is installed
docker --version
docker compose version

# Create application directory
mkdir -p /opt/arxiv-rag
cd /opt/arxiv-rag
```

### Step 4: Clone and Configure

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/arxiv-paper-curator.git .

# Create production environment file
cp .env.production.example .env.production

# Edit configuration (use nano or vim)
nano .env.production
```

**IMPORTANT:** Update these values in `.env.production`:
- Set `DEBUG=false`
- Change PostgreSQL password
- Add your `JINA_API_KEY`
- Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (if using external LLM)
- Generate and set `SECRET_KEY` and `API_KEY`
- Set your domain in `ALLOWED_HOSTS` and `CORS_ORIGINS`

### Step 5: Pull Ollama Model (if using local LLM)

```bash
# Start only Ollama temporarily
docker compose -f compose.production.yml up -d ollama

# Wait 30 seconds for it to start
sleep 30

# Pull the model (this takes 5-10 minutes)
docker exec rag-ollama ollama pull llama3.2:1b

# Verify
docker exec rag-ollama ollama list
```

### Step 6: Deploy All Services

```bash
# Stop the temporary Ollama
docker compose -f compose.production.yml down

# Start all services
docker compose -f compose.production.yml up -d

# Check status
docker compose -f compose.production.yml ps

# View logs
docker compose -f compose.production.yml logs -f
```

### Step 7: Initialize the System

```bash
# Wait for services to be healthy (2-3 minutes)
sleep 120

# Check health
curl http://localhost:8000/api/v1/health

# Trigger initial paper ingestion
docker exec rag-airflow airflow dags trigger arxiv_paper_ingestion
```

### Step 8: Configure Firewall

```bash
# UFW firewall setup
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS (for SSL later)
ufw enable

# Verify
ufw status
```

### Step 9: Test Your Deployment

```bash
# From your local machine
curl http://YOUR_DROPLET_IP/health

# Test search
curl -X POST http://YOUR_DROPLET_IP/api/v1/hybrid-search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "size": 5}'

# Test RAG (wait 15-20 seconds)
curl -X POST http://YOUR_DROPLET_IP/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 2}'
```

## 🌐 Domain Setup (Optional but Recommended)

### Step 1: Configure DNS

1. Go to your domain registrar
2. Add an A record:
   - **Name:** @ (or your subdomain)
   - **Value:** YOUR_DROPLET_IP
   - **TTL:** 3600

### Step 2: Update nginx Configuration

```bash
# Edit nginx config
nano nginx/nginx.conf

# Replace 'server_name _;' with your domain
server_name your-domain.com www.your-domain.com;

# Restart nginx
docker compose -f compose.production.yml restart nginx
```

### Step 3: Add SSL Certificate (Let's Encrypt)

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is configured automatically
# Test renewal
certbot renew --dry-run
```

## 📊 Monitoring & Maintenance

### Check Service Status

```bash
# All services
docker compose -f compose.production.yml ps

# Resource usage
docker stats

# Logs for specific service
docker compose -f compose.production.yml logs api
docker compose -f compose.production.yml logs airflow
```

### Database Backup

```bash
# Backup PostgreSQL
docker exec rag-postgres pg_dump -U rag_user rag_db > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20250130.sql | docker exec -i rag-postgres psql -U rag_user -d rag_db
```

### Update Application

```bash
cd /opt/arxiv-rag

# Pull latest changes
git pull

# Rebuild and restart
docker compose -f compose.production.yml down
docker compose -f compose.production.yml up -d --build

# Check logs
docker compose -f compose.production.yml logs -f
```

## 🔒 Security Best Practices

1. **Change Default Passwords**
   - PostgreSQL password in `.env.production`
   - Generate strong `SECRET_KEY` and `API_KEY`

2. **Firewall Configuration**
   - Only expose ports 80, 443, and 22
   - Consider restricting SSH to specific IPs

3. **Regular Updates**
   - Update Docker images monthly
   - Monitor security advisories

4. **Backup Strategy**
   - Daily database backups
   - Store backups off-server (Digital Ocean Spaces)

5. **Monitoring**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure log rotation

## 🎯 Production Checklist

- [ ] Droplet created and accessible
- [ ] Docker and dependencies installed
- [ ] Repository cloned
- [ ] `.env.production` configured with secure values
- [ ] Ollama model pulled (if using local LLM)
- [ ] All services running (`docker compose ps`)
- [ ] Health endpoint responding
- [ ] Firewall configured
- [ ] Domain DNS configured (optional)
- [ ] SSL certificate installed (optional)
- [ ] Initial data ingestion triggered
- [ ] Backup strategy implemented
- [ ] Monitoring configured

## 💡 Using External LLM (OpenAI/Anthropic)

To reduce server costs, you can use external LLM APIs instead of running Ollama locally.

### Edit `.env.production`:

```bash
# Comment out Ollama settings
# OLLAMA_HOST=http://ollama:11434
# OLLAMA__DEFAULT_MODEL=llama3.2:1b

# Add OpenAI or Anthropic
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Remove Ollama from `compose.production.yml`:

Comment out the entire `ollama` service section.

**Benefits:**
- Lower server costs (can use smaller droplet)
- Better LLM quality (GPT-4, Claude)
- No GPU needed

**Trade-offs:**
- Per-request costs (~$0.001-0.01 per query)
- Requires internet connection
- Data sent to external API

## 📞 Support & Troubleshooting

### Common Issues

**Issue:** Services won't start
```bash
# Check Docker memory
docker system df
docker system prune -a

# Check logs
docker compose -f compose.production.yml logs
```

**Issue:** Out of memory
```bash
# Upgrade droplet size or disable PDF processing
# Edit airflow/dags/arxiv_ingestion/fetching.py
process_pdfs=False
```

**Issue:** Slow responses
```bash
# Use external LLM API (OpenAI/Anthropic)
# Or increase droplet size to 16GB
```

## 🎉 Success!

Your RAG system is now deployed to the cloud! Access it at:
- **API:** http://your-domain.com/api/v1/
- **Docs:** http://your-domain.com/docs
- **Airflow:** http://your-domain.com/airflow/

Next steps:
- Monitor system performance
- Set up automated backups
- Configure monitoring alerts
- Scale as needed

---

**Questions?** Check the [main README](README.md) or open an issue on GitHub.
