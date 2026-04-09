from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Markdown
from textual import work

from notebook.config import NOTES_DIR
from notebook.store import list_notes, read_note, Note
from notebook.widgets.note_list import NoteList, NoteSelected
from notebook.widgets.note_viewer import NoteViewer
from notebook.widgets.search_bar import SearchBar, SearchSubmitted
from notebook.widgets.link_panel import LinkPanel, RelatedNoteClicked


class NotebookApp(App):
    CSS = """
    #sidebar {
        width: 30;
        border-right: solid $accent;
    }
    #main {
        width: 1fr;
    }
    #right-panel {
        width: 30;
        border-left: solid $accent;
    }
    #search-bar {
        dock: top;
        margin: 0 1;
    }
    #note-list {
        height: 1fr;
    }
    #viewer {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    #status {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    #mode-label {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("left", "focus_left", "Left pane", show=False),
        Binding("right", "focus_right", "Right pane", show=False),
        Binding("slash", "focus_search", "Search", show=True),
        Binding("e", "edit_note", "Edit", show=True),
        Binding("b", "go_back", "Back", show=True),
        Binding("n", "new_note", "New Note", show=True),
        Binding("r", "reindex", "Re-index", show=True),
        Binding("c", "show_clusters", "Clusters", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("down", "scroll_page_down", "Page Down", show=True),
        Binding("up", "scroll_page_up", "Page Up", show=True),
    ]

    PANELS = ["#note-list", "#viewer", "#link-panel"]

    TITLE = "Notebook"

    current_note: Note | None = None
    history: list[Note] = []
    mode: str = "browse"  # browse | search | clusters

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield SearchBar(id="search-bar")
                yield NoteList(id="note-list")
            with Vertical(id="main"):
                yield Label("Browse", id="mode-label")
                yield NoteViewer(id="viewer")
            with Vertical(id="right-panel"):
                yield LinkPanel(id="link-panel")
        yield Static("Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.history = []
        self.load_notes()
        self.navigate_to_file("index.md")

    def load_notes(self) -> None:
        notes = list_notes()
        note_list = self.query_one("#note-list", NoteList)
        note_list.set_notes(notes)
        self.set_status(f"{len(notes)} notes loaded")

    def set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.query_one("#mode-label", Label).update(mode.capitalize())

    # --- Navigation ---

    def navigate_to_note(self, note: Note, push_history: bool = True) -> None:
        if push_history and self.current_note is not None:
            self.history.append(self.current_note)
        self.current_note = note
        viewer = self.query_one("#viewer", NoteViewer)
        viewer.show_note(note.title, note.content)
        self.set_mode("browse")
        self.set_status(note.title)
        self.load_related(note)

    def navigate_to_file(self, filename: str) -> bool:
        path = NOTES_DIR / filename
        if not path.exists():
            return False
        try:
            note = read_note(path)
            self.navigate_to_note(note)
            return True
        except Exception:
            return False

    def action_go_back(self) -> None:
        if self.history:
            note = self.history.pop()
            self.navigate_to_note(note, push_history=False)
        else:
            self.set_status("No history")

    # --- Event handlers ---

    def on_note_selected(self, message: NoteSelected) -> None:
        self.navigate_to_note(message.note)

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        href = event.href
        if href.endswith(".md"):
            # Strip any path prefix, resolve relative to notes dir
            filename = Path(href).name
            if self.navigate_to_file(filename):
                event.prevent_default()
                return
        self.set_status(f"Link: {href}")

    def on_related_note_clicked(self, message: RelatedNoteClicked) -> None:
        self.navigate_to_file(message.note_id)

    def _current_panel_index(self) -> int:
        focused = self.focused
        if focused is None:
            return -1
        for i, selector in enumerate(self.PANELS):
            try:
                widget = self.query_one(selector)
                if focused is widget or focused.is_child_of(widget):
                    return i
            except Exception:
                continue
        return -1

    def _focus_panel(self, index: int) -> None:
        selector = self.PANELS[index % len(self.PANELS)]
        try:
            widget = self.query_one(selector)
            # For the link panel, try to focus the ListView inside it
            if selector == "#link-panel":
                from notebook.widgets.link_panel import RelatedNoteList
                try:
                    lst = widget.query_one(RelatedNoteList)
                    lst.focus()
                    return
                except Exception:
                    pass
            widget.focus()
        except Exception:
            pass

    def action_focus_left(self) -> None:
        idx = self._current_panel_index()
        if idx > 0:
            self._focus_panel(idx - 1)
        elif idx == -1:
            self._focus_panel(0)

    def action_focus_right(self) -> None:
        idx = self._current_panel_index()
        if idx < len(self.PANELS) - 1:
            self._focus_panel(idx + 1)
        elif idx == -1:
            self._focus_panel(0)

    @work(thread=True)
    def load_related(self, note: Note) -> None:
        try:
            from notebook.linker import find_related
            related = find_related(note.rel_path, n=5)
            self.app.call_from_thread(self._update_links, related)
        except Exception:
            self.app.call_from_thread(self._update_links, [])

    def _update_links(self, related: list[dict]) -> None:
        panel = self.query_one("#link-panel", LinkPanel)
        panel.update_links(related)

    # --- Search ---

    def on_search_submitted(self, message: SearchSubmitted) -> None:
        self.set_mode("search")
        self.set_status(f"Searching: {message.query}")
        self.run_search(message.query)

    @work(thread=True)
    def run_search(self, query: str) -> None:
        try:
            from notebook.search import search
            results = search(query, n=20)
            self.app.call_from_thread(self._show_search_results, results)
        except Exception as e:
            self.app.call_from_thread(self.set_status, f"Search error: {e}")

    def _show_search_results(self, results: list[dict]) -> None:
        viewer = self.query_one("#viewer", NoteViewer)
        if not results:
            viewer.update("*No results found*")
            self.set_status("No results")
            return
        md = "# Search Results\n\n"
        for r in results:
            title = r.get("metadata", {}).get("title", r["id"])
            score = r.get("score", 0)
            snippet = r.get("snippet", "")
            note_id = r.get("id", "")
            md += f"### [{title}]({note_id}) ({score:.0%})\n{snippet}\n\n---\n\n"
        viewer.update(md)
        self.set_status(f"{len(results)} results")

    # --- Actions ---

    def action_scroll_page_down(self) -> None:
        self.query_one("#viewer", NoteViewer).scroll_page_down()

    def action_scroll_page_up(self) -> None:
        self.query_one("#viewer", NoteViewer).scroll_page_up()

    def action_focus_search(self) -> None:
        self.query_one("#search-bar", SearchBar).focus()

    def action_edit_note(self) -> None:
        if self.current_note is None:
            self.set_status("No note selected")
            return
        path = self.current_note.path
        self._open_editor(str(path))

    def _open_editor(self, filepath: str) -> None:
        import os
        import subprocess
        import sys
        editor = os.environ.get("EDITOR", "")
        with self.suspend():
            if editor:
                subprocess.call([editor, filepath])
            else:
                subprocess.call([sys.executable, "-m", "notebook.editor", filepath])
        # Reload the note after editing
        try:
            note = read_note(Path(filepath))
            self.navigate_to_note(note, push_history=False)
            self.load_notes()
            self.set_status(f"Edited {note.title}")
        except Exception:
            pass

    def action_new_note(self) -> None:
        import time
        name = time.strftime("%Y%m%d-%H%M%S")
        path = NOTES_DIR / f"{name}.md"
        from notebook.store import write_note
        write_note(path, f"# New Note\n\nWrite your note here.\n")
        self.load_notes()
        self._open_editor(str(path))

    def action_reindex(self) -> None:
        self.set_status("Re-indexing...")
        self.do_reindex()

    @work(thread=True)
    def do_reindex(self) -> None:
        try:
            from notebook.index import sync_index
            notes = list_notes()
            stats = sync_index(notes)
            msg = f"Indexed: {stats['indexed']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}"
            self.app.call_from_thread(self.set_status, msg)
        except Exception as e:
            self.app.call_from_thread(self.set_status, f"Index error: {e}")

    def action_show_clusters(self) -> None:
        self.set_mode("clusters")
        self.set_status("Computing clusters...")
        self.do_clusters()

    @work(thread=True)
    def do_clusters(self) -> None:
        try:
            from notebook.clusters import get_clusters
            clusters = get_clusters()
            self.app.call_from_thread(self._show_clusters, clusters)
        except Exception as e:
            self.app.call_from_thread(self.set_status, f"Cluster error: {e}")

    def _show_clusters(self, clusters) -> None:
        viewer = self.query_one("#viewer", NoteViewer)
        if not clusters:
            viewer.update("*No clusters. Index some notes first (press `r`).*")
            self.set_status("No clusters")
            return
        md = "# Topic Clusters\n\n"
        for c in clusters:
            md += f"### {c.label}\n"
            for title, note_id in zip(c.note_titles, c.note_ids):
                md += f"- [{title}]({note_id})\n"
            md += "\n"
        viewer.update(md)
        self.set_status(f"{len(clusters)} clusters found")
