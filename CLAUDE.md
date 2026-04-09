# Notebook Software

Markdown note organization tool with semantic search, auto-clustering, and note linking. Uses embeddinggemma-300m for embeddings and ChromaDB for vector storage. Terminal UI via Textual.

## Running

```bash
python -m notebook            # launch TUI
python -m notebook index      # index all notes into ChromaDB
python -m notebook search "query"  # CLI semantic search
python -m notebook clusters   # show auto-detected topic clusters
```

## Project structure

- `notebook/config.py` — paths, model name, constants
- `notebook/store.py` — markdown file I/O, Note dataclass
- `notebook/embeddings.py` — sentence-transformers model loading and encoding
- `notebook/index.py` — ChromaDB client, collection, upsert/query/sync
- `notebook/search.py` — semantic search (embed query → ChromaDB query)
- `notebook/clusters.py` — KMeans clustering + TF-IDF topic labels
- `notebook/linker.py` — related note suggestions via cosine similarity
- `notebook/app.py` — Textual TUI application
- `notebook/widgets/` — TUI components (note_list, note_viewer, search_bar, link_panel, cluster_view)
- `notes/` — user markdown files (the data)

## Dependencies

Requires: `chromadb`, `sentence-transformers`, `textual`, `rich`, `scikit-learn`, `torch`, `transformers`

Install: `pip install chromadb sentence-transformers textual`

## Key conventions

- Notes are plain `.md` files in `notes/`. Title is extracted from the first `# heading`.
- ChromaDB data persists in `.notebook/chromadb/` — delete to rebuild index from scratch.
- Embedding model is `google/embeddinggemma-300m` (configured in `config.py`).
- Incremental indexing: `sync_index()` compares file mtime to stored metadata, only re-embeds changed files.
- Use `from __future__ import annotations` in modules that use `X | None` type syntax at module level (needed for chromadb/textual compatibility).
- Heavy operations (search, indexing, clustering) run in background threads in the TUI via `@work(thread=True)`.
