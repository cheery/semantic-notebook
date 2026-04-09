"""Wiki bookkeeping — rebuild index.md, append to log.md, sync ChromaDB."""

from datetime import datetime
from pathlib import Path

from notebook.config import NOTES_DIR
from notebook.store import list_notes

SKIP_FILES = {"CLAUDE.md", "index.md", "log.md"}


def rebuild_index() -> int:
    notes = list_notes()
    notes = [n for n in notes if n.path.name not in SKIP_FILES]
    notes.sort(key=lambda n: n.title.lower())

    lines = ["# Index\n"]
    for note in notes:
        lines.append(f"- [{note.title}]({note.path.name})")
    lines.append("")

    (NOTES_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return len(notes)


def append_log(action: str, details: str) -> None:
    log_path = NOTES_DIR / "log.md"
    if not log_path.exists():
        log_path.write_text("# Log\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{timestamp}] {action} | {details}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def sync(message: str | None = None) -> dict:
    # 1. Rebuild index.md
    count = rebuild_index()

    # 2. Append to log
    if message:
        append_log("sync", message)
    else:
        append_log("sync", f"{count} notes indexed")

    # 3. Re-index ChromaDB
    from notebook.index import sync_index
    notes = list_notes()
    notes = [n for n in notes if n.path.name not in SKIP_FILES]
    stats = sync_index(notes)

    return {"notes": count, **stats}
