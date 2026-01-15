# 🛡️ 3-Tier LLM Fallback - Setup Guide

## What You Have Now:

### 4-Tier Automatic Fallback Strategy:

```
Request → Tier 1: Gemini Flash (FREE)
              ↓ (if fails)
          Tier 2: Gemini Pro (Paid upgrade)
              ↓ (if fails)
          Tier 3: Claude 3.5 Haiku (High quality)
              ↓ (if fails)
          Tier 4: OpenAI gpt-4o-mini (Last resort)
              ↓ (if all fail)
          Error: "LLM service temporarily unavailable"
```

---

## Railway Configuration:

### Environment Variables to Add:

```bash
# Tier 1 & 2: Gemini (already configured)
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your-key
GEMINI_MODEL=gemini-2.5-flash

# Tier 3: Claude Haiku (NEW - get API key)
ANTHROPIC_API_KEY=sk-ant-...your-key
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
ANTHROPIC_MAX_TOKENS=2000

# Tier 4: OpenAI (already configured)
OPENAI_API_KEY=sk-proj-...your-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
```

---

## How to Get Anthropic API Key:

### Step 1: Sign Up
1. Go to: https://console.anthropic.com/
2. Sign up with Google or email
3. Navigate to **API Keys** section

### Step 2: Get Free Credits
- New accounts get **$5 free credits**
- No credit card required for testing
- Enough for ~500-1000 queries

### Step 3: Create API Key
1. Click **"Create Key"**
2. Name it: `railway-production`
3. Copy the key (starts with `sk-ant-`)

### Step 4: Add to Railway
1. Railway Dashboard → Your Service → Variables
2. Add: `ANTHROPIC_API_KEY = sk-ant-...`
3. Railway will auto-restart

---

## Cost Analysis:

### Scenario 1: Normal Job Search (10-20 recruiters/day)
```
50 queries/day × 30 days = 1,500 queries/month

Tier 1 (Gemini Flash): 1,400 queries → $0 (free tier)
Tier 2 (Gemini Pro): 80 queries → $0.40
Tier 3 (Claude): 15 queries → $0.45
Tier 4 (OpenAI): 5 queries → $0.10

Total LLM cost: ~$1/month
Railway: ~$10/month
TOTAL: ~$11/month
```

### Scenario 2: Heavy Traffic (50 recruiters/day)
```
250 queries/day × 30 days = 7,500 queries/month

Tier 1: 6,000 queries → $0
Tier 2: 1,000 queries → $5
Tier 3: 400 queries → $12
Tier 4: 100 queries → $2

Total LLM cost: ~$19/month
Railway: ~$10/month
TOTAL: ~$29/month
```

**For job search, expect $11-15/month total**

---

## Testing the Fallback:

### Local Test (Optional):

You can test the fallback locally by:

1. **Test Tier 1 (Gemini):**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "What are transformers?", "top_k": 3}'
   ```
   Check logs: Should say "Tier 1 SUCCESS"

2. **Simulate Tier 1 Failure:**
   - Temporarily set invalid Gemini key
   - Should automatically try Tier 2, 3, 4
   - Check logs for fallback cascade

---

## Deployment Checklist:

### Before Deploying:

- [x] Anthropic SDK installed (`anthropic>=0.75.0`)
- [x] Claude client service created
- [x] Config updated with Anthropic settings
- [x] 3-tier fallback logic implemented
- [ ] Get Anthropic API key
- [ ] Add ANTHROPIC_API_KEY to Railway
- [ ] Push code to GitHub
- [ ] Railway auto-deploy (10-15 min)
- [ ] Test all tiers working

---

## What the Logs Will Show:

### Successful Tier 1:
```
INFO: Successfully generated answer using primary LLM provider
```

### Fallback to Tier 2:
```
WARNING: Tier 1 (Primary) failed: quota exceeded
INFO: Tier 2: Trying Gemini Pro fallback...
INFO: ✅ Tier 2 SUCCESS: Gemini Pro answered
```

### Fallback to Tier 3:
```
WARNING: Tier 2 (Gemini Pro) failed: ...
INFO: Tier 3: Trying Claude Haiku fallback...
INFO: ✅ Tier 3 SUCCESS: Claude Haiku answered
```

### Fallback to Tier 4:
```
WARNING: Tier 3 (Claude) failed: ...
INFO: Tier 4: Trying OpenAI fallback (last resort)...
INFO: ✅ Tier 4 SUCCESS: OpenAI answered
```

### All Tiers Failed:
```
ERROR: ❌ ALL TIERS FAILED - Tier 4 (OpenAI): ...
HTTP 503: LLM service temporarily unavailable
```

---

## Next Steps:

1. **Get Anthropic API Key**: https://console.anthropic.com/
2. **Add to Railway**: `ANTHROPIC_API_KEY` variable
3. **Push code**: Already committed, ready to push
4. **Deploy**: Railway auto-deploys
5. **Test**: Try a query, check logs for tier usage

---

## Questions?

**"Do I need all 3 API keys?"**
- Recommended: Yes, for maximum reliability
- Minimum: Just Gemini (works, but no fallback)

**"What if I don't want to pay for Claude?"**
- Use the $5 free credits
- Or skip Tier 3, fallback goes: Gemini → OpenAI

**"Can I change the tier order?"**
- Yes, edit `ask.py` fallback logic
- Current order optimized for cost vs quality

---

**Ready to deploy! Get your Anthropic API key and let's push to Railway!** 🚀
