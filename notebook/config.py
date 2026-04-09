from pathlib import Path

# Directories
NOTES_DIR = Path("notes")
DATA_DIR = Path(".notebook")
CHROMADB_DIR = DATA_DIR / "chromadb"

# Embedding model via sentence-transformers
EMBEDDING_MODEL = "google/embeddinggemma-300m"

# ChromaDB
COLLECTION_NAME = "notes"

# Clustering
MAX_CLUSTERS = 10
