# Telecom RAG System - Architecture & Technical Documentation

---

## Executive Summary

The **Telecom RAG (Retrieval-Augmented Generation)** system is an AI-powered knowledge assistant designed for telecom operations support. Built on the validated Telco-RAG architecture, it provides intelligent answers to technical queries about 5G/LTE networks, 3GPP standards, network operations, and performance optimization.

### Key Achievements

| Metric | Value |
|--------|-------|
| **Knowledge Base** | 12,500+ telecom documents |
| **Glossary Terms** | 81+ telecom-specific terms |
| **Search Strategy** | Hybrid (BM25 + Dense + RRF) |
| **Evaluation Metrics** | 6 RAGAS-style metrics |
| **Cloud-Ready** | Google Cloud Run optimized |

---

## 1. System Architecture

### 1.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Streamlit)                       │
│                              📡 app.py                                   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        RETRIEVER ORCHESTRATOR                            │
│                          src/retriever.py                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Glossary │  │  Router  │  │  Cache   │  │Evaluator │  │   LLM    │  │
│  │ Enhance  │  │ Strategy │  │ Semantic │  │  RAGAS   │  │Generator │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          RETRIEVAL PIPELINE                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │ Vector Store │    │Hybrid Search│    │  Reranker   │                │
│  │  ChromaDB   │ ──▶│ BM25 + RRF  │ ──▶│Cross-Encoder│                │
│  │   Dense     │    │   Sparse    │    │  Precision  │                │
│  └─────────────┘    └─────────────┘    └─────────────┘                │
└───────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │  ChromaDB   │    │    Redis    │    │  BM25 Index │                │
│  │  Vectors    │    │   Cache     │    │   Pickle    │                │
│  └─────────────┘    └─────────────┘    └─────────────┘                │
└───────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Summary

| Component | File | Purpose |
|-----------|------|---------|
| **Config** | `src/config.py` | Environment variables, feature flags |
| **Embeddings** | `src/embeddings.py` | OpenAI text-embedding-3-large (3072 dims) |
| **Vector Store** | `src/vector_store.py` | ChromaDB for dense retrieval |
| **Hybrid Search** | `src/hybrid_search.py` | BM25 + Dense + RRF fusion |
| **Reranker** | `src/reranker.py` | Cross-encoder (ms-marco-MiniLM) |
| **Router** | `src/router.py` | NN-based query classification |
| **Glossary** | `src/glossary.py` | 81+ telecom term expansion |
| **Cache** | `src/cache.py` | Redis semantic cache (0.95 threshold) |
| **Evaluator** | `src/evaluation.py` | RAGAS metrics + TLM Trust Score |
| **LLM** | `src/llm.py` | OpenAI GPT-4o-mini / Gemini |
| **Retriever** | `src/retriever.py` | Main RAG orchestrator |
| **Data Loader** | `src/data_loader.py` | Document ingestion pipeline |
| **Rate Limiter** | `src/rate_limiter.py` | 50 req/min per session |
| **App** | `app.py` | Streamlit web interface |

---

## 2. Core Features

### 2.1 Hybrid Search (BM25 + Dense + RRF)

The system implements **three-stage retrieval** for optimal precision and recall:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Stage 1:       │     │   Stage 2:       │     │   Stage 3:       │
│   Dense Search   │────▶│   BM25 Search    │────▶│   RRF Fusion     │
│   (Semantic)     │     │   (Keyword)      │     │   (k=60)         │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                         │                        │
        ▼                         ▼                        ▼
   Concept Match            Exact Match             Best of Both
   "5G latency"           "HARQ process"          Combined Ranking
```

**RRF Formula:**
```
score(d) = Σ 1/(k + rank_i(d))
```
Where `k=60` (per Telco-RAG specification)

**Implementation:** `src/hybrid_search.py`
- `TelecomTokenizer`: Custom tokenizer preserving telecom acronyms
- `HybridSearcher`: BM25Okapi + RRF combination
- Cached index: `data/bm25_index.pkl` for fast startup

### 2.2 Neural Network Router

Intelligent query routing selects optimal retrieval strategy:

| Strategy | Use Case | Example |
|----------|----------|---------|
| **DENSE** | Concept/definition questions | "What is 5G NR?" |
| **HYBRID** | Procedural/troubleshooting | "How to fix VSWR alarm?" |
| **KEYWORD** | Error codes/identifiers | "Error 5301" |

**Implementation:** `src/router.py`
- Prototype-based nearest neighbor classification
- Category routing: Standards, Operations, Performance, Architecture

### 2.3 Cross-Encoder Reranking

Post-retrieval precision enhancement:

```
Initial Results (top-12) ──▶ Cross-Encoder ──▶ Reranked Results (top-6)
                              ms-marco-MiniLM-L-6-v2
```

**Benefits:**
- +5-10% precision improvement
- Lazy loading for faster cold starts
- Graceful degradation if unavailable

### 2.4 Semantic Query Cache

Redis-backed cache with embedding similarity:

| Parameter | Value |
|-----------|-------|
| Similarity Threshold | 0.95 |
| TTL | 24 hours |
| Max Cache Size | 1000 entries |

**Flow:**
```
Query ──▶ Embed ──▶ Cosine Similarity Search ──▶ Cache Hit? ──▶ Return
                                                     │
                                                     ▼ (Miss)
                                            Execute Pipeline ──▶ Cache Result
```

### 2.5 Glossary Enhancement

81+ telecom-specific terms for query expansion:

**Example:**
```
Input:  "What is HARQ?"
Output: "What is HARQ (Hybrid Automatic Repeat Request)?"
Terms:  - HARQ: Hybrid Automatic Repeat Request
        - NR: New Radio (5G)
```

### 2.6 HyDE (Hypothetical Document Embeddings)

Optional query enhancement (+2-3.5% accuracy):

```
Query ──▶ LLM generates hypothetical answer ──▶ Embed combined ──▶ Search
```

---

## 3. Evaluation & Trust Metrics

### 3.1 RAGAS-Style Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Faithfulness** | Answer grounded in context | >80% |
| **Relevancy** | Answer addresses question | >80% |
| **Context Precision** | Relevant chunks / total | >70% |
| **Context Recall** | Covered claims / total | >85% |
| **Confidence** | Combined retrieval quality | >60% |
| **Trust Score** | TLM reliability metric | >70% |

### 3.2 TLM Trust Score Formula

```
Trust = (Faithfulness × 0.4) + (Relevancy × 0.3) +
        (Context Precision × 0.2) + (Confidence × 0.1)
```

### 3.3 Abstention Logic

System refuses to answer when confidence is too low:

| Condition | Action |
|-----------|--------|
| Retrieval confidence < 0.2 | Abstain |
| Faithfulness < 0.3 | Abstain |
| Combined confidence < 0.3 | Abstain |

---

## 4. Data Architecture

### 4.1 Document Categories

| Category | Documents | Source Types |
|----------|-----------|--------------|
| Standards | ~3,000 | 3GPP TS specs, ITU guidelines |
| Network Operations | ~4,000 | Vendor manuals, NOC procedures |
| Performance | ~2,500 | KPI definitions, benchmarks |
| Architecture | ~2,000 | Network design, protocols |
| Regulatory | ~500 | Spectrum, compliance |
| Vendor-Specific | ~500 | Nokia, Ericsson, Huawei |

### 4.2 Chunking Parameters (Telco-RAG Validated)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk Size | 125 tokens | Optimal for telecom docs |
| Chunk Overlap | 25 tokens | Context preservation |
| Top-K Results | 6 | Balance precision/latency |
| Context Max | 1500 tokens | LLM context efficiency |

### 4.3 Embedding Model

| Provider | Model | Dimensions | Notes |
|----------|-------|------------|-------|
| OpenAI | text-embedding-3-large | 3072 | +2.29% accuracy |
| Local (fallback) | BAAI/bge-large-en-v1.5 | 1024 | Free, requires download |

---

## 5. Cloud Deployment

### 5.1 Google Cloud Run Configuration

```bash
gcloud run services update telecom-rag \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai,ENABLE_RERANK=false"
```

### 5.2 Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `LLM_PROVIDER` | openai | Primary LLM |
| `EMBEDDING_PROVIDER` | openai | No model download |
| `ENABLE_RERANK` | false | Faster cold starts |
| `ENABLE_HYBRID` | true | Better search quality |
| `ENABLE_REDIS` | false | Unless Redis available |
| `OPENAI_API_KEY` | sk-xxx | Required |

### 5.3 Feature Flags

| Flag | Default | Cloud Setting | Impact |
|------|---------|---------------|--------|
| `ENABLE_RERANK` | true | false | -30s cold start |
| `ENABLE_HYBRID` | true | true | Better results |
| `ENABLE_REDIS` | true | false | No Redis needed |

### 5.4 Graceful Degradation

```
Gemini unavailable ──▶ Fallback to OpenAI ──▶ Fallback to context-only
Redis unavailable ──▶ In-memory cache
Reranker unavailable ──▶ Skip reranking
```

---

## 6. API & Data Flow

### 6.1 Query Pipeline

```
1. USER QUERY
   │
2. RATE LIMIT CHECK ──▶ 50 req/min/session
   │
3. GLOSSARY ENHANCEMENT ──▶ Expand acronyms
   │
4. SEMANTIC CACHE CHECK ──▶ Return if hit (0.95 similarity)
   │
5. NN ROUTER ──▶ Select strategy (DENSE/HYBRID/KEYWORD)
   │
6. RETRIEVAL
   ├── Dense: ChromaDB vector search
   ├── BM25: Keyword search
   └── RRF: Combine rankings
   │
7. RERANKING (optional) ──▶ Cross-encoder precision
   │
8. CONTEXT ASSEMBLY ──▶ Build prompt with sources
   │
9. LLM GENERATION ──▶ GPT-4o-mini
   │
10. EVALUATION ──▶ 6 RAGAS metrics
    │
11. ABSTENTION CHECK ──▶ Refuse if low confidence
    │
12. CACHE RESULT ──▶ Store for future queries
    │
13. RETURN RESPONSE
```

### 6.2 RAGResponse Structure

```python
@dataclass
class RAGResponse:
    answer: str                          # Generated answer
    sources: List[Dict[str, Any]]        # Retrieved documents
    enhanced_query: str                  # Glossary-expanded query
    glossary_terms: str                  # Identified terms
    usage: Dict[str, Any]                # Token usage
    evaluation: EvaluationResult         # Quality metrics
    search_type: str                     # "dense", "hybrid", "reranked"
    abstained: bool                      # Low confidence flag
```

---

## 7. Technology Stack

### 7.1 Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | Latest | Web UI |
| `openai` | Latest | LLM & Embeddings |
| `chromadb` | Latest | Vector store |
| `sentence-transformers` | Latest | Reranking |
| `rank-bm25` | Latest | BM25 search |
| `redis` | Latest | Semantic cache |
| `numpy` | Latest | Vector operations |

### 7.2 Optional Dependencies

| Package | Purpose |
|---------|---------|
| `google-generativeai` | Gemini support |
| `python-dotenv` | Environment management |

---

## 8. Performance Characteristics

### 8.1 Latency Breakdown

| Stage | Time (ms) | Notes |
|-------|-----------|-------|
| Glossary Enhancement | 5-10 | Local lookup |
| Cache Check | 50-100 | Cosine similarity |
| Dense Retrieval | 100-200 | ChromaDB |
| BM25 Search | 50-100 | In-memory |
| RRF Fusion | 10-20 | Numpy ops |
| Reranking | 200-500 | Cross-encoder |
| LLM Generation | 500-1500 | API call |
| Evaluation | 50-100 | Heuristic |
| **Total (w/o rerank)** | **~1-2s** | |
| **Total (w/ rerank)** | **~2-3s** | |

### 8.2 Cold Start Optimization

| Configuration | Cold Start Time |
|---------------|-----------------|
| Full features | 60-120s |
| OpenAI embeddings | 30-45s |
| Disabled reranker | 20-30s |
| Optimized cloud | 15-25s |

---

## 9. Security & Rate Limiting

### 9.1 Rate Limiter

```python
RateLimiter(limit=50, window=60)  # 50 requests per minute per session
```

- Redis-backed for distributed deployments
- Fallback to in-memory for local development

### 9.2 API Key Security

- Environment variables for all secrets
- No hardcoded credentials
- `.env` file excluded from version control

---

## 10. Future Enhancements

### 10.1 Planned Features

| Feature | Priority | Status |
|---------|----------|--------|
| Multi-turn conversation | High | Planned |
| Document upload | Medium | Planned |
| Citation linking | Medium | Planned |
| A/B testing framework | Low | Backlog |

### 10.2 Data Expansion

| Category | Current | Target |
|----------|---------|--------|
| Standards Documents | 3,000 | 5,000 |
| Vendor Manuals | 500 | 2,000 |
| Troubleshooting Guides | 1,000 | 3,000 |

---

## 11. File Structure

```
telecom-rag/
├── app.py                      # Streamlit application
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration & feature flags
│   ├── embeddings.py          # Embedding models
│   ├── vector_store.py        # ChromaDB integration
│   ├── hybrid_search.py       # BM25 + RRF fusion
│   ├── reranker.py            # Cross-encoder reranking
│   ├── router.py              # Query intent classification
│   ├── glossary.py            # Telecom term expansion
│   ├── cache.py               # Redis semantic cache
│   ├── evaluation.py          # RAGAS metrics
│   ├── llm.py                 # LLM integration
│   ├── retriever.py           # Main orchestrator
│   ├── data_loader.py         # Document ingestion
│   └── rate_limiter.py        # Request throttling
├── data/
│   ├── raw/                   # Source documents
│   ├── processed/             # Chunked documents
│   ├── glossary/              # Telecom terms
│   ├── chroma_db/             # Vector store
│   └── bm25_index.pkl         # BM25 cache
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build
├── CLOUD_DEPLOYMENT.md         # Cloud deployment guide
└── DATA_ACQUISITION_PLAN.md    # Data sourcing guide
```

---

## 12. Quick Start

### 12.1 Local Development

```bash
# Clone and setup
git clone <repo>
cd telecom-rag
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run
streamlit run app.py --server.port 8502
```

### 12.2 Cloud Deployment

```bash
# Build and deploy
gcloud run deploy telecom-rag \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --timeout 300s \
  --set-env-vars="LLM_PROVIDER=openai,EMBEDDING_PROVIDER=openai"
```

---

## 13. Contact & Support

- **Primary Developer**: Ajay Maurya
- **Support Contact**: antigravity (cloud deployment)
- **Documentation**: See `CLOUD_DEPLOYMENT.md` for deployment issues

---

*Document Version: 1.0*
*Last Updated: February 2025*
*System Status: Production Ready*
