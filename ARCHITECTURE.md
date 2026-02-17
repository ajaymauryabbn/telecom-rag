# Telecom RAG - Architecture & Flow

This document provides an overview of the application's architecture, explaining the flow of data and the role of each component in the system.

## High-Level Architecture

The application is a Retrieval-Augmented Generation (RAG) system built to answer questions about telecom operations. It follows a sophisticated pipeline that enhances the user's query, retrieves relevant information from a knowledge base of documents, and then generates a trustworthy, evidence-backed answer.

## Architecture Diagram (Flow of a Query)

Here is a diagram representing the decision-making process when a user asks a question:

```
+-----------------+      +----------------------+      +--------------------+
|   User Query    |----->|        app.py        |----->|   retriever.py     |
| (Streamlit UI)  |      | (Rate Limit Check)   |      | (TelecomRetriever) |
+-----------------+      +----------------------+      +--------------------+
                                                             |
                                                             |
+------------------------------------------------------------+
|
v
+-----------------------------+
|   1. Query Enhancement      |
|                             |
|   - router.py: Classifies   |
|     query intent & category.|
|                             |
|   - glossary.py: Expands    |
|     query with telecom      |
|     acronyms.               |
|                             |
|   - HyDE (Optional):        |
|     Generates hypothetical  |
|     answer for better       |
|     semantic matching.      |
+-----------------------------+
      |
      | (Enhanced Query)
      v
+-----------------------------+
|   2. Retrieval              |
|                             |
|   - hybrid_search.py:       |
|     Performs parallel       |
|     keyword (BM25) and      |
|     semantic search.        |
|                             |
|   - vector_store.py:        |
|     Manages the ChromaDB    |
|     vector database.        |
|                             |
|   - Fuses results with RRF. |
+-----------------------------+
      |
      | (Retrieved Documents)
      v
+-----------------------------+
|   3. Reranking (Optional)   |
|                             |
|   - reranker.py: Re-scores  |
|     retrieved documents for |
|     higher relevance using  |
|     a cross-encoder model.  |
+-----------------------------+
      |
      | (Reranked Documents)
      v
+-----------------------------+
|   4. Generation             |
|                             |
|   - llm.py: Constructs a    |
|     prompt using the        |
|     enhanced query and      |
|     reranked documents.     |
|                             |
|   - Sends prompt to an LLM  |
|     (e.g., GPT-4o).         |
+-----------------------------+
      |
      | (Generated Answer)
      v
+-----------------------------+
|   5. Evaluation & Grounding |
|                             |
|   - evaluation.py:          |
|     - Verifies if the answer|
|       is supported by the   |
|       retrieved documents   |
|       (Faithfulness).       |
|     - Calculates TLM Trust  |
|       Score (Weighted avg). |
+-----------------------------+
      |
      |
      |                             +--------------------------+
      +---------------------------->|          app.py          |
                                    | (Displays Final Answer,  |
                                    |  Sources, & Metrics)     |
                                    +--------------------------+

```

## Detailed Architecture Flow

The process begins when a user interacts with the Streamlit web interface (`app.py`).

1.  **Orchestration & Security (`app.py` & `retriever.py`):**
    *   **Rate Limiting:** `app.py` first checks `rate_limiter.py` (Redis-backed) to ensure the user hasn't exceeded their quota (e.g., 50 req/min).
    *   It calls the `query()` method on the `TelecomRetriever` instance (from `retriever.py`), which acts as the main orchestrator for the entire RAG pipeline.

2.  **Query Enhancement:**
    *   **Routing (`router.py`):** The `QueryRouter` analyzes the user's query to determine intent (`FACTUAL`, `OPERATIONAL`) and category (`standards`, `network_operations`, `performance`, `architecture`) to filter the search space.
    *   **Glossary Expansion (`glossary.py`):** The query is passed to `TelecomGlossary` to define technical acronyms (e.g., "HARQ", "gNB").
    *   **HyDE (Hypothetical Document Embeddings):** Optionally, the LLM generates a hallucinated "ideal answer", which is then used to search the vector database. This improves retrieval for short or ambiguous queries.

3.  **Hybrid Search & Retrieval:**
    *   **`hybrid_search.py`:** The enhanced query is used to perform a hybrid search. This involves two search processes running in parallel:
        *   **Semantic Search:** The query is converted into a vector embedding and used to find similar documents in the `ChromaDB` vector store (managed by `vector_store.py`).
        *   **Keyword Search:** A traditional keyword search (BM25) is performed to find documents containing the exact technical terms.
    *   **Fusion:** Data from both searches are combined and re-scored using Reciprocal Rank Fusion (RRF).

4.  **Generation:**
    *   **`llm.py`:** The top-ranked documents are assembled into a context. A structured prompt is created, containing the user's original query, the enhanced query, and the retrieved context.
    *   This complete prompt is sent to a Large Language Model (LLM), which generates the final answer.

5.  **Evaluation and Final Output:**
    *   **`evaluation.py`:** Before displaying the answer, the system performs a final check using the **TLM (Trustworthy Logic Model)** framework.
    *   **Trust Score:** It calculates a weighted score based on **Faithfulness** (grounding), **Relevancy**, and **Confidence**.
    *   **`app.py`:** The final, verified answer is displayed to the user along with the Trust Score and sources.

## User's Perspective Flow

From the user's point of view, the flow is much simpler:

1.  The user opens the web application and sees the "Telecom RAG Assistant" interface.
2.  They type a question into the text box (e.g., "What is carrier aggregation?").
3.  They click the "Search" button.
4.  If they send too many requests quickly, they see a "Rate limit exceeded" warning.
5.  Otherwise, a loading spinner appears while the system performs the complex RAG pipeline.
6.  The generated answer appears on the screen.
7.  Below the answer, the user sees:
    *   **Trust Score:** A high-level metric (0-100%) indicating answer reliability.
    *   **Sources:** An expandable list of the top source documents (PDFs, CSVs) used to generate the answer.
