---
title: Telecom RAG
emoji: 📡
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
# Telecom RAG Assistant

AI-powered Retrieval-Augmented Generation (RAG) system for telecom operations support, deployed on Hugging Face Spaces.

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/ajaymauryabbn/telecom-rag)
[![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python)](https://www.python.org/)
![RAG](https://img.shields.io/badge/RAG-LangChain-green)
![VectorDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![UI](https://img.shields.io/badge/UI-Streamlit-red)

## Live Demo

**Production URL**: https://huggingface.co/spaces/ajaymauryabbn/telecom-rag

> **Note**: Hosted on Hugging Face Spaces (Docker). The application is fast and prevents cold-starts within 48 hours of activity.

Try asking: *"What is HARQ in 5G?"* or *"Explain MIMO technology"*

---

## Demo

![Telecom RAG Demo](docs/hf_demo.webp)

> *Ask any telecom question — the system retrieves relevant documents, generates a grounded answer, and shows a Trust Score with source citations.*

---

## Features

- **Hybrid Search**: Combines BM25 (keyword) + Dense (semantic) + RRF fusion
- **32,802 Documents**: Comprehensive telecom knowledge base
- **Intelligent Routing**: Query intent classification
- **RAGAS Evaluation**: 6-metric answer quality assessment
- **Trustworthy AI**: TLM Trust Scoring for hallucination detection
- **Redis Caching**: Semantic caching for faster responses
- **Cloud Native**: Optimized for Google Cloud Run
- **Rate Limiting**: 50 requests/minute per session

---

## Architecture

```
User Query → Glossary Expansion → Hybrid Retrieval → Reranking → LLM Generation → Evaluation
                                        ↓
                            BM25 + Dense + RRF Fusion
```

**Key Components**:
- **Vector Store**: ChromaDB with 3072-dim embeddings
- **LLM**: OpenAI GPT-4o-mini (with Gemini fallback)
- **Embeddings**: OpenAI text-embedding-3-large
- **Cache**: Redis with semantic similarity matching
- **Evaluation**: RAGAS metrics + TLM Trust Score

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system design.

---

## Performance

| Metric | Value |
|--------|-------|
| **Documents** | 32,802 |
| **Cold Start** | 15-30s |
| **Warm Response** | 1-3s |
| **Accuracy** | 85%+ (RAGAS) |
| **Memory** | 2-3GB |
| **Deployment** | Google Cloud Run |

---

## Tech Stack

- **Backend**: Python 3.9, Streamlit
- **LLM**: OpenAI GPT-4o-mini, Google Gemini
- **Vector DB**: ChromaDB
- **Search**: BM25 + Dense embeddings + RRF
- **Cache**: Redis (optional)
- **Deployment**: Docker, Google Cloud Run

---

## Quick Start

### Prerequisites

- Python 3.9+
- Docker
- OpenAI API Key
- (Optional) Google Cloud account for deployment

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/ajaymauryabbn/telecom-rag.git
cd telecom-rag
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Run with Docker Compose**
```bash
docker-compose up
```

4. **Access the app**
```
http://localhost:8501
```

### Cloud Deployment

```bash
# Deploy to Google Cloud Run
./deploy-cloudbuild.sh
```

See [`CLOUD_DEPLOYMENT.md`](CLOUD_DEPLOYMENT.md) for detailed instructions.

---

## Project Structure

```
telecom-rag/
├── app.py                      # Streamlit UI
├── src/
│   ├── retriever.py           # RAG orchestration
│   ├── vector_store.py        # ChromaDB interface
│   ├── hybrid_search.py       # BM25 + Dense + RRF
│   ├── llm.py                 # LLM integration
│   ├── embeddings.py          # Embedding generation
│   ├── cache.py               # Semantic caching
│   ├── evaluation.py          # RAGAS metrics
│   └── rate_limiter.py        # Rate limiting
├── data/
│   ├── raw/                   # Source documents
│   ├── chroma_db/             # Vector store
│   └── glossary/              # Telecom terms
├── scripts/                   # Dev/build utilities
│   ├── Dockerfile.optimized   # BuildKit-optimized image
│   ├── build-orbstack.sh      # OrbStack build script
│   ├── build-fast.sh          # Fast BuildKit build
│   └── setup-github.sh        # Repo setup helper
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Local orchestration
└── deploy-cloudbuild.sh       # Cloud deployment
```

---

## Configuration

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=openai              # or "gemini"
OPENAI_API_KEY=sk-proj-...       # Required
GOOGLE_API_KEY=...               # Optional

# Embeddings
EMBEDDING_PROVIDER=openai        # or "local"

# Feature Flags
ENABLE_RERANK=false              # Faster cold start
ENABLE_HYBRID=true               # Better accuracy
ENABLE_REDIS=false               # Optional caching

# HuggingFace (for dataset access)
HF_TOKEN=hf_...
```

### Cloud Run Settings

- **Memory**: 4Gi
- **CPU**: 2
- **Timeout**: 300s
- **Concurrency**: 80

---

## Documentation

- **[Architecture](ARCHITECTURE.md)** - Comprehensive system design
- **[Cloud Deployment Guide](CLOUD_DEPLOYMENT.md)** - Production deployment
- **[Docker Instructions](DOCKER_INSTRUCTIONS.md)** - Container setup

---

## Testing

```bash
# Run accuracy tests
python tests/test_accuracy.py

# Run architecture verification
python tests/verify_architecture.py

# Run LLM evaluation tests
python tests/test_llm_eval.py
```

---

## Evaluation Metrics

The system uses **RAGAS** (Retrieval-Augmented Generation Assessment) with 6 metrics:

1. **Faithfulness**: Answer grounded in context
2. **Answer Relevancy**: Addresses the question
3. **Context Precision**: Relevant chunks ranked high
4. **Context Recall**: All needed info retrieved
5. **Context Relevancy**: Retrieved chunks are relevant
6. **TLM Trust Score**: Hallucination detection

---

## Security

- API keys stored in `.env` (not committed)
- `.gitignore` configured for secrets
- `.gcloudignore` prevents secret uploads
- Rate limiting enabled
- Input validation
- No PII storage

---

## Acknowledgments

- **Dataset**: TeleQnA (HuggingFace)
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-3-large
- **Framework**: LangChain, Streamlit
- **Deployment**: Google Cloud Run
