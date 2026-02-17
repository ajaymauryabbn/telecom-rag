# Telecom RAG - Technical Deep Dive

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [User Flow](#2-user-flow)
3. [Data Flow](#3-data-flow)
4. [Component Deep Dive](#4-component-deep-dive)
5. [Algorithms & Techniques](#5-algorithms--techniques)
6. [Data Pipeline](#6-data-pipeline)
7. [Evaluation Framework](#7-evaluation-framework)
8. [Cloud Deployment](#8-cloud-deployment)
9. [Graceful Degradation](#9-graceful-degradation)

---

## 1. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT WEB UI (app.py)                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────────┐  │
│  │  Query    │  │ Sample   │  │ Advanced  │  │  Results Display  │  │
│  │  Input    │  │ Queries  │  │ Settings  │  │  + Eval Metrics   │  │
│  └─────┬────┘  └──────────┘  └───────────┘  └───────────────────┘  │
└────────┼────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (retriever.py)                       │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────────┐  │
│  │  Rate    │──▶│ Semantic │──▶│  Query   │──▶│   Retrieval    │  │
│  │ Limiter  │   │  Cache   │   │  Router  │   │   Pipeline     │  │
│  └──────────┘   └──────────┘   └──────────┘   └───────┬────────┘  │
│                                                        │           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐          │           │
│  │   LLM    │◀──│ Context  │◀──│ Reranker │◀─────────┘           │
│  │Generator │   │ Builder  │   │(Optional)│                       │
│  └────┬─────┘   └──────────┘   └──────────┘                       │
│       │                                                            │
│       ▼                                                            │
│  ┌──────────┐   ┌──────────┐                                      │
│  │  RAGAS   │──▶│ Response │                                      │
│  │Evaluator │   │ Builder  │                                      │
│  └──────────┘   └──────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│  STORAGE LAYER  │          │   EXTERNAL APIS     │
│                 │          │                     │
│ ┌─────────────┐ │          │ ┌─────────────────┐ │
│ │  ChromaDB   │ │          │ │ OpenAI API      │ │
│ │(Vector DB)  │ │          │ │ - GPT-4o-mini   │ │
│ └─────────────┘ │          │ │ - text-embed-3  │ │
│ ┌─────────────┐ │          │ └─────────────────┘ │
│ │  BM25 Index │ │          │ ┌─────────────────┐ │
│ │ (Pickle)    │ │          │ │ HuggingFace     │ │
│ └─────────────┘ │          │ │ - TeleQnA       │ │
│ ┌─────────────┐ │          │ │ - 3GPP-QA       │ │
│ │Redis Cache  │ │          │ └─────────────────┘ │
│ │(Optional)   │ │          │ ┌─────────────────┐ │
│ └─────────────┘ │          │ │ Google Gemini   │ │
└─────────────────┘          │ │ (Fallback)      │ │
                             │ └─────────────────┘ │
                             └─────────────────────┘
```

### Module Dependency Graph

```
app.py
  ├── retriever.py (Orchestrator)
  │     ├── config.py (Settings)
  │     ├── glossary.py (Term Expansion)
  │     ├── vector_store.py (ChromaDB)
  │     │     └── embeddings.py (OpenAI/Local)
  │     ├── hybrid_search.py (BM25 + RRF)
  │     ├── reranker.py (Cross-Encoder)
  │     ├── router.py (Strategy Selection)
  │     │     └── embeddings.py
  │     ├── cache.py (Redis/In-Memory)
  │     ├── evaluation.py (RAGAS Metrics)
  │     │     └── llm.py (Optional LLM Eval)
  │     ├── llm.py (GPT-4o-mini / Gemini)
  │     └── data_loader.py (Ingestion)
  ├── glossary.py
  └── rate_limiter.py
```

---

## 2. User Flow

### Complete User Journey

```
┌──────────┐
│  User    │
│  Opens   │
│  Web App │
└────┬─────┘
     │
     ▼
┌─────────────────────────────┐
│  Streamlit App Initializes  │
│  ┌───────────────────────┐  │
│  │ 1. Load config (.env) │  │
│  │ 2. Init EmbeddingModel│  │     ┌──────────────────────┐
│  │ 3. Init ChromaDB      │──┼────▶│ If empty: Show       │
│  │ 4. Init BM25 index    │  │     │ "Ingest Data" button │
│  │ 5. Init LLM client    │  │     └──────────────────────┘
│  │ 6. Init Router        │  │
│  │ 7. Init Evaluator     │  │
│  └───────────────────────┘  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   User Sees Main Interface  │
│                             │
│  ┌───────────────────────┐  │
│  │ Left Sidebar:         │  │
│  │  - KB Stats           │  │
│  │  - Sample Queries     │  │
│  │  - Advanced Settings  │  │
│  ├───────────────────────┤  │
│  │ Center:               │  │
│  │  - Query Text Area    │  │
│  │  - Search / Clear     │  │
│  ├───────────────────────┤  │
│  │ Right Panel:          │  │
│  │  - Use Cases          │  │
│  │  - Features           │  │
│  │  - Quick Glossary     │  │
│  └───────────────────────┘  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐       ┌──────────────┐
│  User Types Query or Clicks │──────▶│  "What is    │
│  Sample Query Button        │       │  HARQ in 5G?"│
└──────────┬──────────────────┘       └──────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Clicks "Search" Button     │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  RAG Pipeline Executes      │
│  (See Data Flow section)    │
│  ~2-4 seconds               │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│           Results Display                    │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │ Hybrid Search Badge                    │ │
│  ├────────────────────────────────────────┤ │
│  │ Enhanced Query (with glossary expand)  │ │
│  ├────────────────────────────────────────┤ │
│  │ Generated Answer (with citations)      │ │
│  ├────────────────────────────────────────┤ │
│  │ 6 Evaluation Metrics:                  │ │
│  │ [Faith] [Relev] [Conf] [Prec] [Rec]   │ │
│  │ [Trust Score]                          │ │
│  ├────────────────────────────────────────┤ │
│  │ Telecom Terms Identified               │ │
│  ├────────────────────────────────────────┤ │
│  │ Sources (expandable, top-5):           │ │
│  │  - Source name, score, category        │ │
│  │  - Dense + BM25 scores                 │ │
│  │  - Content preview                     │ │
│  ├────────────────────────────────────────┤ │
│  │ Token Usage (expandable)               │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 3. Data Flow

### Query Processing Pipeline (Step-by-Step)

```
User Query: "What is HARQ in 5G NR?"
         │
         ▼
┌─────────────────────────────────────────────┐
│  STEP 1: RATE LIMITING                      │
│                                             │
│  rate_limiter.is_allowed(session_id)        │
│  - Sliding window: 50 req/min per user      │
│  - Redis-backed or in-memory fallback       │
│  - Result: ALLOWED ✅                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 2: SEMANTIC CACHE CHECK               │
│                                             │
│  query_embedding = embed("What is HARQ...") │
│  cached = cache.get(query_embedding)        │
│                                             │
│  For each cached vector:                    │
│    similarity = cosine(query_emb, cached)   │
│    if similarity >= 0.95:                   │
│      return cached response (FAST PATH)     │
│                                             │
│  Result: CACHE MISS → continue pipeline     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 3: QUERY ROUTING                      │
│                                             │
│  Router classifies query intent:            │
│                                             │
│  Strategy Classification:                   │
│  ┌─────────────────────────────────┐        │
│  │ "What is HARQ..." → cosine sim │        │
│  │  vs DENSE prototypes:  0.89    │        │
│  │  vs HYBRID prototypes: 0.72    │        │
│  │  vs KEYWORD prototypes: 0.31   │        │
│  │                                │        │
│  │  → Strategy: HYBRID (default)  │        │
│  └─────────────────────────────────┘        │
│                                             │
│  Category Classification:                   │
│  ┌─────────────────────────────────┐        │
│  │  vs standards:     0.78        │        │
│  │  vs network_ops:   0.65        │        │
│  │  vs performance:   0.42        │        │
│  │  vs architecture:  0.81 ← BEST │        │
│  │                                │        │
│  │  → Category: architecture      │        │
│  └─────────────────────────────────┘        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 4: QUERY ENHANCEMENT                  │
│                                             │
│  Input:  "What is HARQ in 5G NR?"          │
│                                             │
│  Glossary Lookup:                           │
│  ┌─────────────────────────────────┐        │
│  │ HARQ → "Hybrid Automatic       │        │
│  │         Repeat Request"         │        │
│  │ 5G   → "Fifth Generation       │        │
│  │         wireless technology"    │        │
│  │ NR   → "New Radio - 5G radio   │        │
│  │         access technology"      │        │
│  └─────────────────────────────────┘        │
│                                             │
│  Enhanced: "What is HARQ (Hybrid Automatic  │
│  Repeat Request) in 5G (Fifth Generation)   │
│  NR (New Radio)?"                           │
│                                             │
│  Glossary Terms:                            │
│  "- HARQ: Hybrid Automatic Repeat Request   │
│   - 5G: Fifth Generation wireless           │
│   - NR: New Radio"                          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 5: HYBRID RETRIEVAL                               │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  DENSE SEARCH   │    │  BM25 SEARCH    │            │
│  │  (Semantic)     │    │  (Keyword)      │            │
│  │                 │    │                 │            │
│  │  Embed query    │    │  Tokenize query │            │
│  │  → 3072-dim vec │    │  → ["harq",     │            │
│  │                 │    │     "5g", "nr"]  │            │
│  │  ChromaDB       │    │                 │            │
│  │  cosine search  │    │  BM25Okapi      │            │
│  │  top-12 results │    │  score all docs │            │
│  │                 │    │  top-12 results │            │
│  │  Doc1: 0.89     │    │  Doc3: 8.42     │            │
│  │  Doc2: 0.85     │    │  Doc1: 7.91     │            │
│  │  Doc4: 0.78     │    │  Doc5: 6.33     │            │
│  │  ...            │    │  ...            │            │
│  └────────┬────────┘    └────────┬────────┘            │
│           │                      │                     │
│           └──────────┬───────────┘                     │
│                      ▼                                 │
│  ┌─────────────────────────────────────────┐           │
│  │  RECIPROCAL RANK FUSION (RRF)           │           │
│  │                                         │           │
│  │  score(doc) = Σ  1 / (k + rank_i)      │           │
│  │               i                         │           │
│  │  where k = 60                           │           │
│  │                                         │           │
│  │  Doc1: 1/(60+1) + 1/(60+2) = 0.0326    │           │
│  │  Doc3: 1/(60+4) + 1/(60+1) = 0.0320    │           │
│  │  Doc2: 1/(60+2) + 0        = 0.0161    │           │
│  │  Doc5: 0        + 1/(60+3) = 0.0159    │           │
│  │                                         │           │
│  │  → Merged & ranked by RRF score         │           │
│  └─────────────────────────────────────────┘           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│  STEP 6: CONTEXT BUILDING                   │
│                                             │
│  Take top-6 results, build context string:  │
│  Budget: max 1500 tokens                    │
│                                             │
│  "[Source 1: 3GPP_TS_38.321 (network_ops),  │
│   Relevance: 0.89, RRF: 0.0326]            │
│   HARQ (Hybrid Automatic Repeat Request)    │
│   is a combination of high-rate FEC and     │
│   ARQ error-control..."                     │
│                                             │
│  ---                                        │
│                                             │
│  "[Source 2: TeleQnA (architecture),        │
│   Relevance: 0.85, RRF: 0.0320]            │
│   In 5G NR, HARQ supports up to 16         │
│   parallel processes..."                    │
│                                             │
│  (continues until token budget exhausted)   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 7: LLM GENERATION                    │
│                                             │
│  Model: GPT-4o-mini                         │
│  Temperature: 0.3 (focused)                 │
│  Max tokens: 1024                           │
│                                             │
│  Prompt (Telco-RAG format):                 │
│  ┌─────────────────────────────────┐        │
│  │ System: "You are a telecom      │        │
│  │          operations expert..."   │        │
│  │                                 │        │
│  │ [QUESTION]: What is HARQ...?    │        │
│  │ [TERMS]: HARQ: Hybrid Auto...   │        │
│  │ [CONTEXT]: <retrieved docs>     │        │
│  │ [QUESTION]: What is HARQ...?    │  ←repeated│
│  │                                 │        │
│  │ "Provide grounded answer        │        │
│  │  citing [Source: ...] format"    │        │
│  └─────────────────────────────────┘        │
│                                             │
│  → Generated answer with citations          │
│  → Token usage: ~400 prompt, ~200 response  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 8: RAGAS EVALUATION                   │
│                                             │
│  Input: question, answer, context, scores   │
│                                             │
│  ┌─────────────────────────────────┐        │
│  │ Faithfulness: 0.92              │        │
│  │  (7/8 claims supported)         │        │
│  │                                 │        │
│  │ Relevancy: 0.88                 │        │
│  │  (question terms in answer)     │        │
│  │                                 │        │
│  │ Confidence: 0.83                │        │
│  │  (weighted: faith + rel + sim)  │        │
│  │                                 │        │
│  │ Context Precision: 0.67         │        │
│  │  (4/6 chunks highly relevant)   │        │
│  │                                 │        │
│  │ Context Recall: 0.88            │        │
│  │  (7/8 claims covered)           │        │
│  │                                 │        │
│  │ Trust Score: 0.85               │        │
│  │  (40%×F + 30%×R + 20%×P + 10%C)│        │
│  │                                 │        │
│  │ Should Abstain: NO              │        │
│  │  (all above thresholds)         │        │
│  └─────────────────────────────────┘        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 9: CACHE & RESPOND                    │
│                                             │
│  1. Cache response (embedding → payload)    │
│  2. Build RAGResponse dataclass             │
│  3. Return to UI for display                │
│                                             │
│  Total latency: ~2-4 seconds                │
│  (Cache hit: <100ms)                        │
└─────────────────────────────────────────────┘
```

### Data Ingestion Flow

```
┌──────────────────────────────────────────────────┐
│            DATA INGESTION PIPELINE               │
│                                                  │
│  User clicks "Ingest Data" button                │
│                    │                             │
│                    ▼                             │
│  ┌────────────────────────────────┐              │
│  │  TelecomDataLoader.load_all() │              │
│  └──────────────┬─────────────────┘              │
│                 │                                │
│    ┌────────────┼────────────┬──────────┐        │
│    ▼            ▼            ▼          ▼        │
│  ┌──────┐  ┌──────┐  ┌──────────┐ ┌────────┐   │
│  │TeleQ │  │3GPP  │  │5G Faults │ │Built-in│   │
│  │nA    │  │QA    │  │Datasets  │ │KB (30+)│   │
│  │(HF)  │  │(HF)  │  │(HF)     │ │        │   │
│  └──┬───┘  └──┬───┘  └────┬─────┘ └───┬────┘   │
│     │         │            │           │        │
│     └─────────┴────────────┴───────────┘        │
│                    │                             │
│                    ▼                             │
│  ┌────────────────────────────────┐              │
│  │  Category Normalization        │              │
│  │  → standards                   │              │
│  │  → network_operations          │              │
│  │  → performance                 │              │
│  │  → architecture                │              │
│  │  → general                     │              │
│  └──────────────┬─────────────────┘              │
│                 │                                │
│                 ▼                                │
│  ┌────────────────────────────────┐              │
│  │  Dynamic Chunking              │              │
│  │  (category-specific sizes)     │              │
│  │                                │              │
│  │  standards:  125 tokens        │              │
│  │  operations: 250 tokens        │              │
│  │  performance:500 tokens        │              │
│  │  overlap:    25 tokens         │              │
│  └──────────────┬─────────────────┘              │
│                 │                                │
│                 ▼                                │
│  ┌────────────────────────────────┐              │
│  │  Embed All Chunks              │              │
│  │  (OpenAI text-embedding-3-     │              │
│  │   large, 3072 dimensions)      │              │
│  │  Batch: 100 docs/request       │              │
│  └──────────────┬─────────────────┘              │
│                 │                                │
│        ┌────────┴────────┐                       │
│        ▼                 ▼                       │
│  ┌──────────┐    ┌──────────┐                    │
│  │ ChromaDB │    │  BM25    │                    │
│  │ (vectors │    │  Index   │                    │
│  │  + meta) │    │ (pickle) │                    │
│  └──────────┘    └──────────┘                    │
│                                                  │
│  Result: ~12,500+ documents indexed              │
└──────────────────────────────────────────────────┘
```

---

## 4. Component Deep Dive

### 4.1 Embedding Model (`embeddings.py`)

```
┌───────────────────────────────────────────────┐
│              EmbeddingModel                    │
│                                               │
│  Provider Selection:                          │
│  ┌────────────────┐  ┌────────────────────┐   │
│  │  openai         │  │  local              │   │
│  │                │  │                    │   │
│  │  Model:        │  │  Model:            │   │
│  │  text-embed-   │  │  BAAI/bge-large-   │   │
│  │  3-large       │  │  en-v1.5           │   │
│  │                │  │                    │   │
│  │  Dimensions:   │  │  Dimensions:       │   │
│  │  3072          │  │  1024              │   │
│  │                │  │                    │   │
│  │  Cost: $0.13/  │  │  Cost: FREE        │   │
│  │  1M tokens     │  │  (GPU recommended) │   │
│  │                │  │                    │   │
│  │  Speed: Fast   │  │  Speed: Slower     │   │
│  │  (API call)    │  │  (local inference) │   │
│  └────────────────┘  └────────────────────┘   │
│                                               │
│  Methods:                                     │
│  - embed(texts[]) → embeddings[]              │
│  - embed_query(text) → embedding              │
└───────────────────────────────────────────────┘
```

### 4.2 Vector Store (`vector_store.py`)

```
┌───────────────────────────────────────────────┐
│            TelecomVectorStore                  │
│                                               │
│  Backend: ChromaDB (PersistentClient)         │
│  Collection: "telecom_docs"                   │
│  Metric: Cosine Similarity                    │
│  Index: HNSW (Hierarchical Navigable Small    │
│         World graph)                          │
│                                               │
│  Storage:                                     │
│  data/chroma_db/                              │
│  ├── chroma.sqlite3     (metadata DB)         │
│  ├── index/             (HNSW vectors)        │
│  └── ...                                      │
│                                               │
│  Operations:                                  │
│  ┌──────────────────────────────────────┐     │
│  │ add_documents(docs, batch_size=100)  │     │
│  │  → embeds → stores in ChromaDB       │     │
│  │  → retry logic for failed batches    │     │
│  │                                      │     │
│  │ search(query, top_k=6, filter=None)  │     │
│  │  → embed query → HNSW search         │     │
│  │  → returns: content, metadata,       │     │
│  │    distance, similarity              │     │
│  │                                      │     │
│  │ search_by_category(query, cat, k)    │     │
│  │  → filtered search via ChromaDB      │     │
│  │    "where" clause                    │     │
│  └──────────────────────────────────────┘     │
└───────────────────────────────────────────────┘
```

### 4.3 Query Router (`router.py`)

```
┌───────────────────────────────────────────────┐
│              QueryRouter                       │
│                                               │
│  Prototype-Based Nearest Neighbor Classifier  │
│                                               │
│  Strategy Prototypes (6 each):                │
│  ┌─────────────────────────────────────┐      │
│  │ DENSE:   "What is 5G NR?"          │      │
│  │          "Explain beamforming"      │      │
│  │          "Define latency..."        │      │
│  │                                     │      │
│  │ HYBRID:  "How to troubleshoot..."   │      │
│  │          "Steps to configure..."    │      │
│  │          "Resolve cell sleeping"    │      │
│  │                                     │      │
│  │ KEYWORD: "Error code 5301"          │      │
│  │          "Alarm ID 2839"            │      │
│  │          "3GPP TS 38.211"           │      │
│  └─────────────────────────────────────┘      │
│                                               │
│  Algorithm:                                   │
│  1. Embed query                               │
│  2. Compute cosine similarity to ALL          │
│     prototype embeddings                      │
│  3. Find max similarity per strategy          │
│  4. Return strategy with highest score        │
│                                               │
│  Same approach for Category classification    │
│  (standards, network_ops, performance, arch)  │
└───────────────────────────────────────────────┘
```

### 4.4 Glossary System (`glossary.py`)

```
┌───────────────────────────────────────────────┐
│            TelecomGlossary                     │
│                                               │
│  81 Telecom Terms Dictionary                  │
│                                               │
│  Term Detection (Regex):                      │
│  ┌─────────────────────────────────────┐      │
│  │ Pattern 1: [A-Z]{2,6}              │      │
│  │   Matches: HARQ, MIMO, 5G, NR      │      │
│  │                                     │      │
│  │ Pattern 2: Known compound terms     │      │
│  │   Matches: "carrier aggregation",   │      │
│  │   "network slicing", etc.           │      │
│  └─────────────────────────────────────┘      │
│                                               │
│  Query Enhancement:                           │
│  ┌─────────────────────────────────────┐      │
│  │ Input:  "What is HARQ?"            │      │
│  │                                     │      │
│  │ Output:                             │      │
│  │  query: "What is HARQ (Hybrid      │      │
│  │          Automatic Repeat Request)?"│      │
│  │                                     │      │
│  │  terms: "- HARQ: Hybrid Automatic   │      │
│  │          Repeat Request - error     │      │
│  │          correction mechanism..."   │      │
│  └─────────────────────────────────────┘      │
└───────────────────────────────────────────────┘
```

---

## 5. Algorithms & Techniques

### 5.1 Reciprocal Rank Fusion (RRF)

**What:** Merges results from different search strategies without score normalization.

**Why:** Dense (cosine similarity: 0-1) and BM25 (unbounded: 0-∞) scores are incomparable. RRF uses rank positions instead.

```
Formula:  RRF_score(doc) = Σ  1 / (k + rank_i(doc))
                           i∈systems

Where:
  k = 60 (smoothing constant, per Telco-RAG spec)
  rank_i = document's position in system i's results

Example:
  Doc appears at rank 1 in Dense, rank 3 in BM25:
  RRF = 1/(60+1) + 1/(60+3) = 0.01639 + 0.01587 = 0.03226

  Doc appears at rank 5 in Dense only:
  RRF = 1/(60+5) + 0 = 0.01538
```

**Advantage over weighted sum:** No need to normalize scores across systems.

### 5.2 HyDE (Hypothetical Document Embeddings)

**What:** Generates a hypothetical ideal answer, then searches for real documents similar to it.

```
Traditional:     Query → Embed → Search
HyDE:            Query → LLM generates hypothetical answer
                         → Embed (query + hypothesis)
                         → Search

Why it works:
  - Query: "What is HARQ?" (short, ambiguous)
  - Hypothesis: "HARQ is a combination of FEC and ARQ
                 used in 5G NR for reliable transmission"
  - The hypothesis is closer in embedding space to
    actual documents about HARQ
```

**Impact:** +2-3.5% accuracy on ambiguous queries (disabled by default for speed).

### 5.3 Semantic Caching

```
┌────────────────────────────────────────────────┐
│              CACHE LOOKUP                       │
│                                                │
│  New Query Embedding: [0.12, -0.34, 0.78, ...] │
│                                                │
│  Cached Entries:                               │
│  ┌──────────────────────────────────────┐      │
│  │ Entry 1: [0.11, -0.33, 0.79, ...]   │      │
│  │  cosine_sim = 0.97  → ABOVE 0.95 ✅  │      │
│  │  → Return cached response            │      │
│  │                                      │      │
│  │ Entry 2: [0.45, 0.12, -0.56, ...]   │      │
│  │  cosine_sim = 0.34  → BELOW 0.95 ❌  │      │
│  └──────────────────────────────────────┘      │
│                                                │
│  Threshold: 0.95 (near-exact match only)       │
│  Storage: Redis (persistent) or In-Memory      │
│  TTL: 24 hours                                 │
└────────────────────────────────────────────────┘
```

### 5.4 RAGAS Evaluation

```
┌─────────────────────────────────────────────────┐
│          EVALUATION METRICS                      │
│                                                 │
│  1. FAITHFULNESS (Weight: 40%)                  │
│     "Is the answer grounded in the context?"    │
│                                                 │
│     Method: Extract claims → check each claim   │
│             against context via keyword overlap  │
│                                                 │
│     Score = supported_claims / total_claims      │
│                                                 │
│  2. RELEVANCY (Weight: 30%)                     │
│     "Does the answer address the question?"     │
│                                                 │
│     Method: Keyword overlap between question    │
│             terms and answer terms               │
│             (technical terms weighted 2x)        │
│                                                 │
│  3. CONTEXT PRECISION (Weight: 20%)             │
│     "Were the retrieved chunks relevant?"       │
│                                                 │
│     Score = chunks_with_sim>0.5 / total_chunks  │
│                                                 │
│  4. CONTEXT RECALL                              │
│     "Did context cover all claims?"             │
│                                                 │
│     Score = supported_claims / total_claims      │
│                                                 │
│  5. CONFIDENCE                                  │
│     Based on retrieval similarity scores:       │
│     avg(top-3 similarity scores)                │
│                                                 │
│  6. TRUST SCORE (TLM)                           │
│     Weighted combination:                       │
│     0.4×Faith + 0.3×Relev + 0.2×Prec + 0.1×Conf│
│                                                 │
│  ABSTENTION LOGIC:                              │
│  ┌────────────────────────────────────────┐     │
│  │ IF retrieval_confidence < 0.2: ABSTAIN │     │
│  │ IF faithfulness < 0.3: ABSTAIN         │     │
│  │ IF overall_confidence < 0.3: ABSTAIN   │     │
│  │                                        │     │
│  │ → Shows polite refusal with guidance   │     │
│  └────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

## 6. Data Pipeline

### Document Sources & Processing

```
┌──────────────────────────────────────────────────────────┐
│                    DATA SOURCES                           │
│                                                          │
│  ┌─────────────────┐  Source 1: TeleQnA (HuggingFace)   │
│  │  Gated Dataset   │  - Requires HF_TOKEN               │
│  │  Q&A pairs from  │  - Official telecom Q&A            │
│  │  telecom experts │  - Format: question + choices +    │
│  │                  │    answer_idx + explanation         │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 2: 3GPP-QA (Public)        │
│  │  Multiple choice │  - Fallback if TeleQnA unavailable │
│  │  3GPP standards  │  - Format: question + choices      │
│  │  questions       │                                    │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 3: 5G_Faults_Full          │
│  │  Fault diagnosis │  - instruction/input/output format │
│  │  Q&A pairs       │  - Network operations focus        │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 4: telco-5G-data-faults    │
│  │  Structured      │  - [SYMPTOMS] [CAUSES] [ACTIONS]   │
│  │  troubleshooting │  - Parsed with regex               │
│  │  guides          │                                    │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 5: Built-in KB (Always)    │
│  │  30+ curated     │  - Handpicked core telecom topics  │
│  │  Q&A pairs       │  - Guaranteed quality baseline     │
│  │  3GPP citations  │  - Covers: HARQ, MIMO, gNB, KPIs │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 6: Raw PDFs (Optional)     │
│  │  3GPP specs,     │  - PyMuPDF extraction              │
│  │  vendor manuals  │  - Category-based chunking         │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────┐  Source 7: CSV Data (Optional)     │
│  │  KPI metrics,    │  - Pandas-based loading            │
│  │  alarm tables    │  - Row-as-document conversion      │
│  └─────────────────┘                                     │
└──────────────────────────────────────────────────────────┘
```

### Category Normalization

```
Raw Input Category          →    Normalized Category
─────────────────────────────────────────────────────
3gpp, standard, spec,       →    standards
protocol, compliance

operation, maintain,        →    network_operations
troubleshoot, fault, alarm

perform, kpi, optimiz,      →    performance
quality, throughput

architect, fundament,       →    architecture
concept, define, core

(everything else)           →    general
```

---

## 7. Evaluation Framework

### Metric Calculation Details

```
┌──────────────────────────────────────────────────────┐
│  FAITHFULNESS CALCULATION                             │
│                                                      │
│  Answer: "HARQ uses incremental redundancy with      │
│           up to 16 parallel processes in 5G NR.      │
│           It provides reliable data transmission     │
│           through soft combining techniques."        │
│                                                      │
│  Step 1: Extract claims (regex-based)                │
│  ┌──────────────────────────────────────────────┐    │
│  │ Claim 1: "HARQ uses incremental redundancy   │    │
│  │           with up to 16 parallel processes    │    │
│  │           in 5G NR"                           │    │
│  │ Claim 2: "It provides reliable data           │    │
│  │           transmission through soft combining │    │
│  │           techniques"                         │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Step 2: Check each claim against context            │
│  ┌──────────────────────────────────────────────┐    │
│  │ Claim 1: "HARQ", "incremental", "redundancy" │    │
│  │          "16", "parallel", "5G", "NR"         │    │
│  │                                               │    │
│  │  Context contains: HARQ ✅, incremental ✅,    │    │
│  │  redundancy ✅, 16 ✅, parallel ✅              │    │
│  │                                               │    │
│  │  Support ratio: 10/12 = 0.83 > 0.3 → ✅       │    │
│  │                                               │    │
│  │ Claim 2: similarly verified → ✅               │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Faithfulness = 2/2 = 1.0                            │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  TRUST SCORE FORMULA                                  │
│                                                      │
│  Trust = 0.4 × Faithfulness                          │
│        + 0.3 × Relevancy                             │
│        + 0.2 × Context_Precision                     │
│        + 0.1 × Confidence                            │
│                                                      │
│  Example:                                            │
│  Trust = 0.4(0.92) + 0.3(0.88) + 0.2(0.67) + 0.1(0.83)│
│        = 0.368 + 0.264 + 0.134 + 0.083              │
│        = 0.849                                       │
│                                                      │
│  Color coding in UI:                                 │
│    ≥ 0.80: Green  (Good)                             │
│    ≥ 0.60: Yellow (Warning)                          │
│    < 0.60: Red    (Poor)                             │
└──────────────────────────────────────────────────────┘
```

---

## 8. Cloud Deployment

### Google Cloud Run Architecture

```
┌─────────────────────────────────────────────────────┐
│                 GOOGLE CLOUD RUN                     │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Cloud Run Service: telecom-rag-service       │  │
│  │  Region: us-central1                          │  │
│  │  URL: https://telecom-rag-service-...run.app  │  │
│  │                                               │  │
│  │  Resources:                                   │  │
│  │  ┌──────────────────────────────────────┐     │  │
│  │  │ CPU: 2 vCPUs                         │     │  │
│  │  │ Memory: 4 GB                         │     │  │
│  │  │ Timeout: 300 seconds                 │     │  │
│  │  │ Min instances: 0 (scale-to-zero)     │     │  │
│  │  │ Max instances: 10                    │     │  │
│  │  │ Concurrency: default                 │     │  │
│  │  └──────────────────────────────────────┘     │  │
│  │                                               │  │
│  │  Environment Variables:                       │  │
│  │  ┌──────────────────────────────────────┐     │  │
│  │  │ OPENAI_API_KEY=sk-proj-...           │     │  │
│  │  │ LLM_PROVIDER=openai                  │     │  │
│  │  │ EMBEDDING_PROVIDER=openai            │     │  │
│  │  │ ENABLE_HYBRID=true                   │     │  │
│  │  │ ENABLE_RERANK=false (saves memory)   │     │  │
│  │  │ ENABLE_REDIS=false (no Redis)        │     │  │
│  │  │ HF_TOKEN=hf_...                      │     │  │
│  │  └──────────────────────────────────────┘     │  │
│  │                                               │  │
│  │  Container:                                   │  │
│  │  ┌──────────────────────────────────────┐     │  │
│  │  │ Base: python:3.9-slim               │     │  │
│  │  │ Port: 8501 (Streamlit)              │     │  │
│  │  │ Includes:                            │     │  │
│  │  │  - Pre-built chroma_db.tar.gz        │     │  │
│  │  │  - Pre-built bm25_index.pkl          │     │  │
│  │  │  - All source code                   │     │  │
│  │  │  - .streamlit/config.toml            │     │  │
│  │  └──────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Scaling Behavior:                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │ 0 requests → 0 instances (no cost)            │  │
│  │ First request → cold start (~10-15s)          │  │
│  │ Subsequent → warm (~2-4s per query)           │  │
│  │ High traffic → auto-scale to 10 instances     │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Deployment Flow

```
Developer Machine                    Google Cloud
┌──────────────┐                    ┌──────────────┐
│ bash deploy- │───source .env────▶│ Cloud Build  │
│ cloudbuild.sh│                    │              │
│              │───gcloud run ────▶│ Builds Docker│
│              │   deploy --source  │ image from   │
│              │                    │ Dockerfile   │
└──────────────┘                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Container    │
                                    │ Registry     │
                                    │ (GCR)        │
                                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Cloud Run    │
                                    │ deploys new  │
                                    │ revision     │
                                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Service URL  │
                                    │ is live      │
                                    └──────────────┘
```

---

## 9. Graceful Degradation

The system is designed to work at every level even when components fail:

```
┌──────────────────────────────────────────────────────┐
│  DEGRADATION CHAIN                                    │
│                                                      │
│  Full System (All components working):               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Hybrid Search + Reranking + LLM + Eval + Redis Cache│
│  Quality: ★★★★★  Latency: ~3s                       │
│                                                      │
│  Without Reranker:                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Hybrid Search + LLM + Eval + Redis Cache            │
│  Quality: ★★★★☆  Latency: ~2.5s                     │
│                                                      │
│  Without Redis:                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Hybrid Search + LLM + Eval + In-Memory Cache        │
│  Quality: ★★★★☆  Latency: ~3s (no persistent cache) │
│                                                      │
│  Without BM25 (no hybrid):                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Dense-Only Search + LLM + Eval                      │
│  Quality: ★★★☆☆  Latency: ~2s                       │
│                                                      │
│  Without LLM:                                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Hybrid Search + Raw Context Display                 │
│  Quality: ★★☆☆☆  Latency: ~1s                       │
│                                                      │
│  Without Vector Store:                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Shows "Ingest Data" button                          │
│  Quality: N/A     Latency: N/A                       │
└──────────────────────────────────────────────────────┘
```

### Error Handling by Component

| Component | Failure Mode | Fallback Behavior |
|-----------|-------------|-------------------|
| OpenAI API Key | Missing/Invalid | Shows config error with Cloud Run diagnostic command |
| OpenAI Embeddings | Rate limit | Suggests local embeddings or retry |
| LLM (GPT-4o-mini) | API error | Returns raw retrieved context without generation |
| Gemini (fallback) | Import/init fail | Falls back to OpenAI |
| Redis | Connection refused | In-memory cache (non-persistent) |
| BM25 Index | Cache miss | Rebuilds from processed docs; falls back to dense-only |
| Reranker model | Download fail | Skips reranking, returns hybrid results as-is |
| HuggingFace datasets | Auth fail / rate limit | Falls back to public 3GPP-QA then built-in KB |
| ChromaDB | Corruption | Recreates collection from scratch |
| Rate Limiter | Redis down | In-memory sliding window fallback |

---

## Key Numbers to Remember

| Metric | Value | Why |
|--------|-------|-----|
| Chunk size | 125 tokens | Optimal for telecom Q&A (Telco-RAG paper) |
| Chunk overlap | 25 tokens | Maintains context across chunks |
| Top-K retrieval | 6 docs | Balance of quality vs latency |
| Context budget | 1500 tokens | Keeps LLM prompt focused |
| RRF constant (k) | 60 | Standard value for rank fusion |
| Cache threshold | 0.95 | Near-exact match only |
| Abstention threshold | 0.3 | Only refuse very low confidence |
| Embedding dims | 3072 | OpenAI text-embedding-3-large |
| KB documents | ~12,500+ | From 7 data sources |
| Glossary terms | 81 | Core telecom acronyms |
| LLM temperature | 0.3 | Focused, deterministic answers |
