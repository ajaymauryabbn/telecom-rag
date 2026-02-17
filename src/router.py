"""Telecom RAG - Neural Network Router

Classifies query intent to select optimal retrieval strategy:
- FACTUAL: "What is X?" -> Dense Search
- PROCEDURAL: "How to fix X?" -> Hybrid + Rerank
- KEYWORD: "Error 501" -> BM25

Uses sentence-transformers for semantic similarity to labeled prototypes.
"""

from typing import List, Dict, Any, Tuple
from enum import Enum
import numpy as np

class RetrievalStrategy(Enum):
    DENSE = "dense"        # Best for concept/definition questions
    HYBRID = "hybrid"      # Best for robust retrieval
    KEYWORD = "keyword"    # Best for specific error codes/identifiers

class QueryRouter:
    """
    Semantic router for query intent classification.
    Uses embedding similarity to prototype questions.
    """
    
    def __init__(self, embedding_model=None):
        """
        Initialize router.
        
        Args:
            embedding_model: Instance of EmbeddingModel. If None, will load one.
        """
        # Prototype questions for strategy classification
        self.strategy_prototypes = {
            RetrievalStrategy.DENSE: [
                "What is 5G NR?",
                "Explain the concept of beamforming",
                "Define latency in telecom networks",
                "What does 3GPP Release 16 cover?",
                "Meaning of SIB1",
                "Overview of network slicing"
            ],
            RetrievalStrategy.HYBRID: [
                "How to troubleshoot VSWR high alarm?",
                "Steps to configure an X2 interface",
                "Procedure for replacement of BBU",
                "Why is the call drop rate high in this sector?",
                "Resolve cell sleeping issue",
                "Optimization guide for mobility parameters"
            ],
            RetrievalStrategy.KEYWORD: [
                "Error code 5301",
                "Alarm ID 2839",
                "Parameter s-Measure",
                "3GPP TS 38.211",
                "Huawei eNodeB",
                "Ericsson 6648"
            ]
        }
        
        # Prototype questions for category classification (Architecture Alignment)
        self.category_prototypes = {
            "standards": [
                "What is specified in 3GPP Release 15?",
                "TS 38.211 specification details",
                "Regulatory requirements for 5G spectrum",
                "ITU guidelines for IMT-2020",
                "Standard compliant frequency bands"
            ],
            "network_operations": [
                "How to fix cell outage alarm?",
                "Configuration steps for gNodeB",
                "Troubleshooting high VSWR",
                "Maintenance procedure for RRU",
                "Command to restart baseband unit"
            ],
            "performance": [
                "How to improve throughput?",
                "Analyze call drop rate statistics",
                "KPI definitions for 5G integrity",
                "Optimization of handover parameters",
                "Monitoring latency metrics"
            ],
            "architecture": [
                "Architecture of 5G Core Network",
                "Difference between NSA and SA",
                "Function of UPF in 5G",
                "Concept of Network Slicing",
                "Radio Access Network design"
            ]
        }
        
        self.embedding_model = embedding_model
        self.strategy_embeddings = {}
        self.category_embeddings = {}
        self._initialize()
    
    def _initialize(self):
        """Compute embeddings for prototypes."""
        if not self.embedding_model:
            from .embeddings import EmbeddingModel
            self.embedding_model = EmbeddingModel()
            
        print("🧠 Initializing NN Router prototypes...")
        
        # Strategy embeddings
        for strategy, texts in self.strategy_prototypes.items():
            embeddings = [self.embedding_model.embed_query(t) for t in texts]
            self.strategy_embeddings[strategy] = np.array(embeddings)
            
        # Category embeddings
        for category, texts in self.category_prototypes.items():
            embeddings = [self.embedding_model.embed_query(t) for t in texts]
            self.category_embeddings[category] = np.array(embeddings)
            
    def _find_best_match(self, query_emb: np.ndarray, prototypes_dict: Dict[Any, np.ndarray]) -> Tuple[Any, float]:
        """Generic nearest neighbor classifier."""
        best_score = -1.0
        best_label = None
        
        for label, prototypes in prototypes_dict.items():
            scores = []
            for proto in prototypes:
                norm_q = np.linalg.norm(query_emb)
                norm_p = np.linalg.norm(proto)
                if norm_q > 0 and norm_p > 0:
                    score = np.dot(query_emb, proto) / (norm_q * norm_p)
                else:
                    score = 0.0
                scores.append(score)
            
            max_score = max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_label = label
                
        return best_label, float(best_score)

    def route(self, query: str) -> Tuple[RetrievalStrategy, float]:
        """
        Classify query intent (Strategy).
        """
        query_emb = np.array(self.embedding_model.embed_query(query))
        best_strategy, score = self._find_best_match(query_emb, self.strategy_embeddings)
        
        if best_strategy is None: 
            best_strategy = RetrievalStrategy.HYBRID # Default
            
        print(f"🔀 Strategy: {best_strategy.value.upper()} (conf: {score:.2f})")
        return best_strategy, score

    def classify_category(self, query: str) -> Tuple[str, float]:
        """
        Classify document category (Standards, Ops, Perf, Arch).
        """
        query_emb = np.array(self.embedding_model.embed_query(query))
        best_category, score = self._find_best_match(query_emb, self.category_embeddings)
        
        if best_category is None:
            best_category = "general" # Default
            
        print(f"📂 Category: {best_category.upper()} (conf: {score:.2f})")
        return best_category, score

# Global instance
_router = None

def get_router() -> QueryRouter:
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router

if __name__ == "__main__":
    # Test router
    router = QueryRouter()
    
    test_queries = [
        "What is Handover?",
        "How do I fix a cell outage?",
        "Alarm 10234",
        "Procedure for antenna tilt",
        "Explain HARQ"
    ]
    
    for q in test_queries:
        strat, conf = router.route(q)
        cat, cat_conf = router.classify_category(q)
        print(f"'{q}' -> Strat: {strat.value}, Cat: {cat}\n")
