# Telecom RAG - Interview Guide

A comprehensive Q&A guide to explain this project's technical concepts in interviews.

---

## Section 1: Project Overview Questions

### Q: "Tell me about your project."

> I built a **Telecom RAG (Retrieval-Augmented Generation) system** that provides AI-powered answers for telecom operations support - covering 5G networks, 3GPP standards, troubleshooting, and network KPIs.
>
> It's not just a simple RAG - it implements **6 key innovations**:
> 1. **Hybrid Search** - combines semantic (dense) vectors with keyword (BM25) search using Reciprocal Rank Fusion
> 2. **Neural Query Router** - classifies query intent to pick the optimal search strategy
> 3. **RAGAS Evaluation** - 6-metric quality assessment with automatic abstention for low-confidence answers
> 4. **Semantic Caching** - deduplicates similar queries via embedding similarity
> 5. **Glossary Enhancement** - expands 81+ telecom acronyms for better retrieval
> 6. **Graceful Degradation** - works at every level even when components fail
>
> It's deployed on Google Cloud Run and handles a knowledge base of 12,500+ documents from 7 data sources.

### Q: "Why did you build this? What problem does it solve?"

> Telecom engineers deal with massive documentation - 3GPP specs alone are thousands of pages. They need quick, accurate answers when troubleshooting network issues or checking standards compliance.
>
> The problem with generic LLMs is they **hallucinate** telecom-specific details. My system grounds every answer in actual retrieved documents, evaluates faithfulness, and **refuses to answer** when it can't verify the response - which is critical in a domain where wrong answers can cause network outages.

---

## Section 2: RAG Architecture Questions

### Q: "What is RAG and why did you use it?"

> **RAG = Retrieval-Augmented Generation.** Instead of relying solely on an LLM's parametric knowledge (which can hallucinate), RAG first retrieves relevant documents from a knowledge base, then feeds them as context to the LLM.
>
> **Pipeline:** Query → Retrieve relevant docs → Build context → LLM generates grounded answer
>
> **Why RAG over fine-tuning?**
> - No retraining needed when documents update (just re-index)
> - Can cite specific sources (traceability)
> - Can detect when it doesn't have enough information (abstention)
> - Much cheaper than fine-tuning large models

### Q: "Walk me through what happens when a user asks a question."

> 9-step pipeline:
>
> 1. **Rate Limit Check** - Sliding window (50 req/min) prevents abuse
> 2. **Cache Check** - Embed query, search for similar cached queries (threshold: 0.95 cosine similarity). If hit, return cached answer in <100ms
> 3. **Query Routing** - Neural router classifies intent: factual (dense search), procedural (hybrid), or keyword (BM25). Also predicts document category
> 4. **Query Enhancement** - Glossary expands acronyms: "HARQ" → "HARQ (Hybrid Automatic Repeat Request)"
> 5. **Hybrid Retrieval** - Dense search (ChromaDB) + BM25 keyword search, merged with Reciprocal Rank Fusion
> 6. **Context Building** - Top-6 results assembled into a context string with a 1500-token budget
> 7. **LLM Generation** - GPT-4o-mini generates a grounded answer using a structured prompt with question repetition
> 8. **RAGAS Evaluation** - 6 metrics computed: faithfulness, relevancy, context precision/recall, confidence, trust score. If below threshold → abstain
> 9. **Cache & Return** - Cache the response, display with metrics and source citations

### Q: "Why hybrid search instead of just semantic search?"

> Semantic (dense) search excels at understanding meaning - "How to fix antenna issues" matches documents about "VSWR troubleshooting." But it struggles with **exact terms** - error codes, alarm IDs, 3GPP specification numbers.
>
> BM25 (keyword) search is the opposite - great for exact matches but misses semantic similarity.
>
> **Hybrid search combines both.** I use Reciprocal Rank Fusion (RRF) to merge the results:
> ```
> score(doc) = 1/(60+rank_in_dense) + 1/(60+rank_in_BM25)
> ```
> This gives documents that appear in both result sets a higher score, while still surfacing documents that are strong in either signal.

---

## Section 3: Algorithm Deep Dives

### Q: "Explain Reciprocal Rank Fusion. Why k=60?"

> **Problem:** Dense similarity scores (0 to 1) and BM25 scores (0 to unbounded) are on different scales. You can't simply add them.
>
> **RRF Solution:** Instead of using raw scores, use rank positions:
> ```
> RRF(doc) = Σ 1/(k + rank_i)
> ```
>
> **Why k=60?** It's a smoothing constant. A smaller k (like 1) would heavily favor top-ranked documents. k=60 makes the fusion more democratic - the difference between rank 1 and rank 5 is smaller, so both dense and BM25 signals contribute meaningfully. This value was empirically validated in the Telco-RAG paper and is also standard in NIST TREC benchmarks.

### Q: "How does your evaluation system work?"

> I implemented a **RAGAS-style evaluation** with 6 metrics:
>
> 1. **Faithfulness** - Extract factual claims from the answer, check each against the context via keyword overlap. Score = supported/total claims
> 2. **Relevancy** - Measure keyword overlap between question terms and answer terms (technical terms weighted 2x)
> 3. **Context Precision** - What fraction of retrieved chunks were actually relevant (similarity > 0.5)
> 4. **Context Recall** - What fraction of answer claims are covered by the context
> 5. **Confidence** - Average of top-3 retrieval similarity scores
> 6. **Trust Score** - Weighted combination: 40% faithfulness + 30% relevancy + 20% precision + 10% confidence
>
> **Abstention Logic:** If any metric drops below 0.3 (very low), the system refuses to answer and explains why. This prevents hallucinated responses in a safety-critical domain.
>
> There's also an optional **LLM-as-judge** mode where GPT-4o-mini itself scores faithfulness and relevancy (more accurate but slower).

### Q: "What is HyDE and why did you implement it?"

> **HyDE = Hypothetical Document Embeddings.**
>
> **Problem:** Short queries like "What is HARQ?" don't have much semantic content for embedding-based search.
>
> **Solution:** Ask the LLM to generate a hypothetical ideal answer, then search for documents similar to that hypothetical answer.
>
> **Why it works:** The hypothetical answer is closer in embedding space to actual documents about HARQ than the short query alone. It bridges the "query-document gap."
>
> **Trade-off:** +2-3.5% accuracy but adds an extra LLM call (~1s latency). That's why I made it optional and disabled by default.

### Q: "How does the query router work?"

> It's a **prototype-based nearest neighbor classifier** using embedding similarity:
>
> 1. Pre-compute embeddings for 6 prototype questions per strategy (DENSE, HYBRID, KEYWORD)
> 2. When a query arrives, embed it
> 3. Compute cosine similarity against all prototypes
> 4. Pick the strategy whose prototypes have the highest max similarity
>
> **Example:**
> - "What is 5G NR?" → highest sim with DENSE prototypes → pure semantic search
> - "How to fix VSWR alarm?" → highest sim with HYBRID prototypes → hybrid search
> - "Error 5301" → highest sim with KEYWORD prototypes → BM25 search
>
> This is lightweight (no ML training needed) and effective because telecom queries follow predictable patterns.

---

## Section 4: Infrastructure & Deployment

### Q: "How did you deploy this?"

> **Google Cloud Run** - serverless container platform.
>
> **Key decisions:**
> - **Scale-to-zero:** Min instances = 0, so no cost when idle
> - **Pre-built indexes:** ChromaDB and BM25 indexes are compressed into the Docker image so cold starts don't require rebuilding
> - **Feature flags:** Reranker disabled on cloud (saves ~1GB memory), Redis disabled (no managed instance), hybrid search enabled
> - **Environment variables:** API keys passed via `--set-env-vars`, not baked into the image
>
> **Deployment flow:** `deploy-cloudbuild.sh` → sources `.env` → `gcloud run deploy --source=.` → Cloud Build creates Docker image → deploys to Cloud Run

### Q: "How do you handle cold starts?"

> Cloud Run cold starts are a challenge. My mitigations:
>
> 1. **Pre-built ChromaDB** - compressed as `chroma_db.tar.gz` in the Docker image, extracted at build time
> 2. **Cached BM25 index** - serialized as `bm25_index.pkl`, loaded from cache on startup instead of rebuilding from documents
> 3. **OpenAI embeddings** - no local model download needed (vs sentence-transformers which needs ~1GB download)
> 4. **Lazy reranker** - cross-encoder model only loaded on first use (not at startup)
> 5. **Streamlit caching** - `@st.cache_resource` ensures components initialize once per instance

### Q: "Explain your graceful degradation strategy."

> Every component is designed to fail gracefully:
>
> | Component Failure | Fallback |
> |---|---|
> | Redis down | In-memory cache (non-persistent) |
> | LLM unavailable | Returns raw retrieved context |
> | Reranker fails to load | Skips reranking, returns hybrid results |
> | BM25 index missing | Falls back to dense-only search |
> | HuggingFace rate limit | Falls back to public dataset, then built-in KB |
> | OpenAI API key invalid | Shows helpful error with diagnostic command |
>
> The system always tries to provide something useful rather than crashing. In production, this means the service stays up even when external dependencies have issues.

---

## Section 5: Design Decisions

### Q: "Why ChromaDB instead of Pinecone/Weaviate/FAISS?"

> **ChromaDB** was chosen because:
> - **Embedded** - runs inside the application process, no separate database server needed
> - **Persistent** - data survives container restarts via disk storage
> - **Lightweight** - fits within Cloud Run's 4GB memory limit
> - **Python-native** - first-class Python API, easy to integrate
>
> **Why not alternatives:**
> - **Pinecone** - managed service, adds latency for network calls, costs money per vector
> - **FAISS** - no built-in persistence, metadata filtering is manual
> - **Weaviate** - requires separate server, overkill for this scale

### Q: "Why GPT-4o-mini instead of GPT-4o?"

> **Cost vs quality trade-off:**
> - GPT-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
> - GPT-4o: ~$5/1M input tokens, ~$15/1M output tokens
>
> For RAG, the quality difference is minimal because the answer quality depends more on the retrieved context than the model's parametric knowledge. GPT-4o-mini is 30x cheaper and 2-3x faster while being sufficient for summarizing and citing retrieved documents.

### Q: "Why 125-token chunks?"

> Based on the **Telco-RAG paper** and empirical testing:
> - Too small (50 tokens): loses context, fragments sentences
> - Too large (500 tokens): reduces retrieval precision, wastes token budget
> - **125 tokens** is optimal for Q&A-style telecom documents
>
> I also use **dynamic chunk sizing** based on category:
> - Standards docs: 125 tokens (concise, factual)
> - Network operations: 250 tokens (event-based, needs more context)
> - Performance data: 500 tokens (time-series, needs surrounding context)

### Q: "Why did you set the cache similarity threshold at 0.95?"

> It's intentionally strict because we want cache hits only for **nearly identical questions**:
> - "What is HARQ in 5G?" and "What is HARQ in 5G NR?" → same intent, should cache
> - "What is HARQ?" and "What is MIMO?" → different intent, should NOT cache
>
> At 0.95, only near-paraphrases match. At 0.90, you'd get false positives that return answers for different questions. The cost of a cache miss (re-running the pipeline, ~3s) is much lower than the cost of returning a wrong cached answer.

---

## Section 6: Challenges & Learnings

### Q: "What was the hardest challenge?"

> **Balancing retrieval precision vs recall in a specialized domain.**
>
> Telecom has thousands of similar-sounding concepts (PDSCH/PUSCH, gNB/eNB, FR1/FR2). Pure semantic search would often retrieve the wrong related concept. The hybrid search with BM25 solved this because keyword matching catches exact acronyms that embeddings might confuse.
>
> Another challenge was **empty answers from HuggingFace datasets** - many TeleQnA entries had answer indices pointing to empty choices. I had to implement validation to filter these out (hence the "data quality report" in the ingestion pipeline).

### Q: "What would you do differently if starting over?"

> 1. **Use a vector DB with built-in hybrid search** (like Qdrant or Weaviate) instead of managing separate BM25 + ChromaDB
> 2. **Implement streaming responses** - currently the UI waits for the full pipeline, but users would benefit from seeing partial results
> 3. **Use Google Cloud Secret Manager** instead of environment variables for API keys
> 4. **Add automated evaluation** with a test suite of known Q&A pairs to catch regressions

---

## Section 7: Metrics & Performance

### Q: "What are the performance characteristics?"

> | Metric | Value |
> |--------|-------|
> | Cold start | ~10-15s (Cloud Run) |
> | Warm query (cache miss) | ~2-4s |
> | Cache hit | <100ms |
> | Knowledge base | 12,500+ docs |
> | Index size | ~500MB |
> | Memory usage | ~2-3GB |
> | Concurrent users | ~10-20 (per instance) |

### Q: "How would you scale this?"

> **Horizontal:** Cloud Run auto-scales to 10 instances. Each instance handles its own requests independently since ChromaDB is embedded and read-only after ingestion.
>
> **If I needed more:**
> 1. Move to a **managed vector DB** (Pinecone/Qdrant) for shared state across instances
> 2. Add a **Redis cluster** for shared caching (currently per-instance)
> 3. Use **Cloud CDN** for static Streamlit assets
> 4. Implement **async LLM calls** to handle more concurrent requests per instance
> 5. Consider **Google Cloud Memorystore** for managed Redis

---

## Quick Reference: Key Technical Terms

| Term | What It Is | Where It's Used |
|------|-----------|-----------------|
| **RAG** | Retrieval-Augmented Generation | Core architecture pattern |
| **RRF** | Reciprocal Rank Fusion | Merging dense + BM25 results |
| **HyDE** | Hypothetical Document Embeddings | Optional retrieval improvement |
| **BM25** | Best Matching 25 (TF-IDF variant) | Keyword/sparse search |
| **HNSW** | Hierarchical Navigable Small World | ChromaDB's vector index |
| **RAGAS** | RAG Assessment framework | Answer quality evaluation |
| **TLM** | Trustworthy Language Model | Trust score computation |
| **SON** | Self-Organizing Networks | Telecom domain concept |
| **HARQ** | Hybrid Automatic Repeat Request | Common telecom example query |
| **Cross-Encoder** | Model scoring query-doc pairs | Reranking stage |
