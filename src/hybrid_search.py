"""Telecom RAG - Hybrid Search Module

Implements BM25 + Dense Vector hybrid search with Reciprocal Rank Fusion (RRF).
Based on Telco-RAG architecture specification.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from rank_bm25 import BM25Okapi


@dataclass
class SearchResult:
    """Unified search result from hybrid search."""
    content: str
    metadata: Dict[str, Any]
    dense_score: float
    sparse_score: float
    rrf_score: float
    rank: int


class TelecomTokenizer:
    """Simple tokenizer optimized for telecom terminology."""
    
    # Telecom-specific stopwords (common but not informative)
    STOPWORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it',
        'its', 'what', 'which', 'who', 'whom', 'whose'
    }
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        Preserves acronyms and technical terms.
        """
        # Lowercase but preserve acronyms
        text_lower = text.lower()
        
        # Split on whitespace and punctuation, but keep acronyms together
        tokens = re.findall(r'\b[a-z0-9]+(?:-[a-z0-9]+)*\b', text_lower)
        
        # Also extract uppercase acronyms from original text
        acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
        tokens.extend([a.lower() for a in acronyms])
        
        # Remove stopwords but keep technical terms
        filtered = [t for t in tokens if t not in self.STOPWORDS or len(t) <= 3]
        
        return filtered


class HybridSearcher:
    """
    Hybrid search combining dense (semantic) and sparse (BM25) retrieval.
    Uses Reciprocal Rank Fusion (RRF) for score combination.
    """
    
    def __init__(self, rrf_k: int = 60):
        """
        Initialize hybrid searcher.
        
        Args:
            rrf_k: RRF constant (default 60 as per architecture)
        """
        self.rrf_k = rrf_k
        self.tokenizer = TelecomTokenizer()
        self.bm25 = None
        self.corpus_tokens = []
        self.documents = []
        self.is_indexed = False
    
    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of dicts with 'content' and 'metadata' keys
        """
        self.documents = documents
        self.corpus_tokens = []
        
        print(f"🔧 Tokenizing {len(documents)} documents for BM25...")
        for doc in documents:
            content = doc.get('content', '')
            tokens = self.tokenizer.tokenize(content)
            self.corpus_tokens.append(tokens)
        
        self.bm25 = BM25Okapi(self.corpus_tokens)
        self.is_indexed = True
        print(f"✅ BM25 index built with {len(documents)} documents")
    
    def save_index(self, path: str):
        """Save BM25 index to disk for fast reload."""
        import pickle
        save_data = {
            'corpus_tokens': self.corpus_tokens,
            'documents': self.documents,
            'doc_count': len(self.documents)
        }
        with open(path, 'wb') as f:
            pickle.dump(save_data, f)
        print(f"💾 BM25 index saved to {path}")
    
    def load_index(self, path: str) -> bool:
        """Load BM25 index from disk. Returns True if successful."""
        import pickle
        import os
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'rb') as f:
                save_data = pickle.load(f)
            
            self.corpus_tokens = save_data['corpus_tokens']
            self.documents = save_data['documents']
            self.bm25 = BM25Okapi(self.corpus_tokens)
            self.is_indexed = True
            print(f"⚡ BM25 index loaded from cache ({len(self.documents)} docs)")
            return True
        except Exception as e:
            print(f"⚠️ Could not load BM25 cache: {e}")
            return False
    
    def bm25_search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """
        Perform BM25 keyword search.
        
        Returns:
            List of (doc_index, score) tuples
        """
        if not self.is_indexed:
            return []
        
        query_tokens = self.tokenizer.tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(int(idx), float(scores[idx])) for idx in top_indices]
    
    def reciprocal_rank_fusion(
        self,
        dense_results: List[Tuple[int, float]],
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float, float, float]]:
        """
        Combine dense and sparse results using RRF.
        
        Formula: score = sum(1 / (k + rank_i))
        
        Returns:
            List of (doc_index, rrf_score, dense_score, sparse_score) tuples
        """
        scores = {}
        dense_scores = {}
        sparse_scores = {}
        
        # Calculate RRF scores from dense results
        for rank, (idx, score) in enumerate(dense_results, 1):
            rrf_contribution = 1.0 / (self.rrf_k + rank)
            scores[idx] = scores.get(idx, 0) + rrf_contribution
            dense_scores[idx] = score
        
        # Calculate RRF scores from sparse results
        for rank, (idx, score) in enumerate(sparse_results, 1):
            rrf_contribution = 1.0 / (self.rrf_k + rank)
            scores[idx] = scores.get(idx, 0) + rrf_contribution
            sparse_scores[idx] = score
        
        # Sort by combined RRF score
        combined = [
            (idx, rrf_score, dense_scores.get(idx, 0), sparse_scores.get(idx, 0))
            for idx, rrf_score in scores.items()
        ]
        combined.sort(key=lambda x: x[1], reverse=True)
        
        return combined
    
    def hybrid_search(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        top_k: int = 12
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining dense vectors with BM25.
        
        Args:
            query: Search query
            dense_results: Results from vector store with 'content', 'metadata', 'similarity'
            top_k: Number of results to return
            
        Returns:
            List of SearchResult with combined RRF scores
        """
        if not self.is_indexed:
            # Fall back to dense-only if BM25 not indexed
            return [
                SearchResult(
                    content=r['content'],
                    metadata=r['metadata'],
                    dense_score=r.get('similarity', 0),
                    sparse_score=0,
                    rrf_score=r.get('similarity', 0),
                    rank=i + 1
                )
                for i, r in enumerate(dense_results[:top_k])
            ]
        
        # Build dense results index mapping
        content_to_idx = {}
        for i, doc in enumerate(self.documents):
            content_to_idx[doc['content'][:200]] = i  # Use prefix for matching
        
        # Map dense results to document indices
        dense_ranked = []
        for result in dense_results:
            content_prefix = result['content'][:200]
            if content_prefix in content_to_idx:
                idx = content_to_idx[content_prefix]
                dense_ranked.append((idx, result.get('similarity', 0)))
        
        # Get BM25 results
        sparse_ranked = self.bm25_search(query, top_k=top_k * 2)
        
        # Combine with RRF
        combined = self.reciprocal_rank_fusion(dense_ranked, sparse_ranked)
        
        # Build final results
        results = []
        for rank, (idx, rrf_score, dense_score, sparse_score) in enumerate(combined[:top_k], 1):
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append(SearchResult(
                    content=doc['content'],
                    metadata=doc['metadata'],
                    dense_score=dense_score,
                    sparse_score=sparse_score,
                    rrf_score=rrf_score,
                    rank=rank
                ))
        
        return results


# Global instance for caching
_hybrid_searcher = None


def get_hybrid_searcher() -> HybridSearcher:
    """Get or create global hybrid searcher instance."""
    global _hybrid_searcher
    if _hybrid_searcher is None:
        _hybrid_searcher = HybridSearcher(rrf_k=60)
    return _hybrid_searcher


if __name__ == "__main__":
    # Test hybrid search
    searcher = HybridSearcher()
    
    # Sample documents
    test_docs = [
        {"content": "HARQ is Hybrid Automatic Repeat Request used in 5G NR", "metadata": {"source": "test"}},
        {"content": "5G NR uses OFDM modulation for radio transmission", "metadata": {"source": "test"}},
        {"content": "MIMO technology uses multiple antennas for better throughput", "metadata": {"source": "test"}},
    ]
    
    searcher.index_documents(test_docs)
    
    # Simulate dense results
    dense_results = [
        {"content": test_docs[0]["content"], "metadata": test_docs[0]["metadata"], "similarity": 0.85},
        {"content": test_docs[2]["content"], "metadata": test_docs[2]["metadata"], "similarity": 0.72},
    ]
    
    results = searcher.hybrid_search("What is HARQ in 5G?", dense_results, top_k=3)
    
    print("\n🔍 Hybrid Search Results:")
    for r in results:
        print(f"  Rank {r.rank}: RRF={r.rrf_score:.4f}, Dense={r.dense_score:.2f}, BM25={r.sparse_score:.2f}")
        print(f"    {r.content[:60]}...")
