from dataclasses import dataclass
from pathlib import Path
import re

from notebook.config import NOTES_DIR


@dataclass
class Note:
    path: Path
    title: str
    content: str
    mtime: float

    @property
    def rel_path(self) -> str:
        try:
            return str(self.path.relative_to(NOTES_DIR))
        except ValueError:
            return str(self.path)


def extract_title(content: str, path: Path) -> str:
    for line in content.splitlines():
        m = re.match(r"^#\s+(.+)", line)
        if m:
            return m.group(1).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def read_note(path: Path) -> Note:
    content = path.read_text(encoding="utf-8")
    title = extract_title(content, path)
    mtime = path.stat().st_mtime
    return Note(path=path, title=title, content=content, mtime=mtime)


def list_notes(directory: Path | None = None) -> list[Note]:
    d = directory or NOTES_DIR
    notes = []
    for p in sorted(d.rglob("*.md")):
        try:
            notes.append(read_note(p))
        except Exception:
            continue
    return notes


def write_note(path: Path, content: str) -> Note:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return read_note(path)


def delete_note(path: Path) -> None:
    path.unlink(missing_ok=True)
