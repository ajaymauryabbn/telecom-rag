# Cloud Deployment Guide - Telecom RAG

## Quick Start for Google Cloud Run

### Required Environment Variables

Set these in your Cloud Run service configuration:

```bash
# Required
OPENAI_API_KEY=sk-xxx                    # Your OpenAI API key
LLM_PROVIDER=openai                       # Use OpenAI (not Gemini) for reliability
EMBEDDING_PROVIDER=openai                 # Use OpenAI embeddings (no model download)

# Optional - Feature Flags
ENABLE_RERANK=false                       # Disable reranker to speed up cold starts
ENABLE_HYBRID=true                        # Keep hybrid search enabled
ENABLE_REDIS=false                        # Disable Redis if not available

# Optional - External Services
REDIS_URL=redis://your-redis-host:6379/0  # If using Redis
HF_TOKEN=hf_xxx                           # If using HuggingFace models
```

### Cloud Run Settings

```bash
gcloud run services update telecom-rag \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai,ENABLE_RERANK=false"
```

---

## Deployment Checklist

### Before Deployment

- [ ] Set `OPENAI_API_KEY` in environment
- [ ] Set `LLM_PROVIDER=openai`
- [ ] Set `EMBEDDING_PROVIDER=openai`
- [ ] Set `ENABLE_RERANK=false` (optional - speeds up cold start)
- [ ] Allocate 4GB+ memory
- [ ] Set timeout to 300s

### After Deployment

- [ ] Verify app loads without errors
- [ ] Test a sample query
- [ ] Check logs for warnings

---

## Common Issues & Solutions

### 1. "google-generativeai not installed"

**Cause:** `LLM_PROVIDER=gemini` but package not available.

**Fix:** Set `LLM_PROVIDER=openai` in environment variables.

### 2. Cold Start Timeout

**Cause:** App takes too long to start (model downloads, index building).

**Fix:**
- Set `EMBEDDING_PROVIDER=openai` (no model download)
- Set `ENABLE_RERANK=false` (no reranker model download)
- Increase timeout to 300s

### 3. Out of Memory

**Cause:** Default 512MB not enough for models + ChromaDB.

**Fix:** Set memory to 4GB: `--memory=4Gi`

### 4. Redis Connection Failed

**Cause:** No Redis server in cloud environment.

**Fix:** Set `ENABLE_REDIS=false` or deploy a Redis instance (Cloud Memorystore).

### 5. HuggingFace Rate Limits

**Cause:** Model downloads hit rate limits.

**Fix:**
- Set `HF_TOKEN` environment variable
- Or use `EMBEDDING_PROVIDER=openai` to avoid HF downloads

---

## Feature Flag Reference

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_RERANK` | true | Cross-encoder reranking (slower but more accurate) |
| `ENABLE_HYBRID` | true | BM25 + Dense hybrid search |
| `ENABLE_REDIS` | true | Redis for semantic caching |

### Recommended Cloud Settings

```bash
# Fast startup, reliable operation
ENABLE_RERANK=false   # Disable for faster cold starts
ENABLE_HYBRID=true    # Keep for better search quality
ENABLE_REDIS=false    # Unless you have Redis available
```

---

## Docker Build

```dockerfile
# Ensure requirements are installed
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Deploy

```bash
# Build
docker build -t telecom-rag .

# Test locally
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-xxx \
  -e LLM_PROVIDER=openai \
  -e EMBEDDING_PROVIDER=openai \
  telecom-rag

# Deploy to Cloud Run
gcloud run deploy telecom-rag \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --timeout 300s \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai,OPENAI_API_KEY=sk-xxx"
```

---

## Performance Tuning

### For Faster Cold Starts

1. Use OpenAI embeddings (no download): `EMBEDDING_PROVIDER=openai`
2. Disable reranker: `ENABLE_RERANK=false`
3. Pre-build BM25 index in Docker image (advanced)

### For Better Response Quality

1. Enable reranker: `ENABLE_RERANK=true`
2. Enable hybrid search: `ENABLE_HYBRID=true`
3. Use larger context: Increase `CONTEXT_MAX_TOKENS` in config

### For Lower Costs

1. Use smaller memory: `--memory=2Gi` (if reranker disabled)
2. Set min instances to 0: `--min-instances=0`
3. Use `gpt-4o-mini` (already default)

---

## Monitoring

### Check Logs

```bash
gcloud run services logs read telecom-rag --region us-central1
```

### Look For

- `✅ Initialized OpenAI LLM` - LLM working
- `✅ Initialized OpenAI embeddings` - Embeddings working
- `⚠️ Redis unavailable` - Expected if no Redis
- `❌ Error initializing` - Something failed

---

## Troubleshooting Commands

```bash
# Check service status
gcloud run services describe telecom-rag --region us-central1

# View recent logs
gcloud run services logs read telecom-rag --limit 100

# Update environment variables
gcloud run services update telecom-rag \
  --region us-central1 \
  --set-env-vars="KEY=value"

# Redeploy
gcloud run deploy telecom-rag --source .
```
