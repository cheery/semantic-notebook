import sys
from pathlib import Path

from notebook.config import NOTES_DIR


def main():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    args = sys.argv[1:]

    if not args:
        print("Notebook — starting TUI (loading embedding model, this may take a moment)...")
        from notebook.app import NotebookApp
        app = NotebookApp()
        app.run()
    elif args[0] == "index":
        from notebook.store import list_notes
        from notebook.index import sync_index
        notes = list_notes()
        print(f"Found {len(notes)} notes")
        stats = sync_index(notes)
        print(f"Indexed: {stats['indexed']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}")
    elif args[0] == "search" and len(args) > 1:
        query = " ".join(args[1:])
        from notebook.search import search
        results = search(query)
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
    elif args[0] == "clusters":
        from notebook.clusters import get_clusters
        clusters = get_clusters()
        if not clusters:
            print("No clusters. Run 'notebook index' first.")
            return
        for c in clusters:
            print(f"\n[{c.label}]")
            for title in c.note_titles:
                print(f"  - {title}")
    elif args[0] == "wiki" and len(args) > 1 and args[1] == "sync":
        from notebook.wiki import sync
        message = " ".join(args[2:]) if len(args) > 2 else None
        stats = sync(message)
        print(f"Notes: {stats['notes']}, Indexed: {stats['indexed']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}")
    else:
        print("Usage: python -m notebook [index | search <query> | clusters | wiki sync [message]]")


if __name__ == "__main__":
    main()
