# Semantic Notebook — Specification

A semi-formal description of what this program does, structured as models, commands, pipelines, and constraints. Written to be understandable by both humans and LLMs.

## Models

### Note
The core data unit. A markdown file on disk.

```
Note {
    path: Path          -- filesystem location under notes/
    title: String       -- extracted from first "# heading" line, fallback to filename
    content: String     -- raw markdown text
    mtime: Float        -- file modification timestamp
}
```

**Invariants:**
- Every note is a `.md` file in `notes/` (flat, no subdirectories)
- First line that matches `# ...` is the title
- Title never empty (fallback to stem of filename)

### VectorIndex (ChromaDB)
A persistent vector store in `.notebook/chromadb/`.

```
VectorIndex {
    entries: Map<note_id, {
        embedding: Vec<Float>      -- from embeddinggemma-300m, cosine-normalized
        document: String           -- raw note content
        metadata: {title, path, mtime}
    }>
}
```

**Invariants:**
- `note_id` = relative path from `notes/` (e.g. `"docker-basics.md"`)
- Each note has exactly one embedding
- `mtime` in metadata tracks which version is indexed

### TUIState
The interactive state held in memory by the terminal application.

```
TUIState {
    current_note: Note | None
    history: List<Note>
    mode: "browse" | "search" | "clusters"
    note_list: List<Note>          -- all notes known to the TUI
}
```

**Invariants:**
- `current_note` is always an element of `note_list` or `history`
- `history` never contains duplicates (navigating to the same note appends to history without duplicating)

### WikiIndex
Auto-generated bookkeeping files.

```
WikiIndex {
    index.md: Markdown             -- sorted list of links to all notes (except CLAUDE.md, index.md, log.md)
    log.md: Markdown               -- append-only timestamped entries
}
```

## Pipelines

These are the stateless, deterministic data flows. Given the same input, they always produce the same output.

### Embedding Pipeline
```
text -> embeddinggemma-300m -> cosine-normalized Vec<Float>
```
Batch variant: `List<text> -> List<Vec<Float>>`

### Search Pipeline
```
query string -> embed -> VectorIndex.query -> List<{note_id, distance, metadata, document}>
                                              -> score = 1 - distance
                                              -> snippet = first non-heading line, truncated 120 chars
```

### Indexing Pipeline
```
notes/ directory -> list all .md files -> compare mtime with VectorIndex
    -> changed notes: embed + upsert into VectorIndex
    -> deleted notes: remove from VectorIndex
    -> unchanged notes: skip
```

### Clustering Pipeline
```
VectorIndex.get_all_embeddings -> pick k via silhouette score (2..10)
    -> KMeans(k) -> group notes by cluster
    -> TF-IDF on each cluster's documents -> label = top 3 keywords
```

### Related Notes Pipeline
```
note_id -> VectorIndex.get_embedding(note_id)
    -> VectorIndex.query(embedding, n+1) -> filter out self -> take n
    -> score = 1 - distance
```

### Sync Pipeline
```
notes/ -> rebuild index.md (sorted by title, exclude CLAUDE.md/index.md/log.md)
       -> append timestamp to log.md
       -> run Indexing Pipeline
```

### Build Pipeline
```
notes/ + VectorIndex + clusters -> render each note as HTML page
    -> sidebar grouped by cluster
    -> each page shows related notes
    -> output to site/
```

## Commands

Actions that modify state. These are the seams — where things interact and where concurrency matters.

### CLI Commands (stateless, run and exit)
| Command | What it does |
|---------|-------------|
| `index` | Run Indexing Pipeline on all notes |
| `search "q"` | Run Search Pipeline, print results |
| `clusters` | Run Clustering Pipeline, print results |
| `sync [msg]` | Run Sync Pipeline |
| `edit <file>` | Open built-in editor, write to file on save |
| `build` | Run Build Pipeline, write site/ |

### TUI Commands (stateful, long-running)
| Command | Trigger | State change |
|---------|---------|-------------|
| navigate(note) | click note / follow link | push current to history, set current_note |
| go_back | press `b` | pop history, set current_note |
| search(query) | press `/`, type, enter | set mode=search, run Search Pipeline, display results |
| edit | press `e` | suspend TUI, open editor, reload note on return |
| new_note | press `n` | create file, reload list, open editor |
| reindex | press `r` | run Indexing Pipeline, update status |
| show_clusters | press `c` | set mode=clusters, run Clustering Pipeline, display |

## Constraints

### Consistency constraints (must always hold)
1. Every `.md` file in `notes/` can be represented as a Note
2. VectorIndex entries correspond 1:1 with notes that exist on disk (after sync)
3. WikiIndex.index.md contains a link to every note except CLAUDE.md, index.md, log.md
4. TUIState.note_list reflects the files in notes/ at the time of last load

### Operational constraints (how the system behaves)
5. Embedding model is loaded lazily, once, cached in memory (global singleton)
6. ChromaDB client is initialized lazily with thread-safe locking
7. Heavy operations (search, indexing, clustering) run in background threads in the TUI
8. File writes are single syscalls (atomic on Linux for reasonable file sizes)

## Seams — where things can go wrong

### 1. TUI vs. external writers (concurrent access)

**Who:** TUI (long-running process) vs. LLM / external editor / CLI sync (separate process)

**The problem:** TUI loads notes into memory on mount. External process modifies or deletes files. TUI has no filesystem watcher. Staleness is the default, not the exception.

**What breaks:**
- TUI shows stale content after external edit (until manual re-index)
- History stack contains Notes whose files may no longer exist (ghost notes)
- note_list may not reflect files added or removed by external processes

**Current mitigation:** None, beyond user pressing `r` to re-index.

**Possible fix:** `watchdog` (inotify) on notes/ → reload affected notes on file change events.

### 2. Sync vs. TUI index state

**Who:** `python -m notebook sync` (CLI) vs. TUI running concurrently

**The problem:** Both write to ChromaDB. ChromaDB PersistentClient is designed for single-process access. Concurrent writes from two processes could corrupt the index.

**Current mitigation:** None. It works by luck (users don't typically run both simultaneously).

**Possible fix:** File-based lock (`.notebook/lock`) or restrict to single writer.

### 3. Embedding model memory

**Who:** Any module that calls `embed_text` or `embed_batch`

**The problem:** Model is a global singleton, ~600MB in memory. Loaded once per process. If TUI and CLI run simultaneously, two copies load. Not a correctness issue, just resource waste.

**Current mitigation:** Lazy loading. Acceptable for now.

## File formats

### Note file
```
# Title Here

Free-form markdown content. Can include:
- [links](other-note.md) to other notes
- Any standard markdown (code blocks, lists, tables, etc.)
```

### index.md (auto-generated, do not edit by hand)
```
# Index

- [Note Title](filename.md)
- [Another Title](another.md)
```

### log.md (auto-generated, append-only)
```
# Log

## [2026-04-12 14:30] sync | added docker notes
## [2026-04-12 15:00] sync | 12 notes indexed
```
