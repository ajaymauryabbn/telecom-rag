# Data Files Setup

The Telecom RAG system requires large data files that are not included in the Git repository due to size constraints.

## 📦 Required Data Files

The following files need to be generated or downloaded:

1. **`data/chroma_db.tar.gz`** (615MB) - Compressed vector database
2. **`data/bm25_index.pkl`** (12MB) - BM25 search index  
3. **`data/processed/processed_documents.json`** - Processed documents

## 🚀 Setup Options

### Option 1: Download from Cloud Storage (Recommended for Production)

The data files are available in the deployed Cloud Run instance. For local development:

```bash
# Download from Google Cloud Storage (if configured)
gsutil cp gs://telecom-rag-data/chroma_db.tar.gz data/
gsutil cp gs://telecom-rag-data/bm25_index.pkl data/
```

### Option 2: Regenerate Locally (Recommended for Development)

Generate the data files from the raw documents:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the data processing script
python scripts/download_data.py

# This will:
# 1. Process all documents in data/raw/
# 2. Generate embeddings
# 3. Create ChromaDB vector store
# 4. Build BM25 index
# 5. Create chroma_db.tar.gz for deployment
```

**Time**: ~15-30 minutes (depending on your machine and OpenAI API rate limits)

### Option 3: Use Docker (Easiest)

The Docker container automatically extracts `chroma_db.tar.gz` if present:

```bash
# Build and run with Docker
docker-compose up

# The container will extract the data files automatically
```

## 📁 Directory Structure

After setup, your `data/` directory should look like:

```
data/
├── raw/                          # Source documents (included in Git)
│   ├── alarm_docs/
│   ├── config_docs/
│   ├── kpi_docs/
│   └── ...
├── chroma_db/                    # Extracted vector DB (auto-generated)
├── chroma_db.tar.gz             # Compressed vector DB (for deployment)
├── bm25_index.pkl               # BM25 search index
├── processed/
│   └── processed_documents.json
└── glossary/                     # Telecom glossary (included in Git)
    └── telecom_glossary.json
```

## ⚠️ Important Notes

- **Git ignores**: `chroma_db/`, `chroma_db.tar.gz`, `bm25_index.pkl`, and `processed/` are in `.gitignore`
- **Cloud deployment**: The `chroma_db.tar.gz` is extracted automatically in the Docker container
- **Local development**: You can regenerate all data files from the raw documents
- **Size**: Total data files ~650MB (too large for Git, hence excluded)

## 🔧 Troubleshooting

### "ChromaDB not found" error

```bash
# Regenerate the vector database
python scripts/download_data.py
```

### "BM25 index not found" error

The BM25 index is generated automatically when you run the app for the first time if it doesn't exist.

### Docker deployment

The Dockerfile automatically handles data extraction:

```dockerfile
# Extract compressed chroma_db if present
RUN if [ -f data/chroma_db.tar.gz ]; then \
    tar -xzf data/chroma_db.tar.gz -C ./; \
    fi
```

## 📊 Data File Details

| File | Size | Purpose | Regenerate Time |
|------|------|---------|----------------|
| `chroma_db.tar.gz` | 615MB | Vector database (compressed) | N/A (archive) |
| `chroma_db/` | 873MB | Vector database (extracted) | 15-30 min |
| `bm25_index.pkl` | 12MB | Keyword search index | 2-5 min |
| `processed_documents.json` | ~5MB | Processed documents | 2-5 min |

---

**For production deployment**: The data files are already included in the Cloud Run deployment and work out of the box.

**For local development**: Follow Option 2 above to regenerate from source documents.
