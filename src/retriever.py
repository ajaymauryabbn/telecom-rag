"""Telecom RAG - Retriever Module (Enhanced)

Orchestrates the full RAG pipeline with:
1. Query enhancement with glossary (Telco-RAG validated)
2. Hybrid search (Dense + BM25 with RRF fusion)
3. Cross-encoder reranking for improved precision
4. Semantic caching for query deduplication
5. RAGAS-style evaluation with abstention logic
6. LLM generation with citations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from .config import TOP_K_RESULTS, CONTEXT_MAX_TOKENS, ENABLE_RERANK, ENABLE_HYBRID
from .glossary import TelecomGlossary
from .vector_store import TelecomVectorStore
from .llm import TelecomLLM
from .data_loader import TelecomDataLoader
from .hybrid_search import HybridSearcher, SearchResult, get_hybrid_searcher
from .evaluation import RAGEvaluator, EvaluationResult, get_evaluator
from .reranker import Reranker, get_reranker
from .cache import SemanticCache, get_cache
from .router import QueryRouter, RetrievalStrategy, get_router

# Optimized top-k for faster responses (reduced from 12)
DEFAULT_TOP_K = 6


@dataclass
class RAGResponse:
    """Structured RAG response with evaluation metrics."""
    answer: str
    sources: List[Dict[str, Any]]
    enhanced_query: str
    glossary_terms: str
    usage: Dict[str, Any]
    # New evaluation fields
    evaluation: Optional[EvaluationResult] = None
    search_type: str = "dense"  # "dense", "hybrid", or "reranked"
    abstained: bool = False


class TelecomRetriever:
    """Main RAG retriever for telecom queries with hybrid search, reranking, and evaluation."""
    
    def __init__(self, auto_init: bool = True, enable_hybrid: bool = None, enable_rerank: bool = None):
        """
        Initialize the retriever.

        Args:
            auto_init: If True, initialize all components immediately
            enable_hybrid: If True, use hybrid search (BM25 + Dense). Defaults to ENABLE_HYBRID env var.
            enable_rerank: If True, use cross-encoder reranking. Defaults to ENABLE_RERANK env var.
        """
        self.glossary = TelecomGlossary()
        self.vector_store = None
        self.llm = None
        self.hybrid_searcher = None
        self.evaluator = None
        self.reranker = None
        self.is_initialized = False
        # Use env var defaults if not explicitly set
        self.enable_hybrid = enable_hybrid if enable_hybrid is not None else ENABLE_HYBRID
        self.enable_rerank = enable_rerank if enable_rerank is not None else ENABLE_RERANK
        
        if auto_init:
            self.initialize()
    
    def initialize(self):
        """Initialize vector store, hybrid search, reranker, and LLM."""
        try:
            print("🚀 Initializing Telecom RAG Retriever (Enhanced)...")
            
            # Initialize vector store
            self.vector_store = TelecomVectorStore()
            
            # Initialize hybrid searcher
            if self.enable_hybrid:
                self.hybrid_searcher = get_hybrid_searcher()
                print("✅ Hybrid search enabled (BM25 + Dense + RRF)")
            
            # Initialize reranker (lazy - will load on first query)
            if self.enable_rerank:
                self.reranker = get_reranker()
                print("✅ Cross-encoder reranking enabled (lazy load)")
            
            # Initialize evaluator
            self.evaluator = get_evaluator()
            print("✅ RAGAS evaluation enabled")
            
            # Initialize router
            self.router = get_router()
            print("✅ NN Router enabled (Semantic Classification)")
            
            # Check if we have documents
            stats = self.vector_store.get_stats()
            if stats["total_documents"] == 0:
                print("⚠️ Vector store is empty. Run ingest_data() first.")
            else:
                # Build BM25 index from existing documents
                self._build_hybrid_index()
            
            # Initialize LLM (graceful handling for cloud deployment)
            try:
                self.llm = TelecomLLM()
            except (ValueError, ImportError, Exception) as e:
                print(f"⚠️ LLM not available: {e}")
                print("   RAG will work but answers will be context-only (no generation)")
                self.llm = None
            
            self.is_initialized = True
            print("✅ Retriever initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing retriever: {e}")
            raise
    
    def _build_hybrid_index(self):
        """Build BM25 index from vector store documents (with caching)."""
        if not self.enable_hybrid or self.hybrid_searcher is None:
            return
        
        from .config import DATA_DIR
        cache_path = str(DATA_DIR / "bm25_index.pkl")
        
        # Try to load from cache first (FAST PATH)
        if self.hybrid_searcher.load_index(cache_path):
            return  # Cache hit - done!
        
        # Cache miss - rebuild index
        try:
            print("📚 Building BM25 index (first time only)...")
            loader = TelecomDataLoader()
            docs = loader.load_processed_data()
            
            if docs:
                hybrid_docs = [{"content": d.content, "metadata": d.metadata} for d in docs]
                self.hybrid_searcher.index_documents(hybrid_docs)
                # Save to cache for next time
                self.hybrid_searcher.save_index(cache_path)
        except Exception as e:
            print(f"⚠️ Could not build hybrid index: {e}")
    
    def ingest_data(self, force_reload: bool = False):
        """
        Load and ingest telecom data into vector store.
        
        Args:
            force_reload: If True, clear existing data and reload
        """
        if self.vector_store is None:
            self.vector_store = TelecomVectorStore()
        
        # Check if data already exists
        stats = self.vector_store.get_stats()
        if stats["total_documents"] > 0 and not force_reload:
            print(f"📚 Vector store already has {stats['total_documents']} documents")
            print("   Use force_reload=True to reload data")
            return
        
        if force_reload:
            self.vector_store.clear()
        
        # Load data
        loader = TelecomDataLoader()
        documents = loader.load_all_data()
        
        if documents:
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            # Save processed data for caching
            loader.save_processed_data()
            
            # Build hybrid index
            if self.enable_hybrid and self.hybrid_searcher is not None:
                hybrid_docs = [{"content": d.content, "metadata": d.metadata} for d in documents]
                self.hybrid_searcher.index_documents(hybrid_docs)
            
            print(f"\n✅ Ingested {len(documents)} documents into vector store")
        else:
            print("⚠️ No documents to ingest")
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """
        Generate a hypothetical answer for HyDE (Hypothetical Document Embeddings).
        This improves retrieval by searching for documents similar to what an ideal answer looks like.
        
        Per architecture doc: +2-3.5% accuracy improvement.
        """
        if not self.llm:
            return ""
        
        try:
            prompt = f"""You are a telecom expert. Write a short, factual answer (2-3 sentences) to this question:

Question: {query}

Answer:"""
            answer = self.llm.simple_generate(prompt)
            return answer
        except Exception as e:
            print(f"⚠️ HyDE generation failed: {e}")
            return ""
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = DEFAULT_TOP_K,
        category: Optional[str] = None,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        use_hyde: bool = False  # Disabled by default for faster responses
    ) -> Tuple[List[Dict[str, Any]], str, str, str]:
        """
        Retrieve relevant documents using specified strategy.
        
        Args:
            query: User's question
            top_k: Number of results to retrieve
            category: Optional category filter
            strategy: Retrieval strategy (DENSE, HYBRID, KEYWORD)
            use_hyde: Whether to use HyDE (for DENSE/HYBRID)
            
        Returns:
            Tuple of (results, enhanced_query, glossary_terms, search_type)
        """
        # Enhance query with glossary
        enhanced_query, glossary_terms = self.glossary.enhance_query(query)
        
        # Apply HyDE if enabled (useful for Dense/Hybrid, less for Keyword)
        if use_hyde and self.llm and strategy != RetrievalStrategy.KEYWORD:
            hypothetical_answer = self.generate_hypothetical_answer(query)
            if hypothetical_answer:
                enhanced_query = f"{enhanced_query} {hypothetical_answer[:200]}"
        
        search_type = strategy.value
        results = []
        
        # KEYWORD STRATEGY (Pure BM25)
        if strategy == RetrievalStrategy.KEYWORD:
            if self.hybrid_searcher and self.hybrid_searcher.is_indexed:
                # Use raw query for keyword search (better for exact matches)
                bm25_results = self.hybrid_searcher.bm25_search(query, top_k=top_k * 2)
                # Map back to documents
                for idx, score in bm25_results:
                    if idx < len(self.hybrid_searcher.documents):
                        doc = self.hybrid_searcher.documents[idx]
                        results.append({
                            "content": doc['content'],
                            "metadata": doc['metadata'],
                            "similarity": score, # BM25 score
                            "sparse_score": score
                        })
                search_type = "keyword (bm25)"
            else:
                # Fallback to dense if BM25 not ready
                print("⚠️ BM25 non-ready, falling back to dense")
                strategy = RetrievalStrategy.DENSE
        
        # DENSE STRATEGY
        if strategy == RetrievalStrategy.DENSE:
            if category:
                results = self.vector_store.search_by_category(enhanced_query, category, top_k * 2)
            else:
                results = self.vector_store.search(enhanced_query, top_k * 2)
            search_type = "dense"

        # HYBRID STRATEGY
        if strategy == RetrievalStrategy.HYBRID:
            # Get dense results first
            if category:
                dense_results = self.vector_store.search_by_category(enhanced_query, category, top_k * 2)
            else:
                dense_results = self.vector_store.search(enhanced_query, top_k * 2)
            
            if self.hybrid_searcher and self.hybrid_searcher.is_indexed:
                hybrid_results = self.hybrid_searcher.hybrid_search(enhanced_query, dense_results, top_k * 2)
                results = [
                    {
                        "content": r.content,
                        "metadata": r.metadata,
                        "similarity": r.rrf_score * 10,
                        "dense_score": r.dense_score,
                        "sparse_score": r.sparse_score,
                        "rrf_score": r.rrf_score
                    }
                    for r in hybrid_results
                ]
                search_type = "hybrid"
            else:
                results = dense_results[:top_k * 2]
        
        # Apply reranking (Generic for all strategies to improve precision)
        if self.enable_rerank and self.reranker and results:
            # Check availability (lazy load)
            self.reranker.is_available() 
            results = self.reranker.rerank(query, results, top_k)
            search_type = f"{search_type} + reranked"
        else:
            results = results[:top_k]
        
        return results, enhanced_query, glossary_terms, search_type
    
    def _build_context(self, results: List[Dict[str, Any]], max_tokens: int = CONTEXT_MAX_TOKENS) -> str:
        """Build context string from search results with source attribution."""
        context_parts = []
        total_length = 0
        
        for idx, result in enumerate(results, 1):
            source = result["metadata"].get("source", "Unknown")
            category = result["metadata"].get("category", "general")
            content = result["content"]
            similarity = result.get("similarity", 0)
            
            # Check for hybrid search info
            rrf_info = ""
            if "rrf_score" in result:
                rrf_info = f", RRF: {result['rrf_score']:.4f}"
            
            part = f"[Source {idx}: {source} ({category}), Relevance: {similarity:.2f}{rrf_info}]\n{content}"
            
            # Estimate tokens (rough: 4 chars per token)
            part_tokens = len(part) // 4
            if total_length + part_tokens > max_tokens:
                break
            
            context_parts.append(part)
            total_length += part_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def query(
        self, 
        question: str,
        top_k: int = DEFAULT_TOP_K,
        category: Optional[str] = None,
        use_hybrid: bool = True,
        evaluate: bool = True,
        use_llm_eval: bool = False
    ) -> RAGResponse:
        """
        Execute full RAG pipeline with evaluation.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            category: Optional category filter
            use_hybrid: Whether to use hybrid search
            evaluate: Whether to run evaluation
            use_llm_eval: Whether to use LLM for evaluation
            
        Returns:
            RAGResponse with answer, sources, evaluation metrics
        """
        if not self.is_initialized:
            self.initialize()
        
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialized")
        
        # Check if vector store has data
        stats = self.vector_store.get_stats()
        if stats["total_documents"] == 0:
            return RAGResponse(
                answer="⚠️ No documents in knowledge base. Please run data ingestion first.",
                sources=[],
                enhanced_query=question,
                glossary_terms="",
                usage={},
                search_type="none"
            )
        
        # Check semantic cache for similar queries (per architecture Section 7.2)
        cache = get_cache()
        try:
            query_embedding = self.vector_store.embedding_model.embed_query(question)
            cached_response = cache.get(query_embedding)
            if cached_response:
                print("🎯 Cache hit - returning cached response")
                return RAGResponse(**cached_response)
        except Exception as e:
            print(f"⚠️ Cache check failed: {e}")
            query_embedding = None
        
        
        # Determine retrieval strategy and category via router
        strategy = RetrievalStrategy.HYBRID # Default
        predicted_category = None
        
        if self.router:
            strategy, strat_conf = self.router.route(question)
            predicted_category, cat_conf = self.router.classify_category(question)
            
            # User override
            if category: 
                # If category forced, stick to Hybrid for robustness
                strategy = RetrievalStrategy.HYBRID
                predicted_category = category # Use explicit category
        
        # Retrieve documents (using predicted category if not explicitly provided)
        search_category = category if category else predicted_category
        
        results, enhanced_query, glossary_terms, search_type = self.retrieve(
            question, top_k, search_category, strategy=strategy
        )
        
        if not results:
            return RAGResponse(
                answer="I couldn't find relevant information in the knowledge base for your question.",
                sources=[],
                enhanced_query=enhanced_query,
                glossary_terms=glossary_terms,
                usage={},
                search_type=search_type
            )
        
        # Build context
        context = self._build_context(results)
        
        # Get similarity scores for evaluation
        similarity_scores = [r.get("similarity", 0) for r in results]
        
        # Generate response
        if self.llm is None:
            # Return retrieved context without LLM generation
            answer = f"**Retrieved Information (LLM not configured):**\n\n{context}"
            
            return RAGResponse(
                answer=answer,
                sources=results,
                enhanced_query=enhanced_query,
                glossary_terms=glossary_terms,
                usage={},
                search_type=search_type
            )
        
        llm_response = self.llm.generate(
            question=question,
            context=context,
            glossary_terms=glossary_terms
        )
        
        answer = llm_response["answer"]
        evaluation_result = None
        abstained = False
        
        # Run evaluation
        if evaluate and self.evaluator:
            evaluation_result = self.evaluator.evaluate(
                question=question,
                answer=answer,
                context=context,
                similarity_scores=similarity_scores,
                use_llm=use_llm_eval
            )
            
            # Check if we should abstain
            if evaluation_result.should_abstain:
                abstained = True
                answer = self.evaluator.get_abstention_message(evaluation_result.abstention_reason)
                answer += f"\n\n---\n\n**Evaluation Details:**\n- Faithfulness: {evaluation_result.faithfulness_score:.2f}\n- Relevancy: {evaluation_result.relevancy_score:.2f}\n- Confidence: {evaluation_result.confidence_score:.2f}"
        
        # Build response
        response = RAGResponse(
            answer=answer,
            sources=results,
            enhanced_query=enhanced_query,
            glossary_terms=glossary_terms,
            usage=llm_response.get("usage", {}),
            evaluation=evaluation_result,
            search_type=search_type,
            abstained=abstained
        )
        
        # Cache the response (only if not abstained)
        if not abstained:
            try:
                # Convert to dict for caching (exclude non-serializable)
                cache_data = {
                    "answer": response.answer,
                    "sources": response.sources,
                    "enhanced_query": response.enhanced_query,
                    "glossary_terms": response.glossary_terms,
                    "usage": response.usage,
                    "search_type": response.search_type,
                    "abstained": response.abstained
                }
                cache.set(query_embedding, question, cache_data)
            except Exception as e:
                print(f"⚠️ Cache set failed: {e}")
        
        return response
    
    def get_sample_queries(self) -> List[Dict[str, str]]:
        """Get sample queries for UI."""
        return [
            {
                "category": "Technical Definition",
                "query": "What is the HARQ process in 5G NR?",
                "description": "Explains core 5G radio technology"
            },
            {
                "category": "Network Operations",
                "query": "How to troubleshoot VSWR alarm on cell site?",
                "description": "Network maintenance guidance"
            },
            {
                "category": "Standards",
                "query": "What are the key features of 3GPP Release 17?",
                "description": "5G specifications overview"
            },
            {
                "category": "Performance",
                "query": "What KPIs should be monitored for 5G network quality?",
                "description": "Network performance metrics"
            },
            {
                "category": "Architecture",
                "query": "Explain the difference between gNB and eNB",
                "description": "5G vs 4G base stations"
            },
            {
                "category": "Compliance",
                "query": "What spectrum bands are used for 5G FR1?",
                "description": "Regulatory compliance"
            }
        ]


if __name__ == "__main__":
    # Test retriever
    print("🧪 Testing Enhanced Telecom RAG Retriever\n")
    
    retriever = TelecomRetriever(auto_init=True, enable_hybrid=True)
    
    # Check stats
    stats = retriever.vector_store.get_stats()
    print(f"📊 Vector Store Stats: {stats}")
    
    if stats["total_documents"] == 0:
        print("\n📥 Ingesting data...")
        retriever.ingest_data()
    
    # Test query
    test_query = "What is HARQ in 5G?"
    print(f"\n🔍 Testing query: '{test_query}'")
    
    results, enhanced_query, glossary_terms, search_type = retriever.retrieve(test_query)
    
    print(f"\n🔎 Search type: {search_type}")
    print(f"📝 Enhanced query: {enhanced_query}")
    print(f"📖 Glossary terms:\n{glossary_terms}")
    print(f"📄 Retrieved {len(results)} documents")
    
    for idx, r in enumerate(results[:3], 1):
        print(f"\n--- Result {idx} ---")
        print(f"Source: {r['metadata'].get('source', 'Unknown')}")
        print(f"Similarity: {r.get('similarity', 0):.3f}")
        if 'rrf_score' in r:
            print(f"RRF Score: {r['rrf_score']:.4f}")
        print(f"Content: {r['content'][:150]}...")
