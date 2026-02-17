"""Telecom RAG - Semantic Query Cache

Implements semantic caching for query deduplication:
- Uses embedding similarity to detect similar queries
- Cache hits return previous answers without re-running the pipeline
- Reduces latency and LLM costs

Per architecture doc Section 7.2: Similarity threshold 0.95
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime, timedelta



import json
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import os

class SemanticCache:
    """
    Semantic cache with Redis persistence.
    - Vectors: Kept in memory (numpy) for fast cosine similarity search.
    - Payloads: Stored in Redis (hash) for persistence and sharing.
    - Persistence: On startup, vectors are loaded from Redis into memory.
    """
    
    def __init__(
        self, 
        similarity_threshold: float = 0.95,
        max_cache_size: int = 1000,
        ttl_hours: int = 24,
        redis_url: str = None
    ):
        """
        Initialize semantic cache with Redis.

        Args:
            similarity_threshold: Minimum similarity for cache hit
            redis_url: Connection string for Redis
        """
        from .config import ENABLE_REDIS

        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)
        self.redis = None
        self.local_cache = []

        # In-memory vector index: List of (embedding, redis_key)
        self.vector_index: List[Tuple[np.ndarray, str]] = []

        if ENABLE_REDIS:
            # Get Redis URL from env or use provided value
            redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

            try:
                import redis
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )  # Bytes for vectors
                self.redis.ping()
                print("✅ Connected to Redis cache")
                self._load_index_from_redis()
            except Exception as e:
                print(f"⚠️ Redis unavailable: {e}")
                print("   Using in-memory only cache (will be lost on restart)")
                self.redis = None
        else:
            print("ℹ️ Redis disabled via config (ENABLE_REDIS=False)") 

    def _load_index_from_redis(self):
        """Load all cached vectors from Redis into memory."""
        if not self.redis:
            return
            
        try:
            # Keys pattern: "cache:vector:*"
            keys = self.redis.keys("cache:vector:*")
            count = 0
            for key in keys:
                # Key is bytes, decode to str
                key_str = key.decode("utf-8")
                # Get vector (bytes -> numpy)
                vector_bytes = self.redis.get(key)
                if vector_bytes:
                    vector = pickle.loads(vector_bytes)
                    # Extract ID from key: cache:vector:<uuid>
                    cache_id = key_str.split(":")[-1]
                    self.vector_index.append((vector, cache_id))
                    count += 1
            print(f"⚡ Loaded {count} vectors from Redis cache")
        except Exception as e:
            print(f"⚠️ Failed to sync with Redis: {e}")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def get(self, query_embedding: List[float]) -> Optional[Dict[str, Any]]:
        """Get cached response if similar query exists."""
        query_emb = np.array(query_embedding)

        # 1. Search in-memory vector index
        best_sim = -1.0
        best_id = None
        best_idx = None

        for idx, (cached_emb, cache_id) in enumerate(self.vector_index):
            sim = self._cosine_similarity(query_emb, cached_emb)
            if sim > best_sim:
                best_sim = sim
                best_id = cache_id
                best_idx = idx

        # 2. Check threshold
        if best_sim >= self.similarity_threshold and best_id is not None:
            # 3. Retrieve payload from Redis or local
            if self.redis:
                payload_json = self.redis.get(f"cache:payload:{best_id}")
                if payload_json:
                    return json.loads(payload_json)
            else:
                # Local fallback using tracked index
                if best_idx is not None and best_idx < len(self.local_cache):
                    return self.local_cache[best_idx]['payload']

        return None

    def set(self, query_embedding: List[float], query: str, response: Dict[str, Any]):
        """Cache a response."""
        import uuid
        cache_id = str(uuid.uuid4())
        
        # Helper to serialize datetime/numpy in JSON
        def json_serial(obj):
            if isinstance(obj, (datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return str(obj)

        vector_np = np.array(query_embedding)
        
        if self.redis:
            try:
                # 1. Store Vector (for reload)
                self.redis.setex(
                    f"cache:vector:{cache_id}",
                    self.ttl,
                    pickle.dumps(vector_np)
                )
                
                # 2. Store Payload
                self.redis.setex(
                    f"cache:payload:{cache_id}", 
                    self.ttl,
                    json.dumps(response, default=json_serial)
                )
                
                # 3. Add to local index
                self.vector_index.append((vector_np, cache_id))
                
            except Exception as e:
                print(f"⚠️ Redis cache set failed: {e}")
        else:
            # Fallback
            if len(self.local_cache) >= 1000:
                self.local_cache.pop(0)
                self.vector_index.pop(0)
            
            self.local_cache.append({'payload': response})
            self.vector_index.append((vector_np, cache_id)) # ID doesn't matter much here
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_queries": len(self.vector_index),
            "backend": "redis" if self.redis else "in-memory",
            "similarity_threshold": self.similarity_threshold,
        }

    def clear(self):
        if self.redis:
            self.redis.flushdb()
        self.vector_index = []
        self.local_cache = []


# Global instance
_cache_instance: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance


if __name__ == "__main__":
    # Test cache
    cache = SemanticCache(similarity_threshold=0.9)
    
    # Simulate embeddings (random vectors)
    embedding1 = np.random.rand(384).tolist()
    embedding2 = np.random.rand(384).tolist()
    embedding1_similar = (np.array(embedding1) * 0.99 + np.random.rand(384) * 0.01).tolist()
    
    # Test cache miss
    result = cache.get(embedding1)
    print(f"Cache miss: {result}")
    
    # Add to cache
    cache.set(embedding1, "What is HARQ?", {"answer": "HARQ is..."})
    
    # Test cache hit with similar embedding
    result = cache.get(embedding1_similar)
    print(f"Cache hit: {result}")
    
    # Test cache miss with different embedding
    result = cache.get(embedding2)
    print(f"Cache miss different: {result}")
    
    print(f"\nStats: {cache.get_stats()}")
