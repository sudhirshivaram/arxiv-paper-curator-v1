# 🐛 Debugging Production Deployment Issues

## Current Issue

**Error:** `authors field validation error - still getting list instead of string`

**Root Cause:** Railway hasn't deployed the fix yet (still running old code)

---

## ✅ Step-by-Step Fix

### 1. Check Railway Deployment Status

**Go to Railway Dashboard:**
```
https://railway.app/dashboard
```

**Look for:**
- Your project: `arxiv-paper-curator-v1` (or similar)
- Deployment status in the "Deployments" tab

**Expected Status:**
- ✅ **Active** = Deployment complete (green check)
- 🟡 **Building** = Still building the Docker image
- 🟡 **Deploying** = Pushing to production
- ❌ **Failed** = Build/deployment error

### 2. Check Build Logs

**In Railway Dashboard:**
1. Click on your service
2. Go to "Deployments" tab
3. Click on the latest deployment
4. Check "Build Logs" and "Deploy Logs"

**Look for:**
- Build errors
- Missing dependencies
- Python version issues
- Docker build failures

### 3. If Deployment is Still in Progress

**Wait 5-10 minutes** (Railway can be slow sometimes)

Then test again:
```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/hybrid-search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "size": 3}' | jq '.'
```

**Expected:** Should return results (not 500 error)

### 4. If Deployment Failed

**Check these common issues:**

#### Issue 1: Wrong Branch
- Railway might be tracking wrong branch
- **Fix:** Settings → Source → Change branch to `main`

#### Issue 2: Build Failure
- Check build logs for errors
- Common: Missing requirements, Python version mismatch
- **Fix:** Ensure Railway is using Python 3.12

#### Issue 3: Environment Variables
- Missing env vars can cause startup failures
- **Fix:** Check Settings → Variables
- Ensure these are set:
  - `POSTGRES_DATABASE_URL`
  - `OPENSEARCH__HOST`
  - `JINA__API_KEY`
  - `OPENAI_API_KEY` (optional)

#### Issue 4: Deployment Got Stuck
- Sometimes Railway deployments hang
- **Fix:** Manual redeploy

### 5. Force Manual Redeploy

**If deployment seems stuck:**

1. Go to Railway Dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Click "Redeploy" button (top right)
5. Or: Settings → "Trigger Deploy" button

Alternatively, push an empty commit:
```bash
git commit --allow-empty -m "Force Railway redeploy"
git push sushiva main
```

---

## 🧪 Testing the Fix

Once deployment shows "Active" status:

### Test 1: Basic Health Check
```bash
curl https://arxiv-paper-curator-v1-production.up.railway.app/ping
```

**Expected:** `{"status": "ok"}`

### Test 2: Authors Field Fix
```bash
curl -X POST "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/hybrid-search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer", "size": 3}' | jq '.hits[0].authors'
```

**Expected:** `"John Doe, Jane Smith"` (string, not list, no error)

### Test 3: Run Benchmarks
```bash
cd benchmarks
export API_BASE_URL=https://arxiv-paper-curator-v1-production.up.railway.app/api/v1
export OPENAI_API_KEY=your-key-here
python run_benchmark.py
```

**Expected:** Should complete without 500 errors

---

## 🔍 Check What Code is Running

### Verify Deployed Commit

**Check Railway logs for:**
```
Building from commit: ba8dfdc
```

**Or check via API** (if you have a version endpoint):
```bash
curl https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/version
```

### Verify Fix is in Deployed Code

**The fix we pushed:**
- Commit: `0817e88`
- File: `src/schemas/api/search.py`
- Change: `authors: Optional[str]` (was `Optional[list[str] | str]`)

**Check Railway is deploying from correct repo:**
- Settings → Source
- Should show: `sushiva/arxiv-paper-curator-v1`
- Branch: `main`

---

## 📊 Current Status Timeline

| Time | Action | Status |
|------|--------|--------|
| 16:00 | Fixed bug locally | ✅ Done |
| 16:15 | Pushed to `sushiva` repo | ✅ Done |
| 16:16 | Railway deployment triggered | 🟡 In Progress |
| 16:30 | Benchmarks tested | ❌ 500 errors (old code) |
| **Now** | **Waiting for deployment** | ⏳ **Check Railway** |

---

## 🚨 If Nothing Works

### Last Resort: Check Railway Service Settings

1. **Runtime Version:** Python 3.12
2. **Start Command:** Should be something like:
   ```
   uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Root Directory:** `/` (or your project root)

### Contact Railway Support

If deployment consistently fails:
- Railway Dashboard → Help → Contact Support
- Provide: project ID, error logs, deployment ID

---

## ✅ Success Checklist

Once fixed, you should see:

- [ ] Railway deployment status: "Active" (green)
- [ ] Build logs show commit: `ba8dfdc`
- [ ] API returns results (no 500 errors)
- [ ] Authors field is string (not list)
- [ ] Benchmarks run successfully
- [ ] Real metrics obtained

---

## 🎯 Quick Reference Commands

```bash
# Test production API
curl -X POST "$API_BASE_URL/hybrid-search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "size": 3}'

# Force redeploy
git commit --allow-empty -m "Redeploy"
git push sushiva main

# Check Railway status
open https://railway.app/dashboard
```

---

**Current Issue:** Railway deployment not complete. Check dashboard and wait for "Active" status. ⏳
