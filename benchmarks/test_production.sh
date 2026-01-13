#!/bin/bash

# Quick script to test production API and debug 500 errors

API_URL="${API_BASE_URL:-https://arxiv-paper-curator-v1-production.up.railway.app/api/v1}"

echo "🔍 Testing Production API"
echo "========================="
echo "API URL: $API_URL"
echo ""

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
curl -s "${API_URL%/api/v1}/ping" | jq '.' 2>/dev/null || echo "❌ Health check failed"
echo ""

# Test 2: Simple search (should reveal actual error)
echo "2️⃣ Testing hybrid search (detailed error)..."
echo ""
curl -v -X POST "$API_URL/hybrid-search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer attention mechanism",
    "size": 3,
    "use_hybrid": true
  }' 2>&1 | grep -A 50 "HTTP/1.1" | head -60

echo ""
echo ""
echo "========================="
echo "💡 Next Steps:"
echo ""
echo "If you see 500 error:"
echo "1. Check Railway logs: https://railway.app/dashboard"
echo "2. Look for the actual Python traceback in logs"
echo "3. Verify deployment finished (Status: 'Active')"
echo ""
echo "If deployment is still in progress:"
echo "   Wait 2-3 more minutes and run this again:"
echo "   bash benchmarks/test_production.sh"
