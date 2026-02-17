"""Telecom RAG - Vector Store Module

ChromaDB-based vector store for document storage and retrieval.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, TOP_K_RESULTS
from .data_loader import Document
from .embeddings import EmbeddingModel


class TelecomVectorStore:
    """ChromaDB vector store for telecom documents."""
    
    def __init__(self, collection_name: Optional[str] = None):
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        self.embedding_model = EmbeddingModel()
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Ensure persist directory exists
            CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            
            # Initialize client with persistence
            self.client = chromadb.PersistentClient(
                path=str(CHROMA_PERSIST_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            print(f"✅ ChromaDB initialized: {self.collection_name}")
            print(f"   Documents in collection: {self.collection.count()}")
            
        except ImportError:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
    
    def add_documents(self, documents: List[Document], batch_size: int = 100):
        """Add documents to the vector store."""
        if not documents:
            print("⚠️ No documents to add")
            return
        
        print(f"📥 Adding {len(documents)} documents to vector store...")
        
        # Use global document counter to avoid ID collisions
        global_doc_idx = 0
        total_batches = (len(documents) - 1) // batch_size + 1
        
        for batch_num, i in enumerate(range(0, len(documents), batch_size), 1):
            batch = documents[i:i + batch_size]
            
            # Prepare batch data with unique global IDs
            ids = [f"doc_{global_doc_idx + j}" for j in range(len(batch))]
            global_doc_idx += len(batch)
            
            contents = [doc.content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            
            # Generate embeddings with retry logic
            try:
                embeddings = self.embedding_model.embed(contents)
            except Exception as e:
                print(f"⚠️ Error generating embeddings for batch {batch_num}: {e}")
                print("   Retrying with smaller batch...")
                # Retry with individual documents
                embeddings = []
                for content in contents:
                    try:
                        emb = self.embedding_model.embed([content])[0]
                        embeddings.append(emb)
                    except Exception as inner_e:
                        print(f"   Skipping document due to error: {inner_e}")
                        continue
                if not embeddings:
                    print(f"   Skipping entire batch {batch_num}")
                    continue
            
            # Add to collection
            self.collection.add(
                ids=ids[:len(embeddings)],
                embeddings=embeddings,
                documents=contents[:len(embeddings)],
                metadatas=metadatas[:len(embeddings)]
            )
            
            print(f"   Added batch {batch_num}/{total_batches}")
        
        print(f"✅ Vector store now contains {self.collection.count()} documents")
    
    def search(
        self, 
        query: str, 
        top_k: int = TOP_K_RESULTS,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of results with content, metadata, and similarity score
        """
        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)
        
        # Build query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filter_dict:
            query_params["where"] = filter_dict
        
        # Execute query
        results = self.collection.query(**query_params)
        
        # Format results
        formatted_results = []
        
        if results["documents"] and results["documents"][0]:
            for idx in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                    "distance": results["distances"][0][idx] if results["distances"] else 0,
                    "similarity": 1 - results["distances"][0][idx] if results["distances"] else 1
                })
        
        return formatted_results
    
    def search_by_category(
        self, 
        query: str, 
        category: str,
        top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """Search within a specific category."""
        return self.search(query, top_k, filter_dict={"category": category})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        count = self.collection.count()
        
        # Get category distribution if possible
        try:
            sample = self.collection.peek(min(100, count))
            categories = {}
            if sample["metadatas"]:
                for meta in sample["metadatas"]:
                    cat = meta.get("category", "unknown")
                    categories[cat] = categories.get(cat, 0) + 1
        except:
            categories = {}
        
        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "categories_sample": categories
        }
    
    def clear(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"🗑️ Cleared collection: {self.collection_name}")


if __name__ == "__main__":
    # Test vector store
    store = TelecomVectorStore()
    
    # Add sample documents
    test_docs = [
        Document(
            content="HARQ (Hybrid Automatic Repeat Request) is a combination of high-rate forward error correction and ARQ error-control.",
            metadata={"source": "test", "category": "5g_terminology"}
        ),
        Document(
            content="5G NR supports both FDD and TDD modes of operation for flexible spectrum usage.",
            metadata={"source": "test", "category": "5g_specifications"}
        )
    ]
    
    store.add_documents(test_docs)
    
    # Test search
    results = store.search("What is HARQ?")
    print("\n🔍 Search results for 'What is HARQ?':")
    for r in results:
        print(f"  - {r['content'][:100]}... (similarity: {r['similarity']:.3f})")
    
    print("\n📊 Stats:", store.get_stats())
