"""Telecom RAG - Reranker Module

Cross-encoder reranker for improved result ordering.
Uses ms-marco-MiniLM-L-6-v2 for efficient reranking.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class Reranker:
    """Cross-encoder reranker for improving retrieval precision."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", lazy: bool = True):
        """
        Initialize the reranker.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
            lazy: If True, defer model loading until first use (faster startup)
        """
        self.model_name = model_name
        self.model = None
        self._initialized = False
        
        if not lazy:
            self._initialize()
    
    def _initialize(self):
        """Load the cross-encoder model (lazy loading)."""
        if self._initialized:
            return
        
        try:
            from sentence_transformers import CrossEncoder
            
            print(f"🔧 Loading reranker: {self.model_name} (one-time)")
            self.model = CrossEncoder(self.model_name)
            self._initialized = True
            print("✅ Reranker initialized")
            
        except ImportError:
            print("⚠️ sentence-transformers not installed. Reranker disabled.")
            self.model = None
            self._initialized = True
        except Exception as e:
            # Handle HuggingFace rate limits, network errors, etc.
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                print(f"⚠️ HuggingFace rate limit hit when loading reranker. Reranker disabled.")
            else:
                print(f"⚠️ Failed to load reranker: {e}. Reranker disabled.")
            self.model = None
            self._initialized = True
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder.
        
        Args:
            query: Search query
            documents: List of document dicts with 'content' key
            top_k: Number of top results to return
            
        Returns:
            Reranked documents with 'rerank_score' added
        """
        # Lazy initialization - load model on first use
        if not self._initialized:
            self._initialize()
        
        if not self.model or not documents:
            return documents[:top_k]
        
        # Create query-document pairs
        pairs = [(query, doc.get("content", "")[:512]) for doc in documents]
        
        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs)
            
            # Add rerank scores to documents
            for idx, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[idx])
            
            # Sort by rerank score (descending)
            reranked = sorted(documents, key=lambda x: x.get("rerank_score", 0), reverse=True)
            
            return reranked[:top_k]
            
        except Exception as e:
            print(f"⚠️ Reranking failed: {e}")
            return documents[:top_k]
    
    def is_available(self) -> bool:
        """Check if reranker is available (triggers lazy init)."""
        if not self._initialized:
            self._initialize()
        return self.model is not None


# Singleton instance
_reranker_instance: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Get or create reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance


if __name__ == "__main__":
    # Test reranker
    reranker = Reranker()
    
    test_docs = [
        {"content": "HARQ is a hybrid automatic repeat request mechanism.", "similarity": 0.8},
        {"content": "5G NR uses OFDM for radio transmission.", "similarity": 0.7},
        {"content": "HARQ in 5G NR supports 16 parallel processes.", "similarity": 0.75},
    ]
    
    query = "What is HARQ in 5G NR?"
    reranked = reranker.rerank(query, test_docs, top_k=3)
    
    print("\n🔄 Reranked results:")
    for idx, doc in enumerate(reranked):
        print(f"  {idx+1}. Score: {doc.get('rerank_score', 0):.3f} - {doc['content'][:50]}...")
