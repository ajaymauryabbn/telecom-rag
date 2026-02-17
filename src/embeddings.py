"""Telecom RAG - Embeddings Module

Handles embedding generation using:
- Local: sentence-transformers (free)
- OpenAI: text-embedding-3-large (3072 dims, +2.29% accuracy)
"""

from typing import List, Optional
import numpy as np

from .config import (
    EMBEDDING_PROVIDER,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_API_KEY
)


class EmbeddingModel:
    """Unified embedding interface."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or EMBEDDING_PROVIDER
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the embedding model."""
        if self.provider == "openai":
            self._init_openai()
        else:
            self._init_local()
    
    def _init_local(self):
        """Initialize local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            print(f"🔧 Loading local embedding model: {LOCAL_EMBEDDING_MODEL}")
            print("   (This may take a while on first run - ~1GB download)")
            self.model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"✅ Loaded embedding model (dim={self.dimension})")

        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers\n"
                "Or set EMBEDDING_PROVIDER=openai to use OpenAI embeddings instead."
            )
        except Exception as e:
            # Handle HuggingFace rate limits, network errors, model download issues
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise RuntimeError(
                    f"HuggingFace rate limit hit when loading {LOCAL_EMBEDDING_MODEL}.\n"
                    "Solutions:\n"
                    "  1. Set EMBEDDING_PROVIDER=openai and provide OPENAI_API_KEY\n"
                    "  2. Set HF_TOKEN environment variable for authenticated access\n"
                    "  3. Wait a few minutes and try again"
                )
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise RuntimeError(
                    f"Network error loading {LOCAL_EMBEDDING_MODEL}.\n"
                    "For cloud deployment, set EMBEDDING_PROVIDER=openai to avoid model downloads."
                )
            raise RuntimeError(f"Failed to load local embedding model: {e}")
    
    def _init_openai(self):
        """Initialize OpenAI embeddings."""
        try:
            from openai import OpenAI

            if not OPENAI_API_KEY or OPENAI_API_KEY in ("your_openai_api_key_here", ""):
                raise ValueError(
                    "OPENAI_API_KEY not configured. "
                    "Set it via environment variable or in the .env file. "
                    f"Current value: {'(empty)' if not OPENAI_API_KEY else OPENAI_API_KEY[:8] + '...'}"
                )

            self.client = OpenAI(api_key=OPENAI_API_KEY)
            # text-embedding-3-large has 3072 dimensions
            self.dimension = 3072 if "large" in OPENAI_EMBEDDING_MODEL else 1536
            print(f"✅ Initialized OpenAI embeddings: {OPENAI_EMBEDDING_MODEL} (dim={self.dimension})")

        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self.provider == "openai":
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts)
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        embeddings = self.model.encode(texts, show_progress_bar=len(texts) > 10)
        return embeddings.tolist()
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        # OpenAI has a limit of 8191 tokens per request
        # Process in batches
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=batch
            )
            embeddings = [e.embedding for e in response.data]
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        embeddings = self.embed([query])
        return embeddings[0]


if __name__ == "__main__":
    # Test embeddings
    model = EmbeddingModel()
    
    test_texts = [
        "What is HARQ in 5G NR?",
        "Network performance monitoring KPIs",
        "3GPP Release 17 specifications"
    ]
    
    embeddings = model.embed(test_texts)
    print(f"\nGenerated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
