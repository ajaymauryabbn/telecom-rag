#!/usr/bin/env python3
"""
Download Telecom Data Script
=============================

Downloads real telecom data from various sources:
1. TeleQnA dataset from HuggingFace
2. Telecom glossary terms
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import TelecomDataLoader
from src.glossary import TelecomGlossary
from src.vector_store import TelecomVectorStore


def download_and_ingest():
    """Download data and ingest into vector store."""
    print("=" * 60)
    print("📡 Telecom RAG - Data Download & Ingestion")
    print("=" * 60)
    
    # Step 1: Save glossary
    print("\n📖 Step 1: Saving telecom glossary...")
    glossary = TelecomGlossary()
    glossary.save_glossary()
    print(f"   Saved {len(glossary.glossary)} terms")
    
    # Step 2: Load TeleQnA and other data
    print("\n📥 Step 2: Loading telecom documents...")
    loader = TelecomDataLoader()
    documents = loader.load_all_data()
    
    if not documents:
        print("❌ No documents loaded. Check your internet connection.")
        return False
    
    # Step 3: Ingest into vector store
    print("\n🗄️ Step 3: Ingesting into vector store...")
    vector_store = TelecomVectorStore()
    
    # Clear existing data
    vector_store.clear()
    
    # Add documents
    vector_store.add_documents(documents)
    
    # Save processed data for caching
    loader.save_processed_data()
    
    # Print stats
    stats = vector_store.get_stats()
    print("\n" + "=" * 60)
    print("✅ Data ingestion complete!")
    print("=" * 60)
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Collection: {stats['collection_name']}")
    print("\n🚀 You can now run: streamlit run app.py")
    
    return True


if __name__ == "__main__":
    success = download_and_ingest()
    sys.exit(0 if success else 1)
