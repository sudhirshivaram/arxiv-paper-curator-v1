# Google Gemini Setup Guide

## Quick Start - Get Your FREE Gemini API Key (2 minutes)

### Step 1: Get API Key
1. Go to: https://aistudio.google.com/app/apikey
2. Click **"Get API Key"** or **"Create API Key"**
3. Select your Google account (or create one)
4. Click **"Create API key in new project"**
5. **Copy the API key** (starts with `AIza...`)

### Step 2: Add to .env File
Open `.env` and replace `YOUR_GEMINI_API_KEY_HERE` with your actual key:

```bash
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

### Step 3: Test!
Run the test command provided by Claude.

## Why Gemini?

✅ **FREE Tier**: 60 requests/min (vs OpenAI's 3-5)
✅ **Fast**: 2-3 seconds response time
✅ **No Credit Card**: Works immediately
✅ **High Quality**: Google's latest model (Gemini 1.5 Flash)

## Troubleshooting

**Error: "API key not valid"**
- Make sure you copied the full key (starts with `AIza`)
- No spaces or quotes around the key in .env

**Error: "quota exceeded"**
- Free tier: 60 requests/min, 1500/day
- Just wait a minute and try again
