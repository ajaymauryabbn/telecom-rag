"""Telecom RAG - Configuration Module"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _clean_env(key: str, default: str = None) -> str:
    """Get env var and strip surrounding quotes (handles misconfigured .env files)."""
    val = os.getenv(key, default)
    if val:
        val = val.strip().strip("'\"")
    return val


# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GLOSSARY_DIR = DATA_DIR / "glossary"

# Ensure directories exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, GLOSSARY_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_PROVIDER = _clean_env("LLM_PROVIDER", "openai")
OPENAI_API_KEY = _clean_env("OPENAI_API_KEY")
GOOGLE_API_KEY = _clean_env("GOOGLE_API_KEY") or _clean_env("GEMINI_API_KEY")

# Embedding Configuration
EMBEDDING_PROVIDER = _clean_env("EMBEDDING_PROVIDER", "openai")

# Model names
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.0-flash-lite"  # Upgraded: faster than 1.5-flash
LOCAL_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"  # Upgraded: +2.29% accuracy

# Redis Configuration
REDIS_URL = _clean_env("REDIS_URL", "redis://localhost:6379/0")

# Feature Flags (for cloud deployment)
ENABLE_RERANK = _clean_env("ENABLE_RERANK", "true").lower() == "true"
ENABLE_HYBRID = _clean_env("ENABLE_HYBRID", "true").lower() == "true"
ENABLE_REDIS = _clean_env("ENABLE_REDIS", "true").lower() == "true"

# RAG Configuration (Telco-RAG validated settings)
CHUNK_SIZE = 125  # tokens - optimal for telecom docs
CHUNK_OVERLAP = 25  # tokens
TOP_K_RESULTS = 6  # Optimized: Reduced from 12 for faster responses
CONTEXT_MAX_TOKENS = 1500  # Optimized: Reduced from 2500 for faster LLM

# ChromaDB
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = "telecom_docs"

# Prompt Template (Telco-RAG format with question repetition)
TELECOM_PROMPT_TEMPLATE = """You are a telecom operations expert. Answer the following question accurately and concisely.

[QUESTION]: {question}

[TERMS]: {glossary_terms}

[CONTEXT]: 
{context}

[QUESTION]: {question}

Provide a grounded answer citing specific sources from the context. If the context doesn't contain enough information to answer fully, state the limitations clearly. Format your response with:
1. A clear, direct answer
2. Supporting details from the sources
3. Source citations in [Source: document_name] format"""
