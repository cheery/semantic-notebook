from textual.widgets import ListView, ListItem, Label
from textual.message import Message

from notebook.store import Note


class NoteSelected(Message):
    def __init__(self, note: Note):
        super().__init__()
        self.note = note


class NoteList(ListView):
    notes: list[Note] = []

    def set_notes(self, notes: list[Note]) -> None:
        self.notes = notes
        self.clear()
        for note in notes:
            item = ListItem(Label(note.title))
            item._note = note
            self.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        note = getattr(event.item, "_note", None)
        if note:
            self.post_message(NoteSelected(note))
