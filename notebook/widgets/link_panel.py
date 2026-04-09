from textual.widgets import Static, ListView, ListItem, Label
from textual.containers import Vertical
from textual.message import Message


class RelatedNoteClicked(Message):
    def __init__(self, note_id: str):
        super().__init__()
        self.note_id = note_id


class RelatedNoteList(ListView):
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        note_id = getattr(event.item, "_note_id", None)
        if note_id:
            self.post_message(RelatedNoteClicked(note_id))


class LinkPanel(Vertical):
    def update_links(self, related: list[dict]) -> None:
        self.remove_children()
        if not related:
            self.mount(Static("[bold]Related Notes[/bold]"))
            self.mount(Static("  (none)"))
            return
        self.mount(Static("[bold]Related Notes[/bold]"))
        lst = RelatedNoteList()
        self.mount(lst)
        for r in related:
            title = r.get("metadata", {}).get("title", r["id"])
            score = r.get("score", 0)
            note_id = r.get("id", "")
            item = ListItem(Label(f"{score:.0%}  {title}"))
            item._note_id = note_id
            lst.append(item)
