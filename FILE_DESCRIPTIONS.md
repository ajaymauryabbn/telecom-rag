# File Descriptions

This document describes the purpose of each key file within the `src/` directory.

---

### `config.py`
**Purpose:** Central configuration file for the entire application.
*   **Contains:** Hardcoded parameters, paths, model names, and prompt templates. For example, it defines the `CHUNK_SIZE` for document processing, the names of the embedding models to use (`OPENAI_EMBEDDING_MODEL`), and the structure of the prompt sent to the LLM (`TELECOM_PROMPT_TEMPLATE`).
*   **Why it's important:** It allows for easy modification of the system's behavior without changing the code.

---

### `data_loader.py`
**Purpose:** Handles all data ingestion and preparation.
*   **Contains:** The `TelecomDataLoader` class, which is responsible for finding documents, reading their content (PDFs, CSVs, etc.), and splitting them into smaller, manageable chunks.
*   **Why it's important:** This is the first step in building the knowledge base. It implements a sophisticated chunking strategy that is aware of document categories.

---

### `glossary.py`
**Purpose:** Manages the telecom-specific glossary.
*   **Contains:** The `TelecomGlossary` class. Its main function is to take a user's query and "enhance" it by finding and appending definitions for any telecom acronyms or jargon.
*   **Why it's important:** This step significantly improves retrieval accuracy by adding more context to the search query.

---

### `router.py`
**Purpose:** Intelligently routes and classifies incoming queries.
*   **Contains:** The `QueryRouter` class. It uses a neural network approach to classify the user's query into predefined categories and determine the best retrieval strategy.
*   **Why it's important:** It directs the query to the most relevant part of the knowledge base, making the search faster and more accurate.

---

### `vector_store.py`
**Purpose:** Manages the vector database.
*   **Contains:** The `TelecomVectorStore` class, which is a wrapper around `ChromaDB`. It handles the creation of the database, the storage of document embeddings (the vector representations of the text), and the retrieval of those embeddings.
*   **Why it's important:** This is the core of the semantic search capability.

---

### `embeddings.py`
**Purpose:** Handles the creation of vector embeddings.
*   **Contains:** The `TelecomEmbeddings` class. It takes text chunks from the documents and uses a pre-trained model (like `text-embedding-3-large` from OpenAI) to convert them into numerical vectors.
*   **Why it's important:** These embeddings are what allow the system to understand the semantic meaning of the text.

---

### `hybrid_search.py`
**Purpose:** Implements the hybrid search logic.
*   **Contains:** The `HybridSearcher` class. It combines the results of the semantic search (from `vector_store.py`) and a traditional keyword search (BM25). It uses a technique called Reciprocal Rank Fusion (RRF) to merge the two result lists.
*   **Why it's important:** Hybrid search is more robust than either keyword or semantic search alone, providing better results for a wide range of queries.

---

### `reranker.py`
**Purpose:** Re-scores the retrieved documents for relevance.
*   **Contains:** The `Reranker` class. After the initial hybrid search, this module can be used to take the top N documents and re-rank them using a more powerful (but slower) cross-encoder model.
*   **Why it's important:** This is an optional step that can further improve the quality of the documents sent to the LLM, leading to better answers.

---

### `llm.py`
**Purpose:** Manages all interactions with the Large Language Model (LLM).
*   **Contains:** The `TelecomLLM` class. It is responsible for taking the final context and the user query, formatting them into a structured prompt, and sending this prompt to an LLM like GPT-4o to generate the answer.
*   **Why it's important:** This is the "generation" part of RAG.

---

### `evaluation.py`
**Purpose:** Assesses the quality of the generated answer.
*   **Contains:** The `RAGEvaluator` class. After the LLM generates an answer, this module scores it based on metrics like **Faithfulness** (is the answer supported by the sources?) and **Relevancy**.
*   **Why it's important:** This acts as a critical guardrail against hallucinations and ensures the system produces trustworthy output.

---

### `cache.py`
**Purpose:** Implements caching strategies to improve performance and reduce cost.
*   **Contains:** The `SemanticCache` class. It can store the results of previous queries. If a new query is semantically similar to a cached one, the system can return the previous result instead of running the whole pipeline again.
*   **Why it's important:** Caching saves time and money by reducing the number of calls to expensive LLM APIs.

---

### `retriever.py`
**Purpose:** The main orchestrator of the RAG pipeline.
*   **Contains:** The `TelecomRetriever` class. Orchestrates HyDE (Hypothetical Document Embeddings), Query Enhancement, Hybrid Search, Reranking, and Generation.
*   **Why it's important:** It defines the end-to-end logic of the application.

---

### `app.py`
**Purpose:** The main application entrypoint and user interface.
*   **Contains:** The Streamlit code that creates the web interface. It performs rate limiting checks, calls the `TelecomRetriever`, and displays the answer with a TLM Trust Score.
*   **Why it's important:** This is the only part of the system the end-user directly interacts with.

---

### `rate_limiter.py`
**Purpose:** Handles API rate limiting to prevent abuse.
*   **Contains:** The `RateLimiter` class, which uses a Redis-backed token bucket or sliding window algorithm to throttle requests (e.g., 50 req/min).
*   **Why it's important:** Ensures production stability and prevents API quota exhaustion.

---

### `data_loader.py`
**Purpose:** Handles all data ingestion and preparation.
*   **Contains:** The `TelecomDataLoader` class. Supports loading PDFs (via PyMuPDF) and CSVs. Implements **dynamic chunking** (e.g., 500 tokens for performance docs, 125 for specs) to optimize retrieval context.
*   **Why it's important:** Ensures documents are split intelligently based on their category/type for better search relevance.

---

### `cache.py`
**Purpose:** Implements persistent semantic caching.
*   **Contains:** The `SemanticCache` class, backed by **Redis**. It stores embedding-based query results to return instant answers for repeated or similar questions (TTL 24h).
*   **Why it's important:** Reduces latency and LLM costs significantly in production.

---

### `evaluation.py`
**Purpose:** Assesses the quality of the generated answer.
*   **Contains:** The `RAGEvaluator` class. Calculates a **TLM Trust Score** (Trustworthy Logic Model) by combining Faithfulness, Relevancy, and Confidence. Can optionally use LLM-as-a-judge for higher accuracy.
*   **Why it's important:** Provides a single, understandable metric (0-100%) for users to trust the AI's output.
