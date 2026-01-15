# Repository Rename Guide: "Dual-Domain Research Assistant"

## Suggested Repository Names

Choose one that reflects the dual-domain nature:

1. **dual-domain-research-assistant** ⭐ (Recommended)
   - Clear, professional, describes what it does

2. **dual-domain-rag-system**
   - More technical, emphasizes RAG architecture

3. **research-financial-rag-curator**
   - Descriptive of both domains

4. **arxiv-sec-rag-system**
   - Concise, mentions both data sources

---

## Step-by-Step Rename Process

### Step 1: Rename on GitHub (2 minutes)

**For sushiva account:**
1. Go to: https://github.com/sushiva/arxiv-paper-curator-v1/settings
2. Scroll to "Repository name" section
3. Change to: `dual-domain-research-assistant`
4. Click "Rename" button
5. GitHub will redirect you to the new URL

**For sudhirshivaram account (portfolio):**
1. Go to: https://github.com/sudhirshivaram/arxiv-paper-curator-v1/settings
2. Same process as above
3. Change to: `dual-domain-research-assistant`

**✅ GitHub automatically sets up redirects from old URLs!**

---

### Step 2: Update Local Git Remotes (1 minute)

Run these commands after GitHub rename:

```bash
# Update both remotes with new repo name
git remote set-url origin git@github.com-portfolio:sudhirshivaram/dual-domain-research-assistant.git
git remote set-url sushiva git@github.com:sushiva/dual-domain-research-assistant.git

# Verify the change
git remote -v
```

**Expected output:**
```
origin  git@github.com-portfolio:sudhirshivaram/dual-domain-research-assistant.git (fetch)
origin  git@github.com-portfolio:sudhirshivaram/dual-domain-research-assistant.git (push)
sushiva git@github.com:sushiva/dual-domain-research-assistant.git (fetch)
sushiva git@github.com:sushiva/dual-domain-research-assistant.git (push)
```

---

### Step 3: Update Documentation References

Files that reference the old repo name:

**README.md:**
- Line with `cd arxiv-paper-curator-v1` → `cd dual-domain-research-assistant`
- Directory structure references

**FRONTEND_README.md:**
- Repository references

**GIT_WORKFLOW.md:**
- Repository URLs

**Other documentation:**
- PRODUCTION_STATUS.md
- CURRENT_STATUS.md
- BENCHMARK_SETUP_COMPLETE.md
- SYNC_STATUS.md

---

### Step 4: Important - Deployment URLs Don't Change

**⚠️ These URLs will STAY THE SAME:**

- Railway API: `https://arxiv-paper-curator-v1-production.up.railway.app`
- Streamlit UI: `https://arxiv-paper-curator-v1-demo.streamlit.app`

**Why?** These are deployment URLs, not tied to GitHub repo name. Changing them requires redeployment.

**You can keep these URLs OR redeploy with new names:**
- Railway: Can rename service in Railway dashboard
- Streamlit: Can redeploy from new repo URL

---

## Quick Commands (Copy-Paste After GitHub Rename)

```bash
# 1. Update git remotes
git remote set-url origin git@github.com-portfolio:sudhirshivaram/dual-domain-research-assistant.git
git remote set-url sushiva git@github.com:sushiva/dual-domain-research-assistant.git

# 2. Verify
git remote -v

# 3. Test connection
git fetch origin
git fetch sushiva

# 4. Update README references (example)
# You can do this manually or use find-replace in your editor
```

---

## Resume Update After Rename

**Before (Old):**
```
arXiv Paper Curator - Dual-Domain Production RAG System
GitHub: github.com/sushiva/arxiv-paper-curator-v1
```

**After (New):**
```
Dual-Domain Research Assistant - Production RAG System
GitHub: github.com/sushiva/dual-domain-research-assistant
```

**Much clearer what the project does!**

---

## Optional: Update Deployment URLs

If you want matching URLs everywhere:

### Railway Rename:
1. Go to Railway dashboard
2. Select your project
3. Settings → Change project name
4. New URL: `https://dual-domain-research-assistant-production.up.railway.app`

### Streamlit Rename:
1. Redeploy from new GitHub repo URL
2. Or rename in Streamlit dashboard settings
3. New URL: `https://dual-domain-research-assistant.streamlit.app`

---

## Checklist

- [ ] Rename GitHub repo (sushiva account)
- [ ] Rename GitHub repo (sudhirshivaram account)
- [ ] Update local git remotes
- [ ] Test `git fetch` and `git push` work
- [ ] Update README.md references
- [ ] Update other documentation files
- [ ] Update resume with new repo name
- [ ] (Optional) Rename Railway deployment
- [ ] (Optional) Rename Streamlit deployment

---

## Why This Rename Matters for Interviews

**Old Name:** "arXiv Paper Curator"
- Sounds single-domain (just arXiv)
- Undersells your dual-domain architecture

**New Name:** "Dual-Domain Research Assistant"
- Immediately clear it handles multiple domains
- Professional naming
- Highlights the architectural complexity
- Better for resume impact

**First impression matters** - the name should reflect the sophistication of your system!
