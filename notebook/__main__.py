import argparse
import sys
from pathlib import Path

from notebook.config import NOTES_DIR


def cmd_tui(args):
    """Launch the interactive terminal UI."""
    print("Notebook — starting TUI (loading embedding model, this may take a moment)...")
    from notebook.app import NotebookApp
    app = NotebookApp()
    app.run()


def cmd_index(args):
    """Re-index all notes into ChromaDB."""
    from notebook.store import list_notes
    from notebook.index import sync_index
    notes = list_notes()
    print(f"Found {len(notes)} notes")
    stats = sync_index(notes)
    print(f"Indexed: {stats['indexed']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}")


def cmd_search(args):
    """Search notes by meaning."""
    query = " ".join(args.query)
    from notebook.search import search
    results = search(query, n=args.n)
    if not results:
        print("No results found.")
        return
    for r in results:
        title = r.get("metadata", {}).get("title", r["id"])
        score = r.get("score", 0)
        snippet = r.get("snippet", "")
        print(f"  {score:.0%}  {title}")
        if snippet:
            print(f"       {snippet}")
        print()


def cmd_clusters(args):
    """Show auto-detected topic clusters."""
    from notebook.clusters import get_clusters
    clusters = get_clusters()
    if not clusters:
        print("No clusters. Run 'python -m notebook index' first.")
        return
    for c in clusters:
        print(f"\n[{c.label}]")
        for title in c.note_titles:
            print(f"  - {title}")


def cmd_sync(args):
    """Sync wiki bookkeeping after editing notes."""
    from notebook.wiki import sync
    message = " ".join(args.message) if args.message else None
    stats = sync(message)
    print(f"Notes: {stats['notes']}, Indexed: {stats['indexed']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}")


def cmd_edit(args):
    """Open a note in the built-in editor."""
    path = Path(args.file)
    if not path.suffix:
        path = NOTES_DIR / f"{args.file}.md"
    from notebook.editor.app import EditorApp
    app = EditorApp(str(path))
    app.run()


def cmd_build(args):
    """Generate a static website from the notes."""
    from notebook.build import build_site
    print("Building static site...")
    stats = build_site(title=args.title)
    print(f"Generated {stats['pages']} pages ({stats['clusters']} topic clusters)")
    print(f"Output: site/")
    print(f"Preview: python -m http.server -d site 8000")


def main():
    parser = argparse.ArgumentParser(
        prog="notebook",
        description="Markdown note organization with semantic search, clustering, and linking.",
    )
    sub = parser.add_subparsers(dest="command")

    # Default (no subcommand) launches TUI — handled below

    sub.add_parser(
        "tui",
        help="Launch the interactive terminal UI",
        description="Opens the full notebook browser with note list, markdown viewer, "
        "semantic search, cluster view, and related notes panel. "
        "Use this as the main way to browse and organize your notes.",
    )

    sub.add_parser(
        "index",
        help="Re-index all notes into ChromaDB",
        description="Scans the notes/ directory, embeds each note using embeddinggemma-300m, "
        "and stores the embeddings in ChromaDB. Only re-embeds notes that changed "
        "since the last index (based on file modification time). "
        "Run this after adding or editing notes outside the TUI.",
    )

    p_search = sub.add_parser(
        "search",
        help="Semantic search across notes",
        description="Find notes by meaning, not just keywords. The query is embedded and "
        "compared against all indexed notes using cosine similarity. "
        "Example: 'python -m notebook search container deployment' finds notes "
        "about Docker, Kubernetes, etc. even if they don't contain those exact words.",
    )
    p_search.add_argument("query", nargs="+", help="Search query (natural language)")
    p_search.add_argument("-n", type=int, default=10, help="Number of results (default: 10)")

    sub.add_parser(
        "clusters",
        help="Show auto-detected topic clusters",
        description="Groups all indexed notes into topic clusters using KMeans on their "
        "embeddings, then labels each cluster with its top keywords (TF-IDF). "
        "Useful for seeing the shape of your knowledge base and finding notes "
        "that belong together. Requires notes to be indexed first.",
    )

    p_sync = sub.add_parser(
        "sync",
        help="Update index.md, log.md, and ChromaDB after editing notes",
        description="The bookkeeping command. Rebuilds index.md from all notes, appends an "
        "entry to log.md, and re-indexes changed notes in ChromaDB. "
        "Run this after creating, editing, or deleting notes — it keeps "
        "everything consistent in one step. Optionally add a message to "
        "describe what changed (recorded in the log).",
    )
    p_sync.add_argument("message", nargs="*", help="Optional log message (e.g. 'added docker notes')")

    p_edit = sub.add_parser(
        "edit",
        help="Open a note in the built-in editor",
        description="Opens the specified file in the built-in vim-like editor. "
        "The editor has three modes: NORMAL (navigation), INSERT (typing), "
        "and COMMAND (:w save, :q quit, :wq save+quit). "
        "A help bar at the bottom always shows available keys. "
        "If the file doesn't exist, it is created. "
        "You can pass just a name (e.g. 'docker-basics') and .md is added automatically.",
    )
    p_edit.add_argument("file", help="Path or name of the note to edit")

    p_build = sub.add_parser(
        "build",
        help="Generate a static website from the notes",
        description="Builds a self-contained static website in the site/ directory. "
        "Each note becomes an HTML page with rendered markdown. Notes are "
        "grouped by topic cluster in the sidebar, and each page shows related "
        "notes ranked by similarity. The output is ready to publish — drop it "
        "on GitHub Pages, Netlify, or any static host. No JavaScript required. "
        "Preview locally with: python -m http.server -d site 8000",
    )
    p_build.add_argument("--title", default="Semantic Notebook", help="Site title (default: Semantic Notebook)")

    args = parser.parse_args()

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    if args.command is None or args.command == "tui":
        cmd_tui(args)
    elif args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "clusters":
        cmd_clusters(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "edit":
        cmd_edit(args)
    elif args.command == "build":
        cmd_build(args)


if __name__ == "__main__":
    main()
