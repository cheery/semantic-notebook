# Notes Wiki — Schema

You maintain this wiki. The user tells you what to add or gives you a file to ingest. You write and update the markdown notes.

## Structure

- Each note is a `.md` file in `notes/`. Flat directory, no nesting.
- Filename: lowercase, hyphens, short. e.g. `python-async.md`, `docker-basics.md`
- First line is always `# Title`
- Link between notes with standard markdown: `[related topic](other-note.md)`

## Operations

**Add/update**: User tells you something → find the right note to put it in, or create a new one. Update cross-links in related notes. Then run: `python -m notebook sync`

**Ingest**: User gives you a file path → read it, extract key information, write it into new or existing notes as appropriate. Then run: `python -m notebook sync`

**Query**: User asks a question → use `python -m notebook search "query"` to find relevant notes, read them, answer.

The `sync` command updates `index.md`, appends to `log.md`, and re-indexes ChromaDB embeddings. Always run it after changing notes.

## Conventions

- Keep notes focused on one topic. Split if a note grows beyond ~100 lines.
- Cross-link generously. If note A mentions a concept that has its own note B, link to it.
- Don't duplicate — if info belongs in an existing note, update that note.
- `index.md` and `log.md` are managed by the tool. Don't edit them by hand.
